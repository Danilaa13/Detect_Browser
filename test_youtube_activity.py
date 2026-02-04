"""
test_youtube_activity.py
Скрипт для тестирования активности YouTube аккаунтов через комментирование
"""

import asyncio
import logging
import time
import warnings
import traceback
from multiprocessing import Process

from automation.testers.youtube_activity_tester import YouTubeActivityTester

warnings.filterwarnings("ignore", category=ResourceWarning)
warnings.filterwarnings("ignore", message=".*Event loop is closed.*")

# Настраиваем логгер
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)


def run_test_in_process(profile_name: str, comments_per_video: int, interval_minutes: int, num: int, total: int):
    """
    Запустить тест для ОДНОГО профиля в отдельном процессе

    Args:
        profile_name: имя профиля
        comments_per_video: количество комментариев под каждым видео
        interval_minutes: интервал между комментариями в минутах
        num: номер профиля
        total: всего профилей
    """
    print(f"[{num}/{total}] [{profile_name}] 🧪 Запуск теста активности...")

    async def run():
        tester = YouTubeActivityTester('user_data')

        try:
            await tester.test_activity(
                profile_name=profile_name,
                comments_per_video=comments_per_video,
                comment_interval_minutes=interval_minutes
            )
            print(f"[{num}/{total}] [{profile_name}] ✅ Тест завершен")
        except Exception as e:
            print(f"[{num}/{total}] [{profile_name}] ❌ Ошибка: {e}")
            traceback.print_exc()
        finally:
            await asyncio.sleep(2)

    asyncio.run(run())


def run_parallel_tests(profiles_to_test: list, comments_per_video: int, interval_minutes: int, max_parallel: int):
    """
    Запустить тесты для нескольких профилей параллельно

    Args:
        profiles_to_test: список имен профилей
        comments_per_video: количество комментариев под каждым видео
        interval_minutes: интервал между комментариями в минутах
        max_parallel: максимум одновременных процессов
    """
    total = len(profiles_to_test)

    if total <= max_parallel:
        # Запускаем всё сразу
        print(f"\n✅ Запускаю все {total} профилей параллельно\n")
        processes = []

        for i, name in enumerate(profiles_to_test, 1):
            p = Process(
                target=run_test_in_process,
                args=(name, comments_per_video, interval_minutes, i, total)
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
            batch = profiles_to_test[start_idx:end_idx]

            print(f"\n{'='*70}")
            print(f"🔄 ЦИКЛ {cycle + 1}/{cycles} (профили {start_idx + 1}-{end_idx})")
            print("="*70)

            processes = []
            for i, name in enumerate(batch, start_idx + 1):
                p = Process(
                    target=run_test_in_process,
                    args=(name, comments_per_video, interval_minutes, i, total)
                )
                p.start()
                processes.append(p)
                time.sleep(3)

            for p in processes:
                p.join()


def main():
    """Главная функция"""

    print("="*70)
    print("🧪 YOUTUBE ACTIVITY TESTER")
    print("Тест активности аккаунтов через комментирование видео")
    print("="*70)

    # Создаем tester для проверки профилей
    tester = YouTubeActivityTester('user_data')

    if not tester.profiles:
        print(f"\n❌ Профили не найдены в user_data/!")
        print("💡 Создай профили: python main.py")
        return

    profile_names = list(tester.profiles.keys())

    print(f"\n✅ Найдено: {len(profile_names)} профилей в user_data/")
    for i, name in enumerate(profile_names[:10], 1):
        print(f"   {i}. {name}")
    if len(profile_names) > 10:
        print(f"   ... и еще {len(profile_names) - 10}")

    try:
        # Параметры теста
        print("\n" + "="*70)
        print("⚙️  НАСТРОЙКИ ТЕСТА")
        print("="*70)

        num_profiles = int(input("\n🔢 Сколько профилей тестировать?: "))
        if num_profiles > len(profile_names):
            num_profiles = len(profile_names)

        comments_per_video = int(input("💬 Комментариев под каждым видео [5]: ") or "5")
        interval_minutes = int(input("⏱️  Интервал между комментариями (минут) [2]: ") or "2")
        max_parallel = int(input("⚡️ Лимит одновременных профилей [3]: ") or "3")

        profiles_to_test = profile_names[:num_profiles]

        # Подсчет времени
        videos_per_profile = 10  # У нас 10 поисковых запросов
        total_comments_per_profile = videos_per_profile * comments_per_video
        estimated_time_per_profile = (total_comments_per_profile - 1) * interval_minutes

        print("\n" + "="*70)
        print("📊 ИНФОРМАЦИЯ О ТЕСТЕ")
        print("="*70)
        print(f"👥 Профилей: {num_profiles}")
        print(f"📹 Видео на профиль: {videos_per_profile}")
        print(f"💬 Комментариев на видео: {comments_per_video}")
        print(f"💬 Всего комментариев на профиль: {total_comments_per_profile}")
        print(f"⏱️  Интервал между комментариями: {interval_minutes} мин")
        print(f"⏳ Примерное время на профиль: ~{estimated_time_per_profile} минут")
        print(f"⚡️ Одновременно: {max_parallel} профилей")
        print("="*70)

        confirm = input("\n✅ Начать тестирование? (y/n): ").strip().lower()
        if confirm != 'y':
            print("❌ Отменено")
            return

        # Запускаем!
        print("\n" + "="*70)
        print("🚀 ЗАПУСК ТЕСТИРОВАНИЯ")
        print("="*70)

        run_parallel_tests(
            profiles_to_test=profiles_to_test,
            comments_per_video=comments_per_video,
            interval_minutes=interval_minutes,
            max_parallel=max_parallel
        )

        print("\n" + "="*70)
        print("🎉 ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ!")
        print("="*70)

    except KeyboardInterrupt:
        print("\n\n⚠️ Остановлено")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        traceback.print_exc()


if __name__ == '__main__':
    main()
