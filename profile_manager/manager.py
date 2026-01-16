"""
manager.py с АВТОМАТИЗАЦИЕЙ YouTube Shorts
Добавлена функция автоматизации действий в браузере
"""

import asyncio
import logging
import pickle
import random
from asyncio import Task
from pathlib import Path

from browserforge.fingerprints import FingerprintGenerator
from browserforge.headers import Browser
from browserforge.injectors.utils import InjectFunction, only_injectable_headers
from playwright.async_api import Page, async_playwright

from profile_manager.path import StealthPlaywrightPatcher
from profile_manager.structures import Profile, Proxy

logger = logging.getLogger(__name__)

# Настраиваем логгер для вывода в stdout (чтобы работало в multiprocessing)
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[logging.StreamHandler()]
)

USER_DATA_PATH = Path(__file__).parent.parent / 'user_data'
PROFILES_PATH = USER_DATA_PATH / 'profiles.pkl'
PROFILES_PATH.parent.mkdir(parents=True, exist_ok=True)
EXTENSIONS_PATH = Path(__file__).parent.parent / 'extensions'

StealthPlaywrightPatcher().apply_patches()


class ProfileManager:
    def __init__(self):
        self.profiles: dict[str, Profile] = {}
        self.running_tasks: dict[str, Task] = {}
        self.automation_enabled: bool = False  # Флаг автоматизации
        self.automation_duration: int = 0  # Сколько работать (0 = бесконечно)

        self.load_profiles()

    def load_profiles(self):
        try:
            if PROFILES_PATH.exists():
                with open(PROFILES_PATH, 'rb') as f:
                    self.profiles = pickle.load(f)
        except Exception:
            logger.exception('Error loading profiles')

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
            str(extension_path.resolve())
            for extension_path in EXTENSIONS_PATH.iterdir()
            if extension_path.is_dir()
        ]

        return ','.join(extension_dirs)

    def save_profiles(self):
        with open(PROFILES_PATH, 'wb') as f:
            pickle.dump(self.profiles, f)

    @staticmethod
    def parse_proxy(proxy_str: str | None) -> Proxy | None:
        if not proxy_str:
            return None

        parts = proxy_str.split(':')
        if len(parts) not in [3, 5]:
            raise ValueError(
                'Invalid proxy format. Use protocol:host:port or protocol:host:port:user:pass\n'
                'Where protocol is http or socks5. Socks5 does not supports user auth!',
            )

        return Proxy(
            server=f'{parts[0]}://{parts[1]}',
            port=int(parts[2]),
            username=parts[3] if len(parts) > 2 else None,
            password=parts[4] if len(parts) > 3 else None
        )

    async def create_profile(self, name: str, proxy_str: str | None = None) -> str:
        if name in self.profiles:
            raise ValueError(f'Profile "{name}" already exists')

        proxy = self.parse_proxy(proxy_str) if proxy_str else None

        fingerprint = FingerprintGenerator(
            browser=[
                Browser(name='chrome', min_version=130, max_version=130),
            ],
            os=('windows', 'macos'),
            device='desktop',
            locale=('en-US',),
            http_version=2,
        ).generate()

        self.profiles[name] = Profile(fingerprint=fingerprint, proxy=proxy)
        self.save_profiles()
        return name

    async def launch_profile(self, profile_name: str):
        if profile_name not in self.profiles:
            raise ValueError('Profile not found')

        if self.is_profile_running(profile_name):
            raise ValueError('Profile is already running')

        task = asyncio.create_task(self._run_browser(profile_name))
        self.running_tasks[profile_name] = task

    def enable_automation(self, duration_seconds: int = 0):
        """
        Включить автоматизацию YouTube Shorts

        Args:
            duration_seconds: сколько работать (0 = бесконечно)
        """
        self.automation_enabled = True
        self.automation_duration = duration_seconds
        logger.info(f"Автоматизация включена ({duration_seconds}s)")

    async def automate_youtube_shorts(self, page: Page, profile_name: str):
        """
        Автоматизация YouTube Shorts (ЧЕЛОВЕКОПОДОБНО)

        Args:
            page: страница браузера
            profile_name: имя профиля
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
                # Точный селектор из твоего HTML
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
                    # Точный селектор кнопки поиска
                    search_button = page.locator('button.ytSearchboxComponentSearchButton[aria-label="Search"]').first
                    await search_button.click()
                except:
                    # Или просто Enter
                    await page.keyboard.press('Enter')

                await asyncio.sleep(random.uniform(3, 5))

                # ШАГ 9: Кликаем на чип "Shorts"
                logger.info(f"[{profile_name}] 🎬 Выбираю фильтр 'Shorts'...")
                try:
                    # Точный селектор из твоего HTML
                    shorts_chip = page.locator('chip-shape button:has-text("Shorts")').first
                    await shorts_chip.click()
                    await asyncio.sleep(random.uniform(2, 3))
                except Exception as e:
                    logger.warning(f"[{profile_name}] ⚠️ Не нашел чип Shorts: {e}")

                # ШАГ 10: Выбираем 2-й или 3-й шортс из списка
                shorts_position = random.choice([2, 3])
                logger.info(f"[{profile_name}] 🎯 Выбираю {shorts_position}-й шортс из результатов...")

                try:
                    # Ищем миниатюры шортсов
                    await asyncio.sleep(2)  # Ждем загрузки результатов

                    # Варианты селекторов для шортсов в результатах
                    shorts_thumbnails = page.locator('a#thumbnail[href*="/shorts/"], ytd-video-renderer a#thumbnail')

                    # Кликаем на нужный по позиции
                    target_short = shorts_thumbnails.nth(shorts_position - 1)
                    await target_short.click()
                    await asyncio.sleep(random.uniform(3, 5))

                    logger.info(f"[{profile_name}] ✅ Открыл {shorts_position}-й шортс!")

                except Exception as e:
                    logger.warning(f"[{profile_name}] ⚠️ Не удалось выбрать шортс: {e}")

            except Exception as e:
                logger.warning(f"[{profile_name}] ⚠️ Ошибка поиска: {e}")
                # Если ошибка - остаемся на странице Shorts
                pass

            logger.info(f"[{profile_name}] ✅ YouTube Shorts открыт!")

            # ВАЖНО: Кликаем на страницу чтобы установить фокус (для работы клавиатуры)
            try:
                await page.click('body', timeout=2000)
                await asyncio.sleep(1)
            except:
                pass

            # ШАГ 10: ОСНОВНОЙ ЦИКЛ - листаем шортсы
            start_time = asyncio.get_event_loop().time()
            count = 0

            logger.info(f"[{profile_name}] 🔄 Начинаю цикл автоматизации (время работы: {self.automation_duration}s)")

            while True:
                # Проверяем время
                if self.automation_duration > 0:
                    elapsed = asyncio.get_event_loop().time() - start_time
                    if elapsed >= self.automation_duration:
                        logger.info(f"[{profile_name}] ⏱️ Время вышло, завершаю сессию...")

                        # ЧЕЛОВЕКОПОДОБНОЕ ЗАВЕРШЕНИЕ

                        # 1. Досматриваем текущий шортс до конца
                        logger.info(f"[{profile_name}] 👀 Досматриваю последний шортс...")
                        await asyncio.sleep(random.uniform(5, 15))

                        # 2. Выбираем ОДНО действие перед выходом (как реальный человек)
                        exit_action = random.choice(['scroll_more', 'go_home', 'just_exit'])

                        if exit_action == 'scroll_more':
                            # Листаем еще 1-2 шортса
                            extra_shorts = random.randint(1, 2)
                            logger.info(f"[{profile_name}] 📱 Листаю еще {extra_shorts} шортс...")
                            for _ in range(extra_shorts):
                                await page.keyboard.press('ArrowDown')
                                await asyncio.sleep(random.uniform(3, 8))

                        elif exit_action == 'go_home':
                            # Возвращаемся на главную
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
                            # just_exit - сразу выходим
                            logger.info(f"[{profile_name}] 🚪 Просто выхожу...")
                            await asyncio.sleep(random.uniform(1, 2))

                        # 3. Закрываем вкладку естественно
                        logger.info(f"[{profile_name}] 👋 Закрываю вкладку...")
                        await page.keyboard.press('Control+W')
                        await asyncio.sleep(random.uniform(1, 2))

                        logger.info(f"[{profile_name}] ✅ Сессия завершена естественно")
                        break

                logger.info(f"[{profile_name}] ⏬ Листаю вниз (шортс #{count + 1})")

                # Листаем вниз (следующий шортс)
                await page.keyboard.press('ArrowDown')
                count += 1

                # Случайная пауза 5-15 секунд (смотрим видео)
                # Иногда смотрим дольше (15% шанс смотреть 20-30 сек)
                if random.random() < 0.15:
                    pause = random.uniform(20, 30)
                    logger.info(f"[{profile_name}] 👀 Досматриваю видео до конца...")
                else:
                    pause = random.uniform(5, 15)

                await asyncio.sleep(pause)

                logger.info(f"[{profile_name}] ✅ Посмотрел шортс #{count} ({int(pause)}s)")

                # Иногда листаем ВВЕРХ (передумали, вернулись) - 3% шанс
                if random.random() < 0.03:
                    logger.info(f"[{profile_name}] ⬆️ Вернулся к предыдущему")
                    await page.keyboard.press('ArrowUp')
                    await asyncio.sleep(random.uniform(3, 8))
                    count -= 1

                # ЛАЙКАЕМ (15% шанс) - безопасный процент
                if random.random() < 0.15:
                    try:
                        # Ищем кнопку лайка по aria-label
                        like_button = page.locator('button[aria-label*="Нравится"], button[aria-label*="like"]').first
                        await like_button.click(timeout=2000)
                        logger.info(f"[{profile_name}] ❤️ Лайк")
                        await asyncio.sleep(random.uniform(0.5, 1.5))
                    except Exception as e:
                        logger.debug(f"[{profile_name}] ⚠️ Не удалось поставить лайк: {e}")

                # ПОДПИСЫВАЕМСЯ (5% шанс) - очень редко, как реальный человек
                if random.random() < 0.05:
                    try:
                        # Ищем кнопку подписки (русская и английская версия)
                        subscribe_button = page.locator(
                            'button:has-text("Подписаться"), button:has-text("Subscribe")').first
                        await subscribe_button.click(timeout=2000)
                        logger.info(f"[{profile_name}] 🔔 Подписался!")
                        await asyncio.sleep(random.uniform(1, 2))
                    except Exception as e:
                        logger.debug(f"[{profile_name}] ⚠️ Не удалось подписаться: {e}")

                # ПИШЕМ КОММЕНТАРИЙ (7% шанс) - редко, естественно
                if random.random() < 0.07:
                    try:
                        # Список готовых комментариев
                        comments = [
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

                        # Выбираем случайный комментарий
                        comment_text = random.choice(comments)

                        logger.info(f"[{profile_name}] 💬 Пишу комментарий: {comment_text}")

                        # ШАГ 1: Кликаем на кнопку "Посмотреть комментарии" чтобы открыть поле
                        comment_button = page.locator(
                            'button[aria-label*="комментари"], button[aria-label*="comment"]').first
                        await comment_button.click(timeout=3000)
                        await asyncio.sleep(random.uniform(1, 2))

                        # ШАГ 2: Кликаем на placeholder "Введите комментарий"
                        placeholder = page.locator('#simplebox-placeholder').first
                        await placeholder.click(timeout=3000)
                        await asyncio.sleep(random.uniform(0.5, 1))

                        # ШАГ 3: Вводим текст в поле contenteditable
                        input_field = page.locator('#contenteditable-root[contenteditable="true"]').first

                        # Вводим комментарий ПОБУКВЕННО
                        for char in comment_text:
                            await input_field.type(char)
                            await asyncio.sleep(random.uniform(0.1, 0.3))

                        await asyncio.sleep(random.uniform(0.5, 1.5))

                        # ШАГ 4: Отправляем комментарий
                        submit_button = page.locator(
                            'button[aria-label*="Оставить комментарий"], button[aria-label*="Comment"]').first
                        await submit_button.click(timeout=2000)
                        logger.info(f"[{profile_name}] ✅ Комментарий отправлен")

                        await asyncio.sleep(random.uniform(1, 2))

                        # ШАГ 5: ЗАКРЫВАЕМ панель комментариев (крестик)
                        try:
                            # Точный селектор из твоего HTML
                            close_button = page.locator(
                                'button[aria-label="Закрыть"], button[aria-label="Close"]').first
                            await close_button.click(timeout=2000)
                            logger.info(f"[{profile_name}] ✖️ Закрыл панель комментариев")
                            await asyncio.sleep(random.uniform(0.5, 1))
                        except:
                            # Если не нашли кнопку - пробуем ESC
                            await page.keyboard.press('Escape')
                            await asyncio.sleep(random.uniform(0.5, 1))
                    except Exception as e:
                        logger.debug(f"[{profile_name}] ⚠️ Не удалось написать комментарий: {e}")
                        pass

                # Иногда скроллим комментарии (5% шанс)
                if random.random() < 0.05:
                    try:
                        logger.info(f"[{profile_name}] 💬 Смотрю комментарии...")
                        await page.mouse.wheel(0, 300)
                        await asyncio.sleep(random.uniform(2, 4))
                        await page.mouse.wheel(0, -300)
                    except:
                        pass

                # Редко паузим видео и играем снова (2% шанс)
                if random.random() < 0.02:
                    try:
                        logger.info(f"[{profile_name}] ⏸️ Пауза...")
                        await page.keyboard.press('Space')  # Пауза
                        await asyncio.sleep(random.uniform(1, 3))
                        await page.keyboard.press('Space')  # Играть
                        logger.info(f"[{profile_name}] ▶️ Продолжаю")
                    except:
                        pass

                # Очень редко двигаем мышкой (имитация движений) - 8% шанс
                if random.random() < 0.08:
                    try:
                        # Случайное движение мыши
                        x = random.randint(100, 800)
                        y = random.randint(100, 600)
                        await page.mouse.move(x, y)
                    except:
                        pass

                if count % 5 == 0:
                    logger.info(f"[{profile_name}] 📊 Просмотрено: {count} шортсов")

            logger.info(f"[{profile_name}] ✅ Автоматизация завершена. Всего: {count} шортсов")

        except Exception as e:
            logger.error(f"[{profile_name}] ❌ Ошибка автоматизации: {e}")
            import traceback
            traceback.print_exc()

    async def update_proxy(self, profile_name: str, proxy_str: str | None):
        if profile_name not in self.profiles:
            raise ValueError('Profile not found')

        new_proxy = self.parse_proxy(proxy_str) if proxy_str else None
        self.profiles[profile_name].proxy = new_proxy
        self.save_profiles()

    def is_profile_running(self, profile_name: str) -> bool:
        task = self.running_tasks.get(profile_name)
        return task and not task.done()

    @staticmethod
    async def close_page_with_delay(page: Page, delay: float) -> None:
        await asyncio.sleep(delay)
        try:
            await page.close()
        except Exception:
            pass

    async def _run_browser(self, profile_name: str):
        try:
            profile = self.profiles[profile_name]
            async with async_playwright() as playwright:
                user_data_path = USER_DATA_PATH / profile_name

                proxy_config = None
                if profile.proxy:
                    proxy_config = {
                        'server': f'{profile.proxy.server}:{profile.proxy.port}',
                        'username': profile.proxy.username,
                        'password': profile.proxy.password
                    }

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

                await context.add_init_script(
                    InjectFunction(profile.fingerprint),
                )

                # Закрываем стартовую about:blank
                for page in context.pages:
                    if page.url == 'about:blank':
                        _ = asyncio.create_task(
                            self.close_page_with_delay(page, delay=0.25),
                        )

                # ЕСЛИ АВТОМАТИЗАЦИЯ ВКЛЮЧЕНА - работаем с YouTube
                if self.automation_enabled:
                    # Создаем ОДНУ чистую вкладку (как реальный человек)
                    page: Page = await context.new_page()
                    await self.automate_youtube_shorts(page, profile_name)
                    logger.info(f"[{profile_name}] ✅ Автоматизация завершена")
                    # НЕ делаем return! Пусть контекст остается открытым до конца async with

                else:
                    # ИНАЧЕ - обычный режим (как было)
                    for page_url in profile.page_urls or ['https://amiunique.org/fingerprint']:
                        page: Page = await context.new_page()
                        _ = asyncio.create_task(page.goto(page_url))

                    try:
                        while True:
                            await asyncio.sleep(0.25)

                            pages = context.pages
                            if not pages:
                                break

                            self.profiles[profile_name].page_urls = [
                                page.url
                                for page in pages
                                if page.url != 'about:blank'
                            ]
                    except Exception as e:
                        logger.error(f"Monitoring error: {e}")

        except Exception as e:
            logger.exception(f'Profile {profile_name} error: {e}')
        finally:
            _ = self.running_tasks.pop(profile_name, None)
            self.save_profiles()

    def get_profile_names(self) -> list[str]:
        return list(self.profiles.keys())

    def get_profile_status(self, profile_name: str) -> str:
        return 'running' if self.is_profile_running(profile_name) else 'stopped'
