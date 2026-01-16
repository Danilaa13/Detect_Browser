"""
ПАРАЛЛЕЛЬНАЯ ЗАГРУЗКА ВИДЕО
Запускает каждый профиль в отдельном процессе для загрузки Shorts
"""

import asyncio
import pickle
import time
from pathlib import Path
from multiprocessing import Process

import sys

sys.path.insert(0, str(Path(__file__).parent))

from upload_manager.uploader import VideoUploader

PROFILES_PATH = Path('upload_profiles') / 'profiles.pkl'


def load_profiles():
    """Загрузить профили"""
    if not PROFILES_PATH.exists():
        return {}
    with open(PROFILES_PATH, 'rb') as f:
        return pickle.load(f)


def run_upload_in_process(
        profile_name: str,
        videos_count: int,
        pause_minutes: tuple,
        num: int,
        total: int,
        profiles_dir: str
):
    """
    Запустить загрузку в отдельном процессе

    Args:
        profile_name: имя профиля
        videos_count: сколько видео загрузить
        pause_minutes: пауза между видео (мин, макс)
        num: номер профиля
        total: всего профилей
        profiles_dir: папка с профилями
    """

    print(f"[{num}/{total}] [{profile_name}] 🚀 Запуск загрузки...")

    async def run():
        uploader = VideoUploader(profiles_dir=profiles_dir)

        try:
            await uploader.upload_session(
                profile_name=profile_name,
                videos_count=videos_count,
                pause_minutes=pause_minutes
            )

            print(f"[{num}/{total}] [{profile_name}] ✅ Загрузка завершена")

        except Exception as e:
            print(f"[{num}/{total}] [{profile_name}] ❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()

    asyncio.run(run())


def run_parallel_upload(
        num_to_run: int,
        max_parallel: int,
        videos_per_profile: int = 3,
        pause_minutes: tuple = (2, 3),
        profiles_dir: str = 'upload_profiles'
):
    """
    Параллельная загрузка

    Args:
        num_to_run: сколько профилей запустить
        max_parallel: лимит одновременных
        videos_per_profile: видео на профиль
        pause_minutes: пауза между видео (мин, макс)
        profiles_dir: папка с профилями
    """

    profiles_path = Path(profiles_dir) / 'profiles.pkl'

    if not profiles_path.exists():
        print(f"❌ Не найден {profiles_path}")
        return

    with open(profiles_path, 'rb') as f:
        profiles = pickle.load(f)

    if not profiles:
        print(f"❌ Профили не найдены в {profiles_dir}/")
        return

    profile_names = list(profiles.keys())

    if num_to_run > len(profile_names):
        num_to_run = len(profile_names)

    to_run = profile_names[:num_to_run]

    print("=" * 70)
    print("📤 ПАРАЛЛЕЛЬНАЯ ЗАГРУЗКА ВИДЕО")
    print("=" * 70)
    print(f"📊 Профилей: {num_to_run}")
    print(f"⚡️ Одновременно: {max_parallel}")
    print(f"📹 Видео на профиль: {videos_per_profile}")
    print(f"⏸️ Пауза между видео: {pause_minutes[0]}-{pause_minutes[1]} мин")
    print(f"📂 Папка профилей: {profiles_dir}/")
    print("=" * 70)

    # Запускаем батчами
    total = len(to_run)
    processes = []

    for i, name in enumerate(to_run, 1):
        p = Process(
            target=run_upload_in_process,
            args=(name, videos_per_profile, pause_minutes, i, total, profiles_dir)
        )
        p.start()
        processes.append(p)

        # Задержка между запусками
        if i < total:
            time.sleep(3)

        # Ограничение параллельных процессов
        if len(processes) >= max_parallel:
            for proc in processes:
                proc.join()
            processes = []

    # Ждем оставшиеся
    for p in processes:
        p.join()

    print("\n" + "=" * 70)
    print("🎉 ВСЕ ЗАГРУЗКИ ЗАВЕРШЕНЫ!")
    print("=" * 70)


def main():
    """Главная функция"""

    print("=" * 70)
    print("📤 ЗАГРУЗКА YOUTUBE SHORTS")
    print("=" * 70)

    # Выбор папки
    print("\n📂 Выберите папку с профилями:")
    print("   1. upload_profiles/ (начальная заливка)")
    print("   2. active_profiles/ (активная работа)")

    choice = input("\nВыбор (1-2, Enter=1): ").strip() or "1"

    if choice == "2":
        profiles_dir = "active_profiles"
    else:
        profiles_dir = "upload_profiles"

    # Загружаем профили
    profiles_path = Path(profiles_dir) / 'profiles.pkl'

    if not profiles_path.exists():
        print(f"\n❌ Не найден {profiles_path}")
        print(f"💡 Перенесите профили в {profiles_dir}/ через move_profile.py")
        return

    with open(profiles_path, 'rb') as f:
        profiles = pickle.load(f)

    if not profiles:
        print(f"\n❌ Профили не найдены!")
        return

    print(f"\n✅ Найдено: {len(profiles)} профилей в {profiles_dir}/")
    for i, (name, profile) in enumerate(list(profiles.items())[:10], 1):
        proxy_info = ""
        if profile.proxy:
            proxy_info = f" (прокси: {profile.proxy.server})"
        print(f"   {i}. {name}{proxy_info}")

    if len(profiles) > 10:
        print(f"   ... и еще {len(profiles) - 10}")

    # Проверяем папку videos/
    videos_dir = Path('videos')
    if not videos_dir.exists():
        print(f"\n❌ Папка videos/ не найдена!")
        print("💡 Создайте папку videos/ и положите туда .mp4 файлы")
        return

    videos = list(videos_dir.glob('*.mp4'))
    if not videos:
        print(f"\n❌ Нет видео в videos/!")
        return

    print(f"\n📹 Найдено видео: {len(videos)}")

    try:
        num = int(input("\nСколько профилей запустить?: "))
        limit = int(input("Лимит одновременных [10]: ") or "10")
        videos_count = int(input("Видео на профиль [3]: ") or "3")

        run_parallel_upload(
            num_to_run=num,
            max_parallel=limit,
            videos_per_profile=videos_count,
            pause_minutes=(2, 3),
            profiles_dir=profiles_dir
        )

    except KeyboardInterrupt:
        print("\n\n⚠️ Остановлено")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()