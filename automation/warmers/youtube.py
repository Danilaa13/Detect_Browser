"""
automation/warmers/youtube.py
YouTube Shorts прогрев (ПОЛНАЯ логика из manager.py)
"""

import asyncio
import logging
import random
from playwright.async_api import Page

from automation.warmers.base_warmer import BaseWarmer

logger = logging.getLogger(__name__)


class YouTubeWarmer(BaseWarmer):
    """Прогрев для YouTube Shorts с полной человекоподобной логикой"""

    def __init__(self, profiles_dir: str = 'user_data'):
        super().__init__(profiles_dir, 'youtube')

        # Список комментариев (как у тебя)
        self.comments = [
            "👍",
            "🔥🔥🔥",
            "Круто! 😍",
            "💯",
            "Супер! 👏",
            "❤️❤️❤️",
            "Класс! 🎉",
            "Огонь! 🔥",
            "😂😂😂",
            "Топ! 💪",
            "Шикарно! ✨",
            "👌👌👌",
            "Кайф! 🤩",
            "🥰",
            "Зачет! 👍👍",
        ]

    async def navigate_to_platform(self, page: Page, profile_name: str) -> Page:
        """
        Навигация в YouTube Shorts (ТОЧНАЯ копия из manager.py)

        Returns:
            Page: страница YouTube Shorts
        """
        try:
            logger.info(f"[{profile_name}] 🚀 Начинаю человекоподобную автоматизацию")

            # ШАГ 1: Открываем Google
            logger.info(f"[{profile_name}] 🔍 Открываю Google...")
            await page.goto('https://www.google.com', timeout=30000)
            await asyncio.sleep(random.uniform(2, 4))

            # ШАГ 2: Вводим "youtube" в поиск
            logger.info(f"[{profile_name}] ⌨️ Ввожу 'youtube' в поиск...")
            search_input = page.locator('textarea[name="q"]').first
            await search_input.click()
            await asyncio.sleep(random.uniform(0.5, 1))

            # Вводим по буквам (человекоподобно)
            for char in "youtube":
                await search_input.type(char)
                await asyncio.sleep(random.uniform(0.1, 0.3))

            await asyncio.sleep(random.uniform(1, 2))

            # ШАГ 3: Нажимаем Enter
            logger.info(f"[{profile_name}] 🔎 Ищу YouTube...")
            await page.keyboard.press('Enter')
            await asyncio.sleep(random.uniform(2, 4))

            # ШАГ 4: Кликаем на первую ссылку youtube.com
            logger.info(f"[{profile_name}] 🖱️ Кликаю на youtube.com...")
            try:
                youtube_link = page.locator('a[href*="youtube.com"]').first
                await youtube_link.click()
                await asyncio.sleep(random.uniform(3, 5))
            except:
                logger.info(f"[{profile_name}] ⚠️ Не нашел ссылку, перехожу напрямую...")
                await page.goto('https://www.youtube.com', timeout=30000)
                await asyncio.sleep(random.uniform(2, 4))

            # ШАГ 5: Переходим в Shorts (СНАЧАЛА!)
            logger.info(f"[{profile_name}] 📱 Перехожу в раздел Shorts...")
            try:
                shorts_button = page.locator('a[title="Shorts"], a[href*="/shorts"]').first
                await shorts_button.click()
                await asyncio.sleep(random.uniform(3, 5))
            except:
                logger.info(f"[{profile_name}] ⚠️ Не нашел кнопку, перехожу напрямую...")
                await page.goto('https://www.youtube.com/shorts', timeout=30000)
                await asyncio.sleep(random.uniform(2, 4))

            logger.info(f"[{profile_name}] ✅ В разделе Shorts!")

            # ШАГ 6: ТЕПЕРЬ ищем поисковую строку
            logger.info(f"[{profile_name}] 🔍 Кликаю на поиск...")
            try:
                search_input = page.locator('input.ytSearchboxComponentInput[name="search_query"]').first
                await search_input.click()
                await asyncio.sleep(random.uniform(0.5, 1))

                # ШАГ 7: Вводим #мотивация
                logger.info(f"[{profile_name}] ⌨️ Ввожу '#motivation'...")
                search_text = "#motivation"
                for char in search_text:
                    await page.keyboard.type(char)
                    await asyncio.sleep(random.uniform(0.1, 0.3))

                await asyncio.sleep(random.uniform(1, 2))

                # ШАГ 8: Нажимаем кнопку поиска
                logger.info(f"[{profile_name}] 🔎 Нажимаю поиск...")
                try:
                    search_button = page.locator('button.ytSearchboxComponentSearchButton[aria-label="Search"]').first
                    await search_button.click()
                except:
                    await page.keyboard.press('Enter')

                await asyncio.sleep(random.uniform(3, 5))

                # ШАГ 9: Кликаем на чип "Shorts"
                logger.info(f"[{profile_name}] 🎬 Выбираю фильтр 'Shorts'...")
                try:
                    shorts_chip = page.locator('chip-shape button:has-text("Shorts")').first
                    await shorts_chip.click()
                    await asyncio.sleep(random.uniform(2, 3))
                except Exception as e:
                    logger.warning(f"[{profile_name}] ⚠️ Не нашел чип Shorts: {e}")

                # ШАГ 10: Выбираем 2-й или 3-й шортс из списка
                shorts_position = random.choice([2, 3])
                logger.info(f"[{profile_name}] 🎯 Выбираю {shorts_position}-й шортс из результатов...")

                try:
                    await asyncio.sleep(2)
                    shorts_thumbnails = page.locator('a#thumbnail[href*="/shorts/"], ytd-video-renderer a#thumbnail')
                    target_short = shorts_thumbnails.nth(shorts_position - 1)
                    await target_short.click()
                    await asyncio.sleep(random.uniform(3, 5))
                    logger.info(f"[{profile_name}] ✅ Открыл {shorts_position}-й шортс!")
                except Exception as e:
                    logger.warning(f"[{profile_name}] ⚠️ Не удалось выбрать шортс: {e}")

            except Exception as e:
                logger.warning(f"[{profile_name}] ⚠️ Ошибка поиска: {e}")

            logger.info(f"[{profile_name}] ✅ YouTube Shorts открыт!")

            # Устанавливаем фокус (для работы клавиатуры)
            try:
                await page.click('body', timeout=2000)
                await asyncio.sleep(1)
            except:
                pass

            return page

        except Exception as e:
            logger.error(f"[{profile_name}] ❌ Ошибка навигации: {e}")
            raise

    async def watch_content(self, page: Page, profile_name: str, duration_seconds: int):
        """
        Смотреть Shorts с ПОЛНОЙ человекоподобной логикой
        """
        try:
            # Случайная пауза просмотра
            if random.random() < 0.15:
                # 15% - досматриваем до конца
                pause = random.uniform(20, 30)
                logger.info(f"[{profile_name}] 👀 Досматриваю видео до конца...")
            else:
                pause = random.uniform(5, 15)

            await asyncio.sleep(pause)
            logger.info(f"[{profile_name}] ✅ Посмотрел шортс ({int(pause)}s)")

            # Иногда возвращаемся к предыдущему (3%)
            if random.random() < 0.03:
                logger.info(f"[{profile_name}] ⬆️ Вернулся к предыдущему")
                await page.keyboard.press('ArrowUp')
                await asyncio.sleep(random.uniform(3, 8))
            else:
                # Листаем дальше
                logger.info(f"[{profile_name}] ⬇️ Листаю дальше")
                await page.keyboard.press('ArrowDown')
                await asyncio.sleep(random.uniform(1, 2))

            # Редко паузим/играем (2%)
            if random.random() < 0.02:
                try:
                    logger.info(f"[{profile_name}] ⏸️ Пауза...")
                    await page.keyboard.press('Space')
                    await asyncio.sleep(random.uniform(1, 3))
                    await page.keyboard.press('Space')
                    logger.info(f"[{profile_name}] ▶️ Продолжаю")
                except:
                    pass

            # Движения мыши (8%)
            if random.random() < 0.08:
                try:
                    x = random.randint(100, 800)
                    y = random.randint(100, 600)
                    await page.mouse.move(x, y)
                except:
                    pass

            # Скролл комментариев (5%)
            if random.random() < 0.05:
                try:
                    logger.info(f"[{profile_name}] 💬 Смотрю комментарии...")
                    await page.mouse.wheel(0, 300)
                    await asyncio.sleep(random.uniform(2, 4))
                    await page.mouse.wheel(0, -300)
                except:
                    pass

        except Exception as e:
            logger.debug(f"[{profile_name}] ⚠️ Ошибка просмотра: {e}")

    async def interact(self, page: Page, profile_name: str):
        """
        Взаимодействие: лайки, подписки, комментарии (с твоими процентами)
        """
        try:
            # Лайк (15%)
            if random.random() < 0.15:
                try:
                    like_button = page.locator('button[aria-label*="Нравится"], button[aria-label*="like"]').first
                    await like_button.click(timeout=2000)
                    logger.info(f"[{profile_name}] ❤️ Лайк")
                    await asyncio.sleep(random.uniform(0.5, 1.5))
                except Exception as e:
                    logger.debug(f"[{profile_name}] ⚠️ Лайк: {e}")

            # Подписка (5%)
            if random.random() < 0.05:
                try:
                    subscribe_button = page.locator(
                        'button:has-text("Подписаться"), button:has-text("Subscribe")').first
                    await subscribe_button.click(timeout=2000)
                    logger.info(f"[{profile_name}] 🔔 Подписался!")
                    await asyncio.sleep(random.uniform(1, 2))
                except Exception as e:
                    logger.debug(f"[{profile_name}] ⚠️ Подписка: {e}")

            # Комментарий (7%)
            if random.random() < 0.07:
                try:
                    comment_text = random.choice(self.comments)
                    logger.info(f"[{profile_name}] 💬 Пишу комментарий: {comment_text}")

                    # Открываем панель комментариев
                    comment_button = page.locator(
                        'button[aria-label*="комментари"], button[aria-label*="comment"]').first
                    await comment_button.click(timeout=3000)
                    await asyncio.sleep(random.uniform(1, 2))

                    # Кликаем на placeholder
                    placeholder = page.locator('#simplebox-placeholder').first
                    await placeholder.click(timeout=3000)
                    await asyncio.sleep(random.uniform(0.5, 1))

                    # Вводим текст побуквенно
                    input_field = page.locator('#contenteditable-root[contenteditable="true"]').first
                    for char in comment_text:
                        await input_field.type(char)
                        await asyncio.sleep(random.uniform(0.1, 0.3))

                    await asyncio.sleep(random.uniform(0.5, 1.5))

                    # Отправляем
                    submit_button = page.locator(
                        'button[aria-label*="Оставить комментарий"], button[aria-label*="Comment"]').first
                    await submit_button.click(timeout=2000)
                    logger.info(f"[{profile_name}] ✅ Комментарий отправлен")

                    await asyncio.sleep(random.uniform(1, 2))

                    # Закрываем панель
                    try:
                        close_button = page.locator('button[aria-label="Закрыть"], button[aria-label="Close"]').first
                        await close_button.click(timeout=2000)
                        logger.info(f"[{profile_name}] ✖️ Закрыл панель комментариев")
                        await asyncio.sleep(random.uniform(0.5, 1))
                    except:
                        await page.keyboard.press('Escape')
                        await asyncio.sleep(random.uniform(0.5, 1))

                except Exception as e:
                    logger.debug(f"[{profile_name}] ⚠️ Комментарий: {e}")

        except Exception as e:
            logger.debug(f"[{profile_name}] ⚠️ Ошибка взаимодействия: {e}")

    async def warm_session(
            self,
            profile_name: str,
            duration_minutes: int = 30,
            interaction_probability: float = 0.3
    ):
        """
        Сессия прогрева с ЧЕЛОВЕКОПОДОБНЫМ ЗАВЕРШЕНИЕМ (из твоего кода)
        """
        if profile_name not in self.profiles:
            logger.error(f"❌ Профиль {profile_name} не найден!")
            return

        logger.info(f"\n{'=' * 70}")
        logger.info(f"[{profile_name}] 🔥 Начинаю прогрев на YOUTUBE")
        logger.info(f"[{profile_name}] ⏱️ Длительность: {duration_minutes} минут")
        logger.info(f"{'=' * 70}\n")

        context = await self.launch_browser(profile_name)

        try:
            page = await context.new_page()
            platform_page = await self.navigate_to_platform(page, profile_name)

            start_time = asyncio.get_event_loop().time()
            end_time = start_time + (duration_minutes * 60)
            count = 0

            logger.info(f"[{profile_name}] 🔄 Начинаю цикл автоматизации")

            while asyncio.get_event_loop().time() < end_time:
                count += 1
                remaining = int((end_time - asyncio.get_event_loop().time()) / 60)
                logger.info(f"\n[{profile_name}] 🔄 Шортс #{count} (осталось ~{remaining} мин)")

                # Смотрим контент
                await self.watch_content(platform_page, profile_name, 60)

                # Случайное взаимодействие
                if random.random() < interaction_probability:
                    await self.interact(platform_page, profile_name)

                if count % 5 == 0:
                    logger.info(f"[{profile_name}] 📊 Просмотрено: {count} шортсов")

            # ЧЕЛОВЕКОПОДОБНОЕ ЗАВЕРШЕНИЕ (из твоего кода)
            logger.info(f"[{profile_name}] ⏱️ Время вышло, завершаю сессию...")

            # Досматриваем текущий
            logger.info(f"[{profile_name}] 👀 Досматриваю последний шортс...")
            await asyncio.sleep(random.uniform(5, 15))

            # Выбираем действие перед выходом
            exit_action = random.choice(['scroll_more', 'go_home', 'just_exit'])

            if exit_action == 'scroll_more':
                extra_shorts = random.randint(1, 2)
                logger.info(f"[{profile_name}] 📱 Листаю еще {extra_shorts} шортс...")
                for _ in range(extra_shorts):
                    await page.keyboard.press('ArrowDown')
                    await asyncio.sleep(random.uniform(3, 8))

            elif exit_action == 'go_home':
                logger.info(f"[{profile_name}] 🏠 Возвращаюсь на главную...")
                try:
                    home_button = page.locator('yt-icon#logo-icon, a#logo').first
                    await home_button.click(timeout=3000)
                    await asyncio.sleep(random.uniform(2, 4))

                    logger.info(f"[{profile_name}] 📜 Скроллю главную...")
                    await page.mouse.wheel(0, random.randint(500, 1500))
                    await asyncio.sleep(random.uniform(2, 5))
                except:
                    pass

            else:
                logger.info(f"[{profile_name}] 🚪 Просто выхожу...")
                await asyncio.sleep(random.uniform(1, 2))

            # Закрываем вкладку
            logger.info(f"[{profile_name}] 👋 Закрываю вкладку...")
            await page.keyboard.press('Control+W')
            await asyncio.sleep(random.uniform(1, 2))

            logger.info(f"\n{'=' * 70}")
            logger.info(f"[{profile_name}] ✅ Прогрев завершен!")
            logger.info(f"[{profile_name}] 📊 Просмотрено: {count} шортсов")
            logger.info(f"{'=' * 70}\n")

        finally:
            try:
                await context.close()
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.debug(f"Ошибка при закрытии context: {e}")