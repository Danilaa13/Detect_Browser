"""
automation/testers/youtube_activity_tester.py
YouTube Activity Tester - для проверки активности аккаунта и бана
"""

import asyncio
import logging
import random
from playwright.async_api import Page

from automation.base import BaseBrowser

logger = logging.getLogger(__name__)


class YouTubeActivityTester(BaseBrowser):
    """Тестер активности YouTube аккаунта через комментирование видео"""

    def __init__(self, profiles_dir: str = 'user_data'):
        super().__init__(profiles_dir)

        # Список поисковых запросов (10 англоязычных запросов по бизнесу/мотивации)
        self.video_queries = [
            "business motivation 2024",
            "how to start a business",
            "entrepreneurship tips",
            "business podcast best moments",
            "success motivation speech",
            "startup advice for beginners",
            "business mindset transformation",
            "productivity tips for entrepreneurs",
            "business growth strategies",
            "motivational speech for success"
        ]

        # Расширенный список комментариев на английском
        self.comments = [
            "Great content! 👍",
            "Thanks for sharing! 🔥",
            "Very motivating! 💪",
            "Useful tips!",
            "Inspiring! ✨",
            "Love this!",
            "Exactly what I needed to hear!",
            "Awesome advice! 💯",
            "This helped me a lot!",
            "Keep it up! 🙌",
            "Amazing content!",
            "So valuable! 💎",
            "Saved this video!",
            "Really appreciate this! ❤️",
            "Mind blown! 🤯",
            "This is gold! 🏆",
            "Implementing this right now!",
            "Thank you so much!",
            "Subscribed! 🔔",
            "Need more of this content!",
            "Best video on this topic!",
            "Very helpful, thank you! 🙏",
            "Game changer! 💥",
            "Absolutely brilliant!",
            "Pure wisdom! 🧠"
        ]

    async def navigate_to_youtube(self, page: Page, profile_name: str) -> Page:
        """
        Открыть YouTube через Google поиск (человекоподобно)

        Args:
            page: страница браузера
            profile_name: имя профиля

        Returns:
            Page: страница YouTube
        """
        try:
            logger.info(f"[{profile_name}] 🚀 Открываю YouTube...")

            # Открываем Google
            await page.goto('https://www.google.com', timeout=30000)
            await asyncio.sleep(random.uniform(2, 4))

            # Ищем YouTube
            search_input = page.locator('textarea[name="q"]').first
            await search_input.click()
            await asyncio.sleep(random.uniform(0.5, 1))

            for char in "youtube":
                await search_input.type(char)
                await asyncio.sleep(random.uniform(0.1, 0.3))

            await asyncio.sleep(random.uniform(1, 2))
            await page.keyboard.press('Enter')
            await asyncio.sleep(random.uniform(2, 4))

            # Кликаем на youtube.com
            try:
                youtube_link = page.locator('a[href*="youtube.com"]').first
                await youtube_link.click()
                await asyncio.sleep(random.uniform(3, 5))
            except:
                await page.goto('https://www.youtube.com', timeout=30000)
                await asyncio.sleep(random.uniform(2, 4))

            logger.info(f"[{profile_name}] ✅ YouTube открыт!")
            return page

        except Exception as e:
            logger.error(f"[{profile_name}] ❌ Ошибка открытия YouTube: {e}")
            raise

    async def search_and_open_video(self, page: Page, profile_name: str, query: str) -> bool:
        """
        Найти видео по запросу и открыть первое

        Args:
            page: страница YouTube
            profile_name: имя профиля
            query: поисковый запрос

        Returns:
            bool: True если видео открыто, False если ошибка
        """
        try:
            logger.info(f"[{profile_name}] 🔍 Ищу: '{query}'")

            # Кликаем на поиск
            search_button = page.locator('button#search-icon-legacy, ytd-searchbox button').first
            await search_button.click()
            await asyncio.sleep(random.uniform(0.5, 1))

            # Вводим запрос
            search_input = page.locator('input#search, input[name="search_query"]').first
            await search_input.click()
            await asyncio.sleep(random.uniform(0.3, 0.7))

            # Очищаем поле (если там что-то было)
            await search_input.press('Control+A')
            await asyncio.sleep(0.2)

            # Вводим по буквам
            for char in query:
                await search_input.type(char)
                await asyncio.sleep(random.uniform(0.05, 0.15))

            await asyncio.sleep(random.uniform(1, 2))
            await page.keyboard.press('Enter')
            await asyncio.sleep(random.uniform(3, 5))

            logger.info(f"[{profile_name}] 🎯 Открываю первое видео...")

            # Ждем загрузки результатов
            await asyncio.sleep(2)

            # Кликаем на первое видео (НЕ Shorts, НЕ реклама)
            video_selector = 'ytd-video-renderer a#video-title, ytd-video-renderer h3 a'
            first_video = page.locator(video_selector).first
            await first_video.click()
            await asyncio.sleep(random.uniform(4, 6))

            logger.info(f"[{profile_name}] ✅ Видео открыто!")
            return True

        except Exception as e:
            logger.error(f"[{profile_name}] ❌ Ошибка поиска/открытия видео: {e}")
            return False

    async def post_comment(self, page: Page, profile_name: str, comment_text: str) -> bool:
        """
        Опубликовать один комментарий

        Args:
            page: страница с видео
            profile_name: имя профиля
            comment_text: текст комментария

        Returns:
            bool: True если комментарий опубликован, False если ошибка
        """
        try:
            logger.info(f"[{profile_name}] 💬 Пишу комментарий: '{comment_text}'")

            # Скроллим к секции комментариев
            await page.mouse.wheel(0, 600)
            await asyncio.sleep(random.uniform(1, 2))

            # Кликаем на поле ввода комментария
            comment_input = page.locator('#simplebox-placeholder').first
            await comment_input.click(timeout=5000)
            await asyncio.sleep(random.uniform(1, 2))

            # Вводим комментарий побуквенно
            editable_field = page.locator('#contenteditable-root[contenteditable="true"]').first
            for char in comment_text:
                await editable_field.type(char)
                await asyncio.sleep(random.uniform(0.08, 0.2))

            await asyncio.sleep(random.uniform(1, 2))

            # Нажимаем кнопку "Оставить комментарий"
            submit_button = page.locator('button#submit-button[aria-label*="Comment"], button#submit-button:has-text("Comment")').first
            await submit_button.click(timeout=3000)
            await asyncio.sleep(random.uniform(2, 3))

            logger.info(f"[{profile_name}] ✅ Комментарий опубликован!")
            return True

        except Exception as e:
            logger.error(f"[{profile_name}] ❌ Ошибка публикации комментария: {e}")
            return False

    async def test_activity(
        self,
        profile_name: str,
        comments_per_video: int = 5,
        comment_interval_minutes: int = 2,
        video_queries: list = None
    ):
        """
        Основная функция тестирования активности

        Args:
            profile_name: имя профиля
            comments_per_video: количество комментариев под каждым видео
            comment_interval_minutes: интервал между комментариями в минутах
            video_queries: список поисковых запросов (если None, используется self.video_queries)
        """
        if profile_name not in self.profiles:
            logger.error(f"❌ Профиль {profile_name} не найден!")
            return

        queries = video_queries or self.video_queries
        total_videos = len(queries)
        total_comments = total_videos * comments_per_video
        total_time_minutes = (total_comments - 1) * comment_interval_minutes

        logger.info(f"\n{'=' * 70}")
        logger.info(f"[{profile_name}] 🧪 ТЕСТ АКТИВНОСТИ YOUTUBE")
        logger.info(f"{'=' * 70}")
        logger.info(f"📹 Видео: {total_videos}")
        logger.info(f"💬 Комментариев на видео: {comments_per_video}")
        logger.info(f"⏱️  Интервал: {comment_interval_minutes} мин")
        logger.info(f"⏳ Примерное время: ~{total_time_minutes} минут")
        logger.info(f"{'=' * 70}\n")

        context = await self.launch_browser(profile_name)

        try:
            page = await context.new_page()
            await self.navigate_to_youtube(page, profile_name)

            successful_videos = 0
            successful_comments = 0
            failed_comments = 0

            # Обрабатываем каждое видео
            for video_num, query in enumerate(queries, 1):
                logger.info(f"\n{'=' * 70}")
                logger.info(f"[{profile_name}] 📹 ВИДЕО {video_num}/{total_videos}")
                logger.info(f"{'=' * 70}")

                # Открываем видео
                video_opened = await self.search_and_open_video(page, profile_name, query)

                if not video_opened:
                    logger.warning(f"[{profile_name}] ⚠️ Пропускаю видео {video_num}")
                    continue

                successful_videos += 1

                # Ждем загрузки видео
                await asyncio.sleep(random.uniform(3, 5))

                # Оставляем комментарии
                for comment_num in range(1, comments_per_video + 1):
                    comment_text = random.choice(self.comments)

                    logger.info(f"[{profile_name}] 💬 Комментарий {comment_num}/{comments_per_video}")

                    success = await self.post_comment(page, profile_name, comment_text)

                    if success:
                        successful_comments += 1
                    else:
                        failed_comments += 1

                    # Ждем перед следующим комментарием (кроме последнего)
                    if comment_num < comments_per_video:
                        wait_seconds = comment_interval_minutes * 60
                        logger.info(f"[{profile_name}] ⏳ Жду {comment_interval_minutes} мин перед следующим...")
                        await asyncio.sleep(wait_seconds)

                # Если это не последнее видео, переходим к следующему
                if video_num < total_videos:
                    logger.info(f"[{profile_name}] ➡️ Перехожу к следующему видео...")
                    await asyncio.sleep(random.uniform(2, 4))

            # Итоговая статистика
            logger.info(f"\n{'=' * 70}")
            logger.info(f"[{profile_name}] 📊 СТАТИСТИКА ТЕСТА")
            logger.info(f"{'=' * 70}")
            logger.info(f"✅ Обработано видео: {successful_videos}/{total_videos}")
            logger.info(f"✅ Успешных комментариев: {successful_comments}")
            logger.info(f"❌ Неудачных комментариев: {failed_comments}")
            logger.info(f"📈 Успешность: {(successful_comments / total_comments * 100):.1f}%")
            logger.info(f"{'=' * 70}\n")

            # Человекоподобное завершение
            logger.info(f"[{profile_name}] 👋 Завершаю сессию...")
            await asyncio.sleep(random.uniform(2, 4))

            # Закрываем вкладку
            await page.keyboard.press('Control+W')
            await asyncio.sleep(random.uniform(1, 2))

            logger.info(f"[{profile_name}] ✅ Тест завершен!")

        except Exception as e:
            logger.error(f"[{profile_name}] ❌ Критическая ошибка: {e}")
            import traceback
            traceback.print_exc()

        finally:
            try:
                await context.close()
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.debug(f"Ошибка при закрытии context: {e}")
