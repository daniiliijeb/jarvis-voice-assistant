from __future__ import annotations

import json
import logging
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple
from urllib.request import urlopen, Request
from urllib.error import URLError

try:
    import zipfile
    ZIP_AVAILABLE = True
except ImportError:
    ZIP_AVAILABLE = False


@dataclass
class UpdateInfo:
    """Информация об обновлении"""
    available: bool
    current_version: str
    latest_version: str
    download_url: Optional[str] = None
    release_notes: Optional[str] = None
    error: Optional[str] = None


class Updater:
    """Система обновлений для Jarvis
    
    Проверяет наличие новых версий на GitHub и позволяет обновить приложение.
    """
    
    def __init__(self, config_dir: Path, current_version: str, repo_owner: str = "yourusername", repo_name: str = "jarvis-voice-assistant"):
        """
        Args:
            config_dir: Директория с конфигурацией (jarvis/data)
            current_version: Текущая версия приложения
            repo_owner: Владелец репозитория на GitHub
            repo_name: Название репозитория на GitHub
        """
        self.logger = logging.getLogger("jarvis")
        self.config_dir = config_dir
        self.current_version = current_version
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.github_api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
        
        # Файл для хранения информации о последней проверке
        self.last_check_file = config_dir / "last_update_check.txt"
    
    def check_for_updates(self, force: bool = False) -> UpdateInfo:
        """Проверяет наличие обновлений
        
        Args:
            force: Принудительная проверка (игнорирует кэш)
        
        Returns:
            UpdateInfo с информацией об обновлении
        """
        try:
            # Проверяем кэш (не проверяем чаще раза в день)
            if not force:
                if self._should_skip_check():
                    self.logger.debug("Updater: Пропускаю проверку (недавно проверяли)")
                    return UpdateInfo(
                        available=False,
                        current_version=self.current_version,
                        latest_version=self.current_version
                    )
            
            self.logger.info("Updater: Проверка обновлений...")
            
            # Получаем информацию о последнем релизе
            latest_release = self._fetch_latest_release()
            if not latest_release:
                return UpdateInfo(
                    available=False,
                    current_version=self.current_version,
                    latest_version=self.current_version,
                    error="Не удалось получить информацию о релизах"
                )
            
            latest_version = latest_release.get("tag_name", "").lstrip("v")
            download_url = None
            release_notes = latest_release.get("body", "")
            
            # Ищем ZIP архив в assets
            assets = latest_release.get("assets", [])
            for asset in assets:
                if asset.get("name", "").endswith(".zip"):
                    download_url = asset.get("browser_download_url")
                    break
            
            # Если нет ZIP, используем ссылку на репозиторий
            if not download_url:
                download_url = latest_release.get("zipball_url")
            
            # Сравниваем версии
            available = self._compare_versions(self.current_version, latest_version)
            
            # Сохраняем время проверки
            self._save_check_time()
            
            if available:
                self.logger.info(f"Updater: Найдено обновление! Текущая: {self.current_version}, Новая: {latest_version}")
            else:
                self.logger.info(f"Updater: Обновлений нет. Текущая версия: {self.current_version}")
            
            return UpdateInfo(
                available=available,
                current_version=self.current_version,
                latest_version=latest_version,
                download_url=download_url,
                release_notes=release_notes
            )
            
        except Exception as e:
            self.logger.error(f"Updater: Ошибка проверки обновлений: {e}", exc_info=True)
            return UpdateInfo(
                available=False,
                current_version=self.current_version,
                latest_version=self.current_version,
                error=str(e)
            )
    
    def _fetch_latest_release(self) -> Optional[dict]:
        """Получает информацию о последнем релизе с GitHub"""
        try:
            request = Request(self.github_api_url)
            request.add_header("Accept", "application/vnd.github.v3+json")
            
            with urlopen(request, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
                return data
        except URLError as e:
            self.logger.warning(f"Updater: Ошибка подключения к GitHub: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Updater: Ошибка получения релиза: {e}", exc_info=True)
            return None
    
    def _compare_versions(self, current: str, latest: str) -> bool:
        """Сравнивает версии (простое сравнение строк)"""
        if not current or not latest:
            return False
        
        # Убираем префикс 'v' если есть
        current = current.lstrip("v").strip()
        latest = latest.lstrip("v").strip()
        
        # Простое сравнение: если latest != current, значит есть обновление
        return latest != current
    
    def _should_skip_check(self) -> bool:
        """Проверяет, нужно ли пропустить проверку (проверяли недавно)"""
        if not self.last_check_file.exists():
            return False
        
        try:
            from datetime import datetime, timedelta
            last_check_str = self.last_check_file.read_text(encoding="utf-8").strip()
            last_check = datetime.fromisoformat(last_check_str)
            # Проверяем не чаще раза в день
            return datetime.now() - last_check < timedelta(hours=12)
        except Exception:
            return False
    
    def _save_check_time(self) -> None:
        """Сохраняет время последней проверки"""
        try:
            from datetime import datetime
            self.last_check_file.write_text(
                datetime.now().isoformat(),
                encoding="utf-8"
            )
        except Exception as e:
            self.logger.debug(f"Updater: Ошибка сохранения времени проверки: {e}")
    
    def download_and_update(self, update_info: UpdateInfo) -> Tuple[bool, str]:
        """Скачивает и устанавливает обновление
        
        Args:
            update_info: Информация об обновлении
        
        Returns:
            Tuple[успех, сообщение]
        """
        if not update_info.available or not update_info.download_url:
            return False, "Нет доступных обновлений"
        
        try:
            self.logger.info(f"Updater: Начинаю загрузку обновления {update_info.latest_version}...")
            
            # Скачиваем обновление
            with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_file:
                tmp_path = tmp_file.name
                
                self.logger.info(f"Updater: Скачивание с {update_info.download_url}...")
                with urlopen(update_info.download_url, timeout=60) as response:
                    tmp_file.write(response.read())
            
            # Распаковываем
            self.logger.info("Updater: Распаковка обновления...")
            root_dir = self.config_dir.parent.parent.parent  # jarvis/data -> jarvis -> корень
            
            if not ZIP_AVAILABLE:
                return False, "Модуль zipfile недоступен"
            
            with zipfile.ZipFile(tmp_path, 'r') as zip_ref:
                # Находим корневую папку в архиве
                members = zip_ref.namelist()
                if members:
                    # Обычно GitHub создаёт папку owner-repo-commit/
                    root_folder = members[0].split('/')[0]
                    # Извлекаем всё кроме этой папки
                    for member in members:
                        if member.startswith(root_folder + '/'):
                            # Убираем корневую папку из пути
                            new_path = member[len(root_folder) + 1:]
                            if new_path:  # Пропускаем саму папку
                                zip_ref.extract(member, root_dir)
                                # Переименовываем файл
                                old_file = root_dir / member
                                new_file = root_dir / new_path
                                if old_file.exists() and not new_file.exists():
                                    new_file.parent.mkdir(parents=True, exist_ok=True)
                                    old_file.rename(new_file)
            
            # Удаляем временный файл
            try:
                Path(tmp_path).unlink(missing_ok=True)
            except Exception:
                pass
            
            # Обновляем версию
            version_file = self.config_dir / "version.txt"
            version_file.write_text(update_info.latest_version, encoding="utf-8")
            
            self.logger.info(f"Updater: Обновление {update_info.latest_version} установлено успешно!")
            return True, f"Обновление до версии {update_info.latest_version} установлено успешно!"
            
        except Exception as e:
            self.logger.error(f"Updater: Ошибка установки обновления: {e}", exc_info=True)
            return False, f"Ошибка установки обновления: {e}"
