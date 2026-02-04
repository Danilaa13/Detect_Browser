"""
automation/warmers/tiktok.py
TikTok прогрев
"""

import asyncio
import logging
import random
from playwright.async_api import Page

from automation.warmers.base_warmer import BaseWarmer

logger = logging.getLogger(__name__)


class TikTokWarmer(BaseWarmer):
    """Прогрев для TikTok"""

    def __init__(self, profiles_dir: str = 'user_data'):
        super().__init__(profiles_dir, 'tiktok')

    async def navigate_to_platform(self, page: Page, profile_name: str) -> Page:
        """Навигация в TikTok"""
        try:
            logger.info(f"[{profile_name}] 🔍 Открываю Google...")
            await page.goto('https://www.google.com', timeout=30000)
            await asyncio.sleep(random.uniform(2, 4))

            logger.info(f"[{profile_name}] ⌨️ Ввожу 'tiktok'...")
            search_input = page.locator('textarea[name="q"]').first
            await search_input.click()
            for char in "tiktok":
                await page.keyboard.type(char)
                await asyncio.sleep(random.uniform(0.1, 0.3))

            await page.keyboard.press('Enter')
            await asyncio.sleep(random.uniform(2, 4))

            logger.info(f"[{profile_name}] 🖱️ Перехожу на TikTok...")
            try:
                tiktok_link = page.locator('a[href*="tiktok.com"]').first
                await tiktok_link.click()
                await asyncio.sleep(random.uniform(3, 5))
            except:
                await page.goto('https://www.tiktok.com', timeout=30000)
                await asyncio.sleep(random.uniform(2, 4))

            logger.info(f"[{profile_name}] ✅ TikTok открыт")
            return page

        except Exception as e:
            logger.error(f"[{profile_name}] ❌ Ошибка навигации: {e}")
            raise

    async def watch_content(self, page: Page, profile_name: str, duration_seconds: int):
        """Смотреть TikTok видео"""
        try:
            watch_time = random.uniform(
                max(5, duration_seconds * 0.5),
                duration_seconds
            )

            logger.info(f"[{profile_name}] 👀 Смотрю видео (~{int(watch_time)} сек)...")
            await asyncio.sleep(watch_time)

            # Скролл вниз (следующее видео)
            logger.info(f"[{profile_name}] ⬇️ Листаю дальше...")
            await page.keyboard.press('ArrowDown')
            await asyncio.sleep(random.uniform(1, 2))

        except Exception as e:
            logger.debug(f"[{profile_name}] ⚠️ Ошибка просмотра: {e}")

    async def interact(self, page: Page, profile_name: str):
        """Взаимодействие: лайк"""
        try:
            logger.info(f"[{profile_name}] ❤️ Ставлю лайк...")
            # TODO: Добавить селектор кнопки лайка TikTok
            logger.info(f"[{profile_name}] ℹ️ TikTok взаимодействие в разработке")

        except Exception as e:
            logger.debug(f"[{profile_name}] ⚠️ Ошибка взаимодействия: {e}")