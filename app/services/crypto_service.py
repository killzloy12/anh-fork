#!/usr/bin/env python3
"""
₿ CRYPTO SERVICE v2.0
💰 Продвинутый сервис криптовалютных данных

Интеграция с CoinGecko API для получения актуальных курсов криптовалют
"""

import logging
import asyncio
import json
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from cachetools import TTLCache

logger = logging.getLogger(__name__)


class CryptoService:
    """₿ Сервис криптовалют"""
    
    def __init__(self, config):
        self.config = config
        self.crypto_config = config.crypto
        
        # Кэш для курсов
        self.price_cache = TTLCache(maxsize=1000, ttl=300)  # 5 минут
        
        # Популярные криптовалюты
        self.popular_coins = {
            'bitcoin': 'bitcoin',
            'btc': 'bitcoin',
            'ethereum': 'ethereum',
            'eth': 'ethereum',
            'binancecoin': 'binancecoin',
            'bnb': 'binancecoin',
            'cardano': 'cardano',
            'ada': 'cardano',
            'solana': 'solana',
            'sol': 'solana',
            'polkadot': 'polkadot',
            'dot': 'polkadot',
            'chainlink': 'chainlink',
            'link': 'chainlink',
            'litecoin': 'litecoin',
            'ltc': 'litecoin',
            'dogecoin': 'dogecoin',
            'doge': 'dogecoin',
            'toncoin': 'the-open-network',
            'ton': 'the-open-network'
        }
        
        # База URL для API
        self.base_url = "https://api.coingecko.com/api/v3"
        
        logger.info("₿ Crypto Service инициализирован")
    
    async def get_crypto_price(self, coin_query: str, user_id: int = None) -> Dict[str, Any]:
        """💰 Получение курса криптовалюты"""
        
        try:
            # Нормализуем запрос
            coin_id = self._normalize_coin_query(coin_query)
            
            if not coin_id:
                return {
                    'error': True,
                    'message': f'Криптовалюта "{coin_query}" не найдена',
                    'suggestions': list(self.popular_coins.keys())[:5]
                }
            
            # Проверяем кэш
            cache_key = f"price_{coin_id}"
            if cache_key in self.price_cache:
                cached_data = self.price_cache[cache_key]
                cached_data['from_cache'] = True
                return cached_data
            
            # Запрашиваем данные
            price_data = await self._fetch_coin_data(coin_id)
            
            if not price_data:
                return {
                    'error': True,
                    'message': 'Не удалось получить данные о криптовалюте',
                    'suggestions': list(self.popular_coins.keys())[:3]
                }
            
            # Формируем ответ
            result = self._format_price_response(price_data, coin_query, user_id)
            
            # Сохраняем в кэш
            self.price_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения курса криптовалюты: {e}")
            return {
                'error': True,
                'message': 'Произошла ошибка при получении данных',
                'details': str(e)
            }
    
    async def get_trending_crypto(self, limit: int = 7) -> Dict[str, Any]:
        """🔥 Получение трендовых криптовалют"""
        
        try:
            cache_key = "trending_crypto"
            
            # Проверяем кэш
            if cache_key in self.price_cache:
                return self.price_cache[cache_key]
            
            # Запрашиваем трендовые монеты
            url = f"{self.base_url}/search/trending"
            headers = self._get_headers()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        trending_coins = data.get('coins', [])[:limit]
                        
                        # Получаем подробную информацию о трендовых монетах
                        detailed_coins = []
                        for coin_info in trending_coins:
                            coin_id = coin_info['item']['id']
                            coin_data = await self._fetch_coin_data(coin_id)
                            
                            if coin_data:
                                detailed_coins.append({
                                    'name': coin_data['name'],
                                    'symbol': coin_data['symbol'].upper(),
                                    'price': self._format_price(coin_data['current_price']),
                                    'change_24h': self._format_change(coin_data.get('price_change_percentage_24h', 0)),
                                    'market_cap_rank': coin_data.get('market_cap_rank', 'N/A'),
                                    'market_cap': self._format_market_cap(coin_data.get('market_cap', 0))
                                })
                        
                        result = {
                            'error': False,
                            'trending_coins': detailed_coins,
                            'update_time': datetime.now().strftime('%H:%M'),
                            'source': 'CoinGecko'
                        }
                        
                        # Сохраняем в кэш
                        self.price_cache[cache_key] = result
                        return result
                    
                    else:
                        logger.error(f"Ошибка API трендов: {resp.status}")
                        return {
                            'error': True,
                            'message': 'Не удалось получить трендовые криптовалюты'
                        }
                        
        except Exception as e:
            logger.error(f"❌ Ошибка получения трендовых криптовалют: {e}")
            return {
                'error': True,
                'message': 'Произошла ошибка при получении трендов'
            }
    
    async def _fetch_coin_data(self, coin_id: str) -> Optional[Dict]:
        """📊 Получение данных о монете"""
        
        try:
            url = f"{self.base_url}/coins/{coin_id}"
            params = {
                'localization': 'false',
                'tickers': 'false',
                'market_data': 'true',
                'community_data': 'false',
                'developer_data': 'false',
                'sparkline': 'false'
            }
            
            headers = self._get_headers()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        
                        # Извлекаем нужные данные
                        market_data = data.get('market_data', {})
                        usd_data = market_data.get('current_price', {}).get('usd')
                        
                        if usd_data is None:
                            return None
                        
                        return {
                            'id': data.get('id'),
                            'name': data.get('name'),
                            'symbol': data.get('symbol'),
                            'current_price': usd_data,
                            'market_cap': market_data.get('market_cap', {}).get('usd'),
                            'market_cap_rank': market_data.get('market_cap_rank'),
                            'total_volume': market_data.get('total_volume', {}).get('usd'),
                            'price_change_24h': market_data.get('price_change_24h'),
                            'price_change_percentage_24h': market_data.get('price_change_percentage_24h'),
                            'circulating_supply': market_data.get('circulating_supply'),
                            'total_supply': market_data.get('total_supply'),
                            'ath': market_data.get('ath', {}).get('usd'),
                            'atl': market_data.get('atl', {}).get('usd'),
                            'last_updated': market_data.get('last_updated')
                        }
                    else:
                        logger.error(f"Ошибка API монеты: {resp.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"❌ Ошибка получения данных монеты {coin_id}: {e}")
            return None
    
    def _normalize_coin_query(self, query: str) -> Optional[str]:
        """🔍 Нормализация запроса монеты"""
        
        query_lower = query.lower().strip()
        
        # Проверяем популярные монеты
        if query_lower in self.popular_coins:
            return self.popular_coins[query_lower]
        
        # Проверяем по частичному совпадению
        for key, value in self.popular_coins.items():
            if query_lower in key or key in query_lower:
                return value
        
        # Если не найдено, возвращаем исходный запрос
        # (возможно, это точный ID монеты)
        return query_lower if len(query_lower) > 2 else None
    
    def _format_price_response(self, coin_data: Dict, original_query: str, user_id: int = None) -> Dict[str, Any]:
        """📝 Форматирование ответа о цене"""
        
        try:
            price = coin_data['current_price']
            change_24h = coin_data.get('price_change_percentage_24h', 0)
            
            response = {
                'error': False,
                'coin_name': coin_data['name'],
                'symbol': coin_data['symbol'].upper(),
                'price': self._format_price(price),
                'price_raw': price,
                'change_24h': change_24h,
                'change_24h_formatted': self._format_change(change_24h),
                'trend_emoji': self._get_trend_emoji(change_24h),
                'market_cap': self._format_market_cap(coin_data.get('market_cap')),
                'volume_24h': self._format_volume(coin_data.get('total_volume')),
                'market_cap_rank': coin_data.get('market_cap_rank', 'N/A'),
                'last_updated': self._format_last_updated(coin_data.get('last_updated')),
                'price_analysis': self._generate_price_analysis(coin_data),
                'personal_insights': self._generate_personal_insights(coin_data, user_id)
            }
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Ошибка форматирования ответа: {e}")
            return {
                'error': True,
                'message': 'Ошибка обработки данных о криптовалюте'
            }
    
    def _format_price(self, price: float) -> str:
        """💰 Форматирование цены"""
        
        if price >= 1:
            return f"${price:,.2f}"
        elif price >= 0.01:
            return f"${price:.4f}"
        elif price >= 0.0001:
            return f"${price:.6f}"
        else:
            return f"${price:.8f}"
    
    def _format_change(self, change: float) -> str:
        """📈 Форматирование изменения цены"""
        
        if change > 0:
            return f"+{change:.2f}%"
        else:
            return f"{change:.2f}%"
    
    def _get_trend_emoji(self, change: float) -> str:
        """📊 Эмодзи тренда"""
        
        if change > 5:
            return "🚀"
        elif change > 0:
            return "📈"
        elif change > -5:
            return "📉"
        else:
            return "💥"
    
    def _format_market_cap(self, market_cap: Optional[float]) -> str:
        """💎 Форматирование рыночной капитализации"""
        
        if not market_cap:
            return "N/A"
        
        if market_cap >= 1_000_000_000_000:  # Триллион
            return f"${market_cap/1_000_000_000_000:.2f}T"
        elif market_cap >= 1_000_000_000:  # Миллиард
            return f"${market_cap/1_000_000_000:.2f}B"
        elif market_cap >= 1_000_000:  # Миллион
            return f"${market_cap/1_000_000:.2f}M"
        else:
            return f"${market_cap:,.0f}"
    
    def _format_volume(self, volume: Optional[float]) -> str:
        """📦 Форматирование объема торгов"""
        
        if not volume:
            return "N/A"
        
        if volume >= 1_000_000_000:  # Миллиард
            return f"${volume/1_000_000_000:.2f}B"
        elif volume >= 1_000_000:  # Миллион
            return f"${volume/1_000_000:.2f}M"
        else:
            return f"${volume:,.0f}"
    
    def _format_last_updated(self, last_updated: Optional[str]) -> str:
        """⏰ Форматирование времени обновления"""
        
        if not last_updated:
            return "неизвестно"
        
        try:
            update_time = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
            now = datetime.now(update_time.tzinfo)
            diff = now - update_time
            
            if diff.seconds < 60:
                return "только что"
            elif diff.seconds < 3600:
                return f"{diff.seconds // 60} мин назад"
            else:
                return update_time.strftime('%H:%M')
                
        except Exception:
            return "недавно"
    
    def _generate_price_analysis(self, coin_data: Dict) -> str:
        """📊 Генерация анализа цены"""
        
        try:
            change_24h = coin_data.get('price_change_percentage_24h', 0)
            rank = coin_data.get('market_cap_rank')
            
            analysis_parts = []
            
            # Анализ изменения цены
            if change_24h > 10:
                analysis_parts.append("🔥 Сильный рост за сутки!")
            elif change_24h > 5:
                analysis_parts.append("📈 Хороший рост за день.")
            elif change_24h > 0:
                analysis_parts.append("✅ Положительная динамика.")
            elif change_24h > -5:
                analysis_parts.append("📊 Небольшое снижение.")
            elif change_24h > -10:
                analysis_parts.append("📉 Заметное снижение цены.")
            else:
                analysis_parts.append("⚠️ Значительное падение!")
            
            # Анализ позиции в рейтинге
            if rank and rank <= 10:
                analysis_parts.append(f"🏆 Топ-{rank} криптовалюта по капитализации.")
            elif rank and rank <= 50:
                analysis_parts.append(f"⭐ #{rank} в рейтинге криптовалют.")
            elif rank and rank <= 100:
                analysis_parts.append(f"📊 #{rank} место по рыночной капитализации.")
            
            return " ".join(analysis_parts)
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации анализа: {e}")
            return "📊 Данные обновлены."
    
    def _generate_personal_insights(self, coin_data: Dict, user_id: int = None) -> List[str]:
        """💡 Генерация персональных инсайтов"""
        
        insights = []
        
        try:
            change_24h = coin_data.get('price_change_percentage_24h', 0)
            price = coin_data.get('current_price', 0)
            
            # Общие инсайты
            if change_24h > 15:
                insights.append("⚡ Высокая волатильность - будьте осторожны!")
            elif change_24h < -15:
                insights.append("💡 Возможность для покупки на падении.")
            
            if price > 1000:
                insights.append("💰 Высокая цена - рассмотрите дробные покупки.")
            elif price < 1:
                insights.append("🔍 Низкая цена - изучите проект внимательнее.")
            
            # Рекомендации
            insights.append("📚 Всегда изучайте проект перед инвестированием.")
            
            return insights[:3]  # Максимум 3 инсайта
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации инсайтов: {e}")
            return ["💡 Следите за рынком и принимайте взвешенные решения."]
    
    def _get_headers(self) -> Dict[str, str]:
        """📋 Заголовки для API запросов"""
        
        headers = {
            'User-Agent': 'Enhanced-Telegram-Bot/2.0',
            'Accept': 'application/json'
        }
        
        # Добавляем API ключ если есть
        if self.crypto_config.coingecko_api_key:
            headers['x-cg-pro-api-key'] = self.crypto_config.coingecko_api_key
        
        return headers
    
    async def close(self):
        """🔒 Закрытие сервиса"""
        
        try:
            # Очищаем кэш
            self.price_cache.clear()
            
            logger.info("₿ Crypto Service закрыт")
            
        except Exception as e:
            logger.error(f"❌ Ошибка закрытия Crypto Service: {e}")
    
    def get_service_stats(self) -> Dict[str, Any]:
        """📊 Статистика сервиса"""
        
        return {
            'cache_size': len(self.price_cache),
            'popular_coins_count': len(self.popular_coins),
            'api_key_configured': bool(self.crypto_config.coingecko_api_key),
            'service_enabled': self.crypto_config.enabled
        }


__all__ = ["CryptoService"]