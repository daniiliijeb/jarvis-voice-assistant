from __future__ import annotations

import socket
from dataclasses import dataclass
from typing import Dict, Tuple

import speech_recognition as sr


@dataclass
class HealthReport:
    ok_microphone: Tuple[bool, str]
    ok_tts: Tuple[bool, str]
    ok_stt: Tuple[bool, str]
    ok_internet: Tuple[bool, str]
    ok_pyaudio: Tuple[bool, str]
    ok_gpu: Tuple[bool, str]
    ok_ffmpeg: Tuple[bool, str]

    def as_dict(self) -> Dict[str, Dict[str, str]]:
        return {
            "microphone": {"ok": str(self.ok_microphone[0]), "detail": self.ok_microphone[1]},
            "tts": {"ok": str(self.ok_tts[0]), "detail": self.ok_tts[1]},
            "stt": {"ok": str(self.ok_stt[0]), "detail": self.ok_stt[1]},
            "internet": {"ok": str(self.ok_internet[0]), "detail": self.ok_internet[1]},
            "pyaudio": {"ok": str(self.ok_pyaudio[0]), "detail": self.ok_pyaudio[1]},
            "gpu": {"ok": str(self.ok_gpu[0]), "detail": self.ok_gpu[1]},
            "ffmpeg": {"ok": str(self.ok_ffmpeg[0]), "detail": self.ok_ffmpeg[1]},
        }


def check_microphone() -> Tuple[bool, str]:
    try:
        names = sr.Microphone.list_microphone_names()
        if not names:
            return False, "No microphones detected"
        return True, f"Found {len(names)} microphone(s)"
    except Exception as exc:
        return False, f"Error listing microphones: {exc}"


def check_tts() -> Tuple[bool, str]:
    try:
        import pyttsx3

        engine = pyttsx3.init()
        _ = engine.getProperty("rate")
        return True, "pyttsx3 initialized"
    except Exception as exc:
        return False, f"TTS init error: {exc}"


def check_stt() -> Tuple[bool, str]:
    try:
        r = sr.Recognizer()
        _ = r.energy_threshold
        return True, "speech_recognition available"
    except Exception as exc:
        return False, f"STT init error: {exc}"


def check_internet(host: str = "8.8.8.8", port: int = 53, timeout: float = 3.0) -> Tuple[bool, str]:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True, "Internet reachable"
    except Exception as exc:
        return False, f"Internet check failed: {exc}"


def check_pyaudio() -> Tuple[bool, str]:
    try:
        import pyaudio  # noqa: F401

        return True, "PyAudio present"
    except Exception as exc:
        return False, f"PyAudio not available: {exc}"


def check_gpu() -> Tuple[bool, str]:
    try:
        import torch  # type: ignore

        if torch.cuda.is_available():
            return True, f"GPU доступен: {torch.cuda.get_device_name(0)}"
        return False, "GPU недоступен"
    except Exception:
        return False, "GPU недоступен (torch не установлен)"


def check_ffmpeg() -> Tuple[bool, str]:
    """Проверяет наличие ffmpeg (нужен для ElevenLabs)"""
    try:
        import subprocess
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return True, "ffmpeg доступен"
        return False, "ffmpeg не найден в PATH"
    except FileNotFoundError:
        return False, "ffmpeg не установлен (нужен для ElevenLabs)"
    except Exception as exc:
        return False, f"Ошибка проверки ffmpeg: {exc}"


def run_healthcheck() -> HealthReport:
    return HealthReport(
        ok_microphone=check_microphone(),
        ok_tts=check_tts(),
        ok_stt=check_stt(),
        ok_internet=check_internet(),
        ok_pyaudio=check_pyaudio(),
        ok_gpu=check_gpu(),
        ok_ffmpeg=check_ffmpeg(),
    )


