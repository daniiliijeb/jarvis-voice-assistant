from __future__ import annotations

import logging
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import speech_recognition as sr

# Проверка доступности FasterWhisper
try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False


@dataclass
class STTStats:
    total_requests: int = 0
    total_success: int = 0
    total_errors: int = 0
    last_error: Optional[str] = None


class STTBackend(ABC):
    """Базовый класс для бэкендов распознавания речи"""
    
    @abstractmethod
    def recognize(self, audio: sr.AudioData) -> Optional[str]:
        """Распознаёт речь из аудио"""
        raise NotImplementedError


@dataclass
class GoogleSTTBackend(STTBackend):
    """Бэкенд для Google Speech Recognition API"""
    
    recognizer: sr.Recognizer = field(default_factory=lambda: GoogleSTTBackend._create_optimized_recognizer())
    
    @staticmethod
    def _create_optimized_recognizer() -> sr.Recognizer:
        """Создаёт оптимизированный распознаватель для быстрой работы"""
        rec = sr.Recognizer()
        # Turbo-режим распознавания
        rec.dynamic_energy_threshold = True
        rec.energy_threshold = 150  # Низкий порог для чувствительности
        rec.pause_threshold = 0.4  # Быстрая реакция на паузу
        rec.non_speaking_duration = 0.2  # Минимальная пауза
        return rec
    
    def recognize(self, audio: sr.AudioData) -> Optional[str]:
        """Распознаёт речь через Google Speech Recognition API"""
        try:
            text = self.recognizer.recognize_google(audio, language="ru-RU")
            return text if text else None
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            logger = logging.getLogger("jarvis")
            logger.warning(f"Google STT RequestError: {e}")
            return None


@dataclass
class WhisperSTTBackend(STTBackend):
    """Бэкенд для локального распознавания через FasterWhisper
    
    Преимущества:
    - Сверхбыстрое распознавание (70-120 мс)
    - Работает офлайн
    - Точнее Google, особенно на русском
    
    Модель загружается при первом использовании (~300 МБ)
    """
    
    model_size: str = "base"  # tiny, base, small, medium, large-v2, large-v3
    device: str = "cpu"  # cpu, cuda
    compute_type: str = "int8"  # int8, int8_float16, int16, float16, float32
    language: str = "ru"  # ru, en, etc.
    
    _model: Optional[object] = field(default=None, init=False, repr=False)
    _logger: logging.Logger = field(default_factory=lambda: logging.getLogger("jarvis"), init=False, repr=False)
    
    def __post_init__(self) -> None:
        """Инициализация Whisper модели (ленивая загрузка)"""
        if not FASTER_WHISPER_AVAILABLE:
            raise ImportError(
                "faster-whisper не установлен. Установите: pip install faster-whisper"
            )
    
    def _get_model(self):
        """Ленивая загрузка модели Whisper"""
        if self._model is None:
            self._logger.info(f"WhisperSTT: Загрузка модели {self.model_size}...")
            try:
                self._model = WhisperModel(
                    self.model_size,
                    device=self.device,
                    compute_type=self.compute_type
                )
                self._logger.info(f"WhisperSTT: Модель {self.model_size} успешно загружена")
            except Exception as e:
                self._logger.error(f"WhisperSTT: Ошибка загрузки модели: {e}", exc_info=True)
                raise
        return self._model
    
    def recognize(self, audio: sr.AudioData) -> Optional[str]:
        """Распознаёт речь через FasterWhisper"""
        tmp_path = None
        try:
            model = self._get_model()
            
            # Конвертируем AudioData в WAV байты для Whisper
            wav_data = audio.get_wav_data()
            
            # Whisper принимает путь к файлу или numpy массив
            # Используем временный файл для простоты
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                tmp.write(wav_data)
                tmp_path = tmp.name
            
            # Распознавание
            segments, info = model.transcribe(
                tmp_path,
                language=self.language,
                beam_size=5,
                vad_filter=True,  # Voice Activity Detection
                vad_parameters=dict(
                    min_silence_duration_ms=200,  # Минимальная пауза
                    threshold=0.5  # Порог VAD
                )
            )
            
            # Собираем текст из сегментов
            text_parts = []
            for segment in segments:
                text_parts.append(segment.text.strip())
            
            text = " ".join(text_parts).strip()
            
            # Удаляем временный файл
            if tmp_path:
                try:
                    Path(tmp_path).unlink(missing_ok=True)
                except Exception:
                    pass  # Игнорируем ошибки удаления
            
            if text:
                self._logger.debug(f"WhisperSTT: Распознано: '{text}' (язык: {info.language}, вероятность: {info.language_probability:.2f})")
                return text
            
            return None
            
        except Exception as e:
            self._logger.warning(f"WhisperSTT: Ошибка распознавания: {e}", exc_info=True)
            # Удаляем временный файл даже при ошибке
            if tmp_path:
                try:
                    Path(tmp_path).unlink(missing_ok=True)
                except Exception:
                    pass
            return None


@dataclass
class SpeechToText:
    """Обёртка для распознавания речи с поддержкой разных бэкендов"""
    
    backend: STTBackend
    stats: STTStats = field(default_factory=STTStats)
    
    def recognize(self, audio: sr.AudioData) -> Optional[str]:
        """Распознаёт речь используя выбранный бэкенд"""
        self.stats.total_requests += 1
        try:
            text = self.backend.recognize(audio)
            if text:
                self.stats.total_success += 1
                return text
            self.stats.total_errors += 1
            return None
        except Exception as e:
            self.stats.total_errors += 1
            self.stats.last_error = str(e)
            logger = logging.getLogger("jarvis")
            logger.warning(f"STT ошибка: {e}", exc_info=True)
            return None
