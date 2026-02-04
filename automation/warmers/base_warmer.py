"""
automation/warmers/base_warmer.py
Базовый класс для прогрева профилей (YouTube, TikTok, Instagram)
"""

import asyncio
import logging
import random
from abc import ABC, abstractmethod
from playwright.async_api import Page

from automation.base import BaseBrowser

logger = logging.getLogger(__name__)


class BaseWarmer(BaseBrowser, ABC):
    """Базовый класс для прогрева аккаунтов на платформах"""

    def __init__(self, profiles_dir: str, platform_name: str):
        """
        Args:
            profiles_dir: папка с профилями (обычно user_data)
            platform_name: название платформы (youtube, tiktok, instagram)
        """
        super().__init__(profiles_dir)
        self.platform_name = platform_name

    @abstractmethod
    async def navigate_to_platform(self, page: Page, profile_name: str) -> Page:
        """
        Навигация на платформу (переопределяется в каждом прогревателе)

        Args:
            page: начальная страница
            profile_name: имя профиля

        Returns:
            Page: страница платформы
        """
        pass

    @abstractmethod
    async def watch_content(self, page: Page, profile_name: str, duration_seconds: int):
        """
        Смотреть контент (видео/Shorts/Reels)

        Args:
            page: страница платформы
            profile_name: имя профиля
            duration_seconds: сколько секунд смотреть
        """
        pass

    @abstractmethod
    async def interact(self, page: Page, profile_name: str):
        """
        Взаимодействие (лайки, комментарии, подписки)

        Args:
            page: страница платформы
            profile_name: имя профиля
        """
        pass

    async def warm_session(
            self,
            profile_name: str,
            duration_minutes: int = 30,
            interaction_probability: float = 0.3
    ):
        """
        Сессия прогрева: открыть профиль и прогреть N минут

        Args:
            profile_name: имя профиля
            duration_minutes: длительность прогрева в минутах
            interaction_probability: вероятность взаимодействия (0.0-1.0)
        """
        if profile_name not in self.profiles:
            logger.error(f"❌ Профиль {profile_name} не найден!")
            return

        logger.info(f"\n{'=' * 70}")
        logger.info(f"[{profile_name}] 🔥 Начинаю прогрев на {self.platform_name.upper()}")
        logger.info(f"[{profile_name}] ⏱️ Длительность: {duration_minutes} минут")
        logger.info(f"{'=' * 70}\n")

        # Запускаем браузер
        context = await self.launch_browser(profile_name)

        try:
            # Создаем страницу
            page = await context.new_page()

            # ОДИН РАЗ переходим на платформу
            platform_page = await self.navigate_to_platform(page, profile_name)

            # Считаем время
            start_time = asyncio.get_event_loop().time()
            end_time = start_time + (duration_minutes * 60)

            iteration = 1

            while asyncio.get_event_loop().time() < end_time:
                remaining = int((end_time - asyncio.get_event_loop().time()) / 60)
                logger.info(f"\n[{profile_name}] 🔄 Итерация {iteration} (осталось ~{remaining} мин)")

                # Смотрим контент (случайная длительность)
                watch_duration = random.randint(30, 90)
                await self.watch_content(platform_page, profile_name, watch_duration)

                # Случайное взаимодействие
                if random.random() < interaction_probability:
                    await self.interact(platform_page, profile_name)

                # Пауза между итерациями
                pause = random.uniform(5, 15)
                logger.info(f"[{profile_name}] ⏸️ Пауза {int(pause)} сек...")
                await asyncio.sleep(pause)

                iteration += 1

            logger.info(f"\n{'=' * 70}")
            logger.info(f"[{profile_name}] ✅ Прогрев завершен!")
            logger.info(f"[{profile_name}] 📊 Выполнено итераций: {iteration - 1}")
            logger.info(f"{'=' * 70}\n")

        finally:
            # Правильное закрытие для Windows
            try:
                await context.close()
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.debug(f"Ошибка при закрытии context: {e}")