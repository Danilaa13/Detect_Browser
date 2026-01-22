"""
automation/uploaders/youtube.py
YouTube Shorts загрузчик
"""

import asyncio
import logging
import random
from pathlib import Path
from playwright.async_api import Page

from automation.uploaders.base_uploader import BaseUploader

logger = logging.getLogger(__name__)


class YouTubeUploader(BaseUploader):
    """Загрузчик для YouTube Shorts"""

    def __init__(self, profiles_dir: str = 'upload_profiles'):
        super().__init__(profiles_dir, 'youtube')

    async def navigate_to_platform(self, page: Page, profile_name: str) -> Page:
        """
        Навигация в YouTube Studio

        Returns:
            Page: страница YouTube Studio (может быть новая вкладка)
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

            # ШАГ 4: Ждем загрузку YouTube и кнопку профиля
            logger.info(f"[{profile_name}] 👤 Жду загрузку YouTube...")
            try:
                avatar_button = page.locator(
                    'button#avatar-btn, button[aria-label*="Меню аккаунта"], button[aria-label*="Account menu"]').first
                await avatar_button.wait_for(state='visible', timeout=30000)

                logger.info(f"[{profile_name}] 👤 Открываю меню профиля...")
                await avatar_button.click(timeout=10000)
                await asyncio.sleep(random.uniform(1, 2))

            except Exception as e:
                logger.error(f"[{profile_name}] ❌ Не нашел кнопку профиля: {e}")
                logger.info(f"[{profile_name}] 📍 URL: {page.url}")
                raise

            # ШАГ 5: YouTube Studio (может открыться в новой вкладке или той же)
            logger.info(f"[{profile_name}] 🎬 Выбираю YouTube Studio...")
            studio_link = page.locator(
                'tp-yt-paper-item:has-text("Творческая студия"), tp-yt-paper-item:has-text("YouTube Studio"), a:has-text("YouTube Studio")').first

            # Пробуем ждать новую вкладку (timeout 5 сек)
            studio_page = None
            try:
                async with page.context.expect_page(timeout=7000) as new_page_info:
                    await studio_link.click(timeout=7000)

                # Новая вкладка открылась!
                studio_page = await new_page_info.value
                logger.info(f"[{profile_name}] ✅ Открылась новая вкладка Studio")

            except Exception:
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
    ) -> bool:
        """Загрузить одно видео на YouTube"""
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

            # ШАГ 8: Нажимаем Upload videos
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
                    'ytcp-social-suggestions-textbox#title-textarea div#textbox[contenteditable="true"]').first
                await title_input.click(timeout=3000)
                await asyncio.sleep(0.5)
                await page.keyboard.press('Control+A')
                await page.keyboard.press('Backspace')
                await asyncio.sleep(0.3)
                for char in title:
                    await page.keyboard.type(char)
                    await asyncio.sleep(random.uniform(0.05, 0.15))
                logger.info(f"[{profile_name}] ✅ Название добавлено")
            except Exception as e:
                logger.warning(f"[{profile_name}] ⚠️ Название: {e}")

            await asyncio.sleep(random.uniform(1, 2))

            # ШАГ 11: Description
            logger.info(f"[{profile_name}] ✍️ Описание...")
            try:
                # Закрываем dropdown от названия
                await page.keyboard.press('Escape')
                await asyncio.sleep(0.5)

                desc_input = page.locator(
                    'ytcp-social-suggestions-textbox#description-textarea div#textbox[contenteditable="true"]').first
                await desc_input.click(timeout=5000, force=True)
                await asyncio.sleep(0.5)
                await page.keyboard.press('Control+A')
                await page.keyboard.press('Backspace')
                await asyncio.sleep(0.3)
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
                await asyncio.sleep(random.uniform(30, 60))

                # Закрываем диалог через JS клик
                logger.info(f"[{profile_name}] ✖️ Закрываю диалог...")
                try:
                    close_button = page.locator(
                        'ytcp-button-shape button[aria-label="Закрыть"][aria-disabled="false"], ytcp-button-shape button[aria-label="Close"][aria-disabled="false"]').last
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