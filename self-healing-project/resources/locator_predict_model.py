"""
Locator tahmin modeli.

Bu modül, web sayfalarındaki HTML içeriğini analiz ederek en olası locator seçicilerini
tahmin etmeye çalışır. Sistem, kural tabanlı yaklaşımlar kullanarak çalışır.

Özellikler:
- HTML içeriğinden anlamlı özellikler çıkarma
- Locator ID'yi analiz etme
- Birden fazla tahmin stratejisi (metin, öznitelik, semantik, yapısal)
"""

# Standart kütüphaneler
import json
import logging
import re
import time
import traceback
from collections import Counter
from pathlib import Path

# Üçüncü parti kütüphaneler
from bs4 import BeautifulSoup

# Loglama konfigürasyonu
logger = logging.getLogger(__name__)

# Sabit değişkenler
MODEL_DATA_FILE = Path(__file__).parent.parent / "model_data.json"

class LocatorPredictor:
    """
    Locator tahmin modeli.
    
    Bu sınıf, HTML içeriğini analiz ederek web elementleri için
    en olası locator seçicilerini tahmin eder.
    """

    def __init__(self):
        """
        Locator tahmin modelini başlatır ve gerekli verileri yükler.
        """
        self.model_data = self._load_model_data()
        self.common_patterns = self._initialize_default_patterns()
        self.initialized = True
        logger.info("Locator tahmin modeli başlatıldı")

    def _load_model_data(self):
        """
        Model verisini dosyadan yükler veya yeni bir model veri yapısı oluşturur.
        
        Returns:
            dict: Model verisi sözlüğü
        """
        try:
            if MODEL_DATA_FILE.exists():
                with open(MODEL_DATA_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logger.info(f"Model verisi yüklendi: {MODEL_DATA_FILE}")
                return data
            else:
                logger.info(f"Model veri dosyası bulunamadı, yeni bir model başlatılıyor")
                return self._create_empty_model_data()
        except Exception as e:
            logger.error(f"Model veri yükleme hatası: {e}")
            return self._create_empty_model_data()

    def _create_empty_model_data(self):
        """
        Boş bir model veri yapısı oluşturur.
        
        Returns:
            dict: Boş model veri yapısı
        """
        return {
            'locator_patterns': {},  # Başarılı locator kalıpları
            'trained_cases': [],     # Eğitilen örnekler
            'version': '1.0',
            'created_at': time.time()
        }

    def _initialize_default_patterns(self):
        """
        Öntanımlı yaygın kalıpları oluşturur.
        
        Returns:
            dict: Element tiplerine göre kalıp sözlüğü
        """
        return {
            'button': [
                {'pattern': r'btn|button|submit|gönder|ilerle|sepet', 'score': 0.8},
                {'pattern': r'onclick|clickable|tıkla', 'score': 0.7}
            ],
            'link': [
                {'pattern': r'link|bağlantı|href|url', 'score': 0.8},
                {'pattern': r'goto|navigate|yönlendir', 'score': 0.7}
            ],
            'input': [
                {'pattern': r'input|text|password|email|şifre|eposta', 'score': 0.8},
                {'pattern': r'form|field|alan|giriş|entry', 'score': 0.7}
            ],
            'checkbox': [
                {'pattern': r'checkbox|check|tick|onay|işaretle', 'score': 0.9},
                {'pattern': r'select|seç|tercih', 'score': 0.7}
            ],
            'dropdown': [
                {'pattern': r'dropdown|select|combobox|açılır|liste', 'score': 0.9},
                {'pattern': r'option|seçenek|menu', 'score': 0.7}
            ]
        }

    def predict(self, locator_id, html_content, hints):
        """
        Verilen locator_id, HTML içeriği ve ipuçlarına göre olası locator'ları tahmin eder.
        
        Args:
            locator_id (str): Locator benzersiz tanımlayıcısı
            html_content (str): HTML içeriği
            hints (list): Locator ID'den çıkarılan ipuçları
            
        Returns:
            list: Tahmin edilen locator'lar
        """
        logger.info(f"'{locator_id}' için locator tahmin yapılıyor")
        
        try:
            # BeautifulSoup ile HTML içeriğini analiz et
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Tahminler için boş liste oluştur
            predictions = []
            
            # ID tabanlı tahminler
            predictions.append({
                'selector': f"#{locator_id}",
                'type': 'css',
                'score': 0.8
            })
            
            # Metin içeriği için tahminler
            for hint in hints:
                if len(hint) < 4:
                    continue
                    
                predictions.append({
                    'selector': hint,
                    'type': 'text',
                    'score': 0.7
                })
                
                # XPath alternatifi
                predictions.append({
                    'selector': f"//*[contains(text(), '{hint}')]",
                    'type': 'xpath',
                    'score': 0.6
                })
            
            # Eğitilmiş örneklerden tahminler
            for case in self.model_data.get('trained_cases', []):
                predictions.append({
                    'selector': case.get('selector', ''),
                    'type': case.get('selector_type', 'css'),
                    'score': 0.75
                })
            
            # Skorlara göre sırala
            predictions.sort(key=lambda x: x.get('score', 0), reverse=True)
            
            # En iyi 10 tahmini döndür
            return predictions[:10]
            
        except Exception as e:
            logger.error(f"Tahmin sırasında hata oluştu: {e}")
            return []

    def train(self, locator_id, html_content, successful_selector, selector_type):
        """
        Başarılı locator durumlarından model eğitir.
        
        Bu metot, başarılı olan locator'ları kaydederek gelecekteki 
        tahminlerin daha doğru olmasını sağlar.
        
        Args:
            locator_id (str): Locator benzersiz tanımlayıcısı
            html_content (str): HTML içeriği
            successful_selector (str): Başarılı seçici
            selector_type (str): Seçici türü (css, xpath, text, vb.)
            
        Returns:
            bool: Eğitim başarılıysa True
        """
        try:
            logger.info(f"'{locator_id}' için model eğitiliyor")
            
            # Yeni örneği oluştur
            new_case = {
                'locator_id': locator_id,
                'selector': successful_selector,
                'selector_type': selector_type,
                'timestamp': time.time()
            }
            
            # Eğitim verilerine ekle
            self.model_data['trained_cases'].append(new_case)
            
            # Model verisini kaydet
            with open(MODEL_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.model_data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Model verisi kaydedildi: {MODEL_DATA_FILE}")
            
            return True
        except Exception as e:
            logger.error(f"Eğitim sırasında hata: {e}")
            return False 