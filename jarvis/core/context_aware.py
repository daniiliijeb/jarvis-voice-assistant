from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, Tuple

try:
    import pygetwindow as gw
    import pyautogui
    CONTEXT_AVAILABLE = True
except ImportError:
    CONTEXT_AVAILABLE = False


@dataclass
class WindowContext:
    """Информация об активном окне"""
    title: str
    app_name: str  # Название приложения (Chrome, Firefox, VLC, etc.)
    process_name: Optional[str] = None


class ContextAware:
    """Определяет контекст активного окна для контекстно-зависимых команд"""
    
    def __init__(self):
        if not CONTEXT_AVAILABLE:
            raise ImportError(
                "pygetwindow и pyautogui не установлены. "
                "Установите: pip install pygetwindow pyautogui"
            )
        
        self.logger = logging.getLogger("jarvis")
        
        # Маппинг названий приложений для определения контекста
        self.app_keywords = {
            "browser": ["chrome", "firefox", "edge", "opera", "brave", "yandex", "браузер"],
            "youtube": ["youtube", "ютуб"],
            "media": ["vlc", "media player", "windows media", "spotify", "winamp"],
            "code": ["visual studio", "code", "pycharm", "intellij", "sublime"],
            "office": ["word", "excel", "powerpoint", "outlook"],
            "explorer": ["explorer", "проводник", "file explorer"],
        }
    
    def get_active_window(self) -> Optional[WindowContext]:
        """Получает информацию об активном окне"""
        try:
            active = gw.getActiveWindow()
            if not active:
                return None
            
            title = active.title or ""
            app_name = self._detect_app_name(title, active)
            
            self.logger.debug(f"ContextAware: Активное окно - '{title}' (приложение: {app_name})")
            
            return WindowContext(
                title=title,
                app_name=app_name,
                process_name=None  # Можно добавить через psutil если нужно
            )
        except Exception as e:
            self.logger.debug(f"ContextAware: Ошибка получения активного окна: {e}")
            return None
    
    def _detect_app_name(self, title: str, window) -> str:
        """Определяет название приложения по заголовку окна"""
        title_lower = title.lower()
        
        # Проверяем по ключевым словам
        for app_type, keywords in self.app_keywords.items():
            for keyword in keywords:
                if keyword in title_lower:
                    return app_type
        
        # Если не найдено, пытаемся определить по имени процесса
        try:
            if hasattr(window, 'process') and window.process:
                process_name = window.process.lower()
                for app_type, keywords in self.app_keywords.items():
                    for keyword in keywords:
                        if keyword in process_name:
                            return app_type
        except Exception:
            pass
        
        return "unknown"
    
    def is_browser_active(self) -> bool:
        """Проверяет, активен ли браузер"""
        context = self.get_active_window()
        return context is not None and context.app_name == "browser"
    
    def is_youtube_active(self) -> bool:
        """Проверяет, активен ли YouTube"""
        context = self.get_active_window()
        return context is not None and (
            context.app_name == "youtube" or 
            "youtube" in context.title.lower() or
            "ютуб" in context.title.lower()
        )
    
    def is_media_active(self) -> bool:
        """Проверяет, активен ли медиаплеер"""
        context = self.get_active_window()
        return context is not None and context.app_name == "media"
    
    def execute_context_command(self, command: str) -> Tuple[bool, Optional[str]]:
        """Выполняет контекстно-зависимую команду
        
        Returns:
            Tuple[успех, сообщение для JarvisVoice]
        """
        context = self.get_active_window()
        if not context:
            from jarvis.core.jarvis_voice import JarvisVoice
            return False, JarvisVoice.error_general()
        
        command_lower = command.lower()
        
        # Команда "закрой" - закрыть активное окно
        if any(cmd in command_lower for cmd in ["закрой", "закрыть", "close"]):
            return self._close_window(context)
        
        # Команда "обнови" - обновить страницу в браузере
        if any(cmd in command_lower for cmd in ["обнови", "обновить", "refresh", "reload"]):
            if context.app_name == "browser":
                return self._refresh_browser()
            from jarvis.core.jarvis_voice import JarvisVoice
            return False, JarvisVoice.error_unsupported()
        
        # Команда "пауза" - пауза в медиаплеере или YouTube
        if any(cmd in command_lower for cmd in ["пауза", "паузу", "pause", "стоп", "останови"]):
            if context.app_name == "media" or self.is_youtube_active():
                return self._pause_media()
            from jarvis.core.jarvis_voice import JarvisVoice
            return False, JarvisVoice.error_unsupported()
        
        # Команда "дальше" / "следующий" - следующий трек/видео
        if any(cmd in command_lower for cmd in ["дальше", "следующий", "next", "skip"]):
            if context.app_name == "media" or self.is_youtube_active():
                return self._next_media()
            from jarvis.core.jarvis_voice import JarvisVoice
            return False, JarvisVoice.error_unsupported()
        
        # Команда "назад" / "предыдущий" - предыдущий трек/видео
        if any(cmd in command_lower for cmd in ["назад", "предыдущий", "previous", "back"]):
            if context.app_name == "media" or self.is_youtube_active():
                return self._previous_media()
            from jarvis.core.jarvis_voice import JarvisVoice
            return False, JarvisVoice.error_unsupported()
        
        return False, None
    
    def _close_window(self, context: WindowContext) -> Tuple[bool, Optional[str]]:
        """Закрывает активное окно"""
        try:
            active = gw.getActiveWindow()
            if active:
                active.close()
                self.logger.info(f"ContextAware: Закрыто окно '{context.title}'")
                from jarvis.core.jarvis_voice import JarvisVoice
                return True, JarvisVoice.success_action()
            from jarvis.core.jarvis_voice import JarvisVoice
            return False, JarvisVoice.error_general()
        except Exception as e:
            self.logger.error(f"ContextAware: Ошибка закрытия окна: {e}", exc_info=True)
            from jarvis.core.jarvis_voice import JarvisVoice
            return False, JarvisVoice.error_general()
    
    def _refresh_browser(self) -> Tuple[bool, Optional[str]]:
        """Обновляет страницу в браузере (F5)"""
        try:
            pyautogui.press('f5')
            self.logger.info("ContextAware: Обновлена страница в браузере (F5)")
            from jarvis.core.jarvis_voice import JarvisVoice
            return True, JarvisVoice.success_action()
        except Exception as e:
            self.logger.error(f"ContextAware: Ошибка обновления страницы: {e}", exc_info=True)
            from jarvis.core.jarvis_voice import JarvisVoice
            return False, JarvisVoice.error_general()
    
    def _pause_media(self) -> Tuple[bool, Optional[str]]:
        """Ставит на паузу медиа (пробел)"""
        try:
            pyautogui.press('space')
            self.logger.info("ContextAware: Пауза медиа (Space)")
            from jarvis.core.jarvis_voice import JarvisVoice
            return True, JarvisVoice.success_action()
        except Exception as e:
            self.logger.error(f"ContextAware: Ошибка паузы: {e}", exc_info=True)
            from jarvis.core.jarvis_voice import JarvisVoice
            return False, JarvisVoice.error_general()
    
    def _next_media(self) -> Tuple[bool, Optional[str]]:
        """Следующий трек/видео (стрелка вправо)"""
        try:
            # Для YouTube и большинства плееров
            pyautogui.press('right')
            self.logger.info("ContextAware: Следующий трек (Right)")
            from jarvis.core.jarvis_voice import JarvisVoice
            return True, JarvisVoice.success_action()
        except Exception as e:
            self.logger.error(f"ContextAware: Ошибка следующего трека: {e}", exc_info=True)
            from jarvis.core.jarvis_voice import JarvisVoice
            return False, JarvisVoice.error_general()
    
    def _previous_media(self) -> Tuple[bool, Optional[str]]:
        """Предыдущий трек/видео (стрелка влево)"""
        try:
            # Для YouTube и большинства плееров
            pyautogui.press('left')
            self.logger.info("ContextAware: Предыдущий трек (Left)")
            from jarvis.core.jarvis_voice import JarvisVoice
            return True, JarvisVoice.success_action()
        except Exception as e:
            self.logger.error(f"ContextAware: Ошибка предыдущего трека: {e}", exc_info=True)
            from jarvis.core.jarvis_voice import JarvisVoice
            return False, JarvisVoice.error_general()

