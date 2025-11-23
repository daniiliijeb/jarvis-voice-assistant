from __future__ import annotations

import logging
from dataclasses import dataclass

from jarvis.app.config import AppConfig
from jarvis.core.command_router import CommandRouter
from jarvis.core.record import RecordConfig, SpeechListener
from jarvis.core.speech_to_text import SpeechToText
from jarvis.core.text_to_speech import TextToSpeech, Pyttsx3Backend
from jarvis.core.wake_word import has_wake_word, extract_command
from jarvis.core.jarvis_voice import JarvisVoice
from jarvis.memory.memory import SimpleMemory
from jarvis.core.performance import PerformanceStats, timer
from pathlib import Path
import json
import time


@dataclass
class Conversation:
    config: AppConfig
    logger: logging.Logger
    perf_external: PerformanceStats | None = None
    perf_callback: callable | None = None
    tts_external: TextToSpeech | None = None
    stt_external: SpeechToText | None = None

    def __post_init__(self) -> None:
        # Инициализация основных компонентов диалога
        self.listener = SpeechListener(config=RecordConfig())
        self._last_tts_time = 0  # Время последнего TTS для фильтрации
        self._last_command = ""  # Последняя выполненная команда для фильтрации повторов
        # Используем STT из runtime если передан, иначе создаём свой (Google по умолчанию)
        if self.stt_external is not None:
            self.stt = self.stt_external
        else:
            from jarvis.core.speech_to_text import GoogleSTTBackend
            self.stt = SpeechToText(backend=GoogleSTTBackend())
        # Используем TTS из runtime если передан, иначе создаём свой
        if self.tts_external is not None:
            self.tts = self.tts_external
        else:
            self.tts = TextToSpeech(backend=Pyttsx3Backend(rate=180))
        self.router = CommandRouter()
        self.memory = SimpleMemory()
        self.perf = self.perf_external if self.perf_external is not None else PerformanceStats()

    def _interactive_loop(self) -> None:
        self.logger.info("=" * 60)
        self.logger.info("Conversation: Вход в режим INTERACTIVE")
        self.logger.info(f"Conversation: Режим профилирования: {self.config.profile}")
        self.logger.info(f"Conversation: Уровень логирования: {self.config.log_level}")
        self.logger.info("=" * 60)
        
        self.logger.info("Conversation: Начинаю калибровку микрофона...")
        try:
            self.listener.calibrate()
            self.logger.info("Conversation: Калибровка микрофона успешно завершена")
        except Exception as e:
            self.logger.error(f"Conversation: Ошибка калибровки микрофона: {e}", exc_info=True)
            self.logger.warning("Conversation: Продолжаю работу без калибровки...")
        
        self.logger.info("Conversation: Готов к работе. Слушаю команды...")
        while True:
            try:
                self.logger.debug("Conversation: Ожидание аудио от микрофона...")
                audio = self.listener.listen_once()
                if audio is None:
                    self.logger.debug("Conversation: Аудио не получено (тайм-аут или ошибка)")
                    continue
                self.logger.debug("Conversation: Аудио получено, начинаю распознавание...")
                try:
                    if self.config.profile:
                        with timer("stt_ms", lambda n, d: self._on_perf(n, d)):
                            text = self.stt.recognize(audio)
                    else:
                        text = self.stt.recognize(audio)
                except Exception as e:
                    self.logger.warning(f"Ошибка распознавания речи: {e}")
                    continue
                if not text:
                    self.logger.debug("Текст не распознан.")
                    continue
                
                # Фильтрация: игнорируем текст, который похож на ответы Jarvis или повтор команды
                text_lower = text.lower().strip()
                time_since_tts = time.time() - self._last_tts_time if hasattr(self, '_last_tts_time') else 999
                
                # Список слов, которые указывают на ответ Jarvis
                jarvis_response_words = [
                    "открываю", "запускаю", "закрываю", "включаю", "выключаю",
                    "готово", "выполнено", "сделано", "приятного просмотра"
                ]
                
                # Проверка 1: Игнорируем команды в течение 5 секунд после TTS, если они содержат слова из ответов Jarvis
                if time_since_tts < 5.0:
                    if any(word in text_lower for word in jarvis_response_words):
                        self.logger.debug(f"Conversation: Игнорирую распознанный текст (содержит слова ответа Jarvis, время после TTS: {time_since_tts:.1f}с): '{text}'")
                        continue
                    
                    # Проверка 2: Игнорируем команды, которые заканчиваются на "сэр" и были распознаны сразу после TTS
                    if text_lower.endswith("сэр") or " сэр" in text_lower:
                        self.logger.debug(f"Conversation: Игнорирую распознанный текст (заканчивается на 'сэр', время после TTS: {time_since_tts:.1f}с): '{text}'")
                        continue
                    
                    # Проверка 3: Игнорируем повтор последней команды в течение 5 секунд
                    if hasattr(self, '_last_command') and self._last_command:
                        # Нормализуем команды для сравнения (убираем "сэр" и лишние слова)
                        normalized_text = text_lower.replace(" сэр", "").replace("сэр", "").strip()
                        normalized_last = self._last_command.lower().replace(" сэр", "").replace("сэр", "").strip()
                        
                        # Проверяем похожесть команд (если содержат одинаковые ключевые слова)
                        text_words = set(normalized_text.split())
                        last_words = set(normalized_last.split())
                        common_words = text_words & last_words
                        
                        # Если есть общие значимые слова (не предлоги/местоимения)
                        significant_words = {"браузер", "youtube", "калькулятор", "открой", "открывай", "запускай", "запусти"}
                        if common_words & significant_words:
                            self.logger.debug(f"Conversation: Игнорирую распознанный текст (повтор команды, время после TTS: {time_since_tts:.1f}с): '{text}'")
                            continue
                
                # Проверка 4: Игнорируем, если TTS говорит прямо сейчас
                if self.tts.is_speaking():
                    if any(word in text_lower for word in jarvis_response_words) or text_lower.endswith("сэр"):
                        self.logger.debug(f"Conversation: Игнорирую распознанный текст (TTS говорит сейчас): '{text}'")
                        continue
                
                self.logger.info(f"Conversation: Распознано: '{text}'")
                self.memory.add_user(text)
                total_messages = len(self.memory.user_history) + len(self.memory.assistant_history)
                self.logger.debug(f"Conversation: Текст добавлен в память. Всего сообщений: {total_messages}")
                if has_wake_word(text):
                    # Останавливаем предыдущее воспроизведение при новой команде
                    if self.tts.is_speaking():
                        self.logger.debug("Conversation: Останавливаю предыдущее воспроизведение для новой команды")
                        self.tts.stop()
                    
                    # Пытаемся извлечь команду из той же фразы
                    cmd_text = extract_command(text)
                    if not cmd_text:
                        # Если команды нет в фразе, ждём следующую
                        try:
                            # Быстрый ответ "Да, сэр." вместо "Слушаю, сэр"
                            quick_response = "Да, сэр."
                            # Используем асинхронное озвучивание - не блокируем цикл
                            self.tts.speak_async(quick_response)
                            self._last_tts_time = time.time()  # Запоминаем время TTS
                            self.logger.debug("Conversation: Быстрый ответ запущен асинхронно")
                        except Exception as e:
                            self.logger.warning(f"Ошибка TTS: {e}")
                        self.logger.debug("Обнаружено ключевое слово. Ожидание команды...")
                        audio_cmd = self.listener.listen_once()
                        if audio_cmd is None:
                            self.logger.debug("Тайм-аут ожидания команды.")
                            continue
                        try:
                            if self.config.profile:
                                with timer("stt_ms", lambda n, d: self._on_perf(n, d)):
                                    cmd_text = self.stt.recognize(audio_cmd)
                            else:
                                cmd_text = self.stt.recognize(audio_cmd)
                        except Exception as e:
                            self.logger.warning(f"Ошибка распознавания команды: {e}")
                            continue
                        if not cmd_text:
                            self.logger.debug("Команда не распознана.")
                            continue
                    else:
                        self.logger.info(f"Conversation: Команда извлечена из фразы: '{cmd_text}'")
                    self.logger.info(f"Conversation: Выполняю команду: '{cmd_text}'")
                    # Сохраняем последнюю команду для фильтрации повторов
                    self._last_command = cmd_text
                    try:
                        if self.config.profile:
                            with timer("command_ms", lambda n, d: self._on_perf(n, d)):
                                response = self.router.handle(cmd_text)
                        else:
                            response = self.router.handle(cmd_text)
                    except Exception as e:
                        self.logger.error(f"Ошибка выполнения команды: {e}", exc_info=True)
                        response = JarvisVoice.error_general()
                    if response:
                        self.logger.info(f"Conversation: Получен ответ от команды: '{response}'")
                        self.memory.add_assistant(response)
                        total_messages = len(self.memory.user_history) + len(self.memory.assistant_history)
                        self.logger.debug(f"Conversation: Ответ добавлен в память. Всего сообщений: {total_messages}")
                        try:
                            self.logger.debug("Conversation: Начинаю асинхронное озвучивание ответа...")
                            # Используем асинхронное озвучивание - не блокируем цикл
                            # Jarvis продолжит слушать команды во время воспроизведения
                            self.tts.speak_async(response)
                            self._last_tts_time = time.time()  # Запоминаем время TTS
                            self.logger.debug("Conversation: Асинхронное озвучивание запущено, продолжаю слушать команды")
                        except Exception as e:
                            self.logger.error(f"Conversation: Ошибка TTS при озвучивании ответа: {e}", exc_info=True)
                else:
                    # Если нет wake word, но есть команда - выполняем напрямую
                    self.logger.debug(f"Conversation: Wake word не обнаружен, пробую выполнить команду напрямую: '{text}'")
                    # Сохраняем последнюю команду для фильтрации повторов
                    self._last_command = text
                    try:
                        response = self.router.handle(text)
                        if response:
                            self.logger.info(f"Conversation: Команда выполнена напрямую, ответ: '{response}'")
                            self.memory.add_assistant(response)
                            try:
                                self.logger.debug("Conversation: Начинаю асинхронное озвучивание ответа...")
                                # Используем асинхронное озвучивание - не блокируем цикл
                                self.tts.speak_async(response)
                                self._last_tts_time = time.time()  # Запоминаем время TTS
                                self.logger.debug("Conversation: Асинхронное озвучивание запущено, продолжаю слушать команды")
                            except Exception as e:
                                self.logger.error(f"Conversation: Ошибка TTS при озвучивании: {e}", exc_info=True)
                        else:
                            self.logger.debug(f"Conversation: Команда '{text}' не вернула ответа")
                    except Exception as e:
                        self.logger.error(f"Conversation: Ошибка обработки команды '{text}': {e}", exc_info=True)
            except KeyboardInterrupt:
                self.logger.info("=" * 60)
                self.logger.info("Conversation: Остановлено пользователем (KeyboardInterrupt)")
                self.logger.info("Conversation: Выход из интерактивного режима")
                self.logger.info("=" * 60)
                break
            except Exception as e:
                self.logger.error("=" * 60)
                self.logger.error(f"Conversation: КРИТИЧЕСКАЯ ОШИБКА в цикле: {e}", exc_info=True)
                self.logger.error("Conversation: Продолжаю работу после ошибки...")
                self.logger.error("=" * 60)
                # Продолжаем работу после ошибки
                continue

    def _cli_loop(self) -> None:
        self.logger.info("CLI режим. Введите текст и нажмите Enter. Ctrl+C для выхода.")
        while True:
            try:
                text = input("> ").strip()  # noqa: PGH001
            except (EOFError, KeyboardInterrupt):
                self.logger.info("Выход из CLI режима")
                break
            except Exception as e:
                self.logger.error(f"Ошибка ввода: {e}")
                continue
            if not text:
                continue
            try:
                if has_wake_word(text):
                    print("Слушаю, сэр")  # noqa: T201
                    try:
                        cmd = input("Команда: ").strip()  # noqa: PGH001
                    except (EOFError, KeyboardInterrupt):
                        break
                    if not cmd:
                        continue
                    try:
                        response = self.router.handle(cmd)
                        if response:
                            print(response)  # noqa: T201
                    except Exception as e:
                        self.logger.error(f"Ошибка выполнения команды: {e}", exc_info=True)
                        print(f"Ошибка: {e}")  # noqa: T201
                else:
                    try:
                        response = self.router.handle(text)
                        if response:
                            print(response)  # noqa: T201
                    except Exception as e:
                        self.logger.error(f"Ошибка обработки команды: {e}", exc_info=True)
                        print(f"Ошибка: {e}")  # noqa: T201
            except Exception as e:
                self.logger.error(f"Критическая ошибка в CLI цикле: {e}", exc_info=True)
                continue

    def run(self) -> None:
        if self.config.interactive_mode:
            self._interactive_loop()
        else:
            self._cli_loop()

    def _on_perf(self, name: str, duration_ms: float) -> None:
        self.perf.record(name, duration_ms)
        # Периодически выводим средние значения по метрикам
        if self.config.profile and self.perf.counts.get(name, 0) % 10 == 0:
            snapshot = self.perf.snapshot().get(name)
            if snapshot:
                self.logger.info(f"Производительность {name}: среднее {snapshot['avg_ms']} мс за {int(snapshot['count'])} вызовов")
                if self.perf_callback:
                    try:
                        self.perf_callback()
                    except Exception:
                        self.logger.debug("Ошибка коллбэка профилирования", exc_info=True)
                # Сохраняем агрегированную статистику в JSON
                try:
                    all_stats = self.perf.snapshot()
                    avg_stt = all_stats.get("stt_ms", {}).get("avg_ms", 0.0)
                    avg_tts = all_stats.get("tts_ms", {}).get("avg_ms", 0.0)
                    avg_cmd = all_stats.get("command_ms", {}).get("avg_ms", 0.0)
                    out = {
                        "avg_stt": round(float(avg_stt) / 1000.0, 3),  # сек
                        "avg_tts": round(float(avg_tts) / 1000.0, 3),
                        "cmd_latency": round(float(avg_cmd) / 1000.0, 3),
                        "fps_screen": 0,
                        "timestamp": __import__("datetime").datetime.utcnow().strftime("%Y-%m-%d"),
                    }
                    path = self.config.logs_dir / "performance.json"
                    Path(path).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
                except Exception:
                    self.logger.exception("Не удалось записать performance.json")


