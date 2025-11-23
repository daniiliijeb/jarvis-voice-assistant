import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional


Mode = Literal["dev", "prod"]


@dataclass
class AppConfig:
    root_dir: Path
    data_dir: Path
    logs_dir: Path
    version: str
    mode: Mode
    log_level: str
    debug: bool
    profile: bool
    neuro_enabled: bool
    interactive_mode: bool
    # Feature flags
    enable_neuroautomation: bool
    enable_screen_reader: bool
    enable_system_audio: bool
    enable_intent: bool
    enable_copilot: bool
    enable_memory_vectors: bool
    enable_autopatcher: bool
    elevenlabs_api_key: Optional[str] = None
    elevenlabs_voice_id: Optional[str] = None
    stt_engine: str = "google"  # "google" или "whisper"
    github_repo_owner: str = "yourusername"  # Владелец репозитория на GitHub
    github_repo_name: str = "jarvis-voice-assistant"  # Название репозитория

    @staticmethod
    def _detect_root_dir() -> Path:
        # Корень проекта находится на два уровня выше этого файла (jarvis/app/)
        return Path(__file__).resolve().parents[2]

    @staticmethod
    def _read_version(data_dir: Path) -> str:
        version_file = data_dir / "version.txt"
        try:
            return version_file.read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            return "0.0.0"

    @staticmethod
    def _read_api_key(data_dir: Path) -> Optional[str]:
        """Читает API ключ ElevenLabs из файла или переменной окружения"""
        # Сначала проверяем переменную окружения
        env_key = os.getenv("ELEVENLABS_API_KEY")
        if env_key:
            return env_key.strip()
        # Затем проверяем файл
        key_file = data_dir / "elevenlabs_api_key.txt"
        try:
            key = key_file.read_text(encoding="utf-8").strip()
            return key if key else None
        except FileNotFoundError:
            return None

    @staticmethod
    def _read_voice_id(data_dir: Path) -> Optional[str]:
        """Читает voice_id ElevenLabs из файла или переменной окружения"""
        # Сначала проверяем переменную окружения
        env_voice = os.getenv("ELEVENLABS_VOICE_ID")
        if env_voice:
            return env_voice.strip()
        # Затем проверяем файл
        voice_file = data_dir / "elevenlabs_voice_id.txt"
        try:
            voice = voice_file.read_text(encoding="utf-8").strip()
            return voice if voice else None
        except FileNotFoundError:
            return None

    @classmethod
    def load(cls) -> "AppConfig":
        root_dir = cls._detect_root_dir()
        data_dir = root_dir / "jarvis" / "data"
        logs_dir = root_dir / "jarvis" / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        data_dir.mkdir(parents=True, exist_ok=True)

        mode_env = os.getenv("JARVIS_MODE", "dev").strip().lower()
        mode: Mode = "prod" if mode_env == "prod" else "dev"
        log_level = "INFO" if mode == "prod" else "DEBUG"

        debug = os.getenv("JARVIS_DEBUG", "1" if mode == "dev" else "0") in ("1", "true", "True")
        profile = os.getenv("JARVIS_PROFILE", "0") in ("1", "true", "True")
        neuro_enabled = os.getenv("JARVIS_NEURO", "0") in ("1", "true", "True")
        interactive_mode = os.getenv("JARVIS_INTERACTIVE", "1") in ("1", "true", "True")

        return cls(
            root_dir=root_dir,
            data_dir=data_dir,
            logs_dir=logs_dir,
            version=cls._read_version(data_dir),
            mode=mode,
            log_level=log_level,
            debug=debug,
            profile=profile,
            neuro_enabled=neuro_enabled,
            interactive_mode=interactive_mode,
            enable_neuroautomation=os.getenv("ENABLE_NEUROAUTOMATION", "0") in ("1", "true", "True"),
            enable_screen_reader=os.getenv("ENABLE_SCREEN_READER", "0") in ("1", "true", "True"),
            enable_system_audio=os.getenv("ENABLE_SYSTEM_AUDIO", "0") in ("1", "true", "True"),
            enable_intent=os.getenv("ENABLE_INTENT", "0") in ("1", "true", "True"),
            enable_copilot=os.getenv("ENABLE_COPILOT", "0") in ("1", "true", "True"),
            enable_memory_vectors=os.getenv("ENABLE_MEMORY_VECTORS", "0") in ("1", "true", "True"),
            enable_autopatcher=os.getenv("ENABLE_AUTOPATCHER", "0") in ("1", "true", "True"),
            elevenlabs_api_key=cls._read_api_key(data_dir),
            elevenlabs_voice_id=cls._read_voice_id(data_dir),
            stt_engine=os.getenv("STT_ENGINE", "google").strip().lower(),
            github_repo_owner=os.getenv("GITHUB_REPO_OWNER", "yourusername").strip(),
            github_repo_name=os.getenv("GITHUB_REPO_NAME", "jarvis-voice-assistant").strip(),
        )


