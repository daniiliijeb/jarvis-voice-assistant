from typing import Optional


def has_wake_word(text: str) -> bool:
    if not text:
        return False
    return "джарвис" in text.lower()


def extract_command(text: str) -> Optional[str]:
    """Извлекает команду из фразы, содержащей wake word.
    Например: 'Джарвис открой браузер' -> 'открой браузер'
    """
    if not text:
        return None
    text_lower = text.lower()
    if "джарвис" not in text_lower:
        return None
    # Убираем wake word и лишние пробелы
    parts = text_lower.split("джарвис", 1)
    if len(parts) > 1:
        cmd = parts[1].strip()
        return cmd if cmd else None
    return None

