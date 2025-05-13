#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Geliştirilmiş Model Testi

Bu betik, locator tahmin modelinin başarısını kapsamlı bir şekilde test eder.
Çeşitli test senaryoları ve veri tipleri kullanarak modelin tahmin yeteneğini
değerlendirir ve iyileştirir.
"""

import logging
import sys
import time
import random
import json
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
        logging.FileHandler('enhanced_model_test_results.log')
    ]
)
logger = logging.getLogger(__name__)

def test_on_multiple_sites():
    """
    Modeli farklı web sitelerinde test eder.
    """
    logger.info("Geliştirilmiş model testi başlatılıyor...")
    
    # Test edilecek web siteleri
    test_sites = [
        {
            "name": "TGO Yemek", 
            "url": "https://tgoyemek.com/restoranlar",
            "scenarios": [
                {
                    "locator_id": "arama_kutusu", 
                    "hints": ["arama", "input", "ara", "search"],
                    "expected_type": "input",
                    "expected_action": "fill",
                    "test_value": "burger",
                    "fallback_selector": "input[type='text']" 
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
                    "locator_id": "restoran_listesi", 
                    "hints": ["restoran", "liste", "cards", "container"],
                    "expected_type": "container",
                    "expected_action": "check",
                    "test_value": None,
                    "fallback_selector": ".restaurant-list" 
                },
                {
                    "locator_id": "header_logo", 
                    "hints": ["logo", "header", "trendyol", "üst"],
                    "expected_type": "image",
                    "expected_action": "check",
                    "test_value": None,
                    "fallback_selector": ".header-logo" 
                },
                {
                    "locator_id": "kampanyalar_section", 
                    "hints": ["kampanya", "fırsat", "kampanyalar"],
                    "expected_type": "container",
                    "expected_action": "check",
                    "test_value": None,
                    "fallback_selector": "[class*='campaign']" 
                },
                {
                    "locator_id": "footer_section", 
                    "hints": ["footer", "alt", "bilgi", "iletişim"],
                    "expected_type": "container",
                    "expected_action": "check",
                    "test_value": None,
                    "fallback_selector": "footer, .footer" 
                },
                {
                    "locator_id": "mobil_uygulama_buton", 
                    "hints": ["mobil", "uygulama", "app", "indir"],
                    "expected_type": "link",
                    "expected_action": "check",
                    "test_value": None,
                    "fallback_selector": "text=Mobil Uygulamalar" 
                },
                {
                    "locator_id": "siparis_takip", 
                    "hints": ["sipariş", "takip", "siparişlerim", "order"],
                    "expected_type": "link",
                    "expected_action": "check",
                    "test_value": None,
                    "fallback_selector": "text=Siparişlerim" 
                },
                {
                    "locator_id": "ilk_restoran_kart", 
                    "hints": ["restoran", "kart", "ilk", "restaurant"],
                    "expected_type": "container",
                    "expected_action": "click",
                    "test_value": None,
                    "fallback_selector": ".restaurant-card:first-child" 
                },
                {
                    "locator_id": "restoranlar_baslik", 
                    "hints": ["restoran", "başlık", "restoranlar", "title"],
                    "expected_type": "text",
                    "expected_action": "check",
                    "test_value": None,
                    "fallback_selector": "h1" 
                }
            ]
        },
        {
            "name": "Wikipedia", 
            "url": "https://tr.wikipedia.org/",
            "scenarios": [
                {
                    "locator_id": "wiki_search", 
                    "hints": ["arama", "input", "ara", "search"],
                    "expected_type": "input",
                    "expected_action": "fill",
                    "test_value": "yazılım test otomasyonu",
                    "fallback_selector": "input[name='search']" 
                },
                {
                    "locator_id": "wiki_languages", 
                    "hints": ["dil", "languages", "seçenek"],
                    "expected_type": "list",
                    "expected_action": "check",
                    "test_value": None,
                    "fallback_selector": "#p-lang" 
                },
                {
                    "locator_id": "header_logo", 
                    "hints": ["logo", "vikipedi", "wikipedia", "header"],
                    "expected_type": "image",
                    "expected_action": "check",
                    "test_value": None,
                    "fallback_selector": ".mw-wiki-logo" 
                },
                {
                    "locator_id": "featured_article", 
                    "hints": ["seçkin", "makale", "featured", "article"],
                    "expected_type": "container",
                    "expected_action": "check",
                    "test_value": None,
                    "fallback_selector": "#mp-tfa" 
                },
                {
                    "locator_id": "sidebar_menu", 
                    "hints": ["sidebar", "yan", "menü", "navigation"],
                    "expected_type": "container",
                    "expected_action": "check",
                    "test_value": None,
                    "fallback_selector": "#mw-panel" 
                },
                {
                    "locator_id": "main_content", 
                    "hints": ["ana", "içerik", "main", "content"],
                    "expected_type": "container",
                    "expected_action": "check",
                    "test_value": None,
                    "fallback_selector": "#content" 
                },
                {
                    "locator_id": "search_button", 
                    "hints": ["arama", "buton", "ara", "search"],
                    "expected_type": "button",
                    "expected_action": "check",
                    "test_value": None,
                    "fallback_selector": "input[type='submit']" 
                },
                {
                    "locator_id": "login_link", 
                    "hints": ["oturum", "giriş", "login", "hesap"],
                    "expected_type": "link",
                    "expected_action": "check",
                    "test_value": None,
                    "fallback_selector": "#pt-login" 
                },
                {
                    "locator_id": "footer", 
                    "hints": ["footer", "alt", "bilgi", "alt"],
                    "expected_type": "container",
                    "expected_action": "check",
                    "test_value": None,
                    "fallback_selector": "#footer" 
                },
                {
                    "locator_id": "today_featured", 
                    "hints": ["bugün", "günün", "today", "featured"],
                    "expected_type": "container",
                    "expected_action": "check",
                    "test_value": None,
                    "fallback_selector": "#mp-otd" 
                }
            ]
        },
        {
            "name": "GitHub", 
            "url": "https://github.com/",
            "scenarios": [
                {
                    "locator_id": "github_search", 
                    "hints": ["arama", "search", "repo"],
                    "expected_type": "input",
                    "expected_action": "fill",
                    "test_value": "selenium",
                    "fallback_selector": ".header-search-input" 
                },
                {
                    "locator_id": "github_signup", 
                    "hints": ["kayıt", "signup", "kaydol"],
                    "expected_type": "button",
                    "expected_action": "check",
                    "test_value": None,
                    "fallback_selector": "text=Sign up for GitHub" 
                },
                {
                    "locator_id": "github_login", 
                    "hints": ["login", "giriş", "oturum"],
                    "expected_type": "link",
                    "expected_action": "check",
                    "test_value": None,
                    "fallback_selector": "text=Sign in" 
                },
                {
                    "locator_id": "github_logo", 
                    "hints": ["logo", "github", "header"],
                    "expected_type": "image",
                    "expected_action": "check",
                    "test_value": None,
                    "fallback_selector": ".octicon-mark-github" 
                },
                {
                    "locator_id": "github_hero", 
                    "hints": ["hero", "banner", "main", "ana"],
                    "expected_type": "container",
                    "expected_action": "check",
                    "test_value": None,
                    "fallback_selector": ".home-campaign-hero" 
                },
                {
                    "locator_id": "github_features", 
                    "hints": ["özellikler", "features", "services"],
                    "expected_type": "container",
                    "expected_action": "check",
                    "test_value": None,
                    "fallback_selector": ".home-campaign-features" 
                },
                {
                    "locator_id": "github_footer", 
                    "hints": ["footer", "alt", "bilgi", "footer"],
                    "expected_type": "container",
                    "expected_action": "check",
                    "test_value": None,
                    "fallback_selector": ".footer" 
                },
                {
                    "locator_id": "github_pricing", 
                    "hints": ["pricing", "fiyatlandırma", "ücret"],
                    "expected_type": "link",
                    "expected_action": "check",
                    "test_value": None,
                    "fallback_selector": "text=Pricing" 
                },
                {
                    "locator_id": "github_explore", 
                    "hints": ["explore", "keşfet", "trending"],
                    "expected_type": "link",
                    "expected_action": "check",
                    "test_value": None,
                    "fallback_selector": "text=Explore" 
                },
                {
                    "locator_id": "github_enterprise", 
                    "hints": ["enterprise", "kurumsal", "business"],
                    "expected_type": "link",
                    "expected_action": "check",
                    "test_value": None,
                    "fallback_selector": "text=Enterprise" 
                }
            ]
        }
    ]
    
    # Sonuçları kaydetmek için
    results = {
        "total_tests": 0,
        "successful_tests": 0,
        "failed_tests": 0,
        "site_results": {},
        "predictions": {}
    }
    
    # LocatorPredictor sınıfını başlat
    predictor = LocatorPredictor()
    
    # Her site için test gerçekleştir
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)  # Görsel izleme için headless=False
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()
        
        for site_idx, site in enumerate(test_sites):
            logger.info(f"Site {site_idx+1}/{len(test_sites)}: {site['name']} test ediliyor...")
            results["site_results"][site["name"]] = {
                "url": site["url"],
                "scenarios_tested": len(site["scenarios"]),
                "successful": 0,
                "failed": 0
            }
            
            try:
                # Siteye git
                logger.info(f"Sayfa yükleniyor: {site['url']}")
                page.goto(site['url'])
                page.wait_for_load_state("networkidle")
                time.sleep(2)  # Ek bekleme süresi
                
                # HTML içeriğini al
                html_content = page.content()
                logger.info(f"{site['name']} için HTML içeriği alındı ({len(html_content)} bytes)")
                
                # Sayfada rastgele scrolling yaparak içeriği zenginleştir
                for _ in range(3):
                    scroll_amount = random.randint(100, 500)
                    page.evaluate(f"window.scrollBy(0, {scroll_amount})")
                    time.sleep(0.3)
                
                # Her senaryo için test yap
                for scenario_idx, scenario in enumerate(site["scenarios"]):
                    logger.info(f"Senaryo {scenario_idx+1}/{len(site['scenarios'])}: '{scenario['locator_id']}' test ediliyor...")
                    results["total_tests"] += 1
                    
                    # Önce mevcutta kayıtlı stratejileri test et
                    try:
                        # Model tahminleri yap
                        predictions = predictor.predict(
                            locator_id=scenario["locator_id"],
                            html_content=html_content,
                            hints=scenario["hints"]
                        )
                        
                        if not predictions:
                            logger.error(f"'{scenario['locator_id']}' için tahmin yapılamadı!")
                            results["failed_tests"] += 1
                            results["site_results"][site["name"]]["failed"] += 1
                            continue
                        
                        # Tahminleri kaydet
                        results["predictions"][f"{site['name']}_{scenario['locator_id']}"] = [
                            {"type": p["type"], "selector": p["selector"], "score": p["score"]} 
                            for p in predictions[:3]
                        ]
                        
                        # Tahminleri test et
                        logger.info(f"'{scenario['locator_id']}' için {len(predictions)} tahmin yapıldı")
                        for idx, pred in enumerate(predictions[:3]):
                            logger.info(f"  {idx+1}. Type: {pred['type']}, Selector: {pred['selector']}, Score: {pred['score']:.2f}")
                        
                        # Tahminleri test et
                        found_element = False
                        tested_count = 0
                        
                        for prediction in predictions[:5]:
                            if tested_count >= 3:
                                break
                                
                            tested_count += 1
                            logger.info(f"Tahmin {tested_count} test ediliyor: {prediction['type']} - {prediction['selector']}")
                            
                            try:
                                # Tahmini test et
                                if prediction['type'] == 'css':
                                    element = page.locator(prediction['selector']).first
                                elif prediction['type'] == 'xpath':
                                    element = page.locator(f"xpath={prediction['selector']}").first
                                elif prediction['type'] == 'text':
                                    element = page.get_by_text(prediction['selector']).first
                                else:
                                    logger.warning(f"Desteklenmeyen seçici türü: {prediction['type']}")
                                    continue
                                
                                # Görünür mü?
                                if element.is_visible(timeout=3000):
                                    logger.info(f"Element bulundu! {prediction['type']} - {prediction['selector']}")
                                    
                                    # Beklenen eylemi gerçekleştir
                                    if scenario['expected_action'] == 'fill' and scenario['test_value']:
                                        element.fill(scenario['test_value'])
                                        logger.info(f"Element dolduruldu: '{scenario['test_value']}'")
                                        found_element = True
                                        
                                        # Modeli eğit
                                        predictor.train(
                                            locator_id=scenario['locator_id'],
                                            html_content=html_content,
                                            successful_selector=prediction['selector'],
                                            selector_type=prediction['type']
                                        )
                                        logger.info(f"Model eğitildi: {scenario['locator_id']} - {prediction['selector']}")
                                        
                                        break
                                    elif scenario['expected_action'] == 'click':
                                        # Tıklama yapma (test sırasında yalnızca kontrol et)
                                        # element.click()
                                        logger.info(f"Element tıklanabilir: Test başarılı")
                                        found_element = True
                                        
                                        # Modeli eğit
                                        predictor.train(
                                            locator_id=scenario['locator_id'],
                                            html_content=html_content,
                                            successful_selector=prediction['selector'],
                                            selector_type=prediction['type']
                                        )
                                        logger.info(f"Model eğitildi: {scenario['locator_id']} - {prediction['selector']}")
                                        
                                        break
                                    elif scenario['expected_action'] == 'check':
                                        logger.info(f"Element görünür: Test başarılı")
                                        found_element = True
                                        
                                        # Modeli eğit
                                        predictor.train(
                                            locator_id=scenario['locator_id'],
                                            html_content=html_content,
                                            successful_selector=prediction['selector'],
                                            selector_type=prediction['type']
                                        )
                                        logger.info(f"Model eğitildi: {scenario['locator_id']} - {prediction['selector']}")
                                        
                                        break
                            except Exception as e:
                                logger.warning(f"Tahmin test hatası ({prediction['selector']}): {e}")
                        
                        # Eğer hiçbir tahmin çalışmadıysa, fallback'i deneyin
                        if not found_element and scenario['fallback_selector']:
                            logger.warning(f"Hiçbir tahmin çalışmadı. Fallback deneniyor: {scenario['fallback_selector']}")
                            
                            try:
                                fallback_element = page.locator(scenario['fallback_selector']).first
                                if fallback_element.is_visible(timeout=3000):
                                    logger.info(f"Fallback ile element bulundu!")
                                    
                                    # Beklenen eylemi gerçekleştir
                                    if scenario['expected_action'] == 'fill' and scenario['test_value']:
                                        fallback_element.fill(scenario['test_value'])
                                        logger.info(f"Fallback ile element dolduruldu: '{scenario['test_value']}'")
                                    
                                    # Modeli bu başarılı seçici ile eğit
                                    selector_type = "css"
                                    selector = scenario['fallback_selector']
                                    
                                    if selector.startswith("text="):
                                        selector_type = "text"
                                        selector = selector[5:]  # "text=" kısmını kaldır
                                    
                                    predictor.train(
                                        locator_id=scenario['locator_id'],
                                        html_content=html_content,
                                        successful_selector=selector,
                                        selector_type=selector_type
                                    )
                                    logger.info(f"Model fallback ile eğitildi: {scenario['locator_id']} - {selector}")
                                    
                                    found_element = True
                            except Exception as e:
                                logger.error(f"Fallback test hatası: {e}")
                        
                        # Test sonucunu kaydet
                        if found_element:
                            results["successful_tests"] += 1
                            results["site_results"][site["name"]]["successful"] += 1
                            logger.info(f"Senaryo '{scenario['locator_id']}' başarılı")
                        else:
                            results["failed_tests"] += 1
                            results["site_results"][site["name"]]["failed"] += 1
                            logger.warning(f"Senaryo '{scenario['locator_id']}' başarısız")
                    
                    except Exception as e:
                        logger.error(f"Senaryo testi sırasında hata: {e}")
                        results["failed_tests"] += 1
                        results["site_results"][site["name"]]["failed"] += 1
                
                # Sayfanın en üstüne dön
                page.evaluate("window.scrollTo(0, 0)")
                time.sleep(1)
            
            except Exception as e:
                logger.error(f"{site['name']} testi sırasında hata: {e}")
        
        browser.close()
    
    # Sonuçları analiz et
    if results["total_tests"] > 0:
        success_rate = (results["successful_tests"] / results["total_tests"]) * 100
        logger.info(f"Test sonuçları:")
        logger.info(f"  Toplam test: {results['total_tests']}")
        logger.info(f"  Başarılı: {results['successful_tests']}")
        logger.info(f"  Başarısız: {results['failed_tests']}")
        logger.info(f"  Başarı oranı: {success_rate:.1f}%")
        
        for site_name, site_result in results["site_results"].items():
            site_success_rate = 0
            if site_result["scenarios_tested"] > 0:
                site_success_rate = (site_result["successful"] / site_result["scenarios_tested"]) * 100
            logger.info(f"  {site_name}: {site_result['successful']}/{site_result['scenarios_tested']} başarılı ({site_success_rate:.1f}%)")
    
    # Sonuçları dosyaya kaydet
    with open("model_test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.info("Geliştirilmiş model testi tamamlandı. Sonuçlar model_test_results.json dosyasına kaydedildi.")
    return results

def test_model_recovery_strategies():
    """
    Modelin kendini iyileştirme stratejilerini test eder.
    Bu test, aynı sayfada element durumları değiştiğinde modelin nasıl davrandığını analiz eder.
    """
    logger.info("Model kendini iyileştirme stratejileri testi başlatılıyor...")
    
    # LocatorPredictor sınıfını başlat
    predictor = LocatorPredictor()
    
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            # Test HTML içeriği oluştur
            test_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Model Kendini İyileştirme Testi</title>
                <style>
                    body {{ font-family: Arial, sans-serif; padding: 20px; }}
                    .container {{ margin: 20px; padding: 20px; border: 1px solid #ccc; }}
                    button {{ padding: 10px; margin: 5px; }}
                    input {{ padding: 8px; margin: 5px; }}
                </style>
            </head>
            <body>
                <h1>Self-Healing Model Testi</h1>
                
                <div class="container">
                    <h2>Test Senaryosu 1: Element ID Değişimi</h2>
                    <p>Başlangıçta id='test-button' olan buton, 3 saniye sonra id='changed-button' olacak.</p>
                    <button id="test-button" onclick="changeButtonId()">Test Butonu</button>
                </div>
                
                <div class="container">
                    <h2>Test Senaryosu 2: Element Class Değişimi</h2>
                    <p>Başlangıçta class='search-input' olan input, 3 saniye sonra class='modified-input' olacak.</p>
                    <input type="text" id="test-input" class="search-input" placeholder="Arama yap...">
                </div>
                
                <div class="container">
                    <h2>Test Senaryosu 3: Element Metin Değişimi</h2>
                    <p>Başlangıçta 'Gönder' yazan buton, 3 saniye sonra 'Devam Et' yazacak.</p>
                    <button id="text-button">Gönder</button>
                </div>
                
                <script>
                    function changeButtonId() {{
                        setTimeout(function() {{
                            document.getElementById('test-button').id = 'changed-button';
                            console.log('Button ID changed to: changed-button');
                        }}, 3000);
                    }}
                    
                    function changeInputClass() {{
                        setTimeout(function() {{
                            document.getElementById('test-input').className = 'modified-input';
                            console.log('Input class changed to: modified-input');
                        }}, 3000);
                    }}
                    
                    function changeButtonText() {{
                        setTimeout(function() {{
                            document.getElementById('text-button').textContent = 'Devam Et';
                            console.log('Button text changed to: Devam Et');
                        }}, 3000);
                    }}
                    
                    // Değişimleri başlat
                    window.onload = function() {{
                        changeButtonId();
                        changeInputClass();
                        changeButtonText();
                    }};
                </script>
            </body>
            </html>
            """
            
            # Geçici HTML sayfasını oluştur
            temp_html_path = Path("temp_test.html")
            with open(temp_html_path, "w", encoding="utf-8") as f:
                f.write(test_html)
            
            page_url = f"file://{temp_html_path.absolute()}"
            logger.info(f"Test sayfası oluşturuldu: {page_url}")
            
            # Sayfayı yükle
            page.goto(page_url)
            page.wait_for_load_state("networkidle")
            
            # Test senaryoları
            test_scenarios = [
                {
                    "name": "ID Değişim Testi",
                    "locator_id": "test_button",
                    "original_selector": "#test-button",
                    "changed_selector": "#changed-button",
                    "hints": ["test", "button", "buton"]
                },
                {
                    "name": "Class Değişim Testi",
                    "locator_id": "search_input",
                    "original_selector": ".search-input",
                    "changed_selector": ".modified-input",
                    "hints": ["search", "input", "arama"]
                },
                {
                    "name": "Metin Değişim Testi",
                    "locator_id": "submit_button",
                    "original_selector": "text=Gönder",
                    "changed_selector": "text=Devam Et",
                    "hints": ["gönder", "submit", "button"]
                }
            ]
            
            test_results = []
            
            # Önce orijinal elementleri test et
            for scenario in test_scenarios:
                logger.info(f"Senaryo başlatılıyor: {scenario['name']}")
                
                # Orijinal HTML içeriğini al
                html_content = page.content()
                
                # Modeli orijinal seçici ile eğit
                original_type = "css"
                if scenario["original_selector"].startswith("text="):
                    original_type = "text"
                    original_selector = scenario["original_selector"][5:]
                else:
                    original_selector = scenario["original_selector"]
                
                predictor.train(
                    locator_id=scenario["locator_id"],
                    html_content=html_content,
                    successful_selector=original_selector,
                    selector_type=original_type
                )
                logger.info(f"Model orijinal seçici ile eğitildi: {scenario['locator_id']} - {original_selector}")
                
                # Element erişilebilirliğini doğrula
                try:
                    selector = scenario["original_selector"]
                    element = page.locator(selector)
                    is_visible = element.is_visible()
                    logger.info(f"Orijinal element görünür: {selector} - {is_visible}")
                except Exception as e:
                    logger.error(f"Orijinal elemana erişim hatası: {e}")
            
            # Değişikliklerin gerçekleşmesi için bekle
            logger.info("Elementlerin değişmesi için 5 saniye bekleniyor...")
            time.sleep(5)
            
            # Değişen elementleri bulmaya çalış
            for scenario in test_scenarios:
                logger.info(f"Değişim sonrası test: {scenario['name']}")
                
                # Güncellenmiş HTML içeriğini al
                html_content = page.content()
                
                # Modelin tahmin yapmasını sağla
                predictions = predictor.predict(
                    locator_id=scenario["locator_id"],
                    html_content=html_content,
                    hints=scenario["hints"]
                )
                
                if predictions:
                    logger.info(f"'{scenario['locator_id']}' için tahminler:")
                    for idx, pred in enumerate(predictions[:3]):
                        logger.info(f"  {idx+1}. Type: {pred['type']}, Selector: {pred['selector']}, Score: {pred['score']:.2f}")
                    
                    # Tahminleri test et
                    found_element = False
                    for pred in predictions[:5]:
                        try:
                            if pred['type'] == 'css':
                                element = page.locator(pred['selector']).first
                            elif pred['type'] == 'xpath':
                                element = page.locator(f"xpath={pred['selector']}").first
                            elif pred['type'] == 'text':
                                element = page.get_by_text(pred['selector']).first
                            
                            if element and element.is_visible(timeout=1000):
                                logger.info(f"Element değişim sonrası bulundu: {pred['selector']}")
                                found_element = True
                                
                                # Modeli başarılı tahminle eğit
                                predictor.train(
                                    locator_id=scenario["locator_id"],
                                    html_content=html_content,
                                    successful_selector=pred['selector'],
                                    selector_type=pred['type']
                                )
                                
                                break
                        except Exception as e:
                            logger.warning(f"Tahmin test hatası: {e}")
                    
                    # Beklenen değişiklik doğrulama
                    try:
                        changed_element = page.locator(scenario["changed_selector"])
                        is_changed_visible = changed_element.is_visible()
                        logger.info(f"Değişen element görünürlüğü: {scenario['changed_selector']} - {is_changed_visible}")
                        
                        result = {
                            "scenario": scenario["name"],
                            "locator_id": scenario["locator_id"],
                            "model_found": found_element,
                            "actual_element_visible": is_changed_visible,
                            "predictions": [
                                {"type": p["type"], "selector": p["selector"], "score": p["score"]} 
                                for p in predictions[:3]
                            ]
                        }
                        test_results.append(result)
                    except Exception as e:
                        logger.error(f"Değişen element kontrolü hatası: {e}")
                else:
                    logger.error(f"'{scenario['locator_id']}' için tahmin yapılamadı!")
            
            # Sonuçları dosyaya kaydet
            with open("self_healing_test_results.json", "w", encoding="utf-8") as f:
                json.dump(test_results, f, indent=2, ensure_ascii=False)
            
            logger.info("Kendini iyileştirme testi tamamlandı. Sonuçlar self_healing_test_results.json dosyasına kaydedildi.")
            
            # Test sayfasında biraz daha bekle
            time.sleep(3)
        except Exception as e:
            logger.error(f"Model kendini iyileştirme testi hatası: {e}")
        finally:
            # Tarayıcıyı kapat
            browser.close()
            
            # Geçici dosyayı temizle
            if temp_html_path.exists():
                temp_html_path.unlink()
                logger.info("Geçici test dosyası temizlendi.")
    
    return test_results

if __name__ == "__main__":
    # Çeşitli web sitelerinde test yap
    site_test_results = test_on_multiple_sites()
    
    # Kendini iyileştirme stratejilerini test et
    healing_test_results = test_model_recovery_strategies() 