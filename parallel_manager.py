"""
ПАРАЛЛЕЛЬНЫЙ ЗАПУСК ЧЕРЕЗ ОРИГИНАЛЬНЫЙ ProfileManager
Запускает каждый профиль через manager.launch_profile() в отдельном процессе
"""

import asyncio
import pickle
import time
import random
from pathlib import Path
from multiprocessing import Process

# Импортируем оригинальный ProfileManager
import sys

sys.path.insert(0, str(Path(__file__).parent))

from profile_manager.manager import ProfileManager

USER_DATA_PATH = Path('user_data')
PROFILES_PATH = USER_DATA_PATH / 'profiles.pkl'


def load_profiles():
    """Загрузить профили"""
    if not PROFILES_PATH.exists():
        return {}
    with open(PROFILES_PATH, 'rb') as f:
        return pickle.load(f)


def run_profile_in_process(profile_name: str, duration_seconds: int, num: int, total: int):
    """
    Запустить ОДИН профиль через оригинальный ProfileManager
    Эта функция работает в отдельном процессе

    Args:
        profile_name: имя профиля
        duration_seconds: сколько работать
        num: номер профиля
        total: всего профилей
    """

    print(f"[{num}/{total}] [{profile_name}] 🚀 Запуск в процессе {Process().pid}...")

    async def run():
        # Создаем СВОЙ экземпляр ProfileManager в этом процессе
        manager = ProfileManager()

        manager.enable_automation(duration_seconds=duration_seconds)

        try:
            # Запускаем профиль (как в оригинальном CLI)
            await manager.launch_profile(profile_name)

            print(f"[{num}/{total}] [{profile_name}] ✅ Браузер запущен!")

            # Ждем завершения задачи автоматизации (она сама остановится через duration_seconds)
            task = manager.running_tasks.get(profile_name)
            if task:
                await task

            print(f"[{num}/{total}] [{profile_name}] ✅ Автоматизация завершена")

        except Exception as e:
            print(f"[{num}/{total}] [{profile_name}] ❌ Ошибка: {e}")
        finally:
            print(f"[{num}/{total}] [{profile_name}] ✅ Завершен")

    # Запускаем async функцию
    asyncio.run(run())


def run_batch(profiles_to_run: list, duration_seconds: int):
    """Запустить батч профилей в отдельных процессах"""
    processes = []
    total = len(profiles_to_run)

    for i, name in enumerate(profiles_to_run, 1):
        p = Process(
            target=run_profile_in_process,
            args=(name, duration_seconds, i, total)
        )
        p.start()
        processes.append(p)
        time.sleep(3)  # Задержка между запусками

    # Ждем завершения всех
    for p in processes:
        p.join()


def run_parallel(num_to_run: int, max_parallel: int, duration_seconds: int):
    """Параллельный запуск"""

    profiles = load_profiles()

    if not profiles:
        print("❌ Профили не найдены!")
        print("💡 Создайте через: python cli.py")
        return

    profile_names = list(profiles.keys())

    if num_to_run > len(profile_names):
        num_to_run = len(profile_names)

    to_run = profile_names[:num_to_run]

    print("=" * 70)
    print("🎭 ПАРАЛЛЕЛЬНЫЙ ЗАПУСК (ОРИГИНАЛЬНЫЙ ProfileManager)")
    print("=" * 70)
    print(f"📊 Запускаем: {num_to_run} профилей")
    print(f"⚡️ Одновременно: {max_parallel}")
    print(f"⏱️ Время: {duration_seconds} сек")
    print(f"🌐 Метод: ProfileManager.launch_profile() в отдельных процессах")
    print(f"✅ Антидетект: ПОЛНЫЙ")
    print("=" * 70)

    if num_to_run <= max_parallel:
        print(f"\n✅ Запускаю все {num_to_run} сразу\n")
        run_batch(to_run, duration_seconds)
    else:
        cycles = (num_to_run + max_parallel - 1) // max_parallel
        print(f"\n🔄 Циклов: {cycles}\n")

        for cycle in range(cycles):
            start_idx = cycle * max_parallel
            end_idx = min(start_idx + max_parallel, num_to_run)
            batch = to_run[start_idx:end_idx]

            print(f"\n{'=' * 70}")
            print(f"🔄 ЦИКЛ {cycle + 1}/{cycles} (профили {start_idx + 1}-{end_idx})")
            print("=" * 70)

            run_batch(batch, duration_seconds)

            if cycle < cycles - 1:
                pause = random.randint(10, 30)
                print(f"\n⏸️ Пауза {pause} сек...")
                time.sleep(pause)

    print("\n" + "=" * 70)
    print("🎉 ВСЕ ПРОФИЛИ ЗАВЕРШЕНЫ!")
    print("=" * 70)


def main():
    """Главная функция"""

    print("=" * 70)
    print("🎭 ПАРАЛЛЕЛЬНЫЙ ЗАПУСК ПРОФИЛЕЙ")
    print("=" * 70)

    profiles = load_profiles()

    if not profiles:
        print("\n❌ Профили не найдены!")
        print("💡 Создайте через: python cli.py")
        return

    print(f"\n✅ Найдено: {len(profiles)} профилей")
    for i, (name, profile) in enumerate(list(profiles.items())[:10], 1):
        proxy_info = ""
        if profile.proxy:
            proxy_info = f" (прокси: {profile.proxy.server})"
        print(f"   {i}. {name}{proxy_info}")

    if len(profiles) > 10:
        print(f"   ... и еще {len(profiles) - 10}")

    try:
        num = int(input("\nСколько профилей запустить?: "))
        limit = int(input("Лимит одновременных [20]: ") or "20")
        seconds = int(input("Секунд работать [60]: ") or "60")

        run_parallel(num, limit, seconds)

    except KeyboardInterrupt:
        print("\n\n⚠️ Остановлено")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()