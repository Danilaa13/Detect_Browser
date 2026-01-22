"""
parallel_upload.py
Параллельная загрузка видео на разные платформы
"""

import asyncio
import logging
import time
from multiprocessing import Process

from automation.uploaders import YouTubeUploader, TikTokUploader, InstagramUploader

# Настраиваем логгер
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)


def run_upload_in_process(uploader_class, profile_name: str, videos_count: int, num: int, total: int, **kwargs):
    """
    Запустить загрузку для ОДНОГО профиля в отдельном процессе

    Args:
        uploader_class: класс загрузчика (YouTubeUploader, TikTokUploader, etc)
        profile_name: имя профиля
        videos_count: сколько видео загрузить
        num: номер профиля
        total: всего профилей
        **kwargs: параметры для upload_video (title, description, etc)
    """
    print(f"[{num}/{total}] [{profile_name}] 🚀 Запуск загрузки...")

    async def run():
        # Создаем uploader в этом процессе
        uploader = uploader_class()

        try:
            await uploader.upload_session(
                profile_name=profile_name,
                videos_count=videos_count,
                pause_minutes=(2, 3),
                **kwargs
            )
            print(f"[{num}/{total}] [{profile_name}] ✅ Загрузка завершена")
        except Exception as e:
            print(f"[{num}/{total}] [{profile_name}] ❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()

    asyncio.run(run())


def run_parallel_upload(uploader_class, profiles_to_run: list, videos_count: int, max_parallel: int, **kwargs):
    """
    Запустить загрузку для нескольких профилей параллельно

    Args:
        uploader_class: класс загрузчика
        profiles_to_run: список имен профилей
        videos_count: сколько видео на профиль
        max_parallel: максимум одновременных процессов
        **kwargs: параметры для upload_video
    """
    total = len(profiles_to_run)

    if total <= max_parallel:
        # Запускаем всё сразу
        print(f"\n✅ Запускаю все {total} профилей параллельно\n")
        processes = []

        for i, name in enumerate(profiles_to_run, 1):
            p = Process(
                target=run_upload_in_process,
                args=(uploader_class, name, videos_count, i, total),
                kwargs=kwargs
            )
            p.start()
            processes.append(p)
            time.sleep(3)

        for p in processes:
            p.join()
    else:
        # Запускаем батчами
        cycles = (total + max_parallel - 1) // max_parallel
        print(f"\n🔄 Циклов: {cycles}\n")

        for cycle in range(cycles):
            start_idx = cycle * max_parallel
            end_idx = min(start_idx + max_parallel, total)
            batch = profiles_to_run[start_idx:end_idx]

            print(f"\n{'=' * 70}")
            print(f"🔄 ЦИКЛ {cycle + 1}/{cycles} (профили {start_idx + 1}-{end_idx})")
            print("=" * 70)

            processes = []
            for i, name in enumerate(batch, start_idx + 1):
                p = Process(
                    target=run_upload_in_process,
                    args=(uploader_class, name, videos_count, i, total),
                    kwargs=kwargs
                )
                p.start()
                processes.append(p)
                time.sleep(3)

            for p in processes:
                p.join()


def main():
    """Главная функция"""

    print("=" * 70)
    print("🎬 ПАРАЛЛЕЛЬНАЯ ЗАГРУЗКА ВИДЕО")
    print("=" * 70)

    # Выбор платформы
    print("\n📱 ПЛАТФОРМЫ:")
    print("   1. YouTube Shorts")
    print("   2. TikTok (скоро)")
    print("   3. Instagram Reels (скоро)")

    platform_choice = input("\nВыбери платформу (1-3): ").strip()

    if platform_choice == '1':
        uploader_class = YouTubeUploader
        platform_name = "YouTube"
        profiles_dir = 'upload_profiles'
    elif platform_choice == '2':
        uploader_class = TikTokUploader
        platform_name = "TikTok"
        profiles_dir = 'upload_profiles'
    elif platform_choice == '3':
        uploader_class = InstagramUploader
        platform_name = "Instagram"
        profiles_dir = 'upload_profiles'
    else:
        print("❌ Неверный выбор")
        return

    # Создаем uploader для проверки профилей
    uploader = uploader_class(profiles_dir)

    if not uploader.profiles:
        print(f"\n❌ Профили не найдены в {profiles_dir}/!")
        print("💡 Перенеси профили: python move_profile.py")
        return

    profile_names = list(uploader.profiles.keys())

    print(f"\n✅ Найдено: {len(profile_names)} профилей в {profiles_dir}/")
    for i, name in enumerate(profile_names[:10], 1):
        print(f"   {i}. {name}")
    if len(profile_names) > 10:
        print(f"   ... и еще {len(profile_names) - 10}")

    # Проверка видео
    videos = uploader.get_video_files()
    if not videos:
        print(f"\n❌ Нет видео в videos/{uploader.platform_name}/!")
        print(f"💡 Добавь .mp4 файлы в папку videos/{uploader.platform_name}/")
        return

    try:
        # Параметры загрузки
        num_profiles = int(input("\nСколько профилей запустить?: "))
        if num_profiles > len(profile_names):
            num_profiles = len(profile_names)

        max_parallel = int(input("Лимит одновременных [5]: ") or "5")
        videos_count = int(input("Видео на профиль [3]: ") or "3")

        profiles_to_run = profile_names[:num_profiles]

        print("\n" + "=" * 70)
        print(f"🚀 ЗАПУСК ЗАГРУЗКИ НА {platform_name.upper()}")
        print("=" * 70)
        print(f"📊 Профилей: {num_profiles}")
        print(f"⚡️ Одновременно: {max_parallel}")
        print(f"📹 Видео на профиль: {videos_count}")
        print(f"🎬 Всего видео: {num_profiles * videos_count}")
        print("=" * 70)

        # Параметры для upload_video (можно добавить интерактивный ввод)
        upload_params = {}

        if platform_choice == '1':  # YouTube
            use_custom = input("\nИспользовать свои название/описание? (y/n) [n]: ").lower()
            if use_custom == 'y':
                upload_params['title'] = input("Название: ")
                upload_params['description'] = input("Описание: ")
                upload_params['visibility'] = input("Видимость (public/unlisted/private) [public]: ") or 'public'

        # Запускаем!
        run_parallel_upload(
            uploader_class=uploader_class,
            profiles_to_run=profiles_to_run,
            videos_count=videos_count,
            max_parallel=max_parallel,
            **upload_params
        )

        print("\n" + "=" * 70)
        print("🎉 ВСЕ ЗАГРУЗКИ ЗАВЕРШЕНЫ!")
        print("=" * 70)

    except KeyboardInterrupt:
        print("\n\n⚠️ Остановлено")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()