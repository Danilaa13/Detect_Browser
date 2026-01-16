"""
Скрипт для переноса профилей между стадиями
Правильно обрабатывает profiles.pkl - переносит только нужный профиль
"""

import pickle
import shutil
from pathlib import Path


def load_profiles(profiles_path):
    """Загрузить profiles.pkl"""
    if not profiles_path.exists():
        return {}
    with open(profiles_path, 'rb') as f:
        return pickle.load(f)


def save_profiles(profiles, profiles_path):
    """Сохранить profiles.pkl"""
    profiles_path.parent.mkdir(parents=True, exist_ok=True)
    with open(profiles_path, 'wb') as f:
        pickle.dump(profiles, f)


def move_profile(profile_name: str, source_dir: str, target_dir: str, verbose: bool = True):
    """
    Перенести профиль из одной стадии в другую
    
    Args:
        profile_name: имя профиля
        source_dir: откуда (user_data, upload_profiles, design_profiles)
        target_dir: куда (upload_profiles, design_profiles, active_profiles)
        verbose: выводить подробные сообщения
    """
    
    source_base = Path(source_dir)
    target_base = Path(target_dir)
    
    # Пути к profiles.pkl
    source_pkl = source_base / 'profiles.pkl'
    target_pkl = target_base / 'profiles.pkl'
    
    # Пути к папкам профиля
    source_profile = source_base / profile_name
    target_profile = target_base / profile_name
    
    # Проверки
    if not source_pkl.exists():
        if verbose:
            print(f"❌ Не найден {source_pkl}")
        return False
    
    if not source_profile.exists():
        if verbose:
            print(f"❌ Не найдена папка {source_profile}")
        return False
    
    if target_profile.exists():
        if verbose:
            print(f"⚠️ Профиль {profile_name} уже существует в {target_dir}")
            overwrite = input("Перезаписать? (y/n): ").lower()
            if overwrite != 'y':
                return False
        shutil.rmtree(target_profile)
    
    # Загружаем profiles.pkl из источника
    source_profiles = load_profiles(source_pkl)
    
    if profile_name not in source_profiles:
        if verbose:
            print(f"❌ Профиль {profile_name} не найден в {source_pkl}")
        return False
    
    # Получаем данные профиля
    profile_data = source_profiles[profile_name]
    
    if verbose:
        print(f"\n📦 Переношу профиль: {profile_name}")
        print(f"   Откуда: {source_dir}/")
        print(f"   Куда:   {target_dir}/")
    
    # 1. Копируем папку профиля
    shutil.copytree(source_profile, target_profile)
    
    # 2. Обрабатываем profiles.pkl в целевой папке
    target_profiles = load_profiles(target_pkl)
    target_profiles[profile_name] = profile_data
    save_profiles(target_profiles, target_pkl)
    
    # 3. Удаляем из источника
    shutil.rmtree(source_profile)
    
    del source_profiles[profile_name]
    save_profiles(source_profiles, source_pkl)
    
    if verbose:
        print(f"✅ Профиль {profile_name} успешно перенесен!")
    return True


def list_profiles(directory: str):
    """Показать профили в директории"""
    base = Path(directory)
    pkl = base / 'profiles.pkl'
    
    if not pkl.exists():
        print(f"❌ Нет файла {pkl}")
        return []
    
    profiles = load_profiles(pkl)
    
    print(f"\n📋 Профили в {directory}:")
    for i, (name, profile) in enumerate(profiles.items(), 1):
        proxy_info = ""
        if profile.proxy:
            proxy_info = f" (прокси: {profile.proxy.server})"
        print(f"   {i}. {name}{proxy_info}")
    
    return list(profiles.keys())


def main():
    """Главное меню"""
    
    stages = {
        '1': ('user_data', 'ПРОГРЕВ'),
        '2': ('upload_profiles', 'ЗАЛИВКА'),
        '3': ('design_profiles', 'ОФОРМЛЕНИЕ'),
        '4': ('active_profiles', 'АКТИВНАЯ РАБОТА'),
    }
    
    print("="*70)
    print("🔄 ПЕРЕНОС ПРОФИЛЕЙ МЕЖДУ СТАДИЯМИ")
    print("="*70)
    
    while True:
        print("\n📂 Стадии:")
        for key, (dir_name, desc) in stages.items():
            print(f"   {key}. {desc} ({dir_name}/)")
        print("   0. Выход")
        
        print("\n" + "="*70)
        
        # Выбор источника
        source_choice = input("\nОткуда переносим? (1-4, 0 для выхода): ")
        if source_choice == '0':
            break
        
        if source_choice not in stages:
            print("❌ Неверный выбор")
            continue
        
        source_dir, source_desc = stages[source_choice]
        
        # Показываем профили в источнике
        profile_names = list_profiles(source_dir)
        if not profile_names:
            continue
        
        # Выбор режима: одиночный или массовый
        print("\n" + "="*70)
        print("📦 РЕЖИМ ПЕРЕНОСА:")
        print("   1. Один профиль")
        print("   2. Несколько профилей (через запятую)")
        print("   3. ВСЕ профили")
        print("="*70)
        
        mode = input("\nВыбери режим (1-3): ")
        
        # Определяем какие профили переносить
        profiles_to_move = []
        
        if mode == '1':
            # Одиночный перенос
            profile_name = input("\nИмя профиля: ").strip()
            if profile_name not in profile_names:
                print(f"❌ Профиль {profile_name} не найден")
                continue
            profiles_to_move = [profile_name]
            
        elif mode == '2':
            # Несколько профилей
            names_input = input("\nИмена профилей через запятую: ").strip()
            profiles_to_move = [name.strip() for name in names_input.split(',')]
            
            # Проверка
            invalid = [name for name in profiles_to_move if name not in profile_names]
            if invalid:
                print(f"❌ Не найдены профили: {', '.join(invalid)}")
                continue
                
        elif mode == '3':
            # ВСЕ профили
            print(f"\n⚠️ Будут перенесены ВСЕ {len(profile_names)} профилей!")
            confirm_all = input("Продолжить? (y/n): ").lower()
            if confirm_all != 'y':
                print("❌ Отменено")
                continue
            profiles_to_move = profile_names
            
        else:
            print("❌ Неверный выбор")
            continue
        
        # Выбор цели
        print("\n" + "="*70)
        print("Куда переносим?")
        for key, (dir_name, desc) in stages.items():
            if key != source_choice:
                print(f"   {key}. {desc} ({dir_name}/)")
        
        target_choice = input("\nКуда? (1-4): ")
        if target_choice not in stages or target_choice == source_choice:
            print("❌ Неверный выбор")
            continue
        
        target_dir, target_desc = stages[target_choice]
        
        # Подтверждение
        print("\n" + "="*70)
        print(f"⚠️ ПОДТВЕРЖДЕНИЕ ПЕРЕНОСА:")
        print(f"   Профилей: {len(profiles_to_move)}")
        print(f"   Откуда:   {source_desc} ({source_dir}/)")
        print(f"   Куда:     {target_desc} ({target_dir}/)")
        if len(profiles_to_move) <= 10:
            print(f"   Список:   {', '.join(profiles_to_move)}")
        print("="*70)
        
        confirm = input("\nПродолжить? (y/n): ").lower()
        if confirm != 'y':
            print("❌ Отменено")
            continue
        
        # МАССОВЫЙ ПЕРЕНОС
        print("\n🚀 Начинаю перенос...\n")
        
        success_count = 0
        failed_count = 0
        
        for i, profile_name in enumerate(profiles_to_move, 1):
            print(f"[{i}/{len(profiles_to_move)}] Переношу {profile_name}...")
            try:
                success = move_profile(profile_name, source_dir, target_dir, verbose=False)
                if success:
                    success_count += 1
                    print(f"   ✅ Готово\n")
                else:
                    failed_count += 1
                    print(f"   ❌ Ошибка\n")
            except Exception as e:
                failed_count += 1
                print(f"   ❌ Ошибка: {e}\n")
        
        # Итоги
        print("="*70)
        print(f"🎉 ПЕРЕНОС ЗАВЕРШЕН!")
        print(f"   ✅ Успешно:  {success_count}")
        if failed_count > 0:
            print(f"   ❌ С ошибками: {failed_count}")
        print("="*70)


if __name__ == '__main__':
    main()
