"""
Tüm sayfa nesneleri için temel sınıf.

Bu modül, tüm sayfa nesnelerinin (page objects) kalıtım alacağı
temel bir sınıf tanımlar. Sayfaya özgü ortak işlemleri içerir
ve self-healing mekanizmasını kullanır.
"""

import logging
import time
from pathlib import Path
from playwright.sync_api import Page, expect
from features.environment.self_healing import SelfHealingHelper

# Loglama konfigürasyonu
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BasePage:
    """
    Tüm sayfa nesnelerinin temel sınıfı.
    
    Bu sınıf, tüm sayfalarda ortak olan işlemleri (navigasyon, element erişimi,
    tıklama, form doldurma, vb.) sağlar ve self-healing mekanizmasını entegre eder.
    """

    def __init__(self, context):
        """
        BasePage yapıcı metodu.
        
        Args:
            context: Behave context nesnesi
        """
        self.context = context
        self.page = context.page
        
        # Self-healing mekanizmasını başlat
        self.helper = SelfHealingHelper(self.page)
        
        # Ekran görüntüleri için dizin oluştur
        Path("screenshots").mkdir(exist_ok=True)

    def navigate_to(self, url_path=""):
        """
        Belirtilen URL'ye gider.
        
        Args:
            url_path (str, optional): Ana URL'ye eklenecek yol
        """
        base_url = self.context.config.userdata.get("base_url", "https://tgoyemek.com")
        full_url = f"{base_url}/{url_path}".rstrip('/')
        
        logger.info(f"Navigating to: {full_url}")
        self.page.goto(full_url)
        self.wait_for_page_load()

    def wait_for_page_load(self):
        """
        Sayfanın yüklenmesini bekler.
        
        Sayfa tam olarak yüklenene kadar bekler ve JS 
        işlemlerinin tamamlanmasını sağlar.
        """
        try:
            # Önce networkidle beklemesi, sonra JS işlemlerinin tamamlanması
            self.page.wait_for_load_state("networkidle", timeout=10000)
        except Exception as e:
            logger.warning(f"networkidle durumu beklenirken zaman aşımı: {e}")
            
        try:
            # JS işlemlerinin tamamlanmasını bekle (daha güvenilir)
            self.page.evaluate("() => { return new Promise(resolve => setTimeout(resolve, 500)); }")
        except Exception as e:
            logger.warning(f"JS işlemleri beklenirken hata: {e}")
            
        logger.info("Page loaded")

    def get_title(self):
        """
        Sayfa başlığını döndürür.
        
        Returns:
            str: Sayfa başlığı
        """
        return self.page.title()

    def get_current_url(self):
        """
        Mevcut URL'yi döndürür.
        
        Returns:
            str: Mevcut URL
        """
        return self.page.url
    
    def get_element(self, locator_id, selector=None, timeout=5000):
        """
        Bir elementi bulur, gerekirse self-healing mekanizmasını kullanır.
        
        Args:
            locator_id (str): Locator benzersiz tanımlayıcısı
            selector (str, optional): Element için CSS seçici
            timeout (int, optional): Beklenecek süre (ms). Varsayılan 5000.
            
        Returns:
            Locator: Bulunan element
            
        Raises:
            Exception: Element bulunamazsa
        """
        try:
            if hasattr(self, 'helper') and self.helper:
                # Self-healing mekanizmasını kullan
                element = self.helper.get_element(locator_id, selector=selector, timeout=timeout)
                
                # Bulunan elementi türünü kontrol et
                element_type = self._detect_element_type(element)
                logger.debug(f"Found element '{locator_id}' of type '{element_type}'")
                
                return element
            else:
                # Doğrudan element
                if not selector:
                    raise ValueError(f"Selector must be provided for locator ID '{locator_id}'")
                    
                element = self.page.locator(selector).first
                element.wait_for(timeout=timeout)
                return element
                
        except Exception as e:
            error_msg = f"Failed to get element {locator_id} with selector {selector}: {e}"
            logger.error(error_msg)
            self.take_screenshot(f"element_not_found_{locator_id}")
            raise
    
    def is_element_visible(self, locator_id, selector, timeout=5000):
        """
        Bir elementin görünür olup olmadığını kontrol eder.
        
        Args:
            locator_id (str): Locator benzersiz tanımlayıcısı
            selector (str): Element için CSS seçici
            timeout (int, optional): Beklenecek süre (ms). Varsayılan 5000.
            
        Returns:
            bool: Element görünürse True, değilse False
        """
        try:
            element = self.get_element(locator_id, selector, timeout)
            return element.is_visible()
        except Exception as e:
            logger.warning(f"Element {locator_id} is not visible: {e}")
            return False
    
    def is_element_enabled(self, locator_id, selector, timeout=5000):
        """
        Bir elementin etkin olup olmadığını kontrol eder.
        
        Args:
            locator_id (str): Locator benzersiz tanımlayıcısı
            selector (str): Element için CSS seçici
            timeout (int, optional): Beklenecek süre (ms). Varsayılan 5000.
            
        Returns:
            bool: Element etkinse True, değilse False
        """
        try:
            element = self.get_element(locator_id, selector, timeout)
            return element.is_enabled()
        except Exception as e:
            logger.warning(f"Element {locator_id} is not enabled: {e}")
            return False
    
    def click_element(self, locator_id, selector, timeout=5000, retry_count=2):
        """
        Bir elemente tıklar.
        
        Args:
            locator_id (str): Locator benzersiz tanımlayıcısı
            selector (str): Element için CSS seçici
            timeout (int, optional): Beklenecek süre (ms). Varsayılan 5000.
            retry_count (int, optional): Başarısız olursa kaç kez tekrar denenecek. Varsayılan 2.
        
        Returns:
            bool: Başarılıysa True, değilse False
        """
        for attempt in range(retry_count + 1):
            try:
                element = self.get_element(locator_id, selector=selector, timeout=timeout)
                logger.info(f"Clicking element: {locator_id}")
                
                # İlk önce elementin görünür ve tıklanabilir olduğundan emin ol
                element.wait_for(state="visible", timeout=timeout)
                
                # Tıklama denemesi
                try:
                    element.click(timeout=timeout, force=False)
                except Exception as click_error:
                    logger.warning(f"Normal tıklama başarısız: {click_error}, force=True ile deneniyor")
                    # Güvenli olmayan tıklama (force=True) - son çare
                    element.click(timeout=timeout, force=True)
                
                # Sayfa geçişi olabilir, sayfanın yüklenmesini bekle
                self.wait_for_page_load()
                return True
            except Exception as e:
                if attempt < retry_count:
                    logger.warning(f"Click attempt {attempt + 1} failed for {locator_id}, retrying: {e}")
                    time.sleep(1)
                else:
                    logger.error(f"Failed to click element {locator_id} after {retry_count + 1} attempts: {e}")
                    self.take_screenshot(f"click_error_{locator_id}")
                    return False
    
    def fill_text(self, locator_id, selector, text, timeout=5000, retry_count=2):
        """
        Bir metin alanını doldurur.
        
        Args:
            locator_id (str): Locator benzersiz tanımlayıcısı
            selector (str): Element için CSS seçici
            text (str): Girilecek metin
            timeout (int, optional): Beklenecek süre (ms). Varsayılan 5000.
            retry_count (int, optional): Başarısız olursa kaç kez tekrar denenecek. Varsayılan 2.
        
        Returns:
            bool: Başarılıysa True, değilse False
        """
        for attempt in range(retry_count + 1):
            try:
                element = self.get_element(locator_id, selector=selector, timeout=timeout)
                
                # Elementi kontrol et - bu bir input/textarea/select olmalı
                element_type = self._detect_element_type(element)
                
                logger.info(f"Filling text in: {locator_id} with: {text} (element_type: {element_type})")
                
                if element_type in ['input', 'textarea', 'select', 'contenteditable']:
                    element.fill(text)
                    return True
                else:
                    # Doğru bir input elementi bulmayı dene
                    # Farklı bir strateji deneyelim - doğrudan CSS ile
                    fallback_selectors = [
                        "input[type='search']", 
                        "input[type='text']", 
                        ".search-input", 
                        "[placeholder*='ara']",
                        "input[name='search']"
                    ]
                    
                    logger.info(f"Element text giriş alanı değil. Alternatif seçiciler deneniyor: {locator_id}")
                    for alt_selector in fallback_selectors:
                        try:
                            fallback_element = self.page.locator(alt_selector).first
                            fallback_element.wait_for(state="visible", timeout=2000)
                            logger.info(f"Alternatif seçici başarılı: {alt_selector}")
                            fallback_element.fill(text)
                            
                            # Başarılı stratejiyi kaydet
                            self.helper._save_successful_strategy(locator_id, alt_selector, 'css')
                            logger.info(f"Alternatif seçici ile doldurma başarılı: {alt_selector}")
                            
                            return True
                        except Exception as e:
                            logger.warning(f"Alternatif seçici başarısız: {alt_selector}, Hata: {e}")
                            continue
                    
                    # Hiçbir alternatif seçici çalışmadıysa hata fırlat
                    raise ValueError(f"Uygun bir metin giriş alanı bulunamadı: {locator_id}")
                    
            except Exception as e:
                if attempt < retry_count:
                    logger.warning(f"Fill attempt {attempt + 1} failed for {locator_id}, retrying: {e}")
                    time.sleep(1)
                else:
                    logger.error(f"Failed to fill text in element {locator_id} after {retry_count + 1} attempts: {e}")
                    self.take_screenshot(f"fill_error_{locator_id}")
                    return False
    
    def _detect_element_type(self, element):
        """
        Bir elementin türünü tespit eder.
        
        Args:
            element (Locator): Playwright Locator nesnesi
            
        Returns:
            str: Tespit edilen element türü
        """
        try:
            # Elementin tag adını almak için evaluate kullan
            tag_name = self.page.evaluate("""(element) => {
                if (!element) return null;
                return element.tagName ? element.tagName.toLowerCase() : null;
            }""", element)
            
            # contenteditable özelliğini kontrol et
            is_contenteditable = self.page.evaluate("""(element) => {
                if (!element) return false;
                return element.hasAttribute('contenteditable') && 
                       element.getAttribute('contenteditable') !== 'false';
            }""", element)
            
            if tag_name in ['input', 'textarea', 'select']:
                return tag_name
            elif is_contenteditable:
                return 'contenteditable'
            else:
                return tag_name if tag_name else 'unknown'
        except Exception as e:
            logger.warning(f"Element türü tespit edilemedi: {e}")
            return 'unknown'
    
    def get_text(self, locator_id, selector, timeout=5000):
        """
        Bir elementin metnini alır.
        
        Args:
            locator_id (str): Locator benzersiz tanımlayıcısı
            selector (str): Element için CSS seçici
            timeout (int, optional): Beklenecek süre (ms). Varsayılan 5000.
            
        Returns:
            str: Elementin metni, hata durumunda boş string
        """
        try:
            element = self.get_element(locator_id, selector, timeout)
            return element.inner_text()
        except Exception as e:
            logger.error(f"Failed to get text from element {locator_id}: {e}")
            return ""
    
    def count_elements(self, locator_id, selector, timeout=5000):
        """
        Belirli bir seçiciye uyan elementlerin sayısını alır.
        
        Args:
            locator_id (str): Locator benzersiz tanımlayıcısı
            selector (str): Element için CSS seçici
            timeout (int, optional): Beklenecek süre (ms). Varsayılan 5000.
            
        Returns:
            int: Bulunan element sayısı, hata durumunda 0
        """
        try:
            # Self-healing ile elementi bulmaya çalışalım
            element = self.get_element(locator_id, selector, timeout)
            
            # Doğrudan seçiciyi kullanarak sayı alalım
            count = self.page.locator(selector).count()
            return count
        except Exception as e:
            logger.error(f"Failed to count elements for {locator_id}: {e}")
            return 0
    
    def wait_for_timeout(self, ms):
        """
        Belirli bir süre bekler.
        
        Args:
            ms (int): Beklenecek süre (ms)
        """
        self.page.wait_for_timeout(ms)
    
    def wait_for_element(self, locator_id, selector, state="visible", timeout=5000):
        """
        Bir elementin belirli bir duruma gelmesini bekler.
        
        Args:
            locator_id (str): Locator benzersiz tanımlayıcısı
            selector (str): Element için CSS seçici
            state (str, optional): Beklenen durum (visible, hidden, enabled, disabled, stable).
                                   Varsayılan "visible".
            timeout (int, optional): Beklenecek süre (ms). Varsayılan 5000.
            
        Returns:
            bool: Başarılıysa True, değilse False
        """
        try:
            element = self.get_element(locator_id, selector, timeout)
            element.wait_for(state=state, timeout=timeout)
            return True
        except Exception as e:
            logger.warning(f"Timeout waiting for element {locator_id} to be {state}: {e}")
            return False
    
    def take_screenshot(self, name="screenshot"):
        """
        Ekran görüntüsü alır.
        
        Args:
            name (str, optional): Dosya adı. Varsayılan "screenshot".
        """
        try:
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            file_name = f"screenshots/{name}_{timestamp}.png"
            self.page.screenshot(path=file_name)
            logger.info(f"Screenshot saved to {file_name}")
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
    
    def get_page_errors(self):
        """
        Sayfadaki konsol hatalarını alır.
        
        Returns:
            list: Konsol hatalarının listesi
        """
        try:
            # Konsoldaki 'error' tipindeki mesajları al
            errors = self.page.evaluate("""() => {
                if (!window.pageErrors) window.pageErrors = [];
                return window.pageErrors;
            }""")
            return errors
        except Exception as e:
            logger.error(f"Failed to get page errors: {e}")
            return []

    def expect_element_to_be_visible(self, locator_id, selector, timeout=5000):
        """
        Bir elementin görünür olmasını bekler ve doğrular.
        
        Args:
            locator_id (str): Locator benzersiz tanımlayıcısı
            selector (str): Element için CSS seçici
            timeout (int, optional): Beklenecek süre (ms). Varsayılan 5000.
            
        Returns:
            bool: Element görünürse True, değilse False
        """
        try:
            element = self.get_element(locator_id, selector, timeout)
            expect(element).to_be_visible(timeout=timeout)
            return True
        except Exception as e:
            logger.error(f"Element {locator_id} is not visible: {e}")
            self.take_screenshot(f"visibility_error_{locator_id}")
            return False
    
    def expect_element_to_have_text(self, locator_id, selector, text, timeout=5000):
        """
        Bir elementin belirli bir metni içermesini bekler ve doğrular.
        
        Args:
            locator_id (str): Locator benzersiz tanımlayıcısı
            selector (str): Element için CSS seçici
            text (str): Beklenen metin
            timeout (int, optional): Beklenecek süre (ms). Varsayılan 5000.
            
        Returns:
            bool: Element metni içeriyorsa True, değilse False
        """
        try:
            element = self.get_element(locator_id, selector, timeout)
            expect(element).to_contain_text(text, timeout=timeout)
            return True
        except Exception as e:
            logger.error(f"Element {locator_id} does not contain text '{text}': {e}")
            self.take_screenshot(f"text_error_{locator_id}")
            return False
    
    def select_option(self, locator_id, selector, value=None, label=None, index=None, timeout=5000):
        """
        Bir select elementinden bir seçenek seçer.
        
        Args:
            locator_id (str): Locator benzersiz tanımlayıcısı
            selector (str): Element için CSS seçici
            value (str, optional): Seçilecek seçeneğin value değeri
            label (str, optional): Seçilecek seçeneğin görünen metni
            index (int, optional): Seçilecek seçeneğin indeksi
            timeout (int, optional): Beklenecek süre (ms). Varsayılan 5000.
            
        Returns:
            bool: Başarılıysa True, değilse False
        """
        try:
            element = self.get_element(locator_id, selector, timeout)
            select_options = {}
            
            if value is not None:
                select_options['value'] = value
            elif label is not None:
                select_options['label'] = label
            elif index is not None:
                select_options['index'] = index
            
            element.select_option(**select_options)
            return True
        except Exception as e:
            logger.error(f"Failed to select option in {locator_id}: {e}")
            self.take_screenshot(f"select_error_{locator_id}")
            return False
    
    def hover_element(self, locator_id, selector, timeout=5000):
        """
        Bir elementin üzerine fare imlecini getirir.
        
        Args:
            locator_id (str): Locator benzersiz tanımlayıcısı
            selector (str): Element için CSS seçici
            timeout (int, optional): Beklenecek süre (ms). Varsayılan 5000.
            
        Returns:
            bool: Başarılıysa True, değilse False
        """
        try:
            element = self.get_element(locator_id, selector, timeout)
            element.hover()
            return True
        except Exception as e:
            logger.error(f"Failed to hover over element {locator_id}: {e}")
            self.take_screenshot(f"hover_error_{locator_id}")
            return False 