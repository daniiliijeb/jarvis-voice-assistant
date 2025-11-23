from __future__ import annotations

import logging
import tempfile
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import pyttsx3

try:
    from elevenlabs.client import ElevenLabs
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False

# Альтернативные способы воспроизведения для Windows
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False


class TTSBackend(ABC):
    @abstractmethod
    def speak(self, text: str) -> None:  # pragma: no cover - interface
        raise NotImplementedError


@dataclass
class Pyttsx3Backend(TTSBackend):
    rate: Optional[int] = None
    voice_name_contains: Optional[str] = None

    def __post_init__(self) -> None:
        self.engine = pyttsx3.init()
        if self.rate is not None:
            self.engine.setProperty("rate", self.rate)
        if self.voice_name_contains:
            for voice in self.engine.getProperty("voices"):
                name = getattr(voice, "name", "") or ""
                if self.voice_name_contains.lower() in name.lower():
                    self.engine.setProperty("voice", voice.id)
                    break

    def speak(self, text: str) -> None:
        if not text:
            return
        self.engine.say(text)
        self.engine.runAndWait()


@dataclass
class ElevenLabsBackend(TTSBackend):
    """Backend для ElevenLabs - реалистичный голос Jarvis
    
    Популярные voice_id для Jarvis:
    - pNInz6obpgDQGcFmaJgB (Adam) - глубокий, уверенный, по умолчанию
    - ErXwobaYiN019PkySvjV (Antoni) - чёткий, быстрый
    - MF3mGyEYCl7XYWbV9V6O (Elli) - женский, профессиональный
    - TxGEqnHWrfWFTfGW9XjX (Josh) - молодой, энергичный
    - VR6AewLTigWG4xSOukaG (Arnold) - мощный, авторитетный
    - ThT5KcBeYPX3keUQqHPh (Daniel) - британский, элегантный
    - EXAVITQu4vr4xnSDxMaL (Bella) - женский, дружелюбный
    - JBFqnCBsd6RMkjVDRZzb (Rachel) - женский, многоязычный
    
    Получить список всех голосов: https://elevenlabs.io/app/voices
    """
    api_key: str
    voice_id: str = "pNInz6obpgDQGcFmaJgB"  # Adam - по умолчанию
    model: str = "eleven_turbo_v2_5"  # Быстрая модель для мгновенной реакции

    def __post_init__(self) -> None:
        if not ELEVENLABS_AVAILABLE:
            raise ImportError("elevenlabs не установлен. Установите: pip install elevenlabs")
        self.client = ElevenLabs(api_key=self.api_key)

    def speak(self, text: str) -> None:
        if not text:
            return
        try:
            # Генерируем аудио с настройками для быстрого ответа
            # convert() возвращает генератор, нужно собрать все байты
            audio_generator = self.client.text_to_speech.convert(
                text=text,
                voice_id=self.voice_id,
                model_id=self.model,
                output_format="mp3_44100_128"
            )
            # Собираем все байты из генератора
            audio_bytes = b"".join(audio_generator)
            # Воспроизводим аудио (Windows-совместимый способ)
            self._play_audio_windows(audio_bytes)
        except Exception as e:
            # Fallback на pyttsx3 при ошибке
            import logging
            logger = logging.getLogger("jarvis")
            logger.warning(f"Ошибка ElevenLabs, используем fallback: {e}")
            fallback = Pyttsx3Backend(rate=180)
            fallback.speak(text)
    
    def _play_audio_windows(self, audio: bytes) -> None:
        """Воспроизведение аудио на Windows без зависимости от ffplay"""
        import logging
        import time
        logger = logging.getLogger("jarvis")
        
        # Способ 1: pygame.mixer (работает на Windows без ffmpeg для воспроизведения MP3)
        if PYGAME_AVAILABLE:
            tmp_path = None
            try:
                # Инициализируем mixer если ещё не инициализирован
                if not pygame.mixer.get_init():
                    pygame.mixer.init()
                
                # Сохраняем MP3 во временный файл
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                    tmp.write(audio)
                    tmp_path = tmp.name
                
                # Воспроизводим через pygame.mixer
                pygame.mixer.music.load(tmp_path)
                pygame.mixer.music.play()
                # Ждём завершения воспроизведения
                while pygame.mixer.music.get_busy():
                    time.sleep(0.05)  # Уменьшено для быстрой реакции
                
                # Останавливаем и освобождаем файл
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
                time.sleep(0.05)  # Уменьшено для быстрой реакции
                
                # Теперь безопасно удаляем файл
                if tmp_path:
                    try:
                        Path(tmp_path).unlink(missing_ok=True)
                    except Exception as e:
                        logger.debug(f"Не удалось удалить временный файл: {e}")
                
                return
            except Exception as e:
                logger.debug(f"pygame.mixer не сработал: {e}")
                # Пытаемся удалить файл даже при ошибке
                if tmp_path:
                    try:
                        time.sleep(0.1)  # Уменьшено для быстрой реакции
                        Path(tmp_path).unlink(missing_ok=True)
                    except Exception:
                        pass  # Игнорируем ошибки удаления
        
        # Способ 2: Попытка использовать встроенный play() из elevenlabs (если ffmpeg есть)
        try:
            from elevenlabs import play
            play(audio)
            return
        except Exception as e:
            logger.debug(f"elevenlabs.play не сработал: {e}")
        
        # Способ 3: Fallback на pyttsx3
        raise RuntimeError("Не удалось воспроизвести аудио через ElevenLabs")


@dataclass
class TextToSpeech:
    """Обёртка для синтеза речи с поддержкой асинхронного озвучивания"""
    
    backend: TTSBackend
    _current_thread: Optional[threading.Thread] = field(default=None, init=False, repr=False)
    _stop_event: threading.Event = field(default_factory=threading.Event, init=False, repr=False)
    _logger: logging.Logger = field(default_factory=lambda: logging.getLogger("jarvis"), init=False, repr=False)
    
    def speak(self, text: str) -> None:
        """Синхронное озвучивание (блокирует выполнение)"""
        self.backend.speak(text)
    
    def speak_async(self, text: str) -> None:
        """Асинхронное озвучивание (не блокирует выполнение)
        
        Запускает озвучивание в отдельном потоке, позволяя Jarvis
        продолжать слушать команды во время воспроизведения звука.
        """
        if not text:
            return
        
        # Останавливаем предыдущее воспроизведение если оно ещё идёт
        self.stop()
        
        # Запускаем новое озвучивание в отдельном потоке
        def _speak_thread():
            try:
                self._logger.debug(f"TTS: Начало асинхронного озвучивания: '{text[:50]}...'")
                self.backend.speak(text)
                self._logger.debug("TTS: Асинхронное озвучивание завершено")
            except Exception as e:
                self._logger.error(f"TTS: Ошибка при асинхронном озвучивании: {e}", exc_info=True)
            finally:
                # Очищаем ссылку на поток после завершения
                if threading.current_thread() is self._current_thread:
                    self._current_thread = None
        
        self._current_thread = threading.Thread(target=_speak_thread, daemon=True, name="TTS-Thread")
        self._current_thread.start()
        self._logger.debug("TTS: Поток озвучивания запущен")
    
    def stop(self) -> None:
        """Останавливает текущее воспроизведение (если идёт)"""
        if self._current_thread and self._current_thread.is_alive():
            self._logger.debug("TTS: Остановка текущего воспроизведения...")
            # Для pygame.mixer останавливаем музыку
            if PYGAME_AVAILABLE:
                try:
                    pygame.mixer.music.stop()
                except Exception:
                    pass
            # Для pyttsx3 останавливаем движок
            if isinstance(self.backend, Pyttsx3Backend):
                try:
                    self.backend.engine.stop()
                except Exception:
                    pass
            # Устанавливаем флаг остановки
            self._stop_event.set()
            # Ждём завершения потока (с таймаутом)
            self._current_thread.join(timeout=0.5)
            if self._current_thread.is_alive():
                self._logger.warning("TTS: Поток не завершился в течение таймаута")
            self._stop_event.clear()
            self._logger.debug("TTS: Воспроизведение остановлено")
    
    def is_speaking(self) -> bool:
        """Проверяет, идёт ли сейчас озвучивание"""
        return self._current_thread is not None and self._current_thread.is_alive()



