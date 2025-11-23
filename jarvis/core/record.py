from dataclasses import dataclass
from typing import Optional

import speech_recognition as sr


@dataclass
class RecordConfig:
    device_index: Optional[int] = None
    calibration_duration_s: float = 1.0
    timeout_s: float = 5.0
    phrase_time_limit_s: float = 1.5  # Уменьшено для быстрой реакции


class SpeechListener:
    def __init__(self, config: RecordConfig | None = None):
        self.config = config or RecordConfig()
        self.recognizer = sr.Recognizer()

    def calibrate(self) -> None:
        with sr.Microphone(device_index=self.config.device_index) as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=self.config.calibration_duration_s)

    def listen_once(self) -> Optional[sr.AudioData]:
        """Записывает аудио с микрофона с VAD-фильтром и улучшенной обработкой тишины"""
        try:
            with sr.Microphone(device_index=self.config.device_index) as source:
                # Быстрая калибровка под шум (0.3 сек вместо полной калибровки)
                self.recognizer.adjust_for_ambient_noise(source, duration=0.3)

                audio = self.recognizer.listen(
                    source,
                    timeout=self.config.timeout_s,
                    phrase_time_limit=self.config.phrase_time_limit_s
                )

            # VAD-фильтр: игнорируем слишком тихое аудио
            # Если аудио слишком короткое (< 5000 байт) - это скорее всего шум, клавиатура, дыхание
            if audio.frame_data is None or len(audio.frame_data) < 5000:
                # слишком мало аудио — пропускаем
                return None

            return audio

        except Exception:
            # Обрабатываем все исключения (WaitTimeoutError, OSError, и т.д.)
            return None



