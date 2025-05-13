"""
Self-Healing Test Modeli Oluşturucu Yardımcı Modül

Bu modül, self-healing test mekanizması için model verisi oluşturmak üzere
kullanılan temel işlevleri içerir. HTML içeriğini analiz eder ve
self-healing algoritması için lokator eğitim verileri oluşturur.
"""

import os
import json
import logging
import importlib.util
import requests
from bs4 import BeautifulSoup
import re
from pathlib import Path

# ------------------------------------------------------------------------------
# Model İşleme Fonksiyonları
# ------------------------------------------------------------------------------

def load_predictor(model_file):
    """
    LocatorPredictor modelini dinamik olarak yükler.
    
    Args:
        model_file (Path): Model Python dosyasının yolu
        
    Returns:
        LocatorPredictor: Model nesnesi veya None (hata durumunda)
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Model dosyası yükleniyor: {model_file}")
    
    if not model_file.exists():
        logger.error(f"HATA: Model dosyası bulunamadı: {model_file}")
        return None
    
    try:
        # Modülü dinamik olarak yükle
        spec = importlib.util.spec_from_file_location("locator_predict_model", model_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Modeli oluştur
        predictor = module.LocatorPredictor()
        logger.info("Model başarıyla yüklendi")
        return predictor
    except Exception as e:
        logger.error(f"Model yüklenirken hata oluştu: {e}", exc_info=True)
        return None

def train_model(predictor, html_content, locators):
    """
    Verilen HTML içeriği ve lokator listesi ile modeli eğitir.
    
    Args:
        predictor: LocatorPredictor model nesnesi
        html_content (str): HTML içeriği
        locators (list): Lokator listesi. (locator_id, selector, selector_type) tuple'larını içerir.
        
    Returns:
        int: Eğitilen lokator sayısı
    """
    logger = logging.getLogger(__name__)
    trained_count = 0
    
    # HTML içeriğinin ilk 200 karakterini göster
    logger.info(f"Eğitim için kullanılan HTML (ilk 200 karakter): {html_content[:200]}...")
    
    # Sayfadaki temel form elemanlarını ve yapıları analiz et
    try:
        logger.info("Sayfadaki form elemanlarını otomatik analiz ediyorum...")
        soup = BeautifulSoup(html_content, "html.parser")
        
        # Otomatik tespit edilen form elemanları
        auto_locators = []
        
        # 1. Arama giriş alanlarını otomatik tespit et
        search_inputs = soup.select("input[type='search'], input[placeholder*='ara'], input[name*='search'], .search-input")
        if search_inputs:
            logger.info(f"{len(search_inputs)} arama kutusunu otomatik tespit ettim")
            for i, input_el in enumerate(search_inputs[:3]):  # En fazla 3 tanesini al
                input_id = input_el.get('id', '')
                input_class = ' '.join(input_el.get('class', []))
                input_name = input_el.get('name', '')
                input_placeholder = input_el.get('placeholder', '')
                
                css_selector = f"input[type='search'], input[placeholder*='ara'], input[name*='search'], .search-input"
                logger.info(f"Arama kutusu #{i+1}: id={input_id}, class={input_class}, name={input_name}, placeholder={input_placeholder}")
                auto_locators.append(("arama_kutusu", css_selector, "css"))
        
        # 2. Submit butonlarını otomatik tespit et
        submit_buttons = soup.select("button[type='submit'], input[type='submit'], .search-button, button.search")
        if submit_buttons:
            logger.info(f"{len(submit_buttons)} submit butonunu otomatik tespit ettim")
            for i, button in enumerate(submit_buttons[:3]):
                button_id = button.get('id', '')
                button_class = ' '.join(button.get('class', []))
                button_text = button.text.strip() if hasattr(button, 'text') else ''
                
                css_selector = f"button[type='submit'], input[type='submit'], .search-button, button.search"
                logger.info(f"Submit butonu #{i+1}: id={button_id}, class={button_class}, text={button_text}")
                auto_locators.append(("arama_butonu", css_selector, "css"))
        
        # 3. Filtreleme butonlarını otomatik tespit et
        filter_buttons = soup.select("button:contains('Filtre'), button:contains('filter'), [class*='filter'], button[aria-label*='filtre']")
        if filter_buttons:
            logger.info(f"{len(filter_buttons)} filtre butonunu otomatik tespit ettim")
            for i, button in enumerate(filter_buttons[:2]):
                button_text = button.text.strip() if hasattr(button, 'text') else ''
                if button_text:
                    logger.info(f"Filtre butonu #{i+1}: text={button_text}")
                    auto_locators.append(("filtre_butonu", button_text, "text"))
        
        # 4. Restoran kartlarını otomatik tespit et
        restaurant_cards = soup.select(".restaurant-card, .restaurant-item, [class*='restaurant'], [class*='card']")
        if restaurant_cards:
            logger.info(f"{len(restaurant_cards)} restoran kartını otomatik tespit ettim")
            auto_locators.append(("restoran_kartlari", ".restaurant-card, .restaurant-item, [class*='restaurant'], [class*='card']", "css"))
        
        # Otomatik tespit edilen lokatörler ile modeli eğit
        if auto_locators:
            logger.info(f"Toplam {len(auto_locators)} otomatik locator tespit edildi")
            for auto_id, auto_selector, auto_type in auto_locators:
                # Her bir temel lokator için ek varyasyonlar oluştur
                variations = create_selector_variations(auto_selector, auto_type)
                
                # Temel lokator ve varyasyonlarıyla eğit
                try:
                    logger.info(f"Otomatik tespit: '{auto_id}' için model eğitiliyor: {auto_selector} ({auto_type})")
                    predictor.train(auto_id, html_content, auto_selector, auto_type)
                    trained_count += 1
                    
                    # Varyasyonlarla eğit
                    for variant_selector, variant_type in variations:
                        try:
                            predictor.train(auto_id, html_content, variant_selector, variant_type)
                            logger.info(f"  + Varyasyon ile eğitildi: {variant_selector} ({variant_type})")
                            trained_count += 1
                        except Exception as e:
                            logger.warning(f"  - Varyasyon eğitimi başarısız: {e}")
                except Exception as e:
                    logger.error(f"'{auto_id}' için otomatik eğitim başarısız: {e}")
    except Exception as e:
        logger.error(f"Otomatik form elemanı tespiti sırasında hata: {e}")
    
    # Kullanıcının belirttiği lokatorlar ile eğitim
    logger.info(f"Kullanıcı tarafından belirlenen {len(locators)} locator ile eğitim yapılıyor...")
    for locator_id, selector, selector_type in locators:
        logger.info(f"Model '{locator_id}' için eğitiliyor... Seçici: {selector} ({selector_type})")
        try:
            predictor.train(locator_id, html_content, selector, selector_type)
            trained_count += 1
            logger.info(f"'{locator_id}' için model eğitimi başarılı")
            
            # Seçici varyasyonları oluştur ve onlarla da eğit
            variations = create_selector_variations(selector, selector_type)
            for variant_selector, variant_type in variations:
                try:
                    predictor.train(locator_id, html_content, variant_selector, variant_type)
                    logger.debug(f"  + Varyasyon ile eğitildi: {variant_selector} ({variant_type})")
                    trained_count += 1
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"'{locator_id}' için eğitim başarısız: {e}")
    
    logger.info(f"Model eğitimi tamamlandı, {trained_count} toplam eğitim örneği işlendi.")
    return trained_count

def create_selector_variations(selector, selector_type):
    """
    Bir seçiciden olası varyasyonlar oluşturur.
    
    Args:
        selector (str): Orijinal seçici
        selector_type (str): Seçici tipi (css, text, vb.)
        
    Returns:
        list: (selector, type) tuple'larından oluşan varyasyonlar listesi
    """
    variations = []
    
    if selector_type == "css":
        # CSS seçicileri için varyasyonlar
        if "," in selector:
            # Her bir alternatifi ayrı seçici olarak ekle
            for part in selector.split(","):
                part = part.strip()
                if part:
                    variations.append((part, "css"))
        
        # Arama kutuları için XPath alternatifi
        if "input" in selector and ("search" in selector or "ara" in selector):
            variations.append(("//input[@type='search' or @placeholder[contains(., 'ara')] or @name[contains(., 'search')]]", "xpath"))
        
        # Butonlar için text alternatifi
        if "button" in selector and "search" in selector:
            variations.append(("Ara", "text"))
            variations.append(("Search", "text"))
    
    elif selector_type == "text":
        # Metin tabanlı seçiciler için varyasyonlar
        if selector.lower() in ["ara", "search", "filtrele", "filter"]:
            variations.append((f"button:has-text('{selector}')", "css"))
            variations.append((f"//*[contains(text(), '{selector}')]", "xpath"))
    
    return variations

def generate_advanced_selectors(html_content, base_locators):
    """
    HTML analizi yaparak mevcut lokatorlar için ek seçiciler üretir.
    
    Args:
        html_content (str): HTML içeriği
        base_locators (list): Temel lokator listesi
        
    Returns:
        list: Ek lokator listesi
    """
    logger = logging.getLogger(__name__)
    extra_locators = []
    
    try:
        # HTML'yi analiz et
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Form elemanlarını ve etkileşimli elemanları belirle
        form_elements = identify_form_elements(soup)
        
        # Her temel lokator için alternatif seçiciler üret
        for locator_id, selector, selector_type in base_locators:
            # ID'yi analiz et ve olası element türünü tahmin et
            element_type = predict_element_type(locator_id)
            logger.info(f"'{locator_id}' için tahmin edilen element türü: {element_type}")
            
            # CSS seçicileri için
            if selector_type == 'css':
                generate_alternatives_for_css(soup, locator_id, selector, element_type, extra_locators)
            
            # Metin tabanlı seçiciler için
            elif selector_type == 'text':
                generate_alternatives_for_text(soup, locator_id, selector, element_type, extra_locators)
                
            # Element türüne göre özel stratejiler ekle
            if element_type in ['input', 'button', 'link']:
                generate_type_specific_selectors(soup, locator_id, element_type, extra_locators, form_elements)
        
        logger.info(f"{len(extra_locators)} ek seçici oluşturuldu")
        return extra_locators
    except Exception as e:
        logger.error(f"Ek seçici oluşturulurken hata oluştu: {e}")
        return []

def identify_form_elements(soup):
    """
    Sayfadaki tüm form elemanlarını belirler ve kategorize eder.
    
    Args:
        soup (BeautifulSoup): HTML içeriği
        
    Returns:
        dict: Form elemanları ve özellikleri
    """
    form_elements = {
        'inputs': [],
        'buttons': [],
        'selects': [],
        'textareas': [],
        'links': []
    }
    
    # 1. Input elemanları
    for tag in soup.find_all('input'):
        input_type = tag.get('type', 'text')
        form_elements['inputs'].append({
            'element': tag,
            'type': input_type,
            'id': tag.get('id', ''),
            'name': tag.get('name', ''),
            'placeholder': tag.get('placeholder', ''),
            'class': tag.get('class', []),
            'value': tag.get('value', '')
        })
    
    # 2. Butonlar
    for tag in soup.find_all(['button', 'input[type="button"]', 'input[type="submit"]']):
        form_elements['buttons'].append({
            'element': tag,
            'id': tag.get('id', ''),
            'name': tag.get('name', ''),
            'class': tag.get('class', []),
            'text': tag.text.strip() if hasattr(tag, 'text') else ''
        })
    
    # 3. Select ve Textarea
    for tag in soup.find_all(['select', 'textarea']):
        element_type = 'selects' if tag.name == 'select' else 'textareas'
        form_elements[element_type].append({
            'element': tag,
            'id': tag.get('id', ''),
            'name': tag.get('name', ''),
            'class': tag.get('class', [])
        })
    
    # 4. Linkler
    for tag in soup.find_all('a'):
        form_elements['links'].append({
            'element': tag,
            'id': tag.get('id', ''),
            'href': tag.get('href', ''),
            'class': tag.get('class', []),
            'text': tag.text.strip()
        })
    
    return form_elements

def predict_element_type(locator_id):
    """
    Lokator ID'sini analiz ederek olası element türünü tahmin eder.
    
    Args:
        locator_id (str): Lokator benzersiz tanımlayıcısı
        
    Returns:
        str: Tahmin edilen element türü
    """
    locator_lower = locator_id.lower()
    
    # Input/arama elemanları
    if any(keyword in locator_lower for keyword in ['input', 'field', 'text', 'search', 'arama', 'kutu']):
        return 'input'
    
    # Butonlar
    elif any(keyword in locator_lower for keyword in ['button', 'btn', 'buton', 'submit', 'gönder']):
        return 'button'
    
    # Linkler
    elif any(keyword in locator_lower for keyword in ['link', 'lnk', 'href', 'baglanti']):
        return 'link'
    
    # Seçim kutuları
    elif any(keyword in locator_lower for keyword in ['select', 'dropdown', 'combo', 'liste']):
        return 'select'
    
    # Onay kutuları
    elif any(keyword in locator_lower for keyword in ['checkbox', 'check', 'tick', 'onay']):
        return 'checkbox'
    
    # Varsayılan
    return 'element'

def generate_alternatives_for_css(soup, locator_id, selector, element_type, extra_locators):
    """
    CSS seçiciler için alternatif seçiciler oluşturur.
    
    Args:
        soup (BeautifulSoup): HTML içeriği
        locator_id (str): Lokator benzersiz tanımlayıcısı
        selector (str): Orijinal CSS seçici
        element_type (str): Tahmin edilen element türü
        extra_locators (list): Eklenecek ekstra lokatorlar listesi
    """
    try:
        # CSS seçiciyi virgülle ayrılmış parçalara böl
        selector_parts = selector.split(',')
        for part in selector_parts:
            part = part.strip()
            if not part:
                continue
            
            # Bu seçici parçasını eşleşen elementleri bul
            elements = soup.select(part)
            for element in elements:
                # Element için alternatif seçiciler oluştur
                generate_alternatives_for_element(element, locator_id, element_type, extra_locators)
    except Exception as e:
        logger.error(f"CSS seçicisi işlenirken hata: {e}")

def generate_alternatives_for_text(soup, locator_id, text, element_type, extra_locators):
    """
    Metin tabanlı seçiciler için alternatif seçiciler oluşturur.
    
    Args:
        soup (BeautifulSoup): HTML içeriği
        locator_id (str): Lokator benzersiz tanımlayıcısı
        text (str): Aranacak metin
        element_type (str): Tahmin edilen element türü
        extra_locators (list): Eklenecek ekstra lokatorlar listesi
    """
    try:
        # Verilen metni içeren tüm elementleri bul
        elements = soup.find_all(text=lambda t: text.lower() in t.lower() if t else False)
        for text_element in elements:
            if text_element.parent:
                # Element için alternatif seçiciler oluştur
                generate_alternatives_for_element(text_element.parent, locator_id, element_type, extra_locators)
                
                # Metin tabanlı arama için XPath alternatifi
                xpath = f"//*/text()[contains(., '{text}')]/parent::*"
                extra_locators.append((locator_id, xpath, 'xpath'))
    except Exception as e:
        logger.error(f"Metin seçicisi işlenirken hata: {e}")

def generate_alternatives_for_element(element, locator_id, element_type, extra_locators):
    """
    Belirli bir element için alternatif seçiciler oluşturur.
    
    Args:
        element (Tag): BeautifulSoup element
        locator_id (str): Lokator benzersiz tanımlayıcısı
        element_type (str): Tahmin edilen element türü
        extra_locators (list): Eklenecek ekstra lokatorlar listesi
    """
    # ID tabanlı seçici (en spesifik)
    if element.get('id'):
        css_id = f"#{element['id']}"
        extra_locators.append((locator_id, css_id, 'css'))
    
    # Class tabanlı seçici
    if element.get('class') and element['class']:
        class_selector = '.' + '.'.join(element['class'])
        extra_locators.append((locator_id, class_selector, 'css'))
    
    # İç içe eleman yapısı için CSS seçici (belirli derinliğe kadar)
    if element.parent and element.parent.name != '[document]':
        if element.parent.get('id'):
            parent_child = f"#{element.parent['id']} > {element.name}"
            extra_locators.append((locator_id, parent_child, 'css'))
        elif element.parent.get('class') and element.parent['class']:
            parent_class = '.'.join(element.parent['class'])
            parent_child = f".{parent_class} > {element.name}"
            extra_locators.append((locator_id, parent_child, 'css'))
    
    # Diğer öznitelikler için
    for attr, value in element.attrs.items():
        if attr not in ['id', 'class']:
            # Değer string değilse atla (örn. liste)
            if not isinstance(value, str):
                continue
                
            attr_selector = f"{element.name}[{attr}='{value}']"
            extra_locators.append((locator_id, attr_selector, 'css'))
    
    # Eleman türüne özgü seçiciler
    if element_type == 'input':
        # Input elemanları için placeholder'ı kullan
        if element.get('placeholder'):
            placeholder_selector = f"[placeholder='{element['placeholder']}']"
            extra_locators.append((locator_id, placeholder_selector, 'css'))
            
            # Placeholder ile yaklaşık eşleşme
            placeholder_contains = f"[placeholder*='{element['placeholder'][:10]}']"
            extra_locators.append((locator_id, placeholder_contains, 'css'))
    
    elif element_type == 'button' and element.text and len(element.text.strip()) < 50:
        # Butonlar için metin içeriğini kullan
        text_selector = element.text.strip()
        extra_locators.append((locator_id, text_selector, 'text'))
        
        # Rol tabanlı seçici
        role_selector = "button"
        extra_locators.append((locator_id, role_selector, 'role'))
    
    elif element_type == 'link' and element.text and len(element.text.strip()) < 50:
        # Linkler için metin içeriğini kullan
        text_selector = element.text.strip()
        extra_locators.append((locator_id, text_selector, 'text'))
        
        # Rol tabanlı seçici
        role_selector = "link"
        extra_locators.append((locator_id, role_selector, 'role'))
    
    # XPath seçici
    try:
        xpath = get_element_xpath(element)
        if xpath:
            extra_locators.append((locator_id, xpath, 'xpath'))
    except Exception:
        pass

def generate_type_specific_selectors(soup, locator_id, element_type, extra_locators, form_elements):
    """
    Element türüne özgü seçiciler oluşturur.
    
    Args:
        soup (BeautifulSoup): HTML içeriği
        locator_id (str): Lokator benzersiz tanımlayıcısı
        element_type (str): Element türü
        extra_locators (list): Eklenecek ekstra lokatorlar listesi
        form_elements (dict): Belirlenen form elemanları
    """
    # ID'deki olası ipuçlarını çıkar
    hints = locator_id.lower().split('_')
    hints = [h for h in hints if len(h) > 3]
    
    if element_type == 'input':
        for input_data in form_elements['inputs']:
            for hint in hints:
                # ID, name, placeholder gibi özniteliklerde ipucu ara
                for attr in ['id', 'name', 'placeholder']:
                    value = input_data.get(attr, '')
                    if value and hint in value.lower():
                        # İpucu bulundu, CSS seçici oluştur
                        if attr == 'id':
                            selector = f"#{value}"
                        else:
                            selector = f"input[{attr}='{value}']"
                        extra_locators.append((locator_id, selector, 'css'))
                        
                        # Placeholder için alternatif seçici
                        if attr == 'placeholder':
                            selector = value
                            extra_locators.append((locator_id, selector, 'placeholder'))
                
                # Yaygın arama kutusu seçicileri
                common_selectors = [
                    "input[type='search']",
                    "input[type='text']",
                    ".search-input",
                    "input.search",
                    "input[name*='search']",
                    "input[placeholder*='ara']"
                ]
                for selector in common_selectors:
                    extra_locators.append((locator_id, selector, 'css'))
    
    elif element_type == 'button':
        for button_data in form_elements['buttons']:
            for hint in hints:
                # Buton metninde ipucu ara
                if button_data['text'] and hint in button_data['text'].lower():
                    # Metin tabanlı seçici
                    extra_locators.append((locator_id, button_data['text'], 'text'))
                    
                    # Rol tabanlı seçici
                    extra_locators.append((locator_id, "button", 'role'))
                    
                    # XPath tabanlı seçici
                    xpath = f"//button[contains(text(), '{hint}')]"
                    extra_locators.append((locator_id, xpath, 'xpath'))
    
    elif element_type == 'link':
        for link_data in form_elements['links']:
            for hint in hints:
                # Link metninde ipucu ara
                if link_data['text'] and hint in link_data['text'].lower():
                    # Metin tabanlı seçici
                    extra_locators.append((locator_id, link_data['text'], 'text'))
                    
                    # Rol tabanlı seçici
                    extra_locators.append((locator_id, "link", 'role'))
                    
                    # XPath tabanlı seçici
                    xpath = f"//a[contains(text(), '{hint}')]"
                    extra_locators.append((locator_id, xpath, 'xpath'))

def get_element_xpath(element):
    """
    BeautifulSoup elementi için XPath oluşturur.
    
    Args:
        element (Tag): BeautifulSoup element
        
    Returns:
        str: XPath seçici
    """
    components = []
    child = element
    for parent in element.parents:
        if parent.name == '[document]':
            break
        
        # Element kardeşlerini say
        siblings = parent.find_all(child.name, recursive=False)
        if len(siblings) > 1:
            # Birden fazla kardeş varsa, pozisyon belirt
            index = siblings.index(child) + 1
            components.append(f"{child.name}[{index}]")
        else:
            components.append(child.name)
            
        child = parent
    
    components.reverse()
    xpath = '//' + '/'.join(components)
    return xpath

def verify_model_data(model_data_file):
    """
    Oluşturulan model veri dosyasını doğrular ve özet bilgi döndürür.
    
    Args:
        model_data_file (Path): Doğrulanacak model veri dosyasının yolu
        
    Returns:
        dict: Doğrulama sonuçları
    """
    logger = logging.getLogger(__name__)
    results = {
        "success": False,
        "file_exists": False,
        "trained_cases": 0,
        "file_size": 0,
        "error": None
    }
    
    try:
        if model_data_file.exists():
            results["file_exists"] = True
            results["file_size"] = model_data_file.stat().st_size
            
            with open(model_data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                trained_cases = data.get('trained_cases', [])
                results["trained_cases"] = len(trained_cases)
                results["success"] = True
                
                logger.info(f"Model data dosyası doğrulandı: {model_data_file}")
                logger.info(f"Eğitilen toplam lokator sayısı: {len(trained_cases)}")
        else:
            results["error"] = "Dosya bulunamadı"
            logger.error(f"HATA: Model data dosyası bulunamadı: {model_data_file}")
    except Exception as e:
        results["error"] = str(e)
        logger.error(f"Model verisi doğrulanırken hata oluştu: {e}", exc_info=True)
    
    return results

# ------------------------------------------------------------------------------
# HTML İşleme Fonksiyonları
# ------------------------------------------------------------------------------

def get_html_content(url, user_agent=None, cookies=None):
    """
    Belirtilen URL'den HTML içeriğini çeker.
    
    Args:
        url (str): HTML içeriği çekilecek web sayfasının URL'si
        user_agent (str, optional): İsteği gönderirken kullanılacak User-Agent
        cookies (dict, optional): İsteğe dahil edilecek çerezler
        
    Returns:
        str: Web sayfasının HTML içeriği veya None (hata durumunda)
    """
    logger = logging.getLogger(__name__)
    logger.info(f"HTML içeriği çekiliyor: {url}")
    
    if user_agent is None:
        user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
    
    try:
        # Modern tarayıcı gibi davranmak için User-Agent başlığı ekleyelim
        headers = {"User-Agent": user_agent}
        
        # Varsayılan olarak 301/302 yönlendirmelerini takip eder
        response = requests.get(url, headers=headers, cookies=cookies, timeout=10, allow_redirects=True)
        
        if response.status_code == 200:
            logger.info("HTML içeriği başarıyla alındı!")
            return response.text
        else:
            logger.warning(f"HTML içeriği alınamadı. HTTP Durumu: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"HTML içeriği çekilirken hata oluştu: {e}", exc_info=True)
        return None

def create_sample_html():
    """
    Hata durumunda kullanılacak örnek HTML içeriği oluşturur.
    
    Returns:
        str: Örnek HTML içeriği
    """
    logger = logging.getLogger(__name__)
    logger.warning("Gerçek HTML alınamadı, örnek HTML kullanılıyor...")
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Restoranlar | TGO Yemek</title>
    </head>
    <body>
        <header>
            <div class="search-container">
                <input type="search" class="search-input" placeholder="Restoran ara..." name="search">
                <button type="submit" class="search-button">Ara</button>
            </div>
            <button class="filter-button">Filtrele ve Sırala</button>
        </header>
        <main>
            <section class="restaurant-list">
                <div class="restaurant-card">
                    <h2 class="restaurant-name">Pizza Restoran</h2>
                    <p class="restaurant-cuisine">İtalyan</p>
                </div>
                <div class="restaurant-card">
                    <h2 class="restaurant-name">Burger Restoran</h2>
                    <p class="restaurant-cuisine">Amerikan</p>
                </div>
            </section>
            <div class="pagination">
                <a href="#" class="active">1</a>
                <a href="#">2</a>
            </div>
        </main>
        <div id="filter-modal">
            <h3>Meat Burger & Gurme Mutfak</h3>
            <button>Mobil Uygulamalar</button>
        </div>
        <footer>
            <div>Bu site temsili amaçlarla oluşturulmuştur.</div>
        </footer>
    </body>
    </html>
    """

# ------------------------------------------------------------------------------
# Lokator Tanımları
# ------------------------------------------------------------------------------

def get_default_locators():
    """
    Öntanımlı lokator listesini döndürür.
    
    Returns:
        list: (locator_id, selector, selector_type) şeklinde lokator listesi
    """
    return [
        # (locator_id, selector, selector_type)
        ("arama_kutusu", "input[type='search'], .search-input, [placeholder*='ara'], input[name='search']", "css"),
        ("arama_butonu", "button[type='submit'], .search-button, button.search", "css"),
        ("filtre_butonu", "Filtrele ve Sırala", "text"),
        ("kategori_mutfak", "Meat Burger & Gurme Mutfak", "text"),
        ("uygula_butonu", "Mobil Uygulamalar", "text"),
        ("restoran_kartlari", ".restaurant-card, .restaurant-item, .restaurant-box", "css"),
        ("ilk_restoran", ".restaurant-card:first-child", "css"),
        ("aktif_sayfa", ".pagination .active", "css"),
        # Ek lokatorlar (restoranlar özelinde)
        ("restoran_ismi", "h2.restaurant-name, .restaurant-title, .restaurant-card h3", "css"),
        ("restoran_adresi", ".restaurant-address, .address, .location", "css"),
        ("restoran_puani", ".rating, .restaurant-rating, .score", "css")
    ] 