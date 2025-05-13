"""
Self-healing özelliği için yardımcı modül.

Bu modül, web sayfasındaki elementlerin bulunamaması durumunda 
alternatif stratejiler kullanarak elementleri bulmaya çalışan 
bir mekanizma sağlar.

Sağlanan stratejiler:
1. Kaydedilmiş strateji veritabanı
2. Orijinal seçici
3. Metin, ID ve class tabanlı seçiciler
4. Yapay zeka/ML tabanlı tahmin
"""

# Standart kütüphaneler
import json
import logging
import os
import re
import time
import traceback
import random
import importlib.util
from pathlib import Path

# Üçüncü parti kütüphaneler
from playwright.sync_api import Page, Locator, TimeoutError
from bs4 import BeautifulSoup

# Yardımcı modüller
try:
    from utils.helpers import get_project_root
except ImportError:
    # Eğer utils modülü içe aktarılamazsa, yerel bir fonksiyon tanımla
    def get_project_root():
        return Path(__file__).parent.parent.parent

# Loglama konfigürasyonu
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Proje kök dizinini al
PROJECT_ROOT = get_project_root()

# Sabit değişkenler
LOCATOR_DB_FILE = PROJECT_ROOT / "locator_db.json"
MODEL_FILE = PROJECT_ROOT / "resources" / "locator_predict_model.py"


class SelfHealingHelper:
    """
    Self-healing mekanizması için yardımcı sınıf.
    
    Bu sınıf, elementlerin bulunamadığı durumlarda alternatif 
    stratejiler kullanarak elementleri bulma yeteneği sağlar.
    """

    def __init__(self, page: Page):
        """
        Self-healing yardımcısını başlatır.
        
        Args:
            page (Page): Playwright Page nesnesi
        """
        self.page = page
        self.locator_db = self._load_locator_db()
        self.predictor = self._load_predictor()

    def _load_locator_db(self):
        """
        Locator veritabanını yükler.
        
        Returns:
            dict: Locator veritabanı sözlüğü
        """
        if LOCATOR_DB_FILE.exists():
            try:
                with open(LOCATOR_DB_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Locator veritabanı yüklenirken hata oluştu: {e}")
                return {}
        return {}

    def _load_predictor(self):
        """
        Locator tahmin modelini dinamik olarak yükler.
        
        Returns:
            object: Yüklenen LocatorPredictor nesnesi veya None (hata durumunda)
        """
        try:
            if MODEL_FILE.exists():
                logger.info(f"Locator tahmin modeli yükleniyor: {MODEL_FILE}")
                # Dinamik olarak model modülünü yükle
                spec = importlib.util.spec_from_file_location("locator_predict_model", MODEL_FILE)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Modeli oluştur ve döndür
                predictor = module.LocatorPredictor()
                logger.info("Locator tahmin modeli başarıyla yüklendi")
                return predictor
            else:
                logger.warning(f"Locator tahmin modeli bulunamadı: {MODEL_FILE}")
                return None
        except Exception as e:
            logger.error(f"Locator tahmin modeli yüklenirken hata oluştu: {e}")
            logger.error(traceback.format_exc())
            return None

    def _save_locator_db(self):
        """Locator veritabanını dosyaya kaydeder."""
        try:
            with open(LOCATOR_DB_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.locator_db, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Locator veritabanı kaydedilirken hata oluştu: {e}")

    def register_locator(self, locator_id, locator_info):
        """
        Yeni bir locator kaydeder veya mevcut olanı günceller.
        
        Args:
            locator_id (str): Locator benzersiz tanımlayıcısı
            locator_info (dict): Locator bilgileri
        """
        self.locator_db[locator_id] = locator_info
        self._save_locator_db()
        logger.info(f"Locator '{locator_id}' kaydedildi: {locator_info}")

    def get_element(self, locator_id, **kwargs):
        """
        Self-healing özelliğiyle bir elementi bulur.
        
        Bu metot, verilen locator_id için farklı stratejileri sırayla deneyerek
        elementi bulmaya çalışır. Eğer bir strateji başarısız olursa, bir sonraki 
        stratejiyi dener.
        
        Stratejiler:
        1. Kaydedilmiş stratejiler (veritabanından)
        2. Orijinal seçici (fonksiyon çağrısından)
        3. Metin içeriğine dayalı tahminler
        4. ID ve class özelliklerine dayalı tahminler
        5. Yapay zeka tabanlı tahminler
        
        Args:
            locator_id (str): Element için benzersiz tanımlayıcı
            **kwargs: Ek parametreler (timeout, selector, vb.)

        Returns:
            Locator: Bulunan element
            
        Raises:
            Exception: Hiçbir strateji başarılı olmadığında
        """
        timeout = kwargs.get('timeout', 5000)  # Varsayılan timeout 5 saniye
        original_selector = kwargs.get('selector')
        
        # 1. Strateji: Veritabanındaki stratejileri dene
        element = self._try_database_strategies(locator_id, timeout)
        if element:
            return element
        
        # 2. Strateji: Orijinal seçiciyi dene
        element = self._try_original_selector(locator_id, original_selector, timeout)
        if element:
            return element
        
        # Mevcut HTML içeriğini analiz et
        html_content = self.page.content()
        hints = locator_id.lower().split('_')
        
        # 3. Strateji: Temel self-healing yaklaşımlarını dene
        element = self._try_basic_healing_strategies(locator_id, html_content, hints, timeout)
        if element:
            return element
        
        # 4. Strateji: Model tabanlı tahmin stratejisini dene
        element = self._try_prediction_strategy(locator_id, html_content, hints)
        if element:
            return element
        
        # Hiçbir strateji başarılı olmadıysa hata fırlat
        logger.error(f"'{locator_id}' için hiçbir self-healing stratejisi başarılı olmadı")
        raise Exception(f"Element bulunamadı: {locator_id}")

    def _try_database_strategies(self, locator_id, timeout):
        """
        Veritabanından kaydedilmiş stratejileri dener.
        
        Args:
            locator_id (str): Locator benzersiz tanımlayıcısı
            timeout (int): Bekleme süresi (ms)
            
        Returns:
            Locator: Bulunan element veya None
        """
        if locator_id not in self.locator_db:
            logger.info(f"'{locator_id}' için kayıtlı locator stratejisi bulunamadı")
            return None
            
        logger.info(f"'{locator_id}' için kayıtlı locator stratejileri deneniyor")
        strategies = self.locator_db[locator_id]['strategies']
        logger.info(f"'{locator_id}' için {len(strategies)} strateji bulundu")
        
        for i, strategy in enumerate(strategies):
            try:
                selector = strategy['selector']
                selector_type = strategy['type']
                logger.info(f"Strateji {i+1}/{len(strategies)} deneniyor: {selector_type} - {selector}")
                
                element = self._create_element_by_type(selector_type, selector)
                if not element:
                    logger.warning(f"Strateji {i+1} için element oluşturulamadı: {selector_type} - {selector}")
                    continue
                
                # Elementi kontrol edelim
                logger.info(f"Element oluşturuldu, görünürlük kontrol ediliyor...")
                element.wait_for(timeout=timeout)
                logger.info(f"'{locator_id}' için element bulundu: {selector_type} - {selector}")
                
                # Bu stratejiyi listenin başına taşıyalım (en başarılı strateji)
                self._promote_successful_strategy(locator_id, strategy)
                
                return element
            except TimeoutError:
                logger.warning(f"Strateji {i+1} başarısız: {selector_type} - {selector}")
                continue
        
        logger.warning(f"'{locator_id}' için tüm stratejiler ({len(strategies)}) başarısız oldu")
        return None
        
    def _try_original_selector(self, locator_id, original_selector, timeout):
        """
        Orijinal seçiciyi dener.
        
        Args:
            locator_id (str): Locator benzersiz tanımlayıcısı
            original_selector (str): Orijinal CSS seçici
            timeout (int): Bekleme süresi (ms)
            
        Returns:
            Locator: Bulunan element veya None
        """
        if not original_selector:
            logger.info(f"'{locator_id}' için orijinal seçici belirtilmemiş")
            return None
            
        try:
            logger.info(f"Orijinal seçici deneniyor: {original_selector}")
            element = self.page.locator(original_selector).first
            
            logger.info(f"Orijinal seçici elementin görünürlüğü bekleniyor: {original_selector} (timeout: {timeout}ms)")
            element.wait_for(timeout=timeout)
            logger.info(f"Orijinal seçici başarılı oldu: {original_selector}")
            
            # Başarılı stratejiyi kaydet
            self._save_successful_strategy(locator_id, original_selector, 'css')
            logger.info(f"Orijinal seçici strateji olarak kaydedildi: {original_selector}")
            return element
        except TimeoutError:
            logger.warning(f"Orijinal seçici başarısız oldu: {original_selector}")
            return None
        except Exception as e:
            logger.warning(f"Orijinal seçici beklenmeyen hata verdi: {original_selector}, Hata: {e}")
            return None

    def _try_basic_healing_strategies(self, locator_id, html_content, hints, timeout):
        """
        Temel self-healing stratejilerini dener.
        
        Bu stratejiler metin içeriği, ID ve class özellikleri gibi 
        temel HTML özelliklerine dayanır.
        
        Args:
            locator_id (str): Locator benzersiz tanımlayıcısı
            html_content (str): HTML içeriği
            hints (list): Locator ID'den çıkarılan ipuçları
            timeout (int): Bekleme süresi (ms)
            
        Returns:
            Locator: Bulunan element veya None
        """
        logger.info(f"'{locator_id}' için temel self-healing stratejileri deneniyor")
        
        # HTML içeriğini analiz et
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Olası elementleri topla
        possible_elements = []
        possible_elements.extend(self._find_text_based_elements(soup, hints))
        possible_elements.extend(self._find_attribute_based_elements(soup, hints))
        possible_elements.extend(self._find_form_elements(soup, hints))
        
        # Bulunan olası elementleri dene
        return self._try_possible_elements(locator_id, possible_elements, timeout)

    def _find_text_based_elements(self, soup, hints):
        """
        Metin içeriğine dayalı elementleri bulur.
        
        Args:
            soup (BeautifulSoup): Analiz edilmiş HTML içeriği
            hints (list): Aranacak ipuçları
            
        Returns:
            list: Bulunan element bilgilerinin listesi
        """
        elements = []
        
        # Element türlerini kategorize et
        input_elements = ['input', 'textarea', 'select', 'button']
        interactive_elements = input_elements + ['a', 'button', 'details', 'dialog', 'menu']
        
        # Form elemanları için özel selektörler - yüksek öncelikli
        form_selectors = [
            "input[type='search']", 
            "input[type='text']", 
            "input[placeholder]",
            ".search-input", 
            "input.search",
            "input[name='search']", 
            "input[name='q']"
        ]

        # Form elemanlarını doğrudan ara - daha yüksek öncelikli
        for selector in form_selectors:
            try:
                for input_elem in soup.select(selector):
                    elements.append({
                        'element': input_elem,
                        'type': 'css',
                        'selector': selector,
                        'score': 0.9  # Yüksek öncelik
                    })
            except Exception as e:
                logger.warning(f"Form elemanı aranırken hata: {e}")
        
        # Giriş alanlarını locator_id'ye göre akıllıca ara
        if any(h in ["arama", "search", "kutu", "input", "field", "text", "area"] for h in hints):
            input_selectors = ["input[type='search']", "input[type='text']", ".search-input", "[placeholder]"]
            for selector in input_selectors:
                try:
                    for elem in soup.select(selector):
                        elements.append({
                            'element': elem,
                            'type': 'css',
                            'selector': selector,
                            'score': 0.95  # En yüksek öncelik
                        })
                except Exception:
                    pass
                    
        # Butonlar için akıllı arama
        if any(h in ["buton", "button", "submit", "ara", "search", "click"] for h in hints):
            button_selectors = ["button", "input[type='submit']", ".search-button", "button.search"]
            for selector in button_selectors:
                try:
                    for elem in soup.select(selector):
                        elements.append({
                            'element': elem,
                            'type': 'css',
                            'selector': selector,
                            'score': 0.92
                        })
                except Exception:
                    pass
        
        # Metni içeren elementleri kontrol et - orta öncelikli
        for hint in hints:
            if len(hint) > 3:  # Çok kısa ipuçlarını atla
                for tag in soup.find_all(text=lambda t: hint in t.lower() if t else False):
                    if tag.parent:
                        parent = tag.parent
                        
                        # Metin tabanlı seçiciler için input elementlerini atla
                        if parent.name not in input_elements:
                            # Metin tabanlı strateji
                            elements.append({
                                'element': parent,
                                'type': 'text',
                                'selector': tag.text.strip(),
                                'score': 0.7  # Metin tabanlı seçiciler için puan
                            })
                            
                            # Etkileşimli içerik için daha yüksek puan
                            if parent.name in interactive_elements:
                                elements[-1]['score'] = 0.8  # Etkileşimli eleman olduğu için puanı artır
        
        return elements

    def _find_attribute_based_elements(self, soup, hints):
        """
        Öznitelik (ID, class vb.) tabanlı elementleri bulur.
        
        Args:
            soup (BeautifulSoup): Analiz edilmiş HTML içeriği
            hints (list): Aranacak ipuçları
            
        Returns:
            list: Bulunan element bilgilerinin listesi
        """
        elements = []
        
        # Input elementleri için özel stratejiler
        input_selectors = [
            "input[type='search']", 
            "input[type='text']", 
            ".search-input", 
            "[placeholder*='ara']", 
            "input[name='search']",
            "textarea", 
            "select"
        ]
        
        # Input elementleri için otomatik kontrol
        for selector in input_selectors:
            for tag in soup.select(selector):
                for hint in hints:
                    if len(hint) > 3:
                        # Input elemanlarına daha yüksek puan ver
                        elements.append({
                            'element': tag,
                            'type': 'css',
                            'selector': selector,
                            'score': 0.85  # Input elementleri için yüksek puan
                        })
        
        # ID ve class özelliklerine bak
        for hint in hints:
            if len(hint) > 3:
                # ID tabanlı elementler - en yüksek puan (en spesifik)
                for tag in soup.find_all(attrs={'id': lambda x: x and hint in x.lower()}):
                    elements.append({
                        'element': tag,
                        'type': 'css',
                        'selector': f"#{tag['id']}",
                        'score': 0.9  # ID selektörleri en spesifik olduğu için en yüksek puan
                    })
                
                # Class tabanlı elementler
                for tag in soup.find_all(attrs={'class': lambda x: x and hint in ' '.join(x).lower() if isinstance(x, list) else x and hint in x.lower()}):
                    if 'class' in tag.attrs:
                        class_selector = '.'.join(tag['class'])
                        elements.append({
                            'element': tag,
                            'type': 'css',
                            'selector': f".{class_selector}",
                            'score': 0.8  # Class seçicileri için orta-yüksek puan
                        })
                        
                # Name özniteliği - form öğeleri için önemli
                for tag in soup.find_all(attrs={'name': lambda x: x and hint in x.lower()}):
                    elements.append({
                        'element': tag,
                        'type': 'css',
                        'selector': f"[name='{tag['name']}']",
                        'score': 0.85  # Name attribute'ları için yüksek puan
                    })
                    
                # Placeholder özniteliği - arama kutuları için önemli
                for tag in soup.find_all(attrs={'placeholder': lambda x: x and hint in x.lower()}):
                    elements.append({
                        'element': tag,
                        'type': 'css',
                        'selector': f"[placeholder*='{hint}']",
                        'score': 0.85  # Placeholder için yüksek puan
                    })
        
        return elements

    def _find_form_elements(self, soup, hints):
        """
        Form elementlerini (buton, link, input vb.) bulur.
        
        Args:
            soup (BeautifulSoup): Analiz edilmiş HTML içeriği
            hints (list): Aranacak ipuçları
            
        Returns:
            list: Bulunan element bilgilerinin listesi
        """
        elements = []
        
        # Form elemanları için özel arama stratejileri
        input_elements = ['input', 'textarea', 'select']
        button_elements = ['button', 'input[type="button"]', 'input[type="submit"]']
        
        # Her hint için form elemanlarını tara
        for hint in hints:
            if len(hint) > 3:
                # 1. Girdi alanlarını ara
                for tag in soup.find_all(input_elements):
                    # Input elemanlarını daha akıllı bir şekilde sırala
                    if tag.name in input_elements:
                        score_base = 0.8  # Input elemanları için temel puan
                        
                        # ID tabanlı seçici (en spesifik)
                        if tag.get('id') and hint in tag.get('id').lower():
                            elements.append({
                                'element': tag,
                                'type': 'css',
                                'selector': f"#{tag['id']}",
                                'score': score_base + 0.1
                            })
                            
                            # ID tam eşleşme ise ekstra puan
                            if tag.get('id').lower() == hint.lower():
                                elements[-1]['score'] = 0.95
                            
                        # Name attribute'u özellikle form elemanları için önemli
                        if tag.get('name') and hint in tag.get('name').lower():
                            elements.append({
                                'element': tag,
                                'type': 'css',
                                'selector': f"{tag.name}[name='{tag['name']}']",
                                'score': score_base + 0.05
                            })
                            
                            # Name tam eşleşme ise ekstra puan
                            if tag.get('name').lower() == hint.lower():
                                elements[-1]['score'] = 0.92
                        
                        # Placeholder için ayrı bir strateji (arama kutuları vb.)
                        if tag.get('placeholder') and hint in tag.get('placeholder').lower():
                            elements.append({
                                'element': tag,
                                'type': 'css',
                                'selector': f"{tag.name}[placeholder*='{hint}']",
                                'score': score_base + 0.08
                            })
                            
                        # Type özniteliğinde ipucu varsa
                        if tag.get('type') and hint in tag.get('type').lower():
                            elements.append({
                                'element': tag,
                                'type': 'css',
                                'selector': f"{tag.name}[type='{tag['type']}']",
                                'score': score_base + 0.02
                            })
                            
                        # Class özniteliği
                        if tag.get('class'):
                            class_text = ' '.join(tag.get('class'))
                            if hint in class_text.lower():
                                class_selector = '.'.join(tag['class'])
                                elements.append({
                                    'element': tag,
                                    'type': 'css',
                                    'selector': f".{class_selector}",
                                    'score': score_base
                                })
                
                # 2. Butonları ara
                for tag in soup.find_all(['button', 'a']):
                    # Buton ve link için metin içeriği önemli
                    if tag.text and hint in tag.text.lower():
                        # Tam eşleşme veya kısmi eşleşme kontrolü
                        score = 0.85 if tag.text.lower() == hint.lower() else 0.75
                        elements.append({
                            'element': tag,
                            'type': 'text',
                            'selector': tag.text.strip(),
                            'score': score
                        })
                    
                    # Alt özelliği olan butonlar (örn. resimli butonlar)
                    if tag.get('alt') and hint in tag['alt'].lower():
                        elements.append({
                            'element': tag,
                            'type': 'css',
                            'selector': f"{tag.name}[alt*='{hint}']",
                            'score': 0.8
                        })
                        
                    # Aria-label özelliği (erişilebilirlik)
                    if tag.get('aria-label') and hint in tag.get('aria-label').lower():
                        elements.append({
                            'element': tag,
                            'type': 'css',
                            'selector': f"{tag.name}[aria-label*='{hint}']",
                            'score': 0.82
                        })
        
        return elements

    def _try_possible_elements(self, locator_id, possible_elements, timeout):
        """
        Bulunan olası elementleri sırayla dener.
        
        Args:
            locator_id (str): Locator benzersiz tanımlayıcısı
            possible_elements (list): Denenecek olası elementler listesi
            timeout (int): Bekleme süresi (ms)
            
        Returns:
            Locator: Bulunan element veya None
        """
        if not possible_elements:
            logger.warning(f"'{locator_id}' için hiç olası element bulunamadı")
            return None
            
        logger.info(f"'{locator_id}' için toplam {len(possible_elements)} olası element bulundu")
        
        # Locator ID'den element tipini tahmin et
        element_type_hints = self._guess_element_type_from_id(locator_id)
        logger.info(f"'{locator_id}' için tahmin edilen element tipleri: {element_type_hints}")
        
        # Element tipine göre filtreleme ve puanlama
        filtered_elements = self._filter_elements_by_type(possible_elements, element_type_hints)
        
        # Elemanları skora göre sırala (en yüksek puan önce)
        sorted_elements = sorted(
            filtered_elements, 
            key=lambda x: x.get('score', 0), 
            reverse=True
        )
        
        # Log olarak puanları görüntüle
        if len(sorted_elements) > 0:
            top_elements = sorted_elements[:min(3, len(sorted_elements))]
            logger.info("En yüksek puanlı element adayları:")
            for i, e in enumerate(top_elements):
                selector_preview = e['selector'][:30] + "..." if len(e['selector']) > 30 else e['selector']
                logger.info(f"  {i+1}. {e['type']} - {selector_preview} (skor: {e.get('score', 0):.2f})")
        
        # En olası 5 elementi dene (çok fazla deneme yapmayı önle)
        max_attempts = min(5, len(sorted_elements))
        logger.info(f"En olası {max_attempts} element test edilecek")
        
        for i, item in enumerate(sorted_elements[:max_attempts]):
            try:
                selector_type = item['type']
                selector = item['selector']
                score = item.get('score', 0)
                
                logger.info(f"Element #{i+1}/{max_attempts} test ediliyor: {selector_type} - {selector} (skor: {score:.2f})")
                
                element = self._create_element_by_type(selector_type, selector)
                if not element:
                    logger.warning(f"Element oluşturulamadı: {selector_type} - {selector}")
                    continue
                
                # Elementi kontrol et
                logger.info(f"Element görünürlüğünü kontrol ediliyor: {selector_type} - {selector}")
                element.wait_for(timeout=2000)  # Kısa bir timeout ile dene
                
                # Element görünür mü doğrula
                if selector_type == 'css' and element.count() > 1:
                    logger.info(f"Seçici birden fazla elemana eşleşiyor ({element.count()}), ilkini kullanıyoruz")
                
                # Elementin doğru tür olduğunu doğrula (input, button, vs)
                if not self._verify_element_interaction_type(element, element_type_hints):
                    logger.warning(f"Element doğru türde değil: {selector_type} - {selector}")
                    continue
                
                # Başarılı stratejiyi kaydet
                self._save_successful_strategy(locator_id, selector, selector_type)
                logger.info(f"Self-healing başarılı: {selector_type} - {selector} (skor: {score:.2f})")
                
                return element
            except Exception as e:
                logger.warning(f"Element #{i+1} başarısız: {e}")
                continue
        
        logger.warning(f"'{locator_id}' için hiçbir element testi başarılı olmadı")
        return None
        
    def _guess_element_type_from_id(self, locator_id):
        """
        Locator ID'den element tipini tahmin eder.
        
        Args:
            locator_id (str): Locator benzersiz tanımlayıcısı
            
        Returns:
            list: Tahmin edilen element tipleri
        """
        id_lower = locator_id.lower()
        element_types = []
        
        # Giriş alanları
        if any(kw in id_lower for kw in ['input', 'text', 'field', 'area', 'arama', 'search', 'kutu']):
            element_types.append('input')
            
        # Butonlar
        if any(kw in id_lower for kw in ['button', 'buton', 'btn', 'submit', 'gonder', 'ara']):
            element_types.append('button')
            
        # Linkler
        if any(kw in id_lower for kw in ['link', 'baglanti', 'url', 'href']):
            element_types.append('link')
            
        # Seçim elemanları
        if any(kw in id_lower for kw in ['select', 'dropdown', 'option', 'secim', 'liste']):
            element_types.append('select')
            
        # Onay kutuları
        if any(kw in id_lower for kw in ['check', 'tick', 'onay', 'checkbox']):
            element_types.append('checkbox')
            
        # Varsayılan olarak element
        if not element_types:
            element_types.append('element')
            
        return element_types
        
    def _filter_elements_by_type(self, elements, element_type_hints):
        """
        Elementleri türlerine göre filtreler ve skorlarını günceller.
        
        Args:
            elements (list): Filtrelenecek elementler listesi
            element_type_hints (list): Tahmin edilen element tipleri
            
        Returns:
            list: Filtrelenmiş ve puanlanmış elementler listesi
        """
        # Element listesi boşsa filtreleme gerekmez
        if not elements:
            return []
            
        filtered_list = []
        for item in elements:
            # Mevcut skoru al
            base_score = item.get('score', 0.5)
            
            # Element Tag'ine bak
            element = item.get('element')
            selector_type = item.get('type')
            selector = item.get('selector', '')
            
            if not element:
                filtered_list.append(item)
                continue
                
            # HTML tag adını al
            tag_name = getattr(element, 'name', '').lower()
            
            # Tag adına göre
            if tag_name in ['input', 'textarea']:
                if 'input' in element_type_hints and tag_name == 'input':
                    base_score += 0.2
            elif tag_name == 'button' or 'submit' in selector:
                if 'button' in element_type_hints and (tag_name == 'button' or (tag_name == 'input' and 'submit' in selector)):
                    base_score += 0.2
            elif tag_name == 'a' or 'link' in selector:
                if 'link' in element_type_hints and tag_name == 'a':
                    base_score += 0.2
            elif tag_name == 'select':
                if 'select' in element_type_hints and tag_name == 'select':
                    base_score += 0.2
            elif tag_name == 'input' and 'checkbox' in selector:
                if 'checkbox' in element_type_hints and tag_name == 'input' and 'checkbox' in selector:
                    base_score += 0.2
            
            # Filtre koşulları: Tamamen filtrelemek yerine puanı düşür/yükselt
            if 'input' in element_type_hints and tag_name not in ['input', 'textarea', 'select']:
                # Input bekliyoruz ama değil - puanı düşür
                base_score *= 0.5
            
            # Güncellenmiş puanla öğeyi listeye ekle
            item['score'] = min(0.99, base_score)  # Max 0.99 olabilir
            filtered_list.append(item)
            
        return filtered_list
        
    def _determine_element_type(self, tag_name, selector):
        """
        HTML tag adı ve seçiciden element türünü belirler.
        
        Args:
            tag_name (str): Element tag adı
            selector (str): Element seçicisi
            
        Returns:
            str: Element türü
        """
        # Tag adına göre
        if tag_name in ['input', 'textarea']:
            return 'input'
        elif tag_name == 'button' or 'submit' in selector:
            return 'button'
        elif tag_name == 'a' or 'link' in selector:
            return 'link'
        elif tag_name == 'select':
            return 'select'
        elif tag_name == 'input' and 'checkbox' in selector:
            return 'checkbox'
        else:
            return 'element'
            
    def _verify_element_interaction_type(self, element, expected_types):
        """
        Elementin beklenen türlerden biri olup olmadığını doğrular.
        
        Args:
            element: Playwright element 
            expected_types (list): Beklenen element tipleri
            
        Returns:
            bool: Element doğru türde ise True
        """
        try:
            # Element tag adını al
            tag_info = element.evaluate("el => ({ tagName: el.tagName.toLowerCase(), type: el.type })")
            tag_name = tag_info.get('tagName', '').lower()
            input_type = tag_info.get('type', '').lower()
            
            logger.info(f"Element türü doğrulanıyor - Tag: {tag_name}, Type: {input_type}")
            
            # 'input' bekliyorsak
            if 'input' in expected_types:
                if tag_name in ['input', 'textarea', 'select']:
                    return True
                    
            # 'button' bekliyorsak
            if 'button' in expected_types:
                if tag_name == 'button' or (tag_name == 'input' and input_type in ['button', 'submit']):
                    return True
                    
            # 'link' bekliyorsak
            if 'link' in expected_types:
                if tag_name == 'a':
                    return True
                    
            # 'select' bekliyorsak
            if 'select' in expected_types:
                if tag_name == 'select':
                    return True
                    
            # 'checkbox' bekliyorsak
            if 'checkbox' in expected_types:
                if tag_name == 'input' and input_type == 'checkbox':
                    return True
                    
            # 'element' bekliyorsak her türlü element kabul edilebilir
            if 'element' in expected_types:
                return True
                
            # Hiçbir tip eşleşmedi
            return False
        except Exception as e:
            logger.warning(f"Element türü doğrulanırken hata: {e}")
            # Doğrulama başarısız olursa varsayılan olarak True döndür
            # Böylece element en azından denenebilir
            return True

    def _create_element_by_type(self, selector_type, selector):
        """
        Verilen seçici tipi ve değerine göre element oluşturur.
        
        Args:
            selector_type (str): Seçici tipi (css, text, role vb.)
            selector (str): Seçici değeri
            
        Returns:
            Locator: Oluşturulan element veya None (desteklenmeyen tip için)
        """
        if selector_type == 'css':
            return self.page.locator(selector).first
        elif selector_type == 'text':
            return self.page.get_by_text(selector).first
        elif selector_type == 'role':
            return self.page.get_by_role(selector).first
        elif selector_type == 'alt':
            return self.page.get_by_alt_text(selector).first
        elif selector_type == 'label':
            return self.page.get_by_label(selector).first
        elif selector_type == 'placeholder':
            return self.page.get_by_placeholder(selector).first
        elif selector_type == 'testid':
            return self.page.get_by_test_id(selector).first
        elif selector_type == 'xpath' or selector_type.startswith('predicted_xpath'):
            return self.page.locator(f"xpath={selector}").first
        else:
            return None

    def _try_prediction_strategy(self, locator_id, html_content, hints):
        """
        Yapay zeka/ML tabanlı tahmin stratejisini dener.
        
        Args:
            locator_id (str): Locator benzersiz tanımlayıcısı
            html_content (str): HTML içeriği
            hints (list): Locator ID'den çıkarılan ipuçları
            
        Returns:
            Locator: Bulunan element veya None
        """
        if not self.predictor:
            return None
            
        try:
            logger.info(f"'{locator_id}' için locator tahmin modeli kullanılıyor")
            
            # Sayfanın mevcut durumu ve locator_id'yi kullanarak tahmin yap
            predicted_locators = self._predict_locators(locator_id, html_content, hints)
            
            if not predicted_locators:
                return None
                
            # Tahmin edilen locator'ları dene
            for pred in predicted_locators:
                pred_selector = pred['selector']
                pred_type = pred['type']
                pred_score = pred.get('score', 0)
                
                logger.info(f"Tahmin edilen locator deneniyor: {pred_type} - {pred_selector} (skor: {pred_score:.2f})")
                
                try:
                    element = self._create_element_by_type(pred_type, pred_selector)
                    if not element:
                        continue
                    
                    # Elementi kontrol et
                    element.wait_for(timeout=2000)
                    
                    # Başarılı tahmin stratejisini kaydet
                    strategy_type = f"predicted_{pred_type}"
                    self._save_successful_strategy(locator_id, pred_selector, strategy_type)
                    logger.info(f"Locator tahmin başarılı: {pred_type} - {pred_selector}")
                    
                    return element
                except Exception as e:
                    logger.warning(f"Tahmin edilen locator başarısız oldu: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Locator tahmin sırasında hata: {e}")
            logger.error(traceback.format_exc())
            
        return None

    def _promote_successful_strategy(self, locator_id, strategy):
        """
        Başarılı stratejiyi listenin başına taşır.
        
        Args:
            locator_id (str): Locator benzersiz tanımlayıcısı
            strategy (dict): Başarılı strateji
        """
        self.locator_db[locator_id]['strategies'].remove(strategy)
        self.locator_db[locator_id]['strategies'].insert(0, strategy)
        self._save_locator_db()

    def _predict_locators(self, locator_id, html_content, hints):
        """
        Verilen ipuçları ve HTML içeriğini kullanarak olası locator'ları tahmin eder.
        
        Args:
            locator_id (str): Locator ID
            html_content (str): Sayfanın HTML içeriği
            hints (list): Locator ID'den çıkarılan ipuçları
            
        Returns:
            list: Tahmin edilen locator'lar (skor değerleriyle birlikte)
        """
        if not self.predictor:
            return []
            
        try:
            # Predictor sınıfının predict metodunu çağır
            return self.predictor.predict(locator_id, html_content, hints)
        except Exception as e:
            logger.error(f"Locator tahmini sırasında hata: {e}")
            logger.error(traceback.format_exc())
            
            # Basit bir fallback mekanizması (model çalışmazsa)
            return self._fallback_prediction(locator_id, html_content, hints)
            
    def _fallback_prediction(self, locator_id, html_content, hints):
        """
        Model çalışmazsa basit bir tahmin mekanizması sağlar.
        
        Args:
            locator_id (str): Locator ID
            html_content (str): Sayfanın HTML içeriği
            hints (list): Locator ID'den çıkarılan ipuçları
            
        Returns:
            list: Basit tahmini locator'lar
        """
        predicted_locators = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Attribute içinde hint'leri ara
        predicted_locators.extend(self._predict_from_attributes(soup, hints))
        
        # XPath tahminleri oluştur
        predicted_locators.extend(self._create_xpath_predictions(hints))
        
        # Element tiplerine göre tahminler
        predicted_locators.extend(self._predict_by_element_types(hints))
        
        # Rol tabanlı tahminler
        predicted_locators.extend(self._predict_by_roles(hints))
        
        # Skorlara göre sırala (en yüksek skordan başlayarak)
        predicted_locators.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        # En olası 10 tahmini döndür
        return predicted_locators[:10]

    def _predict_from_attributes(self, soup, hints):
        """
        Element özniteliklerinden locator tahminleri yapar.
        
        Args:
            soup (BeautifulSoup): Analiz edilmiş HTML içeriği
            hints (list): Aranacak ipuçları
            
        Returns:
            list: Tahmin edilen locator'lar
        """
        predictions = []
        
        # Attribute içinde hint'leri ara (data-*, aria-*, name, id, class, vb.)
        for tag in soup.find_all(True):  # Tüm elementleri bul
            for attr, value in tag.attrs.items():
                # Attribute değeri string değilse (örneğin liste), string'e çevir
                if not isinstance(value, str):
                    if isinstance(value, list):
                        value = " ".join(value)
                    else:
                        value = str(value)
                
                # Hint'leri attribute değerinde ara
                for hint in hints:
                    if len(hint) > 3 and hint.lower() in value.lower():
                        # CSS seçici oluştur
                        selector = None
                        if attr == 'id':
                            selector = f"#{value}"
                        elif attr == 'class':
                            # Boşlukları nokta ile değiştir
                            selector = f".{value.replace(' ', '.')}"
                        else:
                            # Diğer attribute'lar için
                            selector = f"[{attr}='{value}']"
                        
                        if selector:
                            predictions.append({
                                'selector': selector,
                                'type': 'css',
                                'score': 0.7  # Orta düzeyde güven
                            })
        
        return predictions

    def _create_xpath_predictions(self, hints):
        """
        XPath tabanlı locator tahminleri oluşturur.
        
        Args:
            hints (list): Aranacak ipuçları
            
        Returns:
            list: Tahmin edilen XPath locator'ları
        """
        predictions = []
        
        # Basit XPath'ler oluştur (text içerenler)
        for hint in hints:
            if len(hint) > 3:
                # Buton içinde metin araması
                predictions.append({
                    'selector': f"//button[contains(text(), '{hint}')]",
                    'type': 'xpath',
                    'score': 0.6
                })
                
                # Herhangi bir element içinde metin araması
                predictions.append({
                    'selector': f"//*[contains(text(), '{hint}')]",
                    'type': 'xpath',
                    'score': 0.5
                })
        
        return predictions

    def _predict_by_element_types(self, hints):
        """
        Element tiplerine göre locator tahminleri yapar.
        
        Args:
            hints (list): Aranacak ipuçları
            
        Returns:
            list: Tahmin edilen locator'lar
        """
        predictions = []
        
        # Yaygın element tipleri için tahminler
        element_types = ["button", "a", "input", "select", "textarea", "div", "span"]
        for element_type in element_types:
            for hint in hints:
                if len(hint) > 3:
                    # ID içeren elementler
                    predictions.append({
                        'selector': f"{element_type}[id*='{hint}']",
                        'type': 'css',
                        'score': 0.4
                    })
                    
                    # Class içeren elementler
                    predictions.append({
                        'selector': f"{element_type}[class*='{hint}']",
                        'type': 'css',
                        'score': 0.4
                    })
                    
                    # Metin içeren elementler (giriş alanları hariç)
                    if element_type not in ["input", "select", "textarea"]:
                        predictions.append({
                            'selector': hint,
                            'type': 'text',
                            'score': 0.5
                        })
        
        return predictions

    def _predict_by_roles(self, hints):
        """
        ARIA rolleri tabanlı locator tahminleri yapar.
        
        Args:
            hints (list): Aranacak ipuçları
            
        Returns:
            list: Tahmin edilen role-based locator'lar
        """
        predictions = []
        
        # Buton rolü için ipuçları
        if any(h in ["button", "btn", "buton"] for h in hints):
            predictions.append({
                'selector': "button",
                'type': 'role',
                'score': 0.5
            })
        
        # Link rolü için ipuçları
        if any(h in ["link", "lnk", "baglanti", "bağlantı"] for h in hints):
            predictions.append({
                'selector': "link",
                'type': 'role',
                'score': 0.5
            })
        
        return predictions

    def _save_successful_strategy(self, locator_id, selector, selector_type):
        """
        Başarılı stratejiyi veritabanına kaydeder ve modeli eğitir.
        
        Args:
            locator_id (str): Locator benzersiz tanımlayıcısı
            selector (str): Başarılı seçici
            selector_type (str): Seçici türü
        """
        strategy = {
            'type': selector_type,
            'selector': selector,
            'last_used': time.time()
        }
        
        # Stratejiyi veritabanına kaydet
        self._add_strategy_to_database(locator_id, strategy)
        
        # Modeli eğit
        self._train_model_with_strategy(locator_id, selector, selector_type)
        
    def _add_strategy_to_database(self, locator_id, strategy):
        """
        Stratejiyi veritabanına ekler.
        
        Args:
            locator_id (str): Locator benzersiz tanımlayıcısı
            strategy (dict): Eklenecek strateji
        """
        if locator_id not in self.locator_db:
            self.locator_db[locator_id] = {
                'strategies': [strategy]
            }
        else:
            # Aynı strateji zaten var mı kontrol et
            exists = False
            for existing in self.locator_db[locator_id]['strategies']:
                if (existing['type'] == strategy['type'] and 
                    existing['selector'] == strategy['selector']):
                    existing['last_used'] = strategy['last_used']
                    exists = True
                    break
            
            if not exists:
                self.locator_db[locator_id]['strategies'].insert(0, strategy)
        
        # Veritabanını kaydet
        self._save_locator_db()
        
    def _train_model_with_strategy(self, locator_id, selector, selector_type):
        """
        Modeli başarılı stratejiyle eğitir.
        
        Args:
            locator_id (str): Locator benzersiz tanımlayıcısı
            selector (str): Başarılı seçici
            selector_type (str): Seçici türü
        """
        try:
            if self.predictor and hasattr(self.predictor, 'train'):
                # Eğer selector_type "predicted_" ile başlıyorsa, gerçek türü al
                actual_type = selector_type
                if selector_type.startswith('predicted_'):
                    actual_type = selector_type[len('predicted_'):]
                
                # Sayfanın HTML içeriğini al
                html_content = self.page.content()
                
                # Modeli eğit
                self.predictor.train(locator_id, html_content, selector, actual_type)
                logger.info(f"Model '{locator_id}' için başarılı strateji ile eğitildi: {selector_type} - {selector}")
        except Exception as e:
            logger.error(f"Model eğitimi sırasında hata: {e}")
            logger.error(traceback.format_exc()) 