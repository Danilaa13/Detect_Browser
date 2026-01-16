"""
uploader.py - Загрузка YouTube Shorts
Работает с профилями из upload_profiles/ или active_profiles/
"""

import asyncio
import logging
import pickle
import random
from pathlib import Path
from playwright.async_api import Page, async_playwright

# Настраиваем логгер
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)


class VideoUploader:
    def __init__(self, profiles_dir: str = 'upload_profiles'):
        """
        Args:
            profiles_dir: папка с профилями (upload_profiles или active_profiles)
        """
        self.profiles_dir = Path(profiles_dir)
        self.profiles_path = self.profiles_dir / 'profiles.pkl'
        self.videos_dir = Path('videos')

        self.profiles = {}
        self.load_profiles()

    def load_profiles(self):
        """Загрузить профили"""
        try:
            if self.profiles_path.exists():
                with open(self.profiles_path, 'rb') as f:
                    self.profiles = pickle.load(f)
                logger.info(f"✅ Загружено {len(self.profiles)} профилей из {self.profiles_dir}/")
            else:
                logger.error(f"❌ Не найден {self.profiles_path}")
        except Exception as e:
            logger.exception(f'Ошибка загрузки профилей: {e}')

    def get_video_files(self):
        """Получить список видео файлов"""
        if not self.videos_dir.exists():
            logger.error(f"❌ Папка {self.videos_dir}/ не найдена!")
            return []

        videos = list(self.videos_dir.glob('*.mp4'))
        logger.info(f"📹 Найдено {len(videos)} видео в {self.videos_dir}/")
        return videos

    async def upload_video(
            self,
            page: Page,
            video_path: Path,
            profile_name: str,
            title: str = "Крутое видео #shorts",
            description: str = "Смотри это видео! #shorts #viral",
            visibility: str = "public"
    ):
        """
        Загрузить одно видео на YouTube

        Args:
            page: страница браузера
            video_path: путь к видео файлу
            profile_name: имя профиля
            title: название видео
            description: описание
            visibility: public/unlisted/private
        """
        try:
            logger.info(f"[{profile_name}] 📤 Загружаю: {video_path.name}")

            # ШАГ 1: Переходим в YouTube Studio
            logger.info(f"[{profile_name}] 🎬 Открываю YouTube Studio...")
            await page.goto('https://studio.youtube.com', timeout=60000)
            await asyncio.sleep(random.uniform(3, 5))

            # ШАГ 2: Кликаем "Create" (Создать)
            logger.info(f"[{profile_name}] ➕ Нажимаю 'Создать'...")
            try:
                create_button = page.locator('button[aria-label*="Создать"], button[aria-label*="Create"]').first
                await create_button.click(timeout=5000)
                await asyncio.sleep(random.uniform(1, 2))
            except:
                logger.warning(f"[{profile_name}] ⚠️ Не нашел кнопку 'Создать', ищу альтернативу...")
                # Альтернатива - прямой переход на upload
                await page.goto('https://studio.youtube.com/channel/UC/videos/upload', timeout=30000)
                await asyncio.sleep(random.uniform(2, 3))

            # ШАГ 3: Кликаем "Upload video" (Загрузить видео)
            logger.info(f"[{profile_name}] 📂 Выбираю 'Загрузить видео'...")
            try:
                upload_option = page.locator('text="Загрузить видео", text="Upload video"').first
                await upload_option.click(timeout=5000)
                await asyncio.sleep(random.uniform(1, 2))
            except:
                pass  # Может быть уже на странице загрузки

            # ШАГ 4: Загружаем файл
            logger.info(f"[{profile_name}] 📁 Выбираю файл...")

            # Находим input для файла
            file_input = page.locator('input[type="file"]').first
            await file_input.set_input_files(str(video_path.absolute()))

            logger.info(f"[{profile_name}] ⏳ Файл загружается...")
            await asyncio.sleep(random.uniform(3, 5))

            # ШАГ 5: Заполняем название
            logger.info(f"[{profile_name}] ✍️ Ввожу название...")
            try:
                title_input = page.locator('div[aria-label*="название"], div[aria-label*="title"]').first
                await title_input.click(timeout=3000)
                await asyncio.sleep(0.5)

                # Очищаем поле
                await page.keyboard.press('Control+A')
                await page.keyboard.press('Backspace')

                # Вводим название ПОБУКВЕННО
                for char in title:
                    await page.keyboard.type(char)
                    await asyncio.sleep(random.uniform(0.05, 0.15))

                logger.info(f"[{profile_name}] ✅ Название: {title}")
            except Exception as e:
                logger.warning(f"[{profile_name}] ⚠️ Не удалось ввести название: {e}")

            await asyncio.sleep(random.uniform(1, 2))

            # ШАГ 6: Заполняем описание
            logger.info(f"[{profile_name}] ✍️ Ввожу описание...")
            try:
                desc_input = page.locator('div[aria-label*="описание"], div[aria-label*="description"]').first
                await desc_input.click(timeout=3000)
                await asyncio.sleep(0.5)

                # Вводим описание
                for char in description:
                    await page.keyboard.type(char)
                    await asyncio.sleep(random.uniform(0.05, 0.15))

                logger.info(f"[{profile_name}] ✅ Описание добавлено")
            except Exception as e:
                logger.warning(f"[{profile_name}] ⚠️ Не удалось ввести описание: {e}")

            await asyncio.sleep(random.uniform(1, 2))

            # ШАГ 7: Отмечаем "Не для детей" (обязательно)
            logger.info(f"[{profile_name}] 🔞 Отмечаю 'Не для детей'...")
            try:
                not_for_kids = page.locator('tp-yt-paper-radio-button[name="VIDEO_MADE_FOR_KIDS_NOT_MFK"]').first
                await not_for_kids.click(timeout=3000)
                await asyncio.sleep(1)
            except Exception as e:
                logger.warning(f"[{profile_name}] ⚠️ Не удалось отметить 'Не для детей': {e}")

            # ШАГ 8: Нажимаем "Next" 3 раза (пропускаем дополнительные настройки)
            for i in range(3):
                logger.info(f"[{profile_name}] ⏭️ Нажимаю 'Далее' ({i + 1}/3)...")
                try:
                    next_button = page.locator('button:has-text("Далее"), button:has-text("Next")').first
                    await next_button.click(timeout=5000)
                    await asyncio.sleep(random.uniform(2, 3))
                except Exception as e:
                    logger.warning(f"[{profile_name}] ⚠️ Ошибка на шаге {i + 1}: {e}")

            # ШАГ 9: Выбираем видимость (Public/Unlisted/Private)
            logger.info(f"[{profile_name}] 👁 Устанавливаю видимость: {visibility}...")
            try:
                if visibility.lower() == "public":
                    visibility_radio = page.locator('tp-yt-paper-radio-button[name="PUBLIC"]').first
                elif visibility.lower() == "unlisted":
                    visibility_radio = page.locator('tp-yt-paper-radio-button[name="UNLISTED"]').first
                else:  # private
                    visibility_radio = page.locator('tp-yt-paper-radio-button[name="PRIVATE"]').first

                await visibility_radio.click(timeout=3000)
                await asyncio.sleep(1)
            except Exception as e:
                logger.warning(f"[{profile_name}] ⚠️ Не удалось установить видимость: {e}")

            # ШАГ 10: Нажимаем "Publish" (Опубликовать)
            logger.info(f"[{profile_name}] 🚀 Публикую видео...")
            try:
                publish_button = page.locator('button:has-text("Опубликовать"), button:has-text("Publish")').first
                await publish_button.click(timeout=5000)
                await asyncio.sleep(random.uniform(3, 5))

                logger.info(f"[{profile_name}] ✅ Видео '{video_path.name}' успешно загружено!")
                return True

            except Exception as e:
                logger.error(f"[{profile_name}] ❌ Ошибка публикации: {e}")
                return False

        except Exception as e:
            logger.error(f"[{profile_name}] ❌ Ошибка загрузки видео: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def upload_session(
            self,
            profile_name: str,
            videos_count: int = 3,
            pause_minutes: tuple = (2, 3)
    ):
        """
        Сессия загрузки: открыть профиль и загрузить N видео

        Args:
            profile_name: имя профиля
            videos_count: сколько видео загрузить
            pause_minutes: пауза между видео (мин, макс) в минутах
        """
        if profile_name not in self.profiles:
            logger.error(f"❌ Профиль {profile_name} не найден!")
            return

        profile = self.profiles[profile_name]

        # Получаем список видео
        all_videos = self.get_video_files()
        if not all_videos:
            logger.error(f"❌ Нет видео для загрузки!")
            return

        # Выбираем случайные видео
        videos_to_upload = random.sample(all_videos, min(videos_count, len(all_videos)))

        logger.info(f"\n{'=' * 70}")
        logger.info(f"[{profile_name}] 🚀 Начинаю сессию загрузки")
        logger.info(f"[{profile_name}] 📹 Видео для загрузки: {len(videos_to_upload)}")
        logger.info(f"{'=' * 70}\n")

        async with async_playwright() as playwright:
            user_data_path = self.profiles_dir / profile_name

            # Настраиваем прокси если есть
            proxy_config = None
            if profile.proxy:
                proxy_config = {
                    'server': f'{profile.proxy.server}:{profile.proxy.port}',
                    'username': profile.proxy.username,
                    'password': profile.proxy.password
                }

            # Запускаем браузер
            context = await playwright.chromium.launch_persistent_context(
                user_data_dir=user_data_path,
                channel='chrome',
                headless=False,
                user_agent=profile.fingerprint.navigator.userAgent,
                viewport={
                    'width': profile.fingerprint.screen.width,
                    'height': profile.fingerprint.screen.height
                },
                proxy=proxy_config,
            )

            # Закрываем about:blank
            for page in context.pages:
                if page.url == 'about:blank':
                    await page.close()

            # Создаем новую страницу
            page = await context.new_page()

            # Загружаем видео по очереди
            success_count = 0

            for i, video_path in enumerate(videos_to_upload, 1):
                logger.info(f"\n[{profile_name}] 📤 Видео {i}/{len(videos_to_upload)}")

                success = await self.upload_video(
                    page=page,
                    video_path=video_path,
                    profile_name=profile_name,
                    title="Крутое видео #shorts",
                    description="Смотри это видео! #shorts #viral",
                    visibility="public"
                )

                if success:
                    success_count += 1

                # Пауза перед следующим видео (кроме последнего)
                if i < len(videos_to_upload):
                    pause_sec = random.uniform(pause_minutes[0] * 60, pause_minutes[1] * 60)
                    logger.info(f"[{profile_name}] ⏸️ Пауза {int(pause_sec / 60)} мин...")
                    await asyncio.sleep(pause_sec)

            logger.info(f"\n{'=' * 70}")
            logger.info(f"[{profile_name}] 🎉 Сессия завершена!")
            logger.info(f"[{profile_name}] ✅ Загружено: {success_count}/{len(videos_to_upload)}")
            logger.info(f"{'=' * 70}\n")

            await context.close()