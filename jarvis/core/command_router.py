from __future__ import annotations

import os
import subprocess
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from jarvis.core.jarvis_voice import JarvisVoice


@dataclass
class CommandRouter:
    def __init__(self, runtime=None) -> None:
        import logging
        self.logger = logging.getLogger("jarvis")
        self.runtime = runtime  # Ссылка на JarvisRuntime для доступа к SemanticRouter
    
    def handle(self, text: str) -> Optional[str]:
        t = (text or "").lower().strip()
        if not t:
            self.logger.debug("CommandRouter: получена пустая команда")
            return None
        
        self.logger.debug(f"CommandRouter: обработка команды '{text}' (нормализовано: '{t}')")
        
        # Сначала проверяем контекстно-зависимые команды
        if self.runtime and self.runtime.context_aware:
            try:
                success, message = self.runtime.context_aware.execute_context_command(text)
                if success:
                    self.logger.info(f"CommandRouter: Контекстная команда выполнена: '{text}' -> '{message}'")
                    return message or JarvisVoice.success_action()
            except Exception as e:
                self.logger.debug(f"CommandRouter: Ошибка контекстной команды: {e}")

        # YouTube - много вариаций
        youtube_keywords = [
            "youtube", "ютуб", "ютюб", "ютьюб",
            "открой youtube", "открой ютуб", "открой ютюб",
            "запусти youtube", "запусти ютуб", "запусти ютюб",
            "youtube открой", "ютуб открой", "ютюб открой",
            "надо открыть youtube", "надо открыть ютуб",
            "включи youtube", "включи ютуб",
            "включи видео на youtube", "включи видео на ютуб",
            "покажи youtube", "покажи ютуб",
            "открой видео на youtube", "открой видео на ютуб",
            "запусти видео на youtube", "запусти видео на ютуб",
        ]
        if any(keyword in t for keyword in youtube_keywords):
            self.logger.info(f"CommandRouter: распознана команда YouTube из '{text}'")
            return self._open_youtube()

        # Браузер - много вариаций
        browser_keywords = [
            "браузер", "browser",
            "открой браузер", "запусти браузер",
            "браузер открой", "браузер запусти",
            "надо открыть браузер", "надо запустить браузер",
            "включи браузер", "покажи браузер",
            "интернет", "открой интернет",
            "google", "гугл", "открой гугл",
        ]
        if any(keyword in t for keyword in browser_keywords):
            self.logger.info(f"CommandRouter: распознана команда браузера из '{text}'")
            return self._open_browser()

        # Google - отдельная команда
        google_keywords = [
            "google", "гугл",
            "открой google", "открой гугл",
            "запусти google", "запусти гугл",
            "google открой", "гугл открой",
        ]
        if any(keyword in t for keyword in google_keywords):
            return self._open_google()

        # Папка Загрузки
        downloads_keywords = [
            "загрузки", "загрузка", "downloads",
            "открой загрузки", "открой папку загрузки",
            "запусти загрузки", "покажи загрузки",
            "открой папку загрузок", "открой downloads",
        ]
        if any(keyword in t for keyword in downloads_keywords):
            return self._open_downloads()

        # Рабочий стол
        desktop_keywords = [
            "рабочий стол", "desktop",
            "открой рабочий стол", "открой desktop",
            "покажи рабочий стол", "покажи desktop",
        ]
        if any(keyword in t for keyword in desktop_keywords):
            return self._open_desktop()

        # Документы
        documents_keywords = [
            "документы", "documents",
            "открой документы", "открой папку документы",
            "покажи документы", "открой documents",
        ]
        if any(keyword in t for keyword in documents_keywords):
            return self._open_documents()

        # Изображения
        pictures_keywords = [
            "изображения", "картинки", "pictures", "images",
            "открой изображения", "открой картинки",
            "покажи изображения", "покажи картинки",
            "открой pictures", "открой images",
        ]
        if any(keyword in t for keyword in pictures_keywords):
            return self._open_pictures()

        # Видео
        videos_keywords = [
            "видео", "videos",
            "открой видео", "открой папку видео",
            "покажи видео", "открой videos",
        ]
        if any(keyword in t for keyword in videos_keywords):
            return self._open_videos()

        # Музыка
        music_keywords = [
            "музыка", "music",
            "открой музыку", "открой папку музыку",
            "покажи музыку", "открой music",
        ]
        if any(keyword in t for keyword in music_keywords):
            return self._open_music()

        # Калькулятор
        calc_keywords = [
            "калькулятор", "calculator", "calc",
            "открой калькулятор", "запусти калькулятор",
            "калькулятор открой", "calc",
        ]
        if any(keyword in t for keyword in calc_keywords):
            return self._open_calculator()

        # Блокнот
        notepad_keywords = [
            "блокнот", "notepad",
            "открой блокнот", "запусти блокнот",
            "блокнот открой", "notepad",
        ]
        if any(keyword in t for keyword in notepad_keywords):
            return self._open_notepad()

        # Проводник
        explorer_keywords = [
            "проводник", "explorer", "файлы",
            "открой проводник", "запусти проводник",
            "покажи файлы", "открой файлы",
        ]
        if any(keyword in t for keyword in explorer_keywords):
            return self._open_explorer()

        # Настройки
        settings_keywords = [
            "настройки", "settings", "параметры",
            "открой настройки", "запусти настройки",
            "открой параметры", "settings",
        ]
        if any(keyword in t for keyword in settings_keywords):
            return self._open_settings()

        # Диспетчер задач
        taskmgr_keywords = [
            "диспетчер задач", "task manager", "диспетчер",
            "открой диспетчер задач", "запусти диспетчер задач",
            "task manager", "покажи процессы",
        ]
        if any(keyword in t for keyword in taskmgr_keywords):
            return self._open_task_manager()

        # Панель управления
        control_keywords = [
            "панель управления", "control panel",
            "открой панель управления", "control panel",
        ]
        if any(keyword in t for keyword in control_keywords):
            return self._open_control_panel()

        # Командная строка
        cmd_keywords = [
            "командная строка", "cmd", "терминал",
            "открой командную строку", "запусти cmd",
            "открой терминал", "cmd",
        ]
        if any(keyword in t for keyword in cmd_keywords):
            return self._open_cmd()

        # PowerShell
        powershell_keywords = [
            "powershell", "power shell",
            "открой powershell", "запусти powershell",
        ]
        if any(keyword in t for keyword in powershell_keywords):
            return self._open_powershell()

        # Steam
        steam_keywords = [
            "steam", "стим",
            "открой steam", "запусти steam",
            "steam открой", "стим",
        ]
        if any(keyword in t for keyword in steam_keywords):
            return self._open_steam()

        # Discord
        discord_keywords = [
            "discord", "дискорд",
            "открой discord", "запусти discord",
            "discord открой", "дискорд",
        ]
        if any(keyword in t for keyword in discord_keywords):
            return self._open_discord()

        # Telegram
        telegram_keywords = [
            "telegram", "телеграм", "телеграмм",
            "открой telegram", "запусти telegram",
            "telegram открой", "телеграм",
        ]
        if any(keyword in t for keyword in telegram_keywords):
            return self._open_telegram()

        # Spotify
        spotify_keywords = [
            "spotify", "спотифай",
            "открой spotify", "запусти spotify",
            "spotify открой", "спотифай",
        ]
        if any(keyword in t for keyword in spotify_keywords):
            return self._open_spotify()

        # VLC
        vlc_keywords = [
            "vlc", "ви эль си",
            "открой vlc", "запусти vlc",
            "vlc открой",
        ]
        if any(keyword in t for keyword in vlc_keywords):
            return self._open_vlc()

        # Paint
        paint_keywords = [
            "paint", "краска", "рисование",
            "открой paint", "запусти paint",
            "paint открой", "краска",
        ]
        if any(keyword in t for keyword in paint_keywords):
            return self._open_paint()

        # Word
        word_keywords = [
            "word", "ворд", "microsoft word",
            "открой word", "запусти word",
            "word открой", "ворд",
        ]
        if any(keyword in t for keyword in word_keywords):
            return self._open_word()

        # Excel
        excel_keywords = [
            "excel", "эксель", "microsoft excel",
            "открой excel", "запусти excel",
            "excel открой", "эксель",
        ]
        if any(keyword in t for keyword in excel_keywords):
            return self._open_excel()

        # Обновление
        update_keywords = [
            "обнови", "обновить", "обновление",
            "обнови jarvis", "обнови джарвис",
            "запусти обновление", "проверь обновления",
            "update", "check for updates",
        ]
        if any(keyword in t for keyword in update_keywords):
            if self.runtime and self.runtime.updater:
                self.logger.info(f"CommandRouter: распознана команда обновления из '{text}'")
                return self._update_jarvis()
            else:
                return JarvisVoice.error_unsupported()
        
        # Обновление Jarvis
        update_keywords = [
            "обнови jarvis", "обновить jarvis", "обнови джарвис", "обновить джарвис",
            "обнови приложение", "обновить приложение",
            "проверь обновления", "проверить обновления",
            "update jarvis", "update", "обновление",
        ]
        if any(keyword in t for keyword in update_keywords):
            return self._update_jarvis()
        
        # Системные команды (безопасные)
        if "перезагрузи компьютер" in t or "перезагрузить компьютер" in t:
            return JarvisVoice.error_unsupported()
        if "выключи компьютер" in t or "выключить компьютер" in t:
            return JarvisVoice.error_unsupported()
        if "выключи звук" in t or "отключи звук" in t or "убери звук" in t:
            return JarvisVoice.error_unsupported()
        if "включи звук" in t or "включи звук" in t:
            return JarvisVoice.error_unsupported()

        self.logger.warning(f"CommandRouter: команда не распознана: '{text}'")
        # Fallback на SemanticRouter для умного понимания команд
        if self.runtime and self.runtime.semantic:
            try:
                best_cmd, score = self.runtime.semantic.match(text, threshold=0.62)
                if best_cmd and score >= 0.62:
                    self.logger.info(
                        f"CommandRouter: SemanticRouter распознал команду '{best_cmd}' "
                        f"для '{text}' (score: {score:.3f})"
                    )
                    result = self._execute(best_cmd)
                    if result:
                        return result
            except Exception as e:
                self.logger.debug(f"CommandRouter: Ошибка SemanticRouter: {e}")
        
        # Если ничего не помогло
        return JarvisVoice.not_recognized()

    def _open_browser(self) -> str:
        try:
            self.logger.info("CommandRouter: открываю браузер (https://www.google.com)")
            webbrowser.open("https://www.google.com")
            response = JarvisVoice.opening_browser()
            self.logger.debug(f"CommandRouter: ответ '{response}'")
            return response
        except Exception as e:
            self.logger.error(f"CommandRouter: ошибка открытия браузера: {e}", exc_info=True)
            return JarvisVoice.error_general()

    def _open_youtube(self) -> str:
        try:
            self.logger.info("CommandRouter: открываю YouTube (https://www.youtube.com)")
            webbrowser.open("https://www.youtube.com")
            response = JarvisVoice.opening_youtube()
            self.logger.debug(f"CommandRouter: ответ '{response}'")
            return response
        except Exception as e:
            self.logger.error(f"CommandRouter: ошибка открытия YouTube: {e}", exc_info=True)
            return JarvisVoice.error_general()

    def _open_google(self) -> str:
        try:
            self.logger.info("CommandRouter: открываю Google (https://www.google.com)")
            webbrowser.open("https://www.google.com")
            response = JarvisVoice.opening_google()
            self.logger.debug(f"CommandRouter: ответ '{response}'")
            return response
        except Exception as e:
            self.logger.error(f"CommandRouter: ошибка открытия Google: {e}", exc_info=True)
            return JarvisVoice.error_general()

    def _open_downloads(self) -> str:
        try:
            downloads = Path(os.path.expandvars(r"%USERPROFILE%\Downloads"))
            self.logger.info(f"CommandRouter: открываю папку Загрузки: {downloads}")
            if downloads.exists():
                if os.name == "nt":
                    subprocess.Popen(["explorer", str(downloads)])
                else:
                    subprocess.Popen(["xdg-open", str(downloads)])
                response = JarvisVoice.opening_folder()
                self.logger.debug(f"CommandRouter: папка открыта, ответ '{response}'")
                return response
            else:
                self.logger.warning(f"CommandRouter: папка Загрузки не найдена: {downloads}")
                return JarvisVoice.error_not_found()
        except Exception as e:
            self.logger.error(f"CommandRouter: ошибка открытия папки Загрузки: {e}", exc_info=True)
            return JarvisVoice.error_general()

    def _open_desktop(self) -> str:
        desktop = Path(os.path.expandvars(r"%USERPROFILE%\Desktop"))
        if desktop.exists():
            if os.name == "nt":
                subprocess.Popen(["explorer", str(desktop)])
            else:
                subprocess.Popen(["xdg-open", str(desktop)])
            return JarvisVoice.opening_folder()
        return JarvisVoice.error_not_found()

    def _open_documents(self) -> str:
        documents = Path(os.path.expandvars(r"%USERPROFILE%\Documents"))
        if documents.exists():
            if os.name == "nt":
                subprocess.Popen(["explorer", str(documents)])
            else:
                subprocess.Popen(["xdg-open", str(documents)])
            return JarvisVoice.opening_folder()
        return JarvisVoice.error_not_found()

    def _open_pictures(self) -> str:
        pictures = Path(os.path.expandvars(r"%USERPROFILE%\Pictures"))
        if pictures.exists():
            if os.name == "nt":
                subprocess.Popen(["explorer", str(pictures)])
            else:
                subprocess.Popen(["xdg-open", str(pictures)])
            return JarvisVoice.opening_folder()
        return JarvisVoice.error_not_found()

    def _open_videos(self) -> str:
        videos = Path(os.path.expandvars(r"%USERPROFILE%\Videos"))
        if videos.exists():
            if os.name == "nt":
                subprocess.Popen(["explorer", str(videos)])
            else:
                subprocess.Popen(["xdg-open", str(videos)])
            return JarvisVoice.opening_folder()
        return JarvisVoice.error_not_found()

    def _open_music(self) -> str:
        music = Path(os.path.expandvars(r"%USERPROFILE%\Music"))
        if music.exists():
            if os.name == "nt":
                subprocess.Popen(["explorer", str(music)])
            else:
                subprocess.Popen(["xdg-open", str(music)])
            return JarvisVoice.opening_folder()
        return JarvisVoice.error_not_found()

    def _open_calculator(self) -> str:
        try:
            if os.name == "nt":
                subprocess.Popen(["calc.exe"])
            else:
                subprocess.Popen(["gnome-calculator"])
            return JarvisVoice.opening_app()
        except Exception:
            return JarvisVoice.error_general()

    def _open_notepad(self) -> str:
        try:
            if os.name == "nt":
                subprocess.Popen(["notepad.exe"])
            else:
                subprocess.Popen(["gedit"])
            return JarvisVoice.opening_app()
        except Exception:
            return JarvisVoice.error_general()

    def _open_explorer(self) -> str:
        try:
            if os.name == "nt":
                subprocess.Popen(["explorer.exe"])
            else:
                subprocess.Popen(["nautilus"])
            return JarvisVoice.opening_app()
        except Exception:
            return JarvisVoice.error_general()

    def _open_settings(self) -> str:
        try:
            if os.name == "nt":
                subprocess.Popen(["ms-settings:"])
            else:
                subprocess.Popen(["gnome-control-center"])
            return JarvisVoice.opening_app()
        except Exception:
            return JarvisVoice.error_general()

    def _open_task_manager(self) -> str:
        try:
            if os.name == "nt":
                subprocess.Popen(["taskmgr.exe"])
            else:
                subprocess.Popen(["gnome-system-monitor"])
            return JarvisVoice.opening_app()
        except Exception:
            return JarvisVoice.error_general()

    def _open_control_panel(self) -> str:
        try:
            if os.name == "nt":
                subprocess.Popen(["control.exe"])
            else:
                return JarvisVoice.error_unsupported()
            return JarvisVoice.opening_app()
        except Exception:
            return JarvisVoice.error_general()

    def _open_cmd(self) -> str:
        try:
            if os.name == "nt":
                subprocess.Popen(["cmd.exe"])
            else:
                subprocess.Popen(["gnome-terminal"])
            return JarvisVoice.opening_app()
        except Exception:
            return JarvisVoice.error_general()

    def _open_powershell(self) -> str:
        try:
            if os.name == "nt":
                subprocess.Popen(["powershell.exe"])
            else:
                return JarvisVoice.error_unsupported()
            return JarvisVoice.opening_app()
        except Exception:
            return JarvisVoice.error_general()

    def _open_steam(self) -> str:
        try:
            if os.name == "nt":
                subprocess.Popen(["steam://"])
            else:
                subprocess.Popen(["steam"])
            return JarvisVoice.opening_app()
        except Exception:
            return JarvisVoice.error_not_found()

    def _open_discord(self) -> str:
        try:
            if os.name == "nt":
                # Пробуем найти Discord в стандартных местах
                discord_paths = [
                    os.path.expandvars(r"%LOCALAPPDATA%\Discord\Update.exe"),
                    os.path.expandvars(r"%APPDATA%\Discord\Discord.exe"),
                    r"C:\Users\%USERNAME%\AppData\Local\Discord\Update.exe",
                ]
                for path in discord_paths:
                    expanded = os.path.expandvars(path)
                    if os.path.exists(expanded):
                        subprocess.Popen([expanded, "--processStart", "Discord.exe"])
                        return JarvisVoice.opening_app()
                # Если не нашли, пробуем через команду
                subprocess.Popen(["discord://"])
            else:
                subprocess.Popen(["discord"])
            return JarvisVoice.opening_app()
        except Exception:
            return JarvisVoice.error_not_found()

    def _open_telegram(self) -> str:
        try:
            if os.name == "nt":
                telegram_paths = [
                    os.path.expandvars(r"%LOCALAPPDATA%\Programs\Telegram\Telegram.exe"),
                    os.path.expandvars(r"%APPDATA%\Telegram Desktop\Telegram.exe"),
                ]
                for path in telegram_paths:
                    if os.path.exists(path):
                        subprocess.Popen([path])
                        return JarvisVoice.opening_app()
                subprocess.Popen(["tg://"])
            else:
                subprocess.Popen(["telegram-desktop"])
            return JarvisVoice.opening_app()
        except Exception:
            return JarvisVoice.error_not_found()

    def _open_spotify(self) -> str:
        try:
            if os.name == "nt":
                spotify_paths = [
                    os.path.expandvars(r"%APPDATA%\Spotify\Spotify.exe"),
                    r"C:\Users\%USERNAME%\AppData\Roaming\Spotify\Spotify.exe",
                ]
                for path in spotify_paths:
                    expanded = os.path.expandvars(path)
                    if os.path.exists(expanded):
                        subprocess.Popen([expanded])
                        return JarvisVoice.opening_app()
                subprocess.Popen(["spotify://"])
            else:
                subprocess.Popen(["spotify"])
            return JarvisVoice.opening_app()
        except Exception:
            return JarvisVoice.error_not_found()

    def _open_vlc(self) -> str:
        try:
            if os.name == "nt":
                vlc_paths = [
                    r"C:\Program Files\VideoLAN\VLC\vlc.exe",
                    r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe",
                ]
                for path in vlc_paths:
                    if os.path.exists(path):
                        subprocess.Popen([path])
                        return JarvisVoice.opening_app()
            else:
                subprocess.Popen(["vlc"])
            return JarvisVoice.opening_app()
        except Exception:
            return JarvisVoice.error_not_found()

    def _open_paint(self) -> str:
        try:
            if os.name == "nt":
                subprocess.Popen(["mspaint.exe"])
            else:
                subprocess.Popen(["pinta"])
            return JarvisVoice.opening_app()
        except Exception:
            return JarvisVoice.error_general()

    def _open_word(self) -> str:
        try:
            if os.name == "nt":
                word_paths = [
                    r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
                    r"C:\Program Files (x86)\Microsoft Office\root\Office16\WINWORD.EXE",
                    r"C:\Program Files\Microsoft Office\Office16\WINWORD.EXE",
                ]
                for path in word_paths:
                    if os.path.exists(path):
                        subprocess.Popen([path])
                        return JarvisVoice.opening_app()
            return JarvisVoice.error_not_found()
        except Exception:
            return JarvisVoice.error_general()

    def _open_excel(self) -> str:
        try:
            if os.name == "nt":
                excel_paths = [
                    r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
                    r"C:\Program Files (x86)\Microsoft Office\root\Office16\EXCEL.EXE",
                    r"C:\Program Files\Microsoft Office\Office16\EXCEL.EXE",
                ]
                for path in excel_paths:
                    if os.path.exists(path):
                        subprocess.Popen([path])
                        return JarvisVoice.opening_app()
            return JarvisVoice.error_not_found()
        except Exception:
            return JarvisVoice.error_general()
    
    def _execute(self, command_name: str) -> Optional[str]:
        """Выполняет команду по имени (для SemanticRouter)"""
        command_map = {
            "browser": self._open_browser,
            "youtube": self._open_youtube,
            "google": self._open_google,
            "downloads": self._open_downloads,
            "desktop": self._open_desktop,
            "documents": self._open_documents,
            "calculator": self._open_calculator,
            "notepad": self._open_notepad,
            "explorer": self._open_explorer,
        }
        
        handler = command_map.get(command_name)
        if handler:
            self.logger.info(f"CommandRouter: Выполняю команду '{command_name}' через SemanticRouter")
            return handler()
        
        self.logger.warning(f"CommandRouter: Неизвестная команда '{command_name}' от SemanticRouter")
        return None
    
    def _update_jarvis(self) -> str:
        """Обновляет Jarvis до последней версии"""
        try:
            if not self.runtime or not self.runtime.updater:
                self.logger.warning("CommandRouter: Updater недоступен")
                return JarvisVoice.error_unsupported()
            
            self.logger.info("CommandRouter: Проверка обновлений...")
            
            # Проверяем обновления
            update_info = self.runtime.updater.check_for_updates(force=True)
            
            if not update_info.available:
                if update_info.error:
                    self.logger.warning(f"CommandRouter: Ошибка проверки обновлений: {update_info.error}")
                    return "Сэр, не удалось проверить обновления. Попробуйте позже."
                return f"Сэр, вы используете последнюю версию {update_info.current_version}."
            
            # Есть обновление
            self.logger.info(f"CommandRouter: Найдено обновление {update_info.latest_version}")
            
            # Скачиваем и устанавливаем
            self.logger.info("CommandRouter: Начинаю установку обновления...")
            success, message = self.runtime.updater.download_and_update(update_info)
            
            if success:
                self.logger.info("CommandRouter: Обновление установлено успешно")
                return f"Сэр, обновление до версии {update_info.latest_version} установлено. Перезапустите Jarvis для применения изменений."
            else:
                self.logger.error(f"CommandRouter: Ошибка установки обновления: {message}")
                return f"Сэр, произошла ошибка при установке обновления: {message}"
                
        except Exception as e:
            self.logger.error(f"CommandRouter: Ошибка обновления: {e}", exc_info=True)
            return JarvisVoice.error_general()
