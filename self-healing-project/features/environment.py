"""
Behave için ortam ayarları ve fixture'lar.
"""

from playwright.sync_api import sync_playwright
import os
import logging
from dotenv import load_dotenv
from features.environment.self_healing import SelfHealingHelper
# Yeni utils modüllerini içe aktaralım
from utils.helpers import setup_logging, load_env_variables, get_project_root, update_locator_database

# .env dosyasını yükle
load_dotenv()

# Loglama ayarları
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def before_all(context):
    """Tüm testlerden önce bir kez çalışır."""
    logger.info("Test suite başlatılıyor...")
    
    # Çevre değişkenlerini yükle
    env_vars = load_env_variables()
    
    # Tarayıcı ayarlarını yapılandır
    context.browser_type = env_vars.get("browser", "chromium")
    context.headless = env_vars.get("headless", True)
    
    # Temel URL'yi ayarla
    context.base_url = env_vars.get("base_url", "https://tgoyemek.com")
    
    # Timeout değerini ayarla
    context.timeout = env_vars.get("timeout", 30) * 1000  # milisaniyeye dönüştür
    
    # Proje kök dizinini ayarla
    context.project_root = get_project_root()

    # Self-healing veritabanını güncelle/kontrol et
    try:
        update_locator_database()
    except Exception as e:
        logger.warning(f"Locator veritabanı güncellenirken hata oluştu (devam ediliyor): {e}")


def before_scenario(context, scenario):
    """Her senaryodan önce çalışır."""
    logger.info(f"Senaryo başlatılıyor: {scenario.name}")
    
    try:
        # Playwright'ı başlat
        context.playwright = sync_playwright().start()
        
        # Tarayıcı tipini belirle
        if context.browser_type == "firefox":
            browser = context.playwright.firefox
        elif context.browser_type == "webkit":
            browser = context.playwright.webkit
        else:
            browser = context.playwright.chromium
        
        # Tarayıcıyı başlat (geliştirilmiş ayarlar)
        context.browser = browser.launch(
            headless=context.headless,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu',
                '--window-size=1366,768'
            ]
        )
        
        # Yeni bir bağlam ve sayfa oluştur
        context.browser_context = context.browser.new_context(
            viewport={'width': 1366, 'height': 768},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
            ignore_https_errors=True
        )
        
        # Zaman aşımını ayarla
        context.browser_context.set_default_timeout(context.timeout if hasattr(context, 'timeout') else 30000)
        
        # Yeni sayfa oluştur
        context.page = context.browser_context.new_page()
        
        # Sayfa olayları
        context.page.on("pageerror", lambda error: logger.error(f"Sayfa hatası: {error}"))
        
        # Self-healing helper'ı ayarla
        context.helper = SelfHealingHelper(context.page)
        
    except Exception as e:
        logger.error(f"Senaryo kurulumunda hata: {e}")
        raise


def after_scenario(context, scenario):
    """Her senaryodan sonra çalışır."""
    logger.info(f"Senaryo tamamlandı: {scenario.name}")
    
    # Ekran görüntüsü al (eğer senaryo başarısızsa)
    if scenario.status == "failed":
        try:
            screenshot_dir = "screenshots"
            if not os.path.exists(screenshot_dir):
                os.makedirs(screenshot_dir)
            
            screenshot_path = f"{screenshot_dir}/{scenario.name.replace(' ', '_')}.png"
            
            if hasattr(context, "page") and context.page:
                context.page.screenshot(path=screenshot_path)
                logger.info(f"Ekran görüntüsü alındı: {screenshot_path}")
        except Exception as e:
            logger.error(f"Ekran görüntüsü alınamadı: {e}")
    
    # Tarayıcı kaynakları güvenli bir şekilde temizle
    try:
        # Tüm kaynakları güvenli bir şekilde kapat
        if hasattr(context, "page") and context.page:
            context.page.close()
            
        if hasattr(context, "browser_context") and context.browser_context:
            context.browser_context.close()
            
        if hasattr(context, "browser") and context.browser:
            context.browser.close()
            
        if hasattr(context, "playwright") and context.playwright:
            context.playwright.stop()
    except Exception as e:
        logger.error(f"Temizleme sırasında hata: {e}")


def after_all(context):
    """Tüm testlerden sonra bir kez çalışır."""
    logger.info("Test suite tamamlandı") 