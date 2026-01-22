"""
automation/uploaders/tiktok.py
TikTok загрузчик
"""

import asyncio
import logging
import random
from pathlib import Path
from playwright.async_api import Page

from automation.uploaders.base_uploader import BaseUploader

logger = logging.getLogger(__name__)


class TikTokUploader(BaseUploader):
    """Загрузчик для TikTok"""

    def __init__(self, profiles_dir: str = 'upload_profiles'):
        super().__init__(profiles_dir, 'tiktok')

    async def navigate_to_platform(self, page: Page, profile_name: str) -> Page:
        """
        Навигация в TikTok Upload

        Returns:
            Page: страница загрузки TikTok
        """
        try:
            # ШАГ 1: Google
            logger.info(f"[{profile_name}] 🔍 Открываю Google...")
            await page.goto('https://www.google.com', timeout=30000)
            await asyncio.sleep(random.uniform(2, 4))

            # ШАГ 2: Ищем tiktok
            logger.info(f"[{profile_name}] ⌨️ Ввожу 'tiktok'...")
            search_input = page.locator('textarea[name="q"]').first
            await search_input.click()
            await asyncio.sleep(random.uniform(0.5, 1))

            for char in "tiktok":
                await page.keyboard.type(char)
                await asyncio.sleep(random.uniform(0.1, 0.3))

            await page.keyboard.press('Enter')
            await asyncio.sleep(random.uniform(2, 4))

            # ШАГ 3: Переходим на TikTok
            logger.info(f"[{profile_name}] 🖱️ Перехожу на TikTok...")
            try:
                tiktok_link = page.locator('a[href*="tiktok.com"]').first
                await tiktok_link.click()
                await asyncio.sleep(random.uniform(3, 5))
            except:
                await page.goto('https://www.tiktok.com', timeout=30000)
                await asyncio.sleep(random.uniform(2, 4))

            # ШАГ 4: Ждем загрузку TikTok
            logger.info(f"[{profile_name}] ⏳ Жду загрузку TikTok...")
            await asyncio.sleep(random.uniform(5, 7))

            # ШАГ 5: Кликаем на кнопку Upload
            logger.info(f"[{profile_name}] ⬆️ Нажимаю Upload...")
            try:
                # Ищем кнопку Upload по SVG или тексту
                upload_button = page.locator('button:has-text("Upload"), div:has-text("Upload")').last
                await upload_button.click(timeout=20000)
                await asyncio.sleep(random.uniform(2, 3))
                logger.info(f"[{profile_name}] ✅ Переход в Upload")
            except Exception as e:
                logger.warning(f"[{profile_name}] ⚠️ Не нашел кнопку Upload через текст: {e}")
                # Альтернатива - прямой переход
                await page.goto('https://www.tiktok.com/creator-center/upload', timeout=30000)
                await asyncio.sleep(random.uniform(3, 5))

            # ШАГ 6: Проверяем что попали на страницу загрузки
            logger.info(f"[{profile_name}] ✅ Страница загрузки TikTok открыта")

            return page

        except Exception as e:
            logger.error(f"[{profile_name}] ❌ Ошибка навигации: {e}")
            raise

    async def upload_video(
            self,
            page: Page,
            video_path: Path,
            profile_name: str,
            caption: str = "Крутое видео! #fyp #viral",
            **kwargs
    ) -> bool:
        """Загрузить одно видео на TikTok"""
        try:
            logger.info(f"[{profile_name}] 📤 Загружаю: {video_path.name}")

            # ШАГ 7: Загружаем файл (кнопка "Select video")
            logger.info(f"[{profile_name}] 📁 Выбираю файл...")
            try:
                # Вариант 1: Кликаем на "Select video" кнопку
                select_button = page.locator('button[aria-label="Select video"], button:has-text("Select video")').first

                # Ищем input file (может быть скрыт)
                file_input = page.locator('input[type="file"]').first

                # Загружаем файл
                await file_input.set_input_files(str(video_path.absolute()))
                logger.info(f"[{profile_name}] ⏳ Файл загружается...")
                await asyncio.sleep(random.uniform(5, 10))

            except Exception as e:
                logger.error(f"[{profile_name}] ❌ Не удалось загрузить файл: {e}")
                return False

            # ШАГ 8: Проверяем Cancel окно (если появилось)
            logger.info(f"[{profile_name}] 🔍 Проверяю Cancel окно...")
            try:
                cancel_button = page.locator('button:has-text("Cancel")').first
                await cancel_button.click(timeout=3000)
                await asyncio.sleep(random.uniform(1, 2))
                logger.info(f"[{profile_name}] ✅ Нажал Cancel")
            except:
                logger.info(f"[{profile_name}] ℹ️ Cancel окно не найдено")

            # ШАГ 9: Caption (описание)
            logger.info(f"[{profile_name}] ✍️ Пишу caption...")
            try:
                # Ищем поле для caption
                caption_selectors = [
                    'div[contenteditable="true"][data-placeholder*="caption"]',
                    'div[contenteditable="true"][placeholder*="caption"]',
                    'div[contenteditable="true"]',
                    'textarea[placeholder*="caption"]',
                ]

                caption_input = None
                for selector in caption_selectors:
                    try:
                        caption_input = page.locator(selector).first
                        await caption_input.click(timeout=2000)
                        break
                    except:
                        continue

                if caption_input:
                    await asyncio.sleep(0.5)

                    # НОВОЕ: Очищаем поле (может быть текст по умолчанию)
                    await page.keyboard.press('Control+A')
                    await page.keyboard.press('Backspace')
                    await asyncio.sleep(0.3)

                    # Вводим caption побуквенно
                    for char in caption:
                        await page.keyboard.type(char)
                        await asyncio.sleep(random.uniform(0.05, 0.15))

                    logger.info(f"[{profile_name}] ✅ Caption добавлен")
                else:
                    logger.warning(f"[{profile_name}] ⚠️ Не нашел поле caption")

            except Exception as e:
                logger.warning(f"[{profile_name}] ⚠️ Caption: {e}")

            await asyncio.sleep(random.uniform(2, 3))

            # ШАГ 10: Настройки (Cover, Who can view, etc) - ПРОПУСКАЕМ ПОКА
            # TODO: Добавить настройки если нужно

            # ШАГ 11: Post/Publish
            logger.info(f"[{profile_name}] 🚀 Публикую...")
            try:
                post_button = page.locator('button[data-e2e="post_video_button"]').first
                await post_button.click(timeout=10000)

                logger.info(f"[{profile_name}] ⏳ Жду обработки видео...")
                await asyncio.sleep(random.uniform(3, 5))

                logger.info(f"[{profile_name}] ✅ Видео опубликовано!")

                # ШАГ 12: Переход к загрузке следующего видео (кнопка "+")
                logger.info(f"[{profile_name}] ➕ Перехожу к загрузке следующего...")
                try:
                    # Ищем кнопку "+" (Plus) для нового видео
                    plus_button = page.locator(
                        'button[data-tt="Sidebar_Sidebar_Button"]:has(svg[data-icon="plus-bold"])').last
                    await plus_button.click(timeout=5000)
                    await asyncio.sleep(random.uniform(2, 3))
                    logger.info(f"[{profile_name}] ✅ Готов к следующему видео")
                except Exception as e:
                    logger.warning(f"[{profile_name}] ⚠️ Не нашел кнопку '+': {e}")
                    # Альтернатива - прямой переход
                    await page.goto('https://www.tiktok.com/creator-center/upload', timeout=30000)
                    await asyncio.sleep(random.uniform(2, 3))

                return True

            except Exception as e:
                logger.error(f"[{profile_name}] ❌ Публикация: {e}")
                return False

        except Exception as e:
            logger.error(f"[{profile_name}] ❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()
            return False