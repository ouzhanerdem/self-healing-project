#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Model Testi

Bu betik, locator tahmin modelinin başarısını test eder.
Test senaryoları oluşturarak modelin tahmin ve self-healing
yeteneklerini analiz eder.
"""

import logging
import sys
import time
from pathlib import Path

# Proje kök dizinini sys.path'e ekle
sys.path.append(str(Path(__file__).resolve().parent.parent))

from playwright.sync_api import sync_playwright
from resources.locator_predict_model import LocatorPredictor

# Loglama konfigürasyonu
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('model_test_results.log')
    ]
)
logger = logging.getLogger(__name__)

def test_model_with_known_elements():
    """
    Bilinen elementlerle modeli test eder.
    """
    logger.info("Model test süreci başlatılıyor...")
    
    # Temel URL
    base_url = "https://tgoyemek.com/restoranlar"
    
    # LocatorPredictor sınıfını başlat
    predictor = LocatorPredictor()
    
    # Playwright ile sayfayı aç ve elementleri test et
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)  # Görsel izleme için headless=False
        context = browser.new_context()
        page = context.new_page()
        
        try:
            # Ana sayfaya git
            logger.info(f"Sayfa yükleniyor: {base_url}")
            page.goto(base_url)
            page.wait_for_load_state("networkidle")
            
            # HTML içeriğini al
            html_content = page.content()
            logger.info("HTML içeriği alındı")
            
            # Test edilecek element senaryoları - Gerçek sayfa element yapısına göre uyarlandı
            test_scenarios = [
                {
                    "locator_id": "arama_kutusu", 
                    "hints": ["arama", "input", "ara", "search"],
                    "expected_type": "input",
                    "expected_action": "fill",
                    "test_value": "burger",
                    "fallback_selector": "input[type='text']"  # Eğer tahmin edilemeyen bir durum varsa
                },
                {
                    "locator_id": "filtre_butonu", 
                    "hints": ["filtre", "button", "sırala", "filtrele"],
                    "expected_type": "button",
                    "expected_action": "click",
                    "test_value": None,
                    "fallback_selector": "text=Filtrele ve Sırala" 
                },
                {
                    "locator_id": "restoran_kartlari", 
                    "hints": ["restoran", "kart", "restaurant", "card"],
                    "expected_type": "container",
                    "expected_action": "check",
                    "test_value": None,
                    "fallback_selector": "[class*='restaurant'], [class*='card']"
                }
            ]
            
            # Her senaryo için model tahmin testi
            successful_tests = 0
            failed_tests = 0
            
            for i, scenario in enumerate(test_scenarios):
                logger.info(f"Senaryo {i+1}/{len(test_scenarios)}: '{scenario['locator_id']}' için model test ediliyor...")
                
                # Modele tahmin yaptır
                predictions = predictor.predict(
                    locator_id=scenario["locator_id"],
                    html_content=html_content,
                    hints=scenario["hints"]
                )
                
                if not predictions:
                    logger.error(f"'{scenario['locator_id']}' için tahmin yapılamadı!")
                    failed_tests += 1
                    continue
                
                # En yüksek skorlu ilk 3 tahmini logla
                logger.info(f"Top 3 predictions for '{scenario['locator_id']}':")
                for idx, pred in enumerate(predictions[:3]):
                    logger.info(f"  {idx+1}. Type: {pred['type']}, Selector: {pred['selector']}, Score: {pred['score']:.2f}")
                
                # Her bir tahmini test et - birkaç tahmin işe yaramazsa diğerlerini dene
                found_element = False
                tested_count = 0
                
                for prediction in predictions[:5]:  # İlk 5 tahmini dene
                    if tested_count >= 3:  # En fazla 3 tahmini test et
                        break
                        
                    tested_count += 1
                    logger.info(f"Tahmin {tested_count} test ediliyor: Type: {prediction['type']}, Selector: {prediction['selector']}")
                    
                    try:
                        # Tahmin edilen seçiciye göre elementi bul
                        if prediction['type'] == 'css':
                            element = page.locator(prediction['selector']).first
                        elif prediction['type'] == 'xpath':
                            element = page.locator(f"xpath={prediction['selector']}").first
                        elif prediction['type'] == 'text':
                            element = page.get_by_text(prediction['selector']).first
                        else:
                            logger.warning(f"Desteklenmeyen seçici türü: {prediction['type']}")
                            continue
                        
                        # Element bulundu mu kontrol et (timeout 2 saniye)
                        if element.is_visible(timeout=2000):
                            logger.info(f"Element başarıyla bulundu: '{scenario['locator_id']}' - Tahmin {tested_count}")
                            
                            # Beklenen eylem tipine göre testi gerçekleştir
                            if scenario['expected_action'] == 'fill' and scenario['test_value']:
                                element.fill(scenario['test_value'])
                                logger.info(f"Element dolduruldu: '{scenario['test_value']}'")
                                page.keyboard.press("Escape")  # Olası açılır öneriyi kapat
                            elif scenario['expected_action'] == 'click':
                                element.click()
                                logger.info(f"Elemente tıklandı")
                                time.sleep(1)  # Sayfa tepkisini bekle
                            elif scenario['expected_action'] == 'check':
                                logger.info(f"Element kontrol edildi, görünür")
                            
                            successful_tests += 1
                            found_element = True
                            break
                        
                    except Exception as e:
                        logger.warning(f"Tahmin {tested_count} testi sırasında hata: {e}")
                
                # Eğer hiçbir tahmin işe yaramadıysa, fallback seçici kullan
                if not found_element:
                    logger.warning(f"Hiçbir tahmin işe yaramadı, fallback seçici deneniyor: {scenario['fallback_selector']}")
                    try:
                        fallback_element = page.locator(scenario['fallback_selector']).first
                        if fallback_element.is_visible(timeout=2000):
                            logger.info(f"Fallback seçici ile element bulundu: '{scenario['locator_id']}'")
                            
                            # Model eğitimi - başarılı stratejinin öğrenilmesi
                            logger.info(f"Başarılı strateji ile model eğitiliyor: {scenario['fallback_selector']}")
                            successful_type = "css"
                            if scenario['fallback_selector'].startswith("text="):
                                successful_type = "text"
                                scenario['fallback_selector'] = scenario['fallback_selector'][5:]  # "text=" kısmını kaldır
                                
                            predictor.train(
                                locator_id=scenario['locator_id'],
                                html_content=html_content,
                                successful_selector=scenario['fallback_selector'],
                                selector_type=successful_type
                            )
                            
                            # İşlemi gerçekleştir
                            if scenario['expected_action'] == 'fill' and scenario['test_value']:
                                fallback_element.fill(scenario['test_value'])
                                logger.info(f"Fallback ile element dolduruldu: '{scenario['test_value']}'")
                                page.keyboard.press("Escape")  # Olası açılır öneriyi kapat
                            elif scenario['expected_action'] == 'click':
                                fallback_element.click()
                                logger.info(f"Fallback ile elemente tıklandı")
                                time.sleep(1)
                            elif scenario['expected_action'] == 'check':
                                logger.info(f"Fallback ile element kontrol edildi, görünür")
                                
                            successful_tests += 1
                        else:
                            logger.error(f"Fallback seçici ile de element bulunamadı: '{scenario['locator_id']}'")
                            failed_tests += 1
                    except Exception as e:
                        logger.error(f"Fallback seçici testi sırasında hata: {e}")
                        failed_tests += 1
                
                # Testler arasında biraz bekle
                time.sleep(1)
                
                # Sayfayı yenile (eğer tıklama yapıldıysa)
                if scenario['expected_action'] == 'click':
                    logger.info("Sayfa yeniden yükleniyor...")
                    page.goto(base_url)
                    page.wait_for_load_state("networkidle")
                    html_content = page.content()  # HTML içeriğini güncelle
            
            # Sonuçları özetle
            logger.info(f"Test sonuçları: {successful_tests} başarılı, {failed_tests} başarısız")
            logger.info(f"Başarı oranı: {successful_tests / len(test_scenarios) * 100:.1f}%")
            
            # Özel test: Eğitilmiş modelle bir tahmin yap
            if successful_tests > 0:
                logger.info("Eğitilmiş model testi...")
                trained_predictions = predictor.predict(
                    locator_id="yeni_arama_kutusu",
                    html_content=html_content,
                    hints=["ara", "search"]
                )
                
                logger.info(f"Eğitilmiş model tahminleri:")
                for idx, pred in enumerate(trained_predictions[:3]):
                    logger.info(f"  {idx+1}. Type: {pred['type']}, Selector: {pred['selector']}, Score: {pred['score']:.2f}")
        
        except Exception as e:
            logger.error(f"Test sırasında hata oluştu: {e}")
        finally:
            # Son durumu 3 saniye göster ve kapat
            time.sleep(3)
            browser.close()
    
    logger.info("Model test süreci tamamlandı.")

if __name__ == "__main__":
    test_model_with_known_elements() 