"""
automation/base/browser.py
Базовый класс для запуска браузера (общий для всех платформ)
"""

import asyncio
import logging
import pickle
from pathlib import Path
from playwright.async_api import async_playwright, BrowserContext

from browserforge.injectors.utils import InjectFunction, only_injectable_headers
from profile_manager.path import StealthPlaywrightPatcher
from profile_manager.structures import Profile

# Применяем патчи ОДИН РАЗ при импорте
StealthPlaywrightPatcher().apply_patches()

logger = logging.getLogger(__name__)

EXTENSIONS_PATH = Path(__file__).parent.parent.parent / 'extensions'


class BaseBrowser:
    """Базовый класс для работы с браузером"""

    def __init__(self, profiles_dir: str):
        """
        Args:
            profiles_dir: папка с профилями (upload_profiles, design_profiles, active_profiles)
        """
        base_dir = Path(__file__).parent.parent.parent
        self.profiles_dir = base_dir / profiles_dir
        self.profiles_path = self.profiles_dir / 'profiles.pkl'
        self.profiles = {}
        self.load_profiles()

    def load_profiles(self):
        """Загрузить профили из pickle"""
        try:
            if self.profiles_path.exists():
                with open(self.profiles_path, 'rb') as f:
                    self.profiles = pickle.load(f)
                logger.info(f"✅ Загружено {len(self.profiles)} профилей из {self.profiles_dir.name}/")
            else:
                logger.error(f"❌ Не найден {self.profiles_path}")
        except Exception as e:
            logger.exception(f'Ошибка загрузки профилей: {e}')

    def get_extensions_args(self) -> list[str]:
        """Получить аргументы для загрузки расширений (из manager.py)"""
        extensions_patches: str = self.get_extensions_patches()
        if not extensions_patches:
            return []
        return [
            f"--disable-extensions-except={extensions_patches}",
            f"--load-extension={extensions_patches}",
        ]

    @staticmethod
    def get_extensions_patches() -> str:
        """Получить пути к расширениям"""
        if not EXTENSIONS_PATH.exists():
            return ''
        extension_dirs = [
            str(ext_dir) for ext_dir in EXTENSIONS_PATH.iterdir()
            if ext_dir.is_dir() and (ext_dir / 'manifest.json').exists()
        ]
        return ','.join(extension_dirs)

    @staticmethod
    async def close_page_with_delay(page, delay: float = 0.1):
        """Закрыть страницу с задержкой"""
        await asyncio.sleep(delay)
        await page.close()

    async def launch_browser(self, profile_name: str) -> BrowserContext:
        """
        Запустить браузер для профиля (ТОЧНАЯ КОПИЯ из manager.py)

        Returns:
            BrowserContext с открытым браузером
        """
        if profile_name not in self.profiles:
            raise ValueError(f"Профиль {profile_name} не найден!")

        profile = self.profiles[profile_name]
        user_data_path = self.profiles_dir / profile_name

        playwright = await async_playwright().start()

        # Прокси
        proxy_config = None
        if profile.proxy:
            proxy_config = {
                'server': f'{profile.proxy.server}:{profile.proxy.port}',
                'username': profile.proxy.username,
                'password': profile.proxy.password
            }

        # Запуск браузера - ТОЧНАЯ КОПИЯ из manager.py
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir=str(user_data_path),
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

        # Inject fingerprint script
        await context.add_init_script(
            InjectFunction(profile.fingerprint),
        )

        # Закрываем about:blank
        for p in context.pages:
            if p.url == 'about:blank':
                _ = asyncio.create_task(
                    self.close_page_with_delay(p, delay=0.25),
                )

        return context