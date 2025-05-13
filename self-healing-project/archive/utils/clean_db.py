"""
Veritabanı Temizleme ve Bakım Aracı

Bu araç, locator_db.json veritabanını temizler, optimize eder ve bakımını yapar.
Kullanılmayan, başarısız veya eski stratejileri kaldırır veya yeniden düzenler.
"""

import json
import logging
import argparse
import time
import os
from pathlib import Path
from datetime import datetime, timedelta

# Loglama yapılandırması
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def main():
    """Ana uygulama fonksiyonu."""
    parser = argparse.ArgumentParser(description="Locator veritabanı temizleme ve bakım aracı")
    parser.add_argument("--db-file", type=str, default="locator_db.json", help="Veritabanı dosyası yolu")
    parser.add_argument("--backup", action="store_true", help="İşlem öncesi yedek oluştur")
    parser.add_argument("--remove-stale", action="store_true", help="Kullanılmayan stratejileri kaldır")
    parser.add_argument("--days", type=int, default=30, help="Kaç günden eski stratejileri temizleyeceğini belirtir")
    parser.add_argument("--verify", action="store_true", help="Veritabanını doğrula, işlem yapma")
    parser.add_argument("--optimize", action="store_true", help="Veritabanını optimize et")
    
    args = parser.parse_args()
    
    db_path = Path(args.db_file)
    
    # Veritabanı dosyası var mı kontrol et
    if not db_path.exists():
        logger.error(f"Veritabanı dosyası bulunamadı: {db_path}")
        return 1
    
    # Veritabanını yükle
    try:
        with open(db_path, 'r', encoding='utf-8') as f:
            db = json.load(f)
        logger.info(f"Veritabanı başarıyla yüklendi: {len(db)} locator kaydı")
    except Exception as e:
        logger.error(f"Veritabanı yüklenirken hata oluştu: {e}")
        return 1
    
    # Yedekleme
    if args.backup:
        try:
            backup_path = db_path.with_suffix(f".backup.{int(time.time())}.json")
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(db, f, indent=2, ensure_ascii=False)
            logger.info(f"Veritabanı yedeklendi: {backup_path}")
        except Exception as e:
            logger.error(f"Yedekleme yapılırken hata oluştu: {e}")
            return 1
    
    # Doğrulama moduysa, sadece bilgi ver ve çık
    if args.verify:
        verify_db(db)
        return 0
    
    # Veritabanı temizliği
    if args.remove_stale:
        db = remove_stale_strategies(db, days=args.days)
    
    # Veritabanı optimizasyonu
    if args.optimize:
        db = optimize_db(db)
    
    # Değişiklikler yapıldıysa, kaydet
    if args.remove_stale or args.optimize:
        try:
            with open(db_path, 'w', encoding='utf-8') as f:
                json.dump(db, f, indent=2, ensure_ascii=False)
            logger.info(f"Veritabanı başarıyla güncellendi: {db_path}")
        except Exception as e:
            logger.error(f"Veritabanı kaydedilirken hata oluştu: {e}")
            return 1
    
    return 0

def verify_db(db):
    """
    Veritabanını doğrular ve analiz eder.
    
    Args:
        db (dict): Veritabanı sözlüğü
    """
    total_locators = len(db)
    total_strategies = 0
    empty_locators = []
    strategy_counts = {}
    last_used_by_days = {
        "1_gun": 0,
        "1_hafta": 0,
        "1_ay": 0,
        "3_ay": 0,
        "daha_eski": 0
    }
    
    now = time.time()
    one_day_ago = now - (60 * 60 * 24)
    one_week_ago = now - (60 * 60 * 24 * 7)
    one_month_ago = now - (60 * 60 * 24 * 30)
    three_months_ago = now - (60 * 60 * 24 * 90)
    
    for locator_id, data in db.items():
        strategies = data.get('strategies', [])
        num_strategies = len(strategies)
        total_strategies += num_strategies
        
        if num_strategies == 0:
            empty_locators.append(locator_id)
        
        for strategy in strategies:
            strategy_type = strategy.get('type', 'unknown')
            strategy_counts[strategy_type] = strategy_counts.get(strategy_type, 0) + 1
            
            last_used = strategy.get('last_used', 0)
            if last_used > one_day_ago:
                last_used_by_days["1_gun"] += 1
            elif last_used > one_week_ago:
                last_used_by_days["1_hafta"] += 1
            elif last_used > one_month_ago:
                last_used_by_days["1_ay"] += 1
            elif last_used > three_months_ago:
                last_used_by_days["3_ay"] += 1
            else:
                last_used_by_days["daha_eski"] += 1
    
    # Analiz çıktısı
    logger.info("=== Veritabanı Analizi ===")
    logger.info(f"Toplam locator sayısı: {total_locators}")
    logger.info(f"Toplam strateji sayısı: {total_strategies}")
    logger.info(f"Boş locator sayısı: {len(empty_locators)}")
    
    if empty_locators:
        logger.info(f"Boş locatorlar: {', '.join(empty_locators)}")
    
    logger.info("=== Strateji tipleri ===")
    for strategy_type, count in strategy_counts.items():
        logger.info(f"  {strategy_type}: {count}")
    
    logger.info("=== Son kullanım zamanına göre stratejiler ===")
    logger.info(f"  Son 1 gün içinde: {last_used_by_days['1_gun']}")
    logger.info(f"  Son 1 hafta içinde: {last_used_by_days['1_hafta']}")
    logger.info(f"  Son 1 ay içinde: {last_used_by_days['1_ay']}")
    logger.info(f"  Son 3 ay içinde: {last_used_by_days['3_ay']}")
    logger.info(f"  Daha eski: {last_used_by_days['daha_eski']}")

def remove_stale_strategies(db, days=30):
    """
    Belirli bir süreden daha eski olan stratejileri kaldırır.
    
    Args:
        db (dict): Veritabanı sözlüğü
        days (int): Gün cinsinden süre, bu süreden daha eski stratejiler temizlenir
        
    Returns:
        dict: Temizlenmiş veritabanı
    """
    cutoff_time = time.time() - (60 * 60 * 24 * days)
    removed_count = 0
    cleaned_db = {}
    
    for locator_id, data in db.items():
        strategies = data.get('strategies', [])
        active_strategies = []
        
        for strategy in strategies:
            last_used = strategy.get('last_used', 0)
            if last_used > cutoff_time:
                active_strategies.append(strategy)
            else:
                removed_count += 1
        
        if active_strategies:
            cleaned_db[locator_id] = {'strategies': active_strategies}
    
    logger.info(f"{removed_count} eski strateji kaldırıldı (> {days} gün)")
    logger.info(f"Aktif locator sayısı: {len(cleaned_db)}")
    return cleaned_db

def optimize_db(db):
    """
    Veritabanını optimize eder. 
    
    Her locator için en iyi stratejileri belirler ve gereksiz olanları kaldırır.
    
    Args:
        db (dict): Veritabanı sözlüğü
        
    Returns:
        dict: Optimize edilmiş veritabanı
    """
    optimized_db = {}
    total_removed = 0
    
    for locator_id, data in db.items():
        strategies = data.get('strategies', [])
        
        if not strategies:
            continue
        
        # Stratejileri son kullanım zamanına göre sırala (en yeniler önce)
        sorted_strategies = sorted(strategies, key=lambda s: s.get('last_used', 0), reverse=True)
        
        # Her tip için en iyi stratejileri tut
        best_strategies = {}
        for strategy in sorted_strategies:
            strategy_type = strategy.get('type')
            if strategy_type not in best_strategies:
                best_strategies[strategy_type] = strategy
        
        # En iyi stratejileri birleştir
        optimized_strategies = list(best_strategies.values())
        total_removed += len(strategies) - len(optimized_strategies)
        
        optimized_db[locator_id] = {'strategies': optimized_strategies}
    
    logger.info(f"Optimizasyon: {total_removed} gereksiz strateji kaldırıldı")
    return optimized_db

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code) 