import sys
import argparse
from pathlib import Path

try:
    from jarvis.app.config import AppConfig
    from jarvis.app.logger import get_logger
    from jarvis.app.runtime import JarvisRuntime
    from jarvis.core.conversation import Conversation
    from jarvis.core.health import run_healthcheck
except ImportError as e:
    print(f"ОШИБКА ИМПОРТА: {e}")
    print("Убедитесь, что все зависимости установлены:")
    print("  scripts\\setup_env_simple.bat")
    import traceback
    traceback.print_exc()
    try:
        input("\nНажмите Enter для выхода...")
    except:
        pass
    sys.exit(1)
except Exception as e:
    print(f"ОШИБКА ПРИ ЗАГРУЗКЕ МОДУЛЕЙ: {e}")
    import traceback
    traceback.print_exc()
    try:
        input("\nНажмите Enter для выхода...")
    except:
        pass
    sys.exit(1)


def _print_health() -> int:
    # Команда --health: печать статуса по подсистемам
    report = run_healthcheck()
    d = report.as_dict()
    def line(name: str, key: str) -> str:
        ok = "OK" if d[key]["ok"] == "True" else "FAIL"
        return f"{name} {ok}"
    print(line("микрофон", "microphone"))  # noqa: T201
    print(line("TTS", "tts"))  # noqa: T201
    print(line("STT", "stt"))  # noqa: T201
    print(line("интернет", "internet"))  # noqa: T201
    print(line("PyAudio", "pyaudio"))  # noqa: T201
    print(line("GPU", "gpu"))  # noqa: T201
    print(line("ffmpeg", "ffmpeg"))  # noqa: T201
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Jarvis голосовой ассистент")
    parser.add_argument("--health", action="store_true", help="Показать статус системы и выйти")
    parser.add_argument("--check-update", action="store_true", help="Проверить обновления и выйти")
    parser.add_argument("--update", action="store_true", help="Обновить до последней версии и выйти")
    args = parser.parse_args()

    if args.health:
        return _print_health()
    
    config = AppConfig.load()
    logger = get_logger(config)
    
    # Команды обновления
    if args.check_update or args.update:
        try:
            runtime = JarvisRuntime(config=config)
            
            if not runtime.updater:
                print("ОШИБКА: Updater не настроен.")
                print("Укажите GITHUB_REPO_OWNER и GITHUB_REPO_NAME в переменных окружения.")
                return 1
            
            if args.check_update:
                update_info = runtime.updater.check_for_updates(force=True)
                if update_info.available:
                    print(f"Доступно обновление!")
                    print(f"Текущая версия: {update_info.current_version}")
                    print(f"Последняя версия: {update_info.latest_version}")
                    if update_info.release_notes:
                        print(f"\nЧто нового:\n{update_info.release_notes}")
                    return 0
                else:
                    print(f"Обновлений нет. Текущая версия: {update_info.current_version}")
                    if update_info.error:
                        print(f"Ошибка: {update_info.error}")
                    return 0
            
            if args.update:
                update_info = runtime.updater.check_for_updates(force=True)
                if not update_info.available:
                    print(f"Обновлений нет. Текущая версия: {update_info.current_version}")
                    return 0
                
                print(f"Найдено обновление: {update_info.latest_version}")
                print("Начинаю установку...")
                
                success, message = runtime.updater.download_and_update(update_info)
                if success:
                    print(f"✓ {message}")
                    print("\nОбновление установлено! Перезапустите Jarvis.")
                    return 0
                else:
                    print(f"✗ {message}")
                    return 1
                    
        except Exception as e:
            logger.error(f"Ошибка при работе с обновлениями: {e}", exc_info=True)
            return 1

    logger.info("Jarvis запускается...")
    logger.info(f"Режим: {config.mode}")
    logger.info(f"Версия: {config.version}")
    logger.info(f"Корень: {config.root_dir}")

    runtime = JarvisRuntime(config=config)
    
    # Проверка обновлений при запуске (тихо, в фоне)
    if runtime.updater:
        try:
            update_info = runtime.updater.check_for_updates(force=False)
            if update_info.available:
                logger.info(f"Доступно обновление: {update_info.current_version} -> {update_info.latest_version}")
                # Озвучиваем уведомление об обновлении
                try:
                    from jarvis.core.jarvis_voice import JarvisVoice
                    update_message = f"Сэр, доступно обновление до версии {update_info.latest_version}. Скажите 'обнови jarvis' для установки."
                    runtime.tts.speak_async(update_message)
                    logger.info("Уведомление об обновлении озвучено")
                except Exception as e:
                    logger.debug(f"Ошибка озвучивания уведомления об обновлении: {e}")
        except Exception as e:
            logger.debug(f"Ошибка проверки обновлений: {e}", exc_info=True)
    
    # Приветствие при старте
    try:
        from jarvis.core.jarvis_voice import JarvisVoice
        greeting = JarvisVoice.startup_greeting()
        runtime.tts.speak(greeting)
        logger.info(f"Приветствие озвучено: '{greeting}'")
    except Exception as e:
        logger.debug(f"Ошибка приветствия: {e}", exc_info=True)
    
    # Периодический self-check
    try:
        runtime.check_periodic_health()
    except Exception:
        logger.debug("Ошибка периодического healthcheck", exc_info=True)

    try:
        conversation = Conversation(
            config=config,
            logger=runtime.logger,
            perf_external=runtime.perf,
            perf_callback=runtime.dump_performance_json if config.profile else None,
            tts_external=runtime.tts,
            stt_external=runtime.stt,
        )
        # Fail-safe: защищаем главный цикл
        try:
            conversation.run()
        except Exception as e:  # noqa: BLE001
            runtime.logger.error("Критическая ошибка в разговорном цикле", exc_info=True)
            runtime.restart_runtime()
            # После рестарта попробуем запустить ещё раз один раз
            conversation = Conversation(
                config=config,
                logger=runtime.logger,
                perf_external=runtime.perf,
                perf_callback=runtime.dump_performance_json if config.profile else None,
                tts_external=runtime.tts,
                stt_external=runtime.stt,
            )
            conversation.run()
    except KeyboardInterrupt:
        logger.info("Остановлено пользователем. Выход.")
    except Exception:  # noqa: BLE001
        logger.exception("Необработанная ошибка в main()")
        return 1
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nОстановлено пользователем.")
        try:
            input("Нажмите Enter для выхода...")
        except:
            pass
        sys.exit(0)
    except SystemExit:
        raise
    except Exception as e:
        print(f"\nКРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        try:
            input("\nНажмите Enter для выхода...")
        except:
            pass
        sys.exit(1)


