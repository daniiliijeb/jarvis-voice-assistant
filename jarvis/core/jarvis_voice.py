from __future__ import annotations

import random
from typing import List


class JarvisVoice:
    """Фирменный стиль ответов Jarvis - как в фильме Iron Man"""
    
    # Приветствие при старте
    STARTUP_GREETING = [
        "Привет, сэр. Джарвис онлайн.",
        "Добро пожаловать, сэр. Джарвис готов к работе.",
        "Здравствуйте, сэр. Джарвис на связи.",
    ]
    
    # Приветствия и подтверждения (быстрые ответы)
    GREETINGS = [
        "Да, сэр.",
        "Слушаю, сэр.",
        "К вашим услугам, сэр.",
        "Конечно, сэр.",
    ]
    
    # Успешное выполнение команды
    SUCCESS_OPEN = [
        "Открываю, сэр.",
        "Выполняю, сэр.",
        "Сейчас открою, сэр.",
        "Конечно, сэр.",
        "Сделано, сэр.",
    ]
    
    # Успешное выполнение команды (более формально)
    SUCCESS_ACTION = [
        "Выполнено, сэр.",
        "Готово, сэр.",
        "Сделано, сэр.",
        "Завершено, сэр.",
    ]
    
    # Ошибки - вежливые и умные
    ERROR_NOT_FOUND = [
        "Извините, сэр, но я не могу найти это приложение. Убедитесь, что оно установлено.",
        "Сэр, приложение не найдено. Возможно, оно не установлено на вашем компьютере.",
        "К сожалению, сэр, я не могу найти это приложение. Проверьте, пожалуйста, установку.",
        "Сэр, похоже, что это приложение отсутствует. Установите его, пожалуйста.",
    ]
    
    ERROR_GENERAL = [
        "Извините, сэр, произошла ошибка. Попробуйте ещё раз.",
        "Сэр, что-то пошло не так. Давайте попробуем снова.",
        "К сожалению, сэр, возникла проблема. Повторите команду, пожалуйста.",
        "Сэр, произошла ошибка. Проверьте, пожалуйста, и попробуйте ещё раз.",
    ]
    
    ERROR_UNSUPPORTED = [
        "Извините, сэр, эта команда пока не поддерживается.",
        "Сэр, я ещё не научился выполнять эту команду.",
        "К сожалению, сэр, эта функция пока недоступна.",
        "Сэр, эта команда находится в разработке.",
    ]
    
    # Специфичные ответы для разных действий
    OPENING_BROWSER = [
        "Открываю браузер, сэр.",
        "Запускаю браузер, сэр.",
    ]
    
    OPENING_YOUTUBE = [
        "Запускаю YouTube. Приятного просмотра, сэр.",
        "Открываю YouTube, сэр.",
        "Запускаю YouTube, сэр.",
    ]
    
    OPENING_GOOGLE = [
        "Открываю Google, сэр.",
        "Запускаю Google, сэр.",
        "Google открывается, сэр.",
    ]
    
    OPENING_FOLDER = [
        "Открываю папку, сэр.",
        "Показываю папку, сэр.",
        "Папка открывается, сэр.",
    ]
    
    OPENING_APP = [
        "Запускаю приложение, сэр.",
        "Открываю приложение, сэр.",
        "Приложение запускается, сэр.",
    ]
    
    # Ожидание команды (быстрые ответы)
    LISTENING = [
        "Да, сэр.",
        "Слушаю, сэр.",
    ]
    
    # Не распознано
    NOT_RECOGNIZED = [
        "Сэр, я не уверен, что понял команду.",
        "Извините, сэр, я не понял команду. Повторите, пожалуйста.",
        "Сэр, я не распознал команду. Можете повторить?",
    ]
    
    @staticmethod
    def get_random(phrases: List[str]) -> str:
        """Получить случайную фразу из списка"""
        return random.choice(phrases)
    
    @staticmethod
    def startup_greeting() -> str:
        """Приветствие при старте"""
        return JarvisVoice.get_random(JarvisVoice.STARTUP_GREETING)
    
    @staticmethod
    def greeting() -> str:
        """Приветствие"""
        return JarvisVoice.get_random(JarvisVoice.GREETINGS)
    
    @staticmethod
    def success_open() -> str:
        """Успешное открытие"""
        return JarvisVoice.get_random(JarvisVoice.SUCCESS_OPEN)
    
    @staticmethod
    def success_action() -> str:
        """Успешное выполнение действия"""
        return JarvisVoice.get_random(JarvisVoice.SUCCESS_ACTION)
    
    @staticmethod
    def error_not_found() -> str:
        """Ошибка: не найдено"""
        return JarvisVoice.get_random(JarvisVoice.ERROR_NOT_FOUND)
    
    @staticmethod
    def error_general() -> str:
        """Общая ошибка"""
        return JarvisVoice.get_random(JarvisVoice.ERROR_GENERAL)
    
    @staticmethod
    def error_unsupported() -> str:
        """Ошибка: не поддерживается"""
        return JarvisVoice.get_random(JarvisVoice.ERROR_UNSUPPORTED)
    
    @staticmethod
    def opening_browser() -> str:
        """Открытие браузера"""
        return JarvisVoice.get_random(JarvisVoice.OPENING_BROWSER)
    
    @staticmethod
    def opening_youtube() -> str:
        """Открытие YouTube"""
        return JarvisVoice.get_random(JarvisVoice.OPENING_YOUTUBE)
    
    @staticmethod
    def opening_google() -> str:
        """Открытие Google"""
        return JarvisVoice.get_random(JarvisVoice.OPENING_GOOGLE)
    
    @staticmethod
    def opening_folder() -> str:
        """Открытие папки"""
        return JarvisVoice.get_random(JarvisVoice.OPENING_FOLDER)
    
    @staticmethod
    def opening_app() -> str:
        """Открытие приложения"""
        return JarvisVoice.get_random(JarvisVoice.OPENING_APP)
    
    @staticmethod
    def listening() -> str:
        """Ожидание команды"""
        return JarvisVoice.get_random(JarvisVoice.LISTENING)
    
    @staticmethod
    def not_recognized() -> str:
        """Команда не распознана"""
        return JarvisVoice.get_random(JarvisVoice.NOT_RECOGNIZED)

