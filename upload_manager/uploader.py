"""
uploader.py - Загрузка YouTube Shorts
ТОЧНАЯ КОПИЯ запуска браузера из manager.py
"""

import asyncio
import logging
import pickle
import random
from pathlib import Path
from playwright.async_api import Page, async_playwright

# ТОЧНЫЕ импорты из manager.py
from browserforge.injectors.utils import InjectFunction, only_injectable_headers
from profile_manager.path import StealthPlaywrightPatcher
from profile_manager.structures import Profile

# КРИТИЧНО! Применяем патчи
StealthPlaywrightPatcher().apply_patches()

# Настраиваем логгер
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

# Пути
EXTENSIONS_PATH = Path(__file__).parent.parent / 'extensions'


class VideoUploader:
    def __init__(self, profiles_dir: str = 'upload_profiles'):
        """
        Args:
            profiles_dir: папка с профилями (upload_profiles или active_profiles)
        """
        base_dir = Path(__file__).parent.parent
        self.profiles_dir = base_dir / profiles_dir
        self.profiles_path = self.profiles_dir / 'profiles.pkl'
        self.videos_dir = base_dir / 'videos'

        self.profiles = {}
        self.load_profiles()

    def load_profiles(self):
        """Загрузить профили"""
        try:
            if self.profiles_path.exists():
                with open(self.profiles_path, 'rb') as f:
                    self.profiles = pickle.load(f)
                logger.info(f"✅ Загружено {len(self.profiles)} профилей из {self.profiles_dir.name}/")
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
        logger.info(f"📹 Найдено {len(videos)} видео")
        return videos

    # ТОЧНАЯ КОПИЯ из manager.py
    def get_extensions_args(self) -> list[str]:
        extensions_patches: str = self.get_extensions_patches()
        if not extensions_patches:
            return []

        return [
            f"--disable-extensions-except={extensions_patches}",
            f"--load-extension={extensions_patches}",
        ]

    @staticmethod
    def get_extensions_patches() -> str:
        if not EXTENSIONS_PATH.exists():
            return ''

        extension_dirs = [
            str(ext_dir) for ext_dir in EXTENSIONS_PATH.iterdir()
            if ext_dir.is_dir() and (ext_dir / 'manifest.json').exists()
        ]
        return ','.join(extension_dirs)

    @staticmethod
    async def close_page_with_delay(page: Page, delay: float = 0.1):
        await asyncio.sleep(delay)
        await page.close()

    async def upload_video(
            self,
            page: Page,
            video_path: Path,
            profile_name: str,
            title: str = "Крутое видео #shorts",
            description: str = "Смотри это видео! #shorts #viral",
            visibility: str = "public"
    ):
        """Загрузить одно видео на YouTube"""
        try:
            logger.info(f"[{profile_name}] 📤 Загружаю: {video_path.name}")

            # ШАГ 1: Google
            logger.info(f"[{profile_name}] 🔍 Открываю Google...")
            await page.goto('https://www.google.com', timeout=30000)
            await asyncio.sleep(random.uniform(2, 4))

            # ШАГ 2: Ищем youtube
            logger.info(f"[{profile_name}] ⌨️ Ввожу 'youtube'...")
            search_input = page.locator('textarea[name="q"]').first
            await search_input.click()
            await asyncio.sleep(random.uniform(0.5, 1))

            for char in "youtube":
                await page.keyboard.type(char)
                await asyncio.sleep(random.uniform(0.1, 0.3))

            await page.keyboard.press('Enter')
            await asyncio.sleep(random.uniform(2, 4))

            # ШАГ 3: Переходим на YouTube
            logger.info(f"[{profile_name}] 🖱 Перехожу на YouTube...")
            try:
                youtube_link = page.locator('a[href*="youtube.com"]').first
                await youtube_link.click()
                await asyncio.sleep(random.uniform(3, 5))
            except:
                await page.goto('https://www.youtube.com', timeout=30000)
                await asyncio.sleep(random.uniform(2, 4))

            # ШАГ 4: Кликаем на кнопку профиля (аватарку)
            logger.info(f"[{profile_name}] 👤 Открываю меню профиля...")
            try:
                avatar_button = page.locator(
                    'button#avatar-btn, button[aria-label*="Меню аккаунта"], button[aria-label*="Account menu"]').first
                await avatar_button.click(timeout=5000)
                await asyncio.sleep(random.uniform(1, 2))
            except Exception as e:
                logger.warning(f"[{profile_name}] ⚠️ Не нашел кнопку профиля: {e}")
            # ШАГ 5: Выбираем YouTube Studio
            logger.info(f"[{profile_name}] 🎬 Выбираю YouTube Studio...")
            try:
                studio_link = page.locator(
                    'tp-yt-paper-item:has-text("Творческая студия"), tp-yt-paper-item:has-text("YouTube Studio"), a:has-text("YouTube Studio")').first

                # Ждем новую страницу (открывается в новой вкладке)
                async with page.context.expect_page() as new_page_info:
                    await studio_link.click(timeout=5000)

                # Переключаемся на новую страницу YouTube Studio
                new_page = await new_page_info.value
                await new_page.wait_for_load_state('networkidle')
                page = new_page  # Теперь работаем со Studio!

                logger.info(f"[{profile_name}] ✅ Переключился на YouTube Studio")
                await asyncio.sleep(random.uniform(3, 5))

            except Exception as e:
                logger.warning(f"[{profile_name}] ⚠️ Не нашел YouTube Studio: {e}")
                await page.goto('https://studio.youtube.com', timeout=30000)
                await asyncio.sleep(random.uniform(3, 5))
            # ШАГ 6: Нажимаем Continue (если есть)
            logger.info(f"[{profile_name}] ➡️ Проверяю всплывающее окно...")
            try:
                continue_button = page.locator(
                    'button[aria-label*="Continue"], button[aria-label*="Продолжить"], ytcp-button-shape button:has-text("Continue"), ytcp-button-shape button:has-text("Продолжить")').first
                await continue_button.click(timeout=3000)
                await asyncio.sleep(random.uniform(1, 2))
                logger.info(f"[{profile_name}] ✅ Нажал Continue")
            except:
                logger.info(f"[{profile_name}] ℹ️ Всплывающее окно не найдено")
            # ШАГ 7: Переходим в раздел Контент
            logger.info(f"[{profile_name}] 📂 Перехожу в раздел Контент...")
            try:
                content_icon = page.locator('yt-icon span.yt-icon-shape:has(svg path[d*="M20 2H8"])').first
                await content_icon.click(timeout=5000)
                await asyncio.sleep(random.uniform(2, 3))
            except Exception as e:
                logger.warning(f"[{profile_name}] ⚠️ Не нашел раздел Контент: {e}")
                try:
                    content_link = page.locator('a:has-text("Контент"), a:has-text("Content")').first
                    await content_link.click(timeout=3000)
                    await asyncio.sleep(random.uniform(2, 3))
                except:
                    pass
            # ШАГ 8: Нажимаем Добавить видео
            logger.info(f"[{profile_name}] ➕ Нажимаю 'Добавить видео'...")
            try:
                upload_button = page.locator(
                    'button[aria-label*="Добавить видео"], button[aria-label*="Upload"], ytcp-button-shape button:has-text("Добавить видео"), ytcp-button-shape button:has-text("Upload")').first
                await upload_button.click(timeout=5000)
                await asyncio.sleep(random.uniform(2, 3))
            except Exception as e:
                logger.warning(f"[{profile_name}] ⚠️ Не нашел кнопку загрузки: {e}")
            # ШАГ 9: Загружаем файл
            logger.info(f"[{profile_name}] 📁 Выбираю файл...")
            try:
                file_input = page.locator('input[type="file"]').first
                await file_input.set_input_files(str(video_path.absolute()))
                logger.info(f"[{profile_name}] ⏳ Файл загружается...")
                await asyncio.sleep(random.uniform(5, 8))
            except Exception as e:
                logger.error(f"[{profile_name}] ❌ Не удалось загрузить файл: {e}")
                return False

            # ШАГ 8: Title
            logger.info(f"[{profile_name}] ✍️ Название...")
            try:
                title_input = page.locator('div[aria-label*="название"], div[aria-label*="title"]').first
                await title_input.click(timeout=3000)
                await asyncio.sleep(0.5)
                await page.keyboard.press('Control+A')
                await page.keyboard.press('Backspace')
                for char in title:
                    await page.keyboard.type(char)
                    await asyncio.sleep(random.uniform(0.05, 0.15))
            except Exception as e:
                logger.warning(f"[{profile_name}] ⚠️ Название: {e}")

            await asyncio.sleep(random.uniform(1, 2))

            # ШАГ 9: Description
            logger.info(f"[{profile_name}] ✍️ Описание...")
            try:
                desc_input = page.locator('div[aria-label*="описание"], div[aria-label*="description"]').first
                await desc_input.click(timeout=3000)
                await asyncio.sleep(0.5)
                for char in description:
                    await page.keyboard.type(char)
                    await asyncio.sleep(random.uniform(0.05, 0.15))
            except Exception as e:
                logger.warning(f"[{profile_name}] ⚠️ Описание: {e}")

            await asyncio.sleep(random.uniform(1, 2))

            # ШАГ 10: Not for kids
            logger.info(f"[{profile_name}] 🔞 Не для детей...")
            try:
                not_for_kids = page.locator('tp-yt-paper-radio-button[name="VIDEO_MADE_FOR_KIDS_NOT_MFK"]').first
                await not_for_kids.click(timeout=3000)
                await asyncio.sleep(1)
            except Exception as e:
                logger.warning(f"[{profile_name}] ⚠️ Не для детей: {e}")

            # ШАГ 11: Next 3 times
            for i in range(3):
                logger.info(f"[{profile_name}] ⏭️ Далее ({i + 1}/3)...")
                try:
                    next_button = page.locator('button:has-text("Далее"), button:has-text("Next")').first
                    await next_button.click(timeout=5000)
                    await asyncio.sleep(random.uniform(2, 3))
                except Exception as e:
                    logger.warning(f"[{profile_name}] ⚠️ Далее {i + 1}: {e}")

            # ШАГ 12: Visibility
            logger.info(f"[{profile_name}] 👁 Видимость: {visibility}...")
            try:
                if visibility.lower() == "public":
                    vis_radio = page.locator('tp-yt-paper-radio-button[name="PUBLIC"]').first
                elif visibility.lower() == "unlisted":
                    vis_radio = page.locator('tp-yt-paper-radio-button[name="UNLISTED"]').first
                else:
                    vis_radio = page.locator('tp-yt-paper-radio-button[name="PRIVATE"]').first
                await vis_radio.click(timeout=3000)
                await asyncio.sleep(1)
            except Exception as e:
                logger.warning(f"[{profile_name}] ⚠️ Видимость: {e}")

            # ШАГ 13: Publish
            logger.info(f"[{profile_name}] 🚀 Публикую...")
            try:
                publish_button = page.locator('button:has-text("Опубликовать"), button:has-text("Publish")').first
                await publish_button.click(timeout=5000)
                await asyncio.sleep(random.uniform(3, 5))
                logger.info(f"[{profile_name}] ✅ Видео загружено!")
                return True
            except Exception as e:
                logger.error(f"[{profile_name}] ❌ Публикация: {e}")
                return False

        except Exception as e:
            logger.error(f"[{profile_name}] ❌ Ошибка: {e}")
            return False

    async def upload_session(
            self,
            profile_name: str,
            videos_count: int = 3,
            pause_minutes: tuple = (2, 3)
    ):
        """Сессия загрузки"""
        if profile_name not in self.profiles:
            logger.error(f"❌ Профиль {profile_name} не найден!")
            return

        profile = self.profiles[profile_name]

        all_videos = self.get_video_files()
        if not all_videos:
            logger.error(f"❌ Нет видео!")
            return

        videos_to_upload = random.sample(all_videos, min(videos_count, len(all_videos)))

        logger.info(f"\n{'=' * 70}")
        logger.info(f"[{profile_name}] 🚀 Начинаю сессию загрузки")
        logger.info(f"[{profile_name}] 📹 Видео: {len(videos_to_upload)}")
        logger.info(f"{'=' * 70}\n")

        async with async_playwright() as playwright:
            user_data_path = self.profiles_dir / profile_name

            # ТОЧНАЯ КОПИЯ прокси из manager.py
            proxy_config = None
            if profile.proxy:
                proxy_config = {
                    'server': f'{profile.proxy.server}:{profile.proxy.port}',
                    'username': profile.proxy.username,
                    'password': profile.proxy.password
                }

            # ТОЧНАЯ КОПИЯ запуска из manager.py
            context = await playwright.chromium.launch_persistent_context(
                user_data_dir=user_data_path,
                channel='chrome',
                headless=False,
                user_agent=profile.fingerprint.navigator.userAgent,
                color_scheme='dark',
                viewport={
                    'width': profile.fingerprint.screen.width,
                    'height': profile.fingerprint.screen.height
                },
                extra_http_headers=only_injectable_headers(headers={
                    'Accept-Language': profile.fingerprint.headers.get(
                        'Accept-Language',
                        'en-US,en;q=0.9'
                    ),
                    **profile.fingerprint.headers,
                }, browser_name='chrome'),
                proxy=proxy_config,
                ignore_default_args=[
                    '--enable-automation',
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                ],
                args=self.get_extensions_args(),
            )

            # ТОЧНАЯ КОПИЯ inject из manager.py
            await context.add_init_script(
                InjectFunction(profile.fingerprint),
            )

            # ТОЧНАЯ КОПИЯ закрытия about:blank из manager.py
            for page in context.pages:
                if page.url == 'about:blank':
                    _ = asyncio.create_task(
                        self.close_page_with_delay(page, delay=0.25),
                    )

            # Создаем страницу
            page = await context.new_page()

            # Загружаем видео
            success_count = 0

            for i, video_path in enumerate(videos_to_upload, 1):
                logger.info(f"\n[{profile_name}] 📤 Видео {i}/{len(videos_to_upload)}")

                success = await self.upload_video(
                    page=page,
                    video_path=video_path,
                    profile_name=profile_name,
                )

                if success:
                    success_count += 1

                if i < len(videos_to_upload):
                    pause_sec = random.uniform(pause_minutes[0] * 60, pause_minutes[1] * 60)
                    logger.info(f"[{profile_name}] ⏸️ Пауза {int(pause_sec / 60)} мин...")
                    await asyncio.sleep(pause_sec)

            logger.info(f"\n{'=' * 70}")
            logger.info(f"[{profile_name}] 🎉 Завершено!")
            logger.info(f"[{profile_name}] ✅ Загружено: {success_count}/{len(videos_to_upload)}")
            logger.info(f"{'=' * 70}\n")

            await context.close()