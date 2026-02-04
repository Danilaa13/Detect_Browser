"""
automation module
Модуль автоматизации для работы с социальными платформами
"""

from .uploaders import YouTubeUploader, TikTokUploader, InstagramUploader
from .warmers import YouTubeWarmer, TikTokWarmer, InstagramWarmer

__all__ = [
    'YouTubeUploader',
    'TikTokUploader',
    'InstagramUploader',
    'YouTubeWarmer',
    'TikTokWarmer',
    'InstagramWarmer'
]