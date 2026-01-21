"""
uploader.py - Загрузка YouTube Shorts
ПОЛНАЯ ВЕРСИЯ с одноразовой навигацией и закрытием диалогов
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

    async def navigate_to_studio(self, page: Page, profile_name: str) -> Page:
        """
        Навигация в YouTube Studio (ОДИН РАЗ в начале сессии)
        Возвращает новую страницу Studio
        """
        try:
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
            logger.info(f"[{profile_name}] 🖱️ Перехожу на YouTube...")
            try:
                youtube_link = page.locator('a[href*="youtube.com"]').first
                await youtube_link.click()
                await asyncio.sleep(random.uniform(3, 5))
            except:
                await page.goto('https://www.youtube.com', timeout=30000)
                await asyncio.sleep(random.uniform(2, 4))

            # ШАГ 4: Кликаем на кнопку профиля
            logger.info(f"[{profile_name}] 👤 Открываю меню профиля...")
            avatar_button = page.locator(
                'button#avatar-btn, button[aria-label*="Меню аккаунта"], button[aria-label*="Account menu"]').first
            await avatar_button.click(timeout=10000)
            await asyncio.sleep(random.uniform(1, 2))

            # ШАГ 5: YouTube Studio (может открыться в новой вкладке или той же)
            logger.info(f"[{profile_name}] 🎬 Выбираю YouTube Studio...")
            studio_link = page.locator(
                'tp-yt-paper-item:has-text("Творческая студия"), tp-yt-paper-item:has-text("YouTube Studio"), a:has-text("YouTube Studio")').first

            # Пробуем ждать новую вкладку (timeout 5 сек)
            studio_page = None
            try:
                async with page.context.expect_page(timeout=5000) as new_page_info:
                    await studio_link.click(timeout=5000)

                # Новая вкладка открылась!
                studio_page = await new_page_info.value
                logger.info(f"[{profile_name}] ✅ Открылась новая вкладка Studio")

            except Exception as e:
                # Новая вкладка НЕ открылась - значит переход в той же вкладке
                logger.info(f"[{profile_name}] ℹ️ Studio открылся в той же вкладке")
                studio_page = page

            # Ждем загрузку
            await studio_page.wait_for_load_state('networkidle', timeout=30000)
            logger.info(f"[{profile_name}] ✅ YouTube Studio загружен")
            await asyncio.sleep(random.uniform(3, 5))

            # ШАГ 6: Continue (если есть)
            logger.info(f"[{profile_name}] ➡️ Проверяю всплывающее окно...")
            try:
                continue_button = studio_page.locator(
                    'button[aria-label*="Continue"], button[aria-label*="Продолжить"], ytcp-button-shape button:has-text("Continue"), ytcp-button-shape button:has-text("Продолжить")').first
                await continue_button.click(timeout=3000)
                await asyncio.sleep(random.uniform(1, 2))
                logger.info(f"[{profile_name}] ✅ Нажал Continue")
            except:
                logger.info(f"[{profile_name}] ℹ️ Всплывающее окно не найдено")

            return studio_page

        except Exception as e:
            logger.error(f"[{profile_name}] ❌ Ошибка навигации: {e}")
            raise

    async def upload_video(
            self,
            page: Page,
            video_path: Path,
            profile_name: str,
            title: str = "Крутое видео #shorts",
            description: str = "Смотри это видео! #shorts #viral",
            visibility: str = "public"
    ):
        """Загрузить одно видео (уже в Studio!)"""
        try:
            logger.info(f"[{profile_name}] 📤 Загружаю: {video_path.name}")

            # ШАГ 7: Переходим в раздел Контент
            logger.info(f"[{profile_name}] 📂 Перехожу в раздел Контент...")
            try:
                content_button = page.locator(
                    'tp-yt-paper-icon-item.videos, tp-yt-paper-icon-item:has-text("Content"), tp-yt-paper-icon-item:has-text("Контент")').first
                await content_button.click(timeout=5000)
                await asyncio.sleep(random.uniform(2, 3))
            except Exception as e:
                logger.warning(f"[{profile_name}] ⚠️ Не нашел раздел Контент: {e}")

            # ШАГ 8: Нажимаем Upload videos / Добавить видео
            logger.info(f"[{profile_name}] ➕ Нажимаю 'Upload videos'...")
            try:
                upload_button = page.locator(
                    'button[aria-label="Upload videos"], button[aria-label="Добавить видео"], ytcp-button-shape button:has-text("Upload videos"), ytcp-button-shape button:has-text("Добавить видео")').first
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

            # ШАГ 10: Title
            logger.info(f"[{profile_name}] ✍️ Название...")
            try:
                title_input = page.locator(
                    'div[aria-label*="название"], div[aria-label*="title"], div[aria-label*="Title"]').first
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

            # ШАГ 11: Description
            logger.info(f"[{profile_name}] ✍️ Описание...")
            try:
                # Сначала закрываем dropdown от названия (если открыт)
                await page.keyboard.press('Escape')
                await asyncio.sleep(0.5)

                # Кликаем на поле описания
                desc_input = page.locator(
                    'ytcp-social-suggestions-textbox#description-textarea div#textbox[contenteditable="true"]').first
                await desc_input.click(timeout=5000, force=True)  # force=True игнорирует перекрытие
                await asyncio.sleep(0.5)

                # Очищаем
                await page.keyboard.press('Control+A')
                await page.keyboard.press('Backspace')
                await asyncio.sleep(0.3)

                # Вводим описание
                for char in description:
                    await page.keyboard.type(char)
                    await asyncio.sleep(random.uniform(0.05, 0.15))

                logger.info(f"[{profile_name}] ✅ Описание добавлено")
            except Exception as e:
                logger.warning(f"[{profile_name}] ⚠️ Описание: {e}")

            await asyncio.sleep(random.uniform(1, 2))

            # ШАГ 12: Not for kids
            logger.info(f"[{profile_name}] 🔞 Не для детей...")
            try:
                not_for_kids = page.locator('tp-yt-paper-radio-button[name="VIDEO_MADE_FOR_KIDS_NOT_MFK"]').first
                await not_for_kids.click(timeout=3000)
                await asyncio.sleep(1)
            except Exception as e:
                logger.warning(f"[{profile_name}] ⚠️ Не для детей: {e}")

            # ШАГ 13: Next 3 times
            for i in range(3):
                logger.info(f"[{profile_name}] ⏭️ Далее ({i + 1}/3)...")
                try:
                    next_button = page.locator('button:has-text("Далее"), button:has-text("Next")').first
                    await next_button.click(timeout=5000)
                    await asyncio.sleep(random.uniform(2, 3))
                except Exception as e:
                    logger.warning(f"[{profile_name}] ⚠️ Далее {i + 1}: {e}")

            # ШАГ 14: Visibility
            logger.info(f"[{profile_name}] 👁️ Видимость: {visibility}...")
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

            # ШАГ 15: Publish
            logger.info(f"[{profile_name}] 🚀 Публикую...")
            try:
                publish_button = page.locator('button:has-text("Опубликовать"), button:has-text("Publish")').first
                await publish_button.click(timeout=5000)

                logger.info(f"[{profile_name}] ⏳ Жду обработки видео...")

                # Ждем обработку (30-60 секунд)
                await asyncio.sleep(random.uniform(30, 60))

                # Закрываем диалог через JS клик (обходит visibility)
                logger.info(f"[{profile_name}] ✖️ Закрываю диалог...")
                try:
                    # Находим кнопку
                    close_button = page.locator(
                        'ytcp-button-shape button[aria-label="Закрыть"][aria-disabled="false"], ytcp-button-shape button[aria-label="Close"][aria-disabled="false"]').last

                    # Кликаем через JavaScript (игнорирует CSS visibility)
                    await close_button.evaluate('element => element.click()')
                    await asyncio.sleep(random.uniform(1, 2))
                    logger.info(f"[{profile_name}] ✅ Диалог закрыт")
                except Exception as e:
                    logger.warning(f"[{profile_name}] ⚠️ Ошибка закрытия: {e}")

                return True

            except Exception as e:
                logger.error(f"[{profile_name}] ❌ Публикация: {e}")
                return False

        except Exception as e:
            logger.error(f"[{profile_name}] ❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()
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
            for p in context.pages:
                if p.url == 'about:blank':
                    _ = asyncio.create_task(
                        self.close_page_with_delay(p, delay=0.25),
                    )

            # Создаем страницу
            page = await context.new_page()

            # ОДИН РАЗ переходим в YouTube Studio
            studio_page = await self.navigate_to_studio(page, profile_name)

            # Загружаем видео (УЖЕ В STUDIO!)
            success_count = 0

            for i, video_path in enumerate(videos_to_upload, 1):
                logger.info(f"\n{'=' * 70}")
                logger.info(f"[{profile_name}] 📤 Видео {i}/{len(videos_to_upload)}")
                logger.info(f"{'=' * 70}")

                success = await self.upload_video(
                    page=studio_page,  # Используем страницу Studio!
                    video_path=video_path,
                    profile_name=profile_name,
                )

                if success:
                    success_count += 1

                # Пауза перед следующим
                if i < len(videos_to_upload):
                    pause_sec = random.uniform(pause_minutes[0] * 60, pause_minutes[1] * 60)
                    logger.info(f"[{profile_name}] ⏸️ Пауза {int(pause_sec / 60)} мин...")
                    await asyncio.sleep(pause_sec)

            logger.info(f"\n{'=' * 70}")
            logger.info(f"[{profile_name}] 🎉 Сессия завершена!")
            logger.info(f"[{profile_name}] ✅ Загружено: {success_count}/{len(videos_to_upload)}")
            logger.info(f"{'=' * 70}\n")

            await context.close()
