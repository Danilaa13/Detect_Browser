"""
parallel_warmer.py
Параллельный прогрев профилей на разных платформах
"""

import asyncio
import logging
import time
import warnings
import traceback
from multiprocessing import Process

from automation.warmers import YouTubeWarmer, TikTokWarmer, InstagramWarmer

warnings.filterwarnings("ignore", category=ResourceWarning)
warnings.filterwarnings("ignore", message=".*Event loop is closed.*")

# Настраиваем логгер
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)


def run_warming_in_process(warmer_class, profile_name: str, duration_minutes: int, num: int, total: int):
    """
    Запустить прогрев для ОДНОГО профиля в отдельном процессе
    
    Args:
        warmer_class: класс прогревателя (YouTubeWarmer, TikTokWarmer, etc)
        profile_name: имя профиля
        duration_minutes: длительность прогрева в минутах
        num: номер профиля
        total: всего профилей
    """
    print(f"[{num}/{total}] [{profile_name}] 🔥 Запуск прогрева...")

    async def run():
        warmer = warmer_class('user_data')

        try:
            await warmer.warm_session(
                profile_name=profile_name,
                duration_minutes=duration_minutes,
                interaction_probability=0.3
            )
            print(f"[{num}/{total}] [{profile_name}] ✅ Прогрев завершен")
        except Exception as e:
            print(f"[{num}/{total}] [{profile_name}] ❌ Ошибка: {e}")
            traceback.print_exc()
        finally:
            # Даем время закрыться (для Windows)
            await asyncio.sleep(2)

    asyncio.run(run())


def run_parallel_warming(warmer_class, profiles_to_run: list, duration_minutes: int, max_parallel: int):
    """
    Запустить прогрев для нескольких профилей параллельно
    
    Args:
        warmer_class: класс прогревателя
        profiles_to_run: список имен профилей
        duration_minutes: длительность прогрева
        max_parallel: максимум одновременных процессов
    """
    total = len(profiles_to_run)
    
    if total <= max_parallel:
        # Запускаем всё сразу
        print(f"\n✅ Запускаю все {total} профилей параллельно\n")
        processes = []
        
        for i, name in enumerate(profiles_to_run, 1):
            p = Process(
                target=run_warming_in_process,
                args=(warmer_class, name, duration_minutes, i, total)
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
            
            print(f"\n{'='*70}")
            print(f"🔄 ЦИКЛ {cycle + 1}/{cycles} (профили {start_idx + 1}-{end_idx})")
            print("="*70)
            
            processes = []
            for i, name in enumerate(batch, start_idx + 1):
                p = Process(
                    target=run_warming_in_process,
                    args=(warmer_class, name, duration_minutes, i, total)
                )
                p.start()
                processes.append(p)
                time.sleep(3)
            
            for p in processes:
                p.join()


def main():
    """Главная функция"""
    
    print("="*70)
    print("🔥 ПАРАЛЛЕЛЬНЫЙ ПРОГРЕВ ПРОФИЛЕЙ")
    print("="*70)
    
    # Выбор платформы
    print("\n📱 ПЛАТФОРМЫ:")
    print("   1. YouTube Shorts")
    print("   2. TikTok")
    print("   3. Instagram Reels")
    
    platform_choice = input("\nВыбери платформу (1-3): ").strip()
    
    if platform_choice == '1':
        warmer_class = YouTubeWarmer
        platform_name = "YouTube"
    elif platform_choice == '2':
        warmer_class = TikTokWarmer
        platform_name = "TikTok"
    elif platform_choice == '3':
        warmer_class = InstagramWarmer
        platform_name = "Instagram"
    else:
        print("❌ Неверный выбор")
        return
    
    # Создаем warmer для проверки профилей
    warmer = warmer_class('user_data')
    
    if not warmer.profiles:
        print(f"\n❌ Профили не найдены в user_data/!")
        print("💡 Создай профили: python main.py")
        return
    
    profile_names = list(warmer.profiles.keys())
    
    print(f"\n✅ Найдено: {len(profile_names)} профилей в user_data/")
    for i, name in enumerate(profile_names[:10], 1):
        print(f"   {i}. {name}")
    if len(profile_names) > 10:
        print(f"   ... и еще {len(profile_names) - 10}")
    
    try:
        # Параметры прогрева
        num_profiles = int(input("\nСколько профилей прогреть?: "))
        if num_profiles > len(profile_names):
            num_profiles = len(profile_names)
        
        max_parallel = int(input("Лимит одновременных [5]: ") or "5")
        duration_minutes = int(input("Длительность прогрева (минут) [30]: ") or "30")
        
        profiles_to_run = profile_names[:num_profiles]
        
        print("\n" + "="*70)
        print(f"🔥 ЗАПУСК ПРОГРЕВА НА {platform_name.upper()}")
        print("="*70)
        print(f"📊 Профилей: {num_profiles}")
        print(f"⚡️ Одновременно: {max_parallel}")
        print(f"⏱️ Длительность: {duration_minutes} минут")
        print("="*70)
        
        # Запускаем!
        run_parallel_warming(
            warmer_class=warmer_class,
            profiles_to_run=profiles_to_run,
            duration_minutes=duration_minutes,
            max_parallel=max_parallel
        )
        
        print("\n" + "="*70)
        print("🎉 ВСЕ ПРОГРЕВЫ ЗАВЕРШЕНЫ!")
        print("="*70)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Остановлено")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        traceback.print_exc()


if __name__ == '__main__':
    main()
