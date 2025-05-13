"""
Self-Healing Strateji Analiz Aracı

Bu araç, self-healing mekanizması tarafından kullanılan stratejilerin
başarı oranlarını analiz eder ve raporlar. Strateji tiplerinin etkinliğini
ölçmeye yardımcı olur.
"""

import os
import json
import logging
import argparse
import time
import pandas as pd
import matplotlib.pyplot as plt
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
    parser = argparse.ArgumentParser(description="Self-healing strateji analiz aracı")
    parser.add_argument("--db-file", type=str, default="locator_db.json", help="Veritabanı dosyası yolu")
    parser.add_argument("--model-file", type=str, default="model_data.json", help="Model veri dosyası yolu")
    parser.add_argument("--output-dir", type=str, default="analysis", help="Analiz çıktıları için dizin")
    parser.add_argument("--generate-charts", action="store_true", help="Grafik raporları oluştur")
    
    args = parser.parse_args()
    
    # Çıktı dizini kontrolü
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Veritabanı ve model verilerini yükle
    db = load_database(args.db_file)
    model_data = load_model_data(args.model_file)
    
    if not db or not model_data:
        return 1
    
    # Analizi gerçekleştir
    analysis_results = analyze_strategies(db, model_data)
    
    # Analiz sonuçlarını kaydet
    save_analysis_results(analysis_results, output_dir)
    
    # Grafik raporları oluştur
    if args.generate_charts:
        generate_charts(analysis_results, output_dir)
    
    return 0

def load_database(db_file):
    """
    Veritabanını yükler.
    
    Args:
        db_file (str): Veritabanı dosyasının yolu
        
    Returns:
        dict: Veritabanı sözlüğü veya None (hata durumunda)
    """
    db_path = Path(db_file)
    if not db_path.exists():
        logger.error(f"Veritabanı dosyası bulunamadı: {db_path}")
        return None
    
    try:
        with open(db_path, 'r', encoding='utf-8') as f:
            db = json.load(f)
        logger.info(f"Veritabanı başarıyla yüklendi: {len(db)} locator kaydı")
        return db
    except Exception as e:
        logger.error(f"Veritabanı yüklenirken hata oluştu: {e}")
        return None

def load_model_data(model_file):
    """
    Model verisini yükler.
    
    Args:
        model_file (str): Model veri dosyasının yolu
        
    Returns:
        dict: Model veri sözlüğü veya None (hata durumunda)
    """
    model_path = Path(model_file)
    if not model_path.exists():
        logger.error(f"Model veri dosyası bulunamadı: {model_path}")
        return None
    
    try:
        with open(model_path, 'r', encoding='utf-8') as f:
            model_data = json.load(f)
        
        logger.info(f"Model verisi başarıyla yüklendi, {len(model_data.get('trained_cases', []))} eğitim örneği")
        return model_data
    except Exception as e:
        logger.error(f"Model verisi yüklenirken hata oluştu: {e}")
        return None

def analyze_strategies(db, model_data):
    """
    Strateji başarı oranlarını analiz eder.
    
    Args:
        db (dict): Veritabanı sözlüğü
        model_data (dict): Model veri sözlüğü
        
    Returns:
        dict: Analiz sonuçları
    """
    results = {
        "locator_count": len(db),
        "total_strategies": 0,
        "strategy_types": {},
        "strategy_success_timeline": [],
        "locator_strategy_counts": {},
        "most_successful_strategies": [],
        "least_successful_strategies": [],
        "model_training_count": len(model_data.get('trained_cases', [])),
        "recently_used_strategies": []
    }
    
    now = time.time()
    strategy_timeline = {}  # Zaman aralıklarına göre strateji başarısı
    
    # Her locator için stratejileri analiz et
    for locator_id, data in db.items():
        strategies = data.get('strategies', [])
        results['total_strategies'] += len(strategies)
        results['locator_strategy_counts'][locator_id] = len(strategies)
        
        # Her strateji tipini say
        for strategy in strategies:
            strategy_type = strategy.get('type', 'unknown')
            
            if strategy_type not in results['strategy_types']:
                results['strategy_types'][strategy_type] = {
                    "count": 0,
                    "success_rate": 0,
                    "recently_used": 0
                }
            
            results['strategy_types'][strategy_type]['count'] += 1
            
            # Son kullanım zamanı
            last_used = strategy.get('last_used', 0)
            time_diff = now - last_used
            
            # Son 24 saat içinde kullanıldıysa
            if time_diff < 86400:  # 24 saat (saniye cinsinden)
                results['strategy_types'][strategy_type]['recently_used'] += 1
                
                # Son kullanılan stratejileri kaydet
                results['recently_used_strategies'].append({
                    'locator_id': locator_id,
                    'type': strategy_type,
                    'selector': strategy.get('selector', ''),
                    'last_used': last_used
                })
            
            # Zaman çizelgesi için
            day = int(last_used / 86400)  # Günleri grupla
            if day not in strategy_timeline:
                strategy_timeline[day] = {"total": 0, "by_type": {}}
            
            strategy_timeline[day]["total"] += 1
            if strategy_type not in strategy_timeline[day]["by_type"]:
                strategy_timeline[day]["by_type"][strategy_type] = 0
            strategy_timeline[day]["by_type"][strategy_type] += 1
    
    # Son kullanılan stratejileri sırala (en son kullanılanlar önce)
    results['recently_used_strategies'].sort(key=lambda x: x['last_used'], reverse=True)
    results['recently_used_strategies'] = results['recently_used_strategies'][:10]  # Son 10 strateji
    
    # Zaman çizelgesini dönüştür
    for day, data in sorted(strategy_timeline.items()):
        timestamp = day * 86400  # Gün değerini saniyeye çevir
        date_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
        
        results['strategy_success_timeline'].append({
            'date': date_str,
            'total': data['total'],
            'by_type': data['by_type']
        })
    
    # Başarı oranları
    for strategy_type, data in results['strategy_types'].items():
        # Son kullanılma oranı başarı göstergesi olarak kabul edilebilir
        success_rate = data['recently_used'] / data['count'] if data['count'] > 0 else 0
        results['strategy_types'][strategy_type]['success_rate'] = success_rate
    
    # En başarılı ve en başarısız stratejileri bul
    sorted_strategies = sorted(
        [(k, v['success_rate']) for k, v in results['strategy_types'].items()],
        key=lambda x: x[1],
        reverse=True
    )
    
    results['most_successful_strategies'] = sorted_strategies[:3]  # En başarılı 3 strateji
    results['least_successful_strategies'] = sorted_strategies[-3:]  # En başarısız 3 strateji
    
    return results

def save_analysis_results(results, output_dir):
    """
    Analiz sonuçlarını dosyaya kaydeder.
    
    Args:
        results (dict): Analiz sonuçları
        output_dir (Path): Çıktı dizini
    """
    # JSON olarak kaydet
    json_path = output_dir / "analysis_results.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4, ensure_ascii=False)
    
    # Metin raporu olarak kaydet
    txt_path = output_dir / "analysis_report.txt"
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write("=== Self-Healing Strateji Analiz Raporu ===\n")
        f.write(f"Oluşturma Zamanı: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write(f"Toplam Locator Sayısı: {results['locator_count']}\n")
        f.write(f"Toplam Strateji Sayısı: {results['total_strategies']}\n")
        f.write(f"Model Eğitim Sayısı: {results['model_training_count']}\n\n")
        
        f.write("== Strateji Tipleri ==\n")
        for strategy_type, data in results['strategy_types'].items():
            f.write(f"  {strategy_type}:\n")
            f.write(f"    Sayı: {data['count']}\n")
            f.write(f"    Başarı Oranı: {data['success_rate']:.2%}\n")
            f.write(f"    Son Kullanım: {data['recently_used']}\n")
        
        f.write("\n== En Başarılı Stratejiler ==\n")
        for strategy_type, success_rate in results['most_successful_strategies']:
            f.write(f"  {strategy_type}: {success_rate:.2%}\n")
        
        f.write("\n== En Başarısız Stratejiler ==\n")
        for strategy_type, success_rate in results['least_successful_strategies']:
            f.write(f"  {strategy_type}: {success_rate:.2%}\n")
        
        f.write("\n== Son Kullanılan Stratejiler ==\n")
        for strategy in results['recently_used_strategies']:
            date_str = datetime.fromtimestamp(strategy['last_used']).strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"  {strategy['locator_id']} - {strategy['type']} ({date_str}): {strategy['selector']}\n")
    
    logger.info(f"Analiz sonuçları kaydedildi: {json_path} ve {txt_path}")

def generate_charts(results, output_dir):
    """
    Analiz sonuçlarından görsel grafikler oluşturur.
    
    Args:
        results (dict): Analiz sonuçları
        output_dir (Path): Çıktı dizini
    """
    try:
        # Strateji tipi dağılımı pasta grafiği
        plt.figure(figsize=(10, 6))
        strategy_counts = {k: v['count'] for k, v in results['strategy_types'].items()}
        plt.pie(strategy_counts.values(), labels=strategy_counts.keys(), autopct='%1.1f%%', startangle=90)
        plt.axis('equal')
        plt.title('Strateji Tipi Dağılımı')
        plt.tight_layout()
        plt.savefig(output_dir / "strategy_type_distribution.png")
        plt.close()
        
        # Strateji başarı oranları çubuk grafiği
        plt.figure(figsize=(12, 6))
        strategy_success = {k: v['success_rate'] for k, v in results['strategy_types'].items()}
        plt.bar(strategy_success.keys(), [x * 100 for x in strategy_success.values()])
        plt.xlabel('Strateji Tipi')
        plt.ylabel('Başarı Oranı (%)')
        plt.title('Strateji Başarı Oranları')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(output_dir / "strategy_success_rates.png")
        plt.close()
        
        # Zamana göre strateji kullanımı çizgi grafiği
        if results['strategy_success_timeline']:
            plt.figure(figsize=(14, 7))
            dates = [item['date'] for item in results['strategy_success_timeline']]
            totals = [item['total'] for item in results['strategy_success_timeline']]
            
            plt.plot(dates, totals, marker='o', linestyle='-', color='blue')
            plt.xlabel('Tarih')
            plt.ylabel('Strateji Kullanım Sayısı')
            plt.title('Zamana Göre Strateji Kullanımı')
            plt.xticks(rotation=45)
            plt.grid(True, linestyle='--', alpha=0.7)
            plt.tight_layout()
            plt.savefig(output_dir / "strategy_usage_timeline.png")
            plt.close()
        
        logger.info(f"Grafikler oluşturuldu: {output_dir}")
    except Exception as e:
        logger.error(f"Grafik oluşturma sırasında hata: {e}")

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code) 