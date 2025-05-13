"""
Test Veri Oluşturucu Araç

Bu araç, self-healing mekanizmasını test etmek için çeşitli senaryolarda
HTML içeriği oluşturur. Rastgele değişikliklerle elementlerin 
bulunabilirliğini test etmeye yardımcı olur.
"""

import os
import json
import logging
import argparse
import random
from pathlib import Path
from bs4 import BeautifulSoup

# Loglama yapılandırması
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def main():
    """Ana uygulama fonksiyonu."""
    parser = argparse.ArgumentParser(description="Self-healing test veri oluşturucu")
    parser.add_argument("--base-html", type=str, help="Temel HTML dosyası")
    parser.add_argument("--output-dir", type=str, default="test_data", help="Çıktı dizini")
    parser.add_argument("--scenarios", type=int, default=5, help="Oluşturulacak test senaryosu sayısı")
    parser.add_argument("--changes", type=int, default=3, help="Her senaryoda yapılacak değişiklik sayısı")
    
    args = parser.parse_args()
    
    # Çıktı dizinini oluştur
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Temel HTML içeriğini al
    if args.base_html and Path(args.base_html).exists():
        with open(args.base_html, 'r', encoding='utf-8') as f:
            base_html = f.read()
    else:
        base_html = create_sample_html()
    
    # Senaryoları oluştur
    create_test_scenarios(base_html, output_dir, args.scenarios, args.changes)
    
    return 0

def create_test_scenarios(base_html, output_dir, num_scenarios=5, num_changes=3):
    """
    Verilen temel HTML üzerinde çeşitli değişiklikler yaparak test senaryoları oluşturur.
    
    Args:
        base_html (str): Temel HTML içeriği
        output_dir (Path): Çıktı dizini
        num_scenarios (int): Oluşturulacak senaryo sayısı
        num_changes (int): Her senaryoda yapılacak değişiklik sayısı
    """
    # Temel HTML'i kaydet
    base_path = output_dir / "base.html"
    with open(base_path, 'w', encoding='utf-8') as f:
        f.write(base_html)
    logger.info(f"Temel HTML kaydedildi: {base_path}")
    
    # Her senaryo için
    for i in range(num_scenarios):
        # HTML'i parse et
        soup = BeautifulSoup(base_html, 'html.parser')
        
        # Değişiklikleri kaydet
        changes = []
        
        # Belirli sayıda değişiklik yap
        for j in range(num_changes):
            change_type = random.choice([
                'change_id',
                'change_class',
                'change_attribute',
                'change_text',
                'add_wrapper',
                'remove_element'
            ])
            
            # Rastgele bir element seç
            all_elements = soup.find_all(True)
            if not all_elements:
                continue
                
            element = random.choice(all_elements)
            
            # Değişikliği uygula
            if change_type == 'change_id' and 'id' in element.attrs:
                old_id = element['id']
                element['id'] = f"modified_{old_id}_{i}_{j}"
                changes.append(f"ID değiştirildi: {old_id} -> {element['id']}")
                
            elif change_type == 'change_class' and 'class' in element.attrs:
                old_class = ' '.join(element['class'])
                element['class'] = [f"modified_{c}_{i}_{j}" for c in element['class']]
                changes.append(f"Class değiştirildi: {old_class} -> {' '.join(element['class'])}")
                
            elif change_type == 'change_attribute':
                attributes = [attr for attr in element.attrs.keys() if attr not in ['id', 'class']]
                if attributes:
                    attr = random.choice(attributes)
                    old_value = element[attr]
                    element[attr] = f"modified_{old_value}_{i}_{j}"
                    changes.append(f"Öznitelik değiştirildi: {attr}={old_value} -> {attr}={element[attr]}")
                    
            elif change_type == 'change_text' and element.string:
                old_text = element.string
                element.string = f"Modified: {old_text} [{i}_{j}]"
                changes.append(f"Metin değiştirildi: '{old_text}' -> '{element.string}'")
                
            elif change_type == 'add_wrapper':
                wrapper = soup.new_tag('div')
                wrapper['class'] = [f"wrapper_{i}_{j}"]
                element.wrap(wrapper)
                changes.append(f"Element sarmalandı: <{element.name}> -> <div class='wrapper_{i}_{j}'><{element.name}></div>")
                
            elif change_type == 'remove_element':
                tag_name = element.name
                if tag_name not in ['html', 'body', 'head']:
                    changes.append(f"Element kaldırıldı: <{tag_name}>")
                    element.decompose()
        
        # Değiştirilmiş HTML'i kaydet
        scenario_path = output_dir / f"scenario_{i+1}.html"
        with open(scenario_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
            
        # Değişiklik kaydını oluştur
        changes_path = output_dir / f"scenario_{i+1}_changes.txt"
        with open(changes_path, 'w', encoding='utf-8') as f:
            f.write(f"Senaryo {i+1} Değişiklikleri:\n")
            f.write("-" * 50 + "\n")
            for idx, change in enumerate(changes, 1):
                f.write(f"{idx}. {change}\n")
        
        logger.info(f"Senaryo {i+1} oluşturuldu: {scenario_path}")
    
    logger.info(f"Toplam {num_scenarios} senaryo oluşturuldu")

def create_sample_html():
    """
    Örnek HTML içeriği oluşturur.
    
    Returns:
        str: Örnek HTML içeriği
    """
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Restoranlar | TGO Yemek</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 0; }
            header { background-color: #f8f8f8; padding: 10px; }
            .search-container { display: flex; margin: 10px 0; }
            .search-input { padding: 8px; width: 300px; border: 1px solid #ddd; }
            .search-button { padding: 8px 15px; background: #e74c3c; color: white; border: none; cursor: pointer; }
            .filter-button { padding: 8px 15px; background: #3498db; color: white; border: none; cursor: pointer; margin-left: 10px; }
            main { padding: 20px; }
            .restaurant-list { display: flex; flex-wrap: wrap; }
            .restaurant-card { width: 300px; margin: 10px; border: 1px solid #eee; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .restaurant-name { margin-top: 0; color: #333; }
            .restaurant-cuisine { color: #777; }
            .pagination { margin: 20px 0; }
            .pagination a { text-decoration: none; padding: 8px 12px; margin: 0 5px; border: 1px solid #ddd; color: #333; }
            .pagination a.active { background-color: #3498db; color: white; border-color: #3498db; }
            #filter-modal { display: none; position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 400px; background: white; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.2); z-index: 1000; }
            footer { background-color: #333; color: white; text-align: center; padding: 20px; margin-top: 30px; }
        </style>
    </head>
    <body>
        <header>
            <h1>TGO Yemek - Restoranlar</h1>
            <div class="search-container">
                <input type="search" class="search-input" id="search-box" placeholder="Restoran ara..." name="search">
                <button type="submit" class="search-button" id="search-btn">Ara</button>
            </div>
            <button class="filter-button" id="filter-btn">Filtrele ve Sırala</button>
        </header>
        <main>
            <h2>Restoranlar (15)</h2>
            <section class="restaurant-list">
                <div class="restaurant-card" id="restaurant-1">
                    <h2 class="restaurant-name">Pizza Restoran</h2>
                    <p class="restaurant-cuisine">İtalyan</p>
                    <p class="restaurant-address">Kadıköy, İstanbul</p>
                    <p class="restaurant-rating">★★★★☆ 4.2</p>
                </div>
                <div class="restaurant-card" id="restaurant-2">
                    <h2 class="restaurant-name">Burger Restoran</h2>
                    <p class="restaurant-cuisine">Amerikan</p>
                    <p class="restaurant-address">Beşiktaş, İstanbul</p>
                    <p class="restaurant-rating">★★★★★ 4.8</p>
                </div>
                <div class="restaurant-card" id="restaurant-3">
                    <h2 class="restaurant-name">Sushi & Asya Mutfağı</h2>
                    <p class="restaurant-cuisine">Japon</p>
                    <p class="restaurant-address">Şişli, İstanbul</p>
                    <p class="restaurant-rating">★★★★☆ 4.3</p>
                </div>
            </section>
            <div class="pagination">
                <a href="#" class="active">1</a>
                <a href="#">2</a>
                <a href="#">3</a>
                <a href="#">Sonraki</a>
            </div>
        </main>
        <div id="filter-modal">
            <h3>Filtreler</h3>
            <div class="filter-section">
                <h4>Mutfak</h4>
                <label><input type="checkbox" name="cuisine" value="italian"> İtalyan</label>
                <label><input type="checkbox" name="cuisine" value="american"> Amerikan</label>
                <label><input type="checkbox" name="cuisine" value="japanese"> Japon</label>
            </div>
            <div class="filter-section">
                <h4>Puan</h4>
                <label><input type="radio" name="rating" value="4"> 4+</label>
                <label><input type="radio" name="rating" value="3"> 3+</label>
            </div>
            <button id="apply-filters">Uygula</button>
            <button id="close-modal">Kapat</button>
        </div>
        <footer>
            <div>Bu site temsili amaçlarla oluşturulmuştur.</div>
            <div>TGO Yemek Demo © 2025</div>
        </footer>
    </body>
    </html>
    """

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code) 