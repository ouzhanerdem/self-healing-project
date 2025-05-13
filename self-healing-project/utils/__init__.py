"""
Self-Healing Test Yardımcı Modülleri

Bu paket, self-healing test mekanizması için çeşitli yardımcı modülleri içerir.
"""

from pathlib import Path

# Paket yolu için yardımcı fonksiyon
def get_package_path():
    """Paket dizininin tam yolunu döndürür."""
    return Path(__file__).parent.absolute()