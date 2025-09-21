#!/usr/bin/env python3
"""
₿ CRYPTO MODULE v2.0
Модуль интеграции с криптовалютным сервисом
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class CryptoModule:
    """₿ Модуль криптовалют"""
    
    def __init__(self, crypto_service):
        self.crypto_service = crypto_service
        
        # Избранные монеты пользователей
        self.user_favorites = {}
        
        logger.info("₿ Crypto Module инициализирован")
    
    async def handle_crypto_request(self, user_id: int, coin_query: str) -> Dict[str, Any]:
        """💰 Обработка запроса криптовалюты"""
        
        if not self.crypto_service:
            return {
                'error': True,
                'message': 'Криптовалютный сервис отключен'
            }
        
        try:
            # Получаем данные о монете
            crypto_data = await self.crypto_service.get_crypto_price(coin_query, user_id)
            
            # Добавляем персональные рекомендации
            if not crypto_data.get('error', False):
                crypto_data['recommendations'] = self._generate_recommendations(crypto_data)
            
            return crypto_data
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки криптозапроса: {e}")
            return {
                'error': True,
                'message': 'Ошибка получения данных о криптовалюте'
            }
    
    async def get_trending_crypto(self) -> Dict[str, Any]:
        """🔥 Получение трендовых криптовалют"""
        
        if not self.crypto_service:
            return {
                'error': True,
                'message': 'Криптовалютный сервис отключен'
            }
        
        return await self.crypto_service.get_trending_crypto()
    
    def _generate_recommendations(self, crypto_data: Dict) -> List[str]:
        """💡 Генерация рекомендаций"""
        
        recommendations = []
        change_24h = crypto_data.get('change_24h', 0)
        
        if change_24h > 10:
            recommendations.append("⚠️ Высокая волатильность - будьте осторожны")
        elif change_24h > 5:
            recommendations.append("📈 Хороший рост - следите за трендом")
        elif change_24h < -10:
            recommendations.append("💡 Возможность для покупки на падении")
        
        recommendations.append("📚 Всегда изучайте проект перед инвестированием")
        
        return recommendations[:3]
    
    async def add_to_favorites(self, user_id: int, coin_symbol: str) -> bool:
        """⭐ Добавление в избранное"""
        
        try:
            if user_id not in self.user_favorites:
                self.user_favorites[user_id] = []
            
            if coin_symbol not in self.user_favorites[user_id]:
                self.user_favorites[user_id].append(coin_symbol.lower())
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка добавления в избранное: {e}")
            return False
    
    def get_user_favorites(self, user_id: int) -> List[str]:
        """⭐ Получение избранных монет"""
        
        return self.user_favorites.get(user_id, [])


__all__ = ["CryptoModule"]