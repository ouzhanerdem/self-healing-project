"""
Restoran detay sayfası için Page Object.
"""

import logging
from features.pages.base_page import BasePage

logger = logging.getLogger(__name__)

class RestaurantDetailPage(BasePage):
    """
    TGO Yemek Restoran Detay sayfası için Page Object.
    Restoran detay sayfasına özgü tüm elementleri ve işlemleri içerir.
    """
    
    def __init__(self, context):
        """
        Restoran detay sayfası için Page Object yapıcı metodu.
        
        Args:
            context: Behave context nesnesi
        """
        super().__init__(context)
        
        # Sayfa selektörleri
        self.selectors = {
            # Restoran bilgileri
            "restaurant_name": "h1, .restaurant-title, .restaurant-name",
            "restaurant_info": ".restaurant-info, .restaurant-details, address, .rating",
            "menu_items": ".menu-item, .dish, .food-item",
            "restaurant_address": "address, .address, [itemprop='address']",
            "restaurant_rating": ".rating, .stars, [itemprop='ratingValue']",
            "restaurant_cuisine": ".cuisine, .restaurant-type, [itemprop='servesCuisine']",
            
            # Butonlar ve etkileşimli öğeler
            "order_button": "button:has-text('Sipariş Ver'), .order-button, .order-now",
            "add_to_favorites": ".add-to-favorites, .favorite-button, .save-restaurant",
            "share_button": ".share, .share-button, button:has-text('Paylaş')",
            
            # Yorum bölümü
            "reviews_section": ".reviews, .comments, #reviews",
            "add_review_button": ".add-review, .write-review, button:has-text('Yorum Yap')"
        }
    
    def is_restaurant_detail_page(self):
        """
        Mevcut sayfanın restoran detay sayfası olup olmadığını kontrol eder.
        
        Returns:
            bool: Restoran detay sayfasıysa True, değilse False
        """
        try:
            # URL'de restoran bulunmalı
            current_url = self.get_current_url()
            if "restaurant" in current_url or "restoran" in current_url:
                logger.info(f"URL restoran içeriyor: {current_url}")
                return True
                
            # Restoran başlığı bulunmalı
            page_heading = self.page.locator("h1, h2.restaurant-title").first
            if page_heading and page_heading.is_visible():
                logger.info(f"Restoran başlığı bulundu: {page_heading.inner_text()}")
                return True
                
            # Demo kontrolleri kaldırıldı
                
            logger.warning("Detay sayfası kriterleri bulunamadı")
            return False
        except Exception as e:
            logger.error(f"Detay sayfası kontrolünde hata: {e}")
            # Hata durumunda, mevcut sayfayı detay sayfası olarak kabul edelim (test devam etsin)
            return False
    
    def get_restaurant_name(self):
        """
        Restoran adını alır.
        
        Returns:
            str: Restoran adı
        """
        return self.get_text("restoran_detay_isim", self.selectors["restaurant_name"])
    
    def get_restaurant_info(self):
        """
        Restoran bilgilerini alır.
        
        Returns:
            str: Restoran bilgileri
        """
        return self.get_text("restoran_temel_bilgileri", self.selectors["restaurant_info"])
    
    def is_restaurant_info_visible(self):
        """
        Restoran bilgilerinin görünür olup olmadığını kontrol eder.
        
        Returns:
            bool: Bilgiler görünürse True, değilse False
        """
        return self.is_element_visible("restoran_temel_bilgileri", self.selectors["restaurant_info"])
    
    def has_menu_items(self):
        """
        Menü öğelerinin olup olmadığını kontrol eder.
        
        Returns:
            bool: Menü öğeleri varsa True, yoksa False
        """
        try:
            count = self.count_elements("menu_ogeleri", self.selectors["menu_items"])
            return count > 0
        except Exception:
            return False
    
    def get_restaurant_address(self):
        """
        Restoran adresini alır.
        
        Returns:
            str: Restoran adresi
        """
        try:
            return self.get_text("restoran_adresi", self.selectors["restaurant_address"])
        except Exception:
            return ""
    
    def get_restaurant_rating(self):
        """
        Restoran puanını alır.
        
        Returns:
            str: Restoran puanı
        """
        try:
            return self.get_text("restoran_puani", self.selectors["restaurant_rating"])
        except Exception:
            return ""
    
    def click_order_button(self):
        """
        Sipariş ver butonuna tıklar.
        
        Returns:
            bool: Başarılıysa True, değilse False
        """
        try:
            self.click_element("siparis_butonu", self.selectors["order_button"])
            return True
        except Exception as e:
            logger.warning(f"Sipariş butonuna tıklanamadı: {e}")
            return False
    
    def click_add_to_favorites(self):
        """
        Favorilere ekle butonuna tıklar.
        
        Returns:
            bool: Başarılıysa True, değilse False
        """
        try:
            self.click_element("favorilere_ekle", self.selectors["add_to_favorites"])
            return True
        except Exception as e:
            logger.warning(f"Favorilere ekle butonuna tıklanamadı: {e}")
            return False 