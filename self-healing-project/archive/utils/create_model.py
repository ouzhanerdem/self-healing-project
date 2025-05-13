#!/usr/bin/env python3
"""
Self-Healing Test Modeli Oluşturma Aracı

Bu script, self-healing test mekanizması için gerekli model verisini oluşturur.
Web sayfasından HTML içeriği alarak, lokatorlar için eğitim verisi oluşturur ve
`model_data.json` dosyasına kaydeder.

Kullanım:
    python utils/create_model.py

Ayarlar:
    Web sayfası URL'si için .env dosyasındaki URL değişkeni kullanılır veya
    varsayılan değer olarak 'https://tgoyemek.com/restoranlar' kullanılır.
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from dotenv import load_dotenv

# utils modülünün yolunu ekleyelim
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))

# model_creator modülünü içe aktaralım
from utils.model_creator import (
    load_predictor,
    train_model,
    verify_model_data,
    get_html_content,
    create_sample_html,
    get_default_locators
)

# ------------------------------------------------------------------------------
# Script Yapılandırması
# ------------------------------------------------------------------------------

def setup_logging(log_level):
    """Loglama konfigürasyonunu ayarlar."""
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("model_creator.log", mode="w")
        ]
    )
    return logging.getLogger(__name__)

def parse_arguments():
    """Komut satırı argümanlarını ayrıştırır."""
    parser = argparse.ArgumentParser(description="Self-Healing Test Modeli Oluşturma Aracı")
    parser.add_argument("--url", type=str, help="HTML içeriği çekilecek URL")
    parser.add_argument("--model-dir", type=str, default=str(project_root), 
                        help="Lokator tahmin modeli dosyasının bulunduğu dizin")
    parser.add_argument("--output", type=str, default="model_data.json",
                        help="Oluşturulacak model veri dosyasının adı")
    parser.add_argument("--predictor-file", type=str, default="resources/locator_predict_model.py",
                        help="Lokator tahmin modeli dosyasının adı")
    parser.add_argument("--verbose", action="store_true", help="Daha fazla loglama")
    parser.add_argument("--user-agent", type=str, help="Kullanıcı aracı")
    parser.add_argument("--locator-file", type=str, help="Özel lokator dosyası")
    return parser.parse_args()

# ------------------------------------------------------------------------------
# Ana İşlevler
# ------------------------------------------------------------------------------

def get_url_from_env():
    """Environment değişkenlerinden URL değerini alır."""
    # .env dosyasını yükle
    load_dotenv()
    return os.getenv("TEST_URL", "https://tgoyemek.com/restoranlar")

def save_model_data(model_data, output_file):
    """Model verisini JSON dosyasına kaydeder."""
    logger = logging.getLogger(__name__)
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(model_data, f, indent=2)
        logger.info(f"Model verisi kaydedildi: {output_file}")
        return True
    except Exception as e:
        logger.error(f"Model verisi kaydedilirken hata oluştu: {e}", exc_info=True)
        return False

def main():
    """
    Ana işlev.
    
    Komut satırı argümanlarını işler, modeli yükler, HTML içeriğini alır
    ve lokatorlar ile modeli eğitir.
    
    Returns:
        int: Çıkış kodu
    """
    args = parse_arguments()
    
    # Loglama düzeyini ayarlayalım
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)
    
    logger = logging.getLogger(__name__)
    logger.info("Self-Healing Test Modeli Oluşturma Aracı başlatılıyor...")
    
    # Hedef URL'yi belirleyelim
    target_url = args.url or "https://tgoyemek.com/restoranlar"
    logger.info(f"Hedef URL: {target_url}")
    
    # Model dosyası yolunu hazırlayalım
    project_root = get_project_root()
    model_file = project_root / "resources" / "locator_predict_model.py"
    
    # Tahmin modelini yükleyelim
    predictor = load_predictor(model_file)
    if not predictor:
        logger.error("Tahmin modeli yüklenemedi!")
        return 1
    
    # HTML içeriğini alalım
    html_content = get_html_content(target_url, args.user_agent, None)
    if not html_content:
        html_content = create_sample_html()
    
    # Varsayılan lokatörleri alalım
    locators = get_default_locators()
    
    # Custom lokator tanımlamaları için dosyayı kontrol et
    if args.locator_file and os.path.exists(args.locator_file):
        try:
            with open(args.locator_file, 'r', encoding='utf-8') as f:
                custom_locators = json.load(f)
                locators.extend([(loc['id'], loc['selector'], loc['type']) for loc in custom_locators])
                logger.info(f"{len(custom_locators)} özel lokator tanımı eklendi")
        except Exception as e:
            logger.error(f"Özel lokator dosyası yüklenirken hata: {e}")
    
    # Kaç adet lokator için eğitim yapılacağını gösterelim
    logger.info(f"{len(locators)} lokator eğitim için hazırlanıyor...")
    
    # Modeli eğitelim
    trained_count = train_model(predictor, html_content, locators)
    
    # Eğitim sonuçlarını değerlendirelim
    if trained_count > 0:
        # Model verisini kaydet
        model_data_file = args.output or "model_data.json"
        try:
            # _save_model_data metodunu kullanarak modeli kaydet
            if hasattr(predictor, '_save_model_data'):
                predictor._save_model_data()
                logger.info(f"Model verisi başarıyla kaydedildi: {model_data_file}")
            else:
                # Eğer _save_model_data metodu yoksa, model_data dosyasını manuel olarak kopyala
                model_data_src = predictor.model_data if hasattr(predictor, 'model_data') else None
                if model_data_src:
                    with open(model_data_file, 'w', encoding='utf-8') as f:
                        json.dump(model_data_src, f, indent=2, ensure_ascii=False)
                    logger.info(f"Model verisi manual olarak kaydedildi: {model_data_file}")
            
            # Model verisi doğrula
            verify_results = verify_model_data(Path(model_data_file))
            if verify_results.get('success'):
                logger.info(f"Model verisi doğrulandı: {trained_count} eğitim örneği, {verify_results.get('trained_cases')} toplam model örneği")
                return 0
            else:
                logger.warning(f"Model verisi kaydedildi ancak doğrulama başarısız olabilir: {verify_results.get('error')}")
                return 1
        except Exception as e:
            logger.error(f"Model verisi kaydedilirken hata: {e}")
            return 1
    else:
        logger.error("Hiçbir lokator için model eğitimi yapılamadı!")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 