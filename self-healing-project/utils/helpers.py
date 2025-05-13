"""
Self-Healing Test Yardımcı Fonksiyonları

Bu modül, test projesinde kullanılan genel yardımcı fonksiyonları içerir.
Gerçekten kullanılan fonksiyonlarla sınırlandırılmış ve optimize edilmiştir.
"""

import os
import json
import logging
from pathlib import Path
import time
import re
from dotenv import load_dotenv

def setup_logging(log_file=None, level=logging.INFO):
    """
    Loglama yapılandırmasını ayarlar.
    
    Args:
        log_file (str, optional): Log dosyasının yolu
        level (int, optional): Loglama seviyesi, varsayılan olarak INFO
        
    Returns:
        logging.Logger: Logger nesnesi
    """
    handlers = [logging.StreamHandler()]
    
    if log_file:
        handlers.append(logging.FileHandler(log_file, mode="w"))
    
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers
    )
    
    return logging.getLogger(__name__)

def load_env_variables(env_file=None):
    """
    Environment değişkenlerini .env dosyasından yükler.
    
    Args:
        env_file (str, optional): .env dosyasının yolu
        
    Returns:
        dict: Environment değişkenlerini içeren sözlük
    """
    if env_file:
        load_dotenv(env_file)
    else:
        load_dotenv()
    
    # Test için kullanılan temel değişkenleri al
    env_vars = {
        "browser": os.getenv("BROWSER", "chromium"),
        "headless": os.getenv("HEADLESS", "true").lower() == "true",
        "base_url": os.getenv("TEST_URL", "https://tgoyemek.com"),
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "screenshot_dir": os.getenv("SCREENSHOT_DIR", "screenshots"),
        "timeout": int(os.getenv("TIMEOUT", "30"))
    }
    
    return env_vars

def get_project_root():
    """
    Proje kök dizininin yolunu döndürür.
    
    Returns:
        Path: Proje kök dizini
    """
    # utils paketinin içindeki helpers.py dosyasının konumundan 2 seviye yukarı
    return Path(__file__).parent.parent.absolute()

def update_locator_database(force_update=False):
    """
    Locator veritabanını varsayılan değerlerle günceller/oluşturur.
    Eğer veritabanı dosyası yoksa veya force_update True ise, yeni bir 
    veritabanı oluşturulur; tüm varsayılan lokatorlar ile yüklenir.
    
    Args:
        force_update (bool): Zorla güncelleme yapılıp yapılmayacağı
        
    Returns:
        bool: Güncelleme başarılı ise True, değilse False
    """
    logger = logging.getLogger(__name__)
    project_root = get_project_root()
    locator_db_file = project_root / "locator_db.json"
    
    # Dosyanın var olup olmadığını ve yaşını kontrol et
    create_new = False
    
    if not locator_db_file.exists():
        logger.info("Locator veritabanı bulunamadı, yeni veritabanı oluşturuluyor")
        create_new = True
    elif force_update:
        logger.info("Locator veritabanı zorla güncelleniyor")
        create_new = True
    else:
        # Dosya yaşını kontrol et (7 günden eski mi?)
        file_age = time.time() - locator_db_file.stat().st_mtime
        if file_age > 7 * 24 * 60 * 60:  # 7 gün
            logger.info("Locator veritabanı 7 günden eski, güncelleniyor")
            create_new = True
    
    if create_new:
        try:
            # Varsayılan veritabanını oluştur
            locator_db = _generate_default_locator_database()
            
            # Varsa eski veritabanını yedekle
            if locator_db_file.exists():
                backup_file = project_root / f"locator_db_backup_{int(time.time())}.json"
                import shutil
                shutil.copy2(locator_db_file, backup_file)
                logger.info(f"Eski veritabanı yedeklendi: {backup_file}")
            
            # Yeni veritabanını kaydet
            with open(locator_db_file, 'w', encoding='utf-8') as f:
                json.dump(locator_db, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Yeni locator veritabanı oluşturuldu: {locator_db_file}")
            return True
        except Exception as e:
            logger.error(f"Locator veritabanı güncellenirken hata: {e}")
            return False
    else:
        logger.debug("Locator veritabanı güncel, güncelleme yapılmadı")
        return True

def _generate_default_locator_database():
    """
    Varsayılan locator veritabanı sözlüğünü oluşturur.
    
    Returns:
        dict: Varsayılan locator veritabanı sözlüğü
    """
    # Varsayılan zaman damgası
    timestamp = time.time()
    
    # Varsayılan veri yapısı
    locator_db = {
        "arama_kutusu": {
            "strategies": [
                {
                    "type": "css",
                    "selector": "input[type='search'], .search-input, [placeholder*='ara'], input[name='search']",
                    "last_used": timestamp
                },
                {
                    "type": "css",
                    "selector": "input[placeholder]",
                    "last_used": timestamp - 100  # Biraz daha eski
                },
                {
                    "type": "xpath",
                    "selector": "//input[@type='search' or contains(@placeholder, 'ara')]",
                    "last_used": timestamp - 200
                }
            ]
        },
        "arama_butonu": {
            "strategies": [
                {
                    "type": "css",
                    "selector": "button[type='submit'], .search-button, button.search",
                    "last_used": timestamp
                },
                {
                    "type": "text",
                    "selector": "Ara",
                    "last_used": timestamp - 100
                },
                {
                    "type": "css",
                    "selector": "input[type='submit']",
                    "last_used": timestamp - 200
                }
            ]
        },
        "filtre_butonu": {
            "strategies": [
                {
                    "type": "text",
                    "selector": "Filtrele",
                    "last_used": timestamp
                },
                {
                    "type": "css",
                    "selector": ".filter-button, [data-testid='filter']",
                    "last_used": timestamp - 100
                }
            ]
        },
        "restoran_kartlari": {
            "strategies": [
                {
                    "type": "css",
                    "selector": ".restaurant-card, .restaurant-item, .restaurant-box",
                    "last_used": timestamp
                },
                {
                    "type": "css",
                    "selector": "[class*='restaurant'], [class*='card']",
                    "last_used": timestamp - 100
                }
            ]
        }
    }
    
    return locator_db 