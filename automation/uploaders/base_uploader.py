"""
automation/uploaders/base_uploader.py
Базовый класс для загрузчиков видео (YouTube, TikTok, Instagram)
"""

import asyncio
import logging
import random
from pathlib import Path
from abc import ABC, abstractmethod
from playwright.async_api import Page

from automation.base import BaseBrowser

logger = logging.getLogger(__name__)


class BaseUploader(BaseBrowser, ABC):
    """Базовый класс для загрузки видео на платформы"""

    def __init__(self, profiles_dir: str, platform_name: str):
        """
        Args:
            profiles_dir: папка с профилями
            platform_name: название платформы (youtube, tiktok, instagram)
        """
        super().__init__(profiles_dir)
        self.platform_name = platform_name

        # Папка с видео для этой платформы
        base_dir = Path(__file__).parent.parent.parent
        self.videos_dir = base_dir / 'videos' / platform_name

        if not self.videos_dir.exists():
            logger.warning(f"⚠️ Папка {self.videos_dir} не существует")

    def get_video_files(self):
        """Получить список видео файлов"""
        if not self.videos_dir.exists():
            logger.error(f"❌ Папка {self.videos_dir}/ не найдена!")
            return []

        videos = list(self.videos_dir.glob('*.mp4'))
        logger.info(f"📹 Найдено {len(videos)} видео для {self.platform_name}")
        return videos

    @abstractmethod
    async def navigate_to_platform(self, page: Page, profile_name: str) -> Page:
        """
        Навигация на платформу (переопределяется в каждом загрузчике)

        Args:
            page: начальная страница
            profile_name: имя профиля

        Returns:
            Page: страница платформы (может быть новая вкладка)
        """
        pass

    @abstractmethod
    async def upload_video(
            self,
            page: Page,
            video_path: Path,
            profile_name: str,
            **kwargs
    ) -> bool:
        """
        Загрузить одно видео (переопределяется в каждом загрузчике)

        Args:
            page: страница платформы
            video_path: путь к видео
            profile_name: имя профиля
            **kwargs: дополнительные параметры (title, description, etc)

        Returns:
            bool: успешно ли загружено
        """
        pass

    async def upload_session(
            self,
            profile_name: str,
            videos_count: int = 3,
            pause_minutes: tuple = (2, 3),
            **upload_kwargs
    ):
        """
        Сессия загрузки: открыть профиль и загрузить N видео

        Args:
            profile_name: имя профиля
            videos_count: сколько видео загрузить
            pause_minutes: пауза между видео (мин, макс) в минутах
            **upload_kwargs: параметры для upload_video
        """
        if profile_name not in self.profiles:
            logger.error(f"❌ Профиль {profile_name} не найден!")
            return

        all_videos = self.get_video_files()
        if not all_videos:
            logger.error(f"❌ Нет видео для загрузки!")
            return

        # Выбираем случайные видео
        videos_to_upload = random.sample(all_videos, min(videos_count, len(all_videos)))

        logger.info(f"\n{'=' * 70}")
        logger.info(f"[{profile_name}] 🚀 Начинаю сессию загрузки на {self.platform_name.upper()}")
        logger.info(f"[{profile_name}] 📹 Видео: {len(videos_to_upload)}")
        logger.info(f"{'=' * 70}\n")

        # Запускаем браузер
        context = await self.launch_browser(profile_name)

        try:
            # Создаем начальную страницу
            page = await context.new_page()

            # ОДИН РАЗ переходим на платформу
            platform_page = await self.navigate_to_platform(page, profile_name)

            # Загружаем видео
            success_count = 0

            for i, video_path in enumerate(videos_to_upload, 1):
                logger.info(f"\n{'=' * 70}")
                logger.info(f"[{profile_name}] 📤 Видео {i}/{len(videos_to_upload)}")
                logger.info(f"{'=' * 70}")

                success = await self.upload_video(
                    page=platform_page,
                    video_path=video_path,
                    profile_name=profile_name,
                    **upload_kwargs
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


        finally:
            # Правильное закрытие для Windows
            try:
                await context.close()
                await asyncio.sleep(0.5)  # Даем время закрыться
            except Exception as e:
                logger.debug(f"Ошибка при закрытии context: {e}")