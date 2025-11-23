from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from jarvis.app.config import AppConfig
from jarvis.app.logger import get_logger
from jarvis.core.command_router import CommandRouter
from jarvis.core.health import run_healthcheck
from jarvis.core.performance import PerformanceStats
from jarvis.core.record import RecordConfig, SpeechListener
from jarvis.core.speech_to_text import SpeechToText, GoogleSTTBackend, WhisperSTTBackend
from jarvis.core.text_to_speech import Pyttsx3Backend, TextToSpeech, ElevenLabsBackend
from jarvis.core.semantic_router import SemanticRouter
from jarvis.core.context_aware import ContextAware
from jarvis.core.updater import Updater
from jarvis.memory.memory import SimpleMemory


class JarvisRuntime:
    # Центральный объект, объединяющий подсистемы: конфиг, логи, производительность, здоровье, память, команды
    def __init__(self, config: Optional[AppConfig] = None) -> None:
        self.logger = get_logger(config or AppConfig.load())
        self.logger.info("=" * 60)
        self.logger.info("JarvisRuntime: Инициализация системы...")
        
        self.config = config or AppConfig.load()
        self.logger.info(f"JarvisRuntime: Конфигурация загружена. Режим: {self.config.mode}, Версия: {self.config.version}")
        
        self.perf = PerformanceStats()
        self.logger.debug("JarvisRuntime: PerformanceStats инициализирован")
        
        self.memory = SimpleMemory()
        self.logger.debug("JarvisRuntime: SimpleMemory инициализирован")
        
        self.router = CommandRouter(runtime=self)
        self.logger.debug("JarvisRuntime: CommandRouter инициализирован")
        
        # Инициализация SemanticRouter для умного понимания команд
        self.logger.info("JarvisRuntime: Инициализация SemanticRouter...")
        try:
            self.semantic = SemanticRouter()
            self._setup_semantic_intents()
            self.logger.info("JarvisRuntime: SemanticRouter успешно инициализирован")
        except Exception as e:
            self.logger.warning(f"JarvisRuntime: Ошибка инициализации SemanticRouter: {e}", exc_info=True)
            self.logger.warning("JarvisRuntime: Продолжаю работу без SemanticRouter (будут использоваться только ключевые слова)")
            self.semantic = None
        
        # Инициализация ContextAware для контекстно-зависимых команд
        self.logger.info("JarvisRuntime: Инициализация ContextAware...")
        try:
            self.context_aware = ContextAware()
            self.logger.info("JarvisRuntime: ContextAware успешно инициализирован")
        except Exception as e:
            self.logger.warning(f"JarvisRuntime: Ошибка инициализации ContextAware: {e}", exc_info=True)
            self.logger.warning("JarvisRuntime: Продолжаю работу без ContextAware (контекстные команды недоступны)")
            self.context_aware = None
        
        # Инициализация Updater для проверки обновлений
        self.logger.info("JarvisRuntime: Инициализация Updater...")
        try:
            self.updater = Updater(
                config_dir=self.config.data_dir,
                current_version=self.config.version,
                repo_owner=self.config.github_repo_owner,
                repo_name=self.config.github_repo_name
            )
            self.logger.info("JarvisRuntime: Updater успешно инициализирован")
        except Exception as e:
            self.logger.warning(f"JarvisRuntime: Ошибка инициализации Updater: {e}", exc_info=True)
            self.logger.warning("JarvisRuntime: Продолжаю работу без Updater (проверка обновлений недоступна)")
            self.updater = None
        
        # Инициализация Updater для проверки обновлений
        self.logger.info("JarvisRuntime: Инициализация Updater...")
        try:
            github_repo = self.config.github_repo or os.getenv("JARVIS_GITHUB_REPO")
            if github_repo:
                # Обновляем репозиторий в Updater
                self.updater = Updater(root_dir=self.config.root_dir)
                self.updater.GITHUB_REPO = github_repo
                self.updater.GITHUB_API_URL = f"https://api.github.com/repos/{github_repo}/releases/latest"
                self.logger.info(f"JarvisRuntime: Updater инициализирован для репозитория: {github_repo}")
            else:
                self.logger.warning("JarvisRuntime: GitHub репозиторий не указан. Проверка обновлений недоступна.")
                self.logger.warning("JarvisRuntime: Укажите JARVIS_GITHUB_REPO=username/repo-name")
                self.updater = None
        except Exception as e:
            self.logger.warning(f"JarvisRuntime: Ошибка инициализации Updater: {e}", exc_info=True)
            self.logger.warning("JarvisRuntime: Продолжаю работу без Updater (проверка обновлений недоступна)")
            self.updater = None
        
        # Используем ElevenLabs если есть API ключ, иначе fallback на pyttsx3
        if self.config.elevenlabs_api_key:
            try:
                voice_id = self.config.elevenlabs_voice_id or "pNInz6obpgDQGcFmaJgB"  # Adam - по умолчанию
                self.logger.info(f"JarvisRuntime: Инициализация ElevenLabs TTS (voice_id: {voice_id})...")
                self.tts = TextToSpeech(backend=ElevenLabsBackend(
                    api_key=self.config.elevenlabs_api_key,
                    voice_id=voice_id
                ))
                self.logger.info(f"JarvisRuntime: ElevenLabs TTS успешно инициализирован (voice_id: {voice_id})")
            except Exception as e:
                self.logger.error(f"JarvisRuntime: Ошибка инициализации ElevenLabs: {e}", exc_info=True)
                self.logger.warning("JarvisRuntime: Переключаюсь на pyttsx3 TTS...")
                self.tts = TextToSpeech(backend=Pyttsx3Backend(rate=180))
                self.logger.info("JarvisRuntime: pyttsx3 TTS инициализирован")
        else:
            self.logger.info("JarvisRuntime: ElevenLabs API ключ не найден, использую pyttsx3 TTS")
            self.tts = TextToSpeech(backend=Pyttsx3Backend(rate=180))
            self.logger.info("JarvisRuntime: pyttsx3 TTS инициализирован")
        
        # Инициализация STT с выбором движка
        self.logger.info(f"JarvisRuntime: Инициализация SpeechToText (движок: {self.config.stt_engine})...")
        try:
            if self.config.stt_engine == "whisper":
                try:
                    self.logger.info("JarvisRuntime: Использую Whisper STT (локальное распознавание)")
                    stt_backend = WhisperSTTBackend(
                        model_size="base",  # Можно настроить через переменные окружения
                        device="cpu",  # cpu или cuda
                        compute_type="int8",  # int8 для быстрой работы
                        language="ru"
                    )
                    self.stt = SpeechToText(backend=stt_backend)
                    self.logger.info("JarvisRuntime: Whisper STT успешно инициализирован")
                except Exception as e:
                    self.logger.error(f"JarvisRuntime: Ошибка инициализации Whisper: {e}", exc_info=True)
                    self.logger.warning("JarvisRuntime: Переключаюсь на Google STT...")
                    self.stt = SpeechToText(backend=GoogleSTTBackend())
                    self.logger.info("JarvisRuntime: Google STT инициализирован (fallback)")
            else:
                # По умолчанию Google STT
                self.logger.info("JarvisRuntime: Использую Google STT (онлайн распознавание)")
                self.stt = SpeechToText(backend=GoogleSTTBackend())
                self.logger.info("JarvisRuntime: Google STT инициализирован")
        except Exception as e:
            self.logger.error(f"JarvisRuntime: Критическая ошибка инициализации STT: {e}", exc_info=True)
            # Fallback на Google STT
            self.stt = SpeechToText(backend=GoogleSTTBackend())
            self.logger.warning("JarvisRuntime: Использую Google STT (fallback после ошибки)")
        
        self.logger.info("JarvisRuntime: Инициализация SpeechListener...")
        self.listener = SpeechListener(config=RecordConfig())
        self.logger.info("JarvisRuntime: SpeechListener инициализирован")
        
        self._ensure_dirs()
        self.logger.info("JarvisRuntime: Все директории проверены/созданы")
        
        # Предзагрузка модулей для ускорения работы
        self.logger.info("JarvisRuntime: Предзагрузка модулей для ускорения...")
        
        # Предзагрузка STT — холодный старт распознавания
        try:
            if isinstance(self.stt.backend, WhisperSTTBackend):
                # Для Whisper предзагружаем модель
                _ = self.stt.backend._get_model()
                self.logger.debug("JarvisRuntime: Whisper модель предзагружена")
            elif isinstance(self.stt.backend, GoogleSTTBackend):
                # Для Google просто проверяем recognizer
                _ = self.stt.backend.recognizer
                self.logger.debug("JarvisRuntime: Google STT recognizer предзагружен")
        except Exception as e:
            self.logger.warning(f"JarvisRuntime: Ошибка предзагрузки STT: {e}")
        
        # Предзагрузка TTS — холодный старт ElevenLabs/pyttsx3
        try:
            self.tts.speak(" ")  # Минимальная фраза для прогрева
            self.logger.debug("JarvisRuntime: TTS предзагружен (прогрет)")
        except Exception as e:
            self.logger.warning(f"JarvisRuntime: Ошибка предзагрузки TTS: {e}")
        
        self.logger.info("JarvisRuntime: Предзагрузка завершена")
        self.logger.info("=" * 60)
        self.logger.info("JarvisRuntime: Инициализация завершена успешно")
        self.logger.info("=" * 60)

    def _ensure_dirs(self) -> None:
        self.config.logs_dir.mkdir(parents=True, exist_ok=True)
        self.config.data_dir.mkdir(parents=True, exist_ok=True)

    def _setup_semantic_intents(self) -> None:
        """Заполняет базу намерений для SemanticRouter примерами команд"""
        if not self.semantic:
            return
        
        # Браузер - много вариаций
        self.semantic.add_intent("browser", [
            "открой браузер",
            "запусти браузер",
            "открой интернет",
            "включи браузер",
            "покажи браузер",
            "выведи браузер",
            "запусти хром",
            "открой хром",
            "включи хром",
            "выведи гугл",
            "покажи окно интернет-поиска",
            "мне бы веб-страничку",
            "открой веб-браузер",
            "запусти веб-браузер",
            "открой chrome",
            "запусти chrome",
            "browser",
            "open browser",
            "launch browser",
        ])
        
        # YouTube
        self.semantic.add_intent("youtube", [
            "открой youtube",
            "запусти youtube",
            "открой ютуб",
            "запусти ютуб",
            "включи youtube",
            "включи ютуб",
            "покажи youtube",
            "покажи ютуб",
            "открой видео на youtube",
            "открой видео на ютуб",
            "запусти видео на youtube",
            "запусти видео на ютуб",
            "включи видео на youtube",
            "включи видео на ютуб",
            "youtube",
            "open youtube",
            "launch youtube",
        ])
        
        # Google
        self.semantic.add_intent("google", [
            "открой google",
            "запусти google",
            "открой гугл",
            "запусти гугл",
            "включи google",
            "включи гугл",
            "покажи google",
            "покажи гугл",
            "google",
            "open google",
            "launch google",
        ])
        
        # Загрузки
        self.semantic.add_intent("downloads", [
            "открой загрузки",
            "открой папку загрузки",
            "покажи загрузки",
            "загрузки",
            "downloads",
            "открой downloads",
            "покажи downloads",
        ])
        
        # Рабочий стол
        self.semantic.add_intent("desktop", [
            "открой рабочий стол",
            "покажи рабочий стол",
            "рабочий стол",
            "desktop",
            "открой desktop",
            "покажи desktop",
        ])
        
        # Документы
        self.semantic.add_intent("documents", [
            "открой документы",
            "открой папку документы",
            "покажи документы",
            "документы",
            "documents",
            "открой documents",
        ])
        
        # Калькулятор
        self.semantic.add_intent("calculator", [
            "открой калькулятор",
            "запусти калькулятор",
            "включи калькулятор",
            "калькулятор",
            "calculator",
            "calc",
            "открой calc",
        ])
        
        # Блокнот
        self.semantic.add_intent("notepad", [
            "открой блокнот",
            "запусти блокнот",
            "включи блокнот",
            "блокнот",
            "notepad",
            "открой notepad",
        ])
        
        # Проводник
        self.semantic.add_intent("explorer", [
            "открой проводник",
            "запусти проводник",
            "открой файлы",
            "покажи файлы",
            "проводник",
            "explorer",
            "открой explorer",
        ])
        
        self.logger.info(f"SemanticRouter: Загружено {len(self.semantic.commands)} намерений")

    def dump_performance_json(self) -> None:
        # Сохраняем агрегированные метрики производительности в logs/performance.json
        snapshot = self.perf.snapshot()
        avg_stt = snapshot.get("stt_ms", {}).get("avg_ms", 0.0)
        avg_tts = snapshot.get("tts_ms", {}).get("avg_ms", 0.0)
        cmd_latency = snapshot.get("command_ms", {}).get("avg_ms", 0.0)
        payload = {
            "avg_stt": round(avg_stt / 1000.0, 3) if avg_stt else 0.0,  # секунды
            "avg_tts": round(avg_tts / 1000.0, 3) if avg_tts else 0.0,
            "cmd_latency": round(cmd_latency / 1000.0, 3) if cmd_latency else 0.0,
            "fps_screen": 0,  # зарезервировано под будущий трекер FPS
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        dst = self.config.logs_dir / "performance.json"
        try:
            dst.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            self.logger.error("Не удалось записать performance.json", exc_info=True)

    def restart_runtime(self) -> None:
        # Переинициализация подсистем без завершения процесса
        try:
            self.logger.info("Перезапуск подсистем JarvisRuntime...")
            self.perf = PerformanceStats()
            self.memory = SimpleMemory()
            self.router = CommandRouter(runtime=self)
            # Используем ElevenLabs если есть API ключ
            if self.config.elevenlabs_api_key:
                try:
                    voice_id = self.config.elevenlabs_voice_id or "pNInz6obpgDQGcFmaJgB"
                    self.tts = TextToSpeech(backend=ElevenLabsBackend(
                        api_key=self.config.elevenlabs_api_key,
                        voice_id=voice_id
                    ))
                except Exception:
                    self.tts = TextToSpeech(backend=Pyttsx3Backend(rate=180))
            else:
                self.tts = TextToSpeech(backend=Pyttsx3Backend(rate=180))
            # Переинициализация STT с тем же движком
            if self.config.stt_engine == "whisper":
                try:
                    stt_backend = WhisperSTTBackend(
                        model_size="base",
                        device="cpu",
                        compute_type="int8",
                        language="ru"
                    )
                    self.stt = SpeechToText(backend=stt_backend)
                except Exception:
                    self.stt = SpeechToText(backend=GoogleSTTBackend())
            else:
                self.stt = SpeechToText(backend=GoogleSTTBackend())
            self.listener = SpeechListener(config=RecordConfig())
            # Переинициализация SemanticRouter
            try:
                self.semantic = SemanticRouter()
                self._setup_semantic_intents()
            except Exception as e:
                self.logger.warning(f"Не удалось переинициализировать SemanticRouter: {e}")
                self.semantic = None
            # Переинициализация ContextAware
            try:
                self.context_aware = ContextAware()
            except Exception as e:
                self.logger.warning(f"Не удалось переинициализировать ContextAware: {e}")
                self.context_aware = None
            # Переинициализация Updater
            try:
                github_repo = self.config.github_repo or os.getenv("JARVIS_GITHUB_REPO")
                if github_repo:
                    self.updater = Updater(root_dir=self.config.root_dir)
                    self.updater.GITHUB_REPO = github_repo
                    self.updater.GITHUB_API_URL = f"https://api.github.com/repos/{github_repo}/releases/latest"
            except Exception as e:
                self.logger.warning(f"Не удалось переинициализировать Updater: {e}")
                self.updater = None
        except Exception:
            self.logger.error("Не удалось перезапустить подсистемы", exc_info=True)

    def run_health_once_and_print(self) -> int:
        # Выполнить healthcheck и вывести краткий отчёт в консоль
        report = run_healthcheck().as_dict()
        mapping = {
            "microphone": "микрофон",
            "tts": "TTS",
            "stt": "STT",
            "internet": "интернет",
            "pyaudio": "PyAudio",
            "gpu": "GPU",
            "ffmpeg": "ffmpeg",
        }
        for key in ["microphone", "tts", "stt", "internet", "pyaudio", "gpu", "ffmpeg"]:
            item = report.get(key, {})
            ok = item.get("ok") == "True"
            msg = f"{mapping[key]} {'OK' if ok else 'НЕ ОК'}"
            print(msg)  # noqa: T201
        return 0

    def check_periodic_health(self) -> None:
        # Самопроверка раз в 7 дней, при проблеме — озвучить предупреждение
        marker = self.config.data_dir / "last_healthcheck.txt"
        need_check = True
        if marker.exists():
            try:
                ts = marker.read_text(encoding="utf-8").strip()
                last_dt = datetime.fromisoformat(ts)
                if datetime.now() - last_dt < timedelta(days=7):
                    need_check = False
            except Exception:
                need_check = True
        if not need_check:
            return

        report = run_healthcheck().as_dict()
        bad = []
        for k in ["microphone", "tts", "stt", "internet", "pyaudio"]:
            if report.get(k, {}).get("ok") != "True":
                bad.append(k)

        try:
            marker.write_text(datetime.now().isoformat(), encoding="utf-8")
        except Exception:
            pass

        if bad:
            try:
                from jarvis.core.jarvis_voice import JarvisVoice
                self.tts.speak("Сэр, у меня проблема со звуком. Рекомендую проверить драйвер.")
            except Exception:
                self.logger.error("Ошибка при попытке озвучить предупреждение.", exc_info=True)
    
    def _check_updates_background(self) -> None:
        """Проверка обновлений в фоновом режиме при старте"""
        if not self.updater:
            return
        
        try:
            # Проверяем обновления асинхронно (не блокируем запуск)
            import threading
            
            def check_thread():
                try:
                    update_info = self.updater.check_for_updates(timeout=5.0)
                    if update_info.available:
                        self.logger.info(
                            f"Updater: Доступно обновление {update_info.latest_version}! "
                            f"Текущая версия: {update_info.current_version}"
                        )
                        # Озвучиваем уведомление асинхронно
                        try:
                            message = (
                                f"Сэр, доступно обновление до версии {update_info.latest_version}. "
                                f"Скажите 'Джарвис обнови' для установки."
                            )
                            if hasattr(self, 'tts'):
                                self.tts.speak_async(message)
                        except Exception:
                            pass
                except Exception as e:
                    self.logger.debug(f"Ошибка фоновой проверки обновлений: {e}")
            
            thread = threading.Thread(target=check_thread, daemon=True, name="UpdateChecker")
            thread.start()
            self.logger.debug("JarvisRuntime: Запущена фоновая проверка обновлений")
        except Exception as e:
            self.logger.debug(f"Ошибка запуска проверки обновлений: {e}")
        
        try:
            update_info = self.updater.check_update(force=True)
            if not update_info.has_update:
                return False, f"Обновление не требуется. Используется последняя версия {update_info.latest_version}."
            
            # Выполняем обновление
            success, message = self.updater.update()
            return success, message
        except Exception as e:
            self.logger.error(f"Ошибка проверки/обновления: {e}", exc_info=True)
            return False, f"Ошибка: {e}"


