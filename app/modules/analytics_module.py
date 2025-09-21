#!/usr/bin/env python3
"""
📊 ANALYTICS MODULE v2.0
Модуль интеграции с аналитическим сервисом
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class AnalyticsModule:
    """📊 Модуль аналитики"""
    
    def __init__(self, analytics_service):
        self.analytics_service = analytics_service
        
        logger.info("📊 Analytics Module инициализирован")
    
    async def track_user_action(self, user_id: int, chat_id: int, action: str, metadata: Dict = None) -> bool:
        """📋 Отслеживание действия пользователя"""
        
        if not self.analytics_service:
            return False
        
        return await self.analytics_service.track_user_activity(
            user_id, chat_id, action, metadata
        )
    
    async def get_user_dashboard(self, user_id: int) -> Dict[str, Any]:
        """📊 Получение дашборда пользователя"""
        
        if not self.analytics_service:
            return {'error': 'Аналитический сервис недоступен'}
        
        try:
            analytics = await self.analytics_service.get_user_analytics(user_id)
            
            # Форматируем для отображения
            if analytics.get('error'):
                return analytics
            
            dashboard = {
                'user_id': user_id,
                'basic_stats': analytics.get('basic_stats', {}),
                'activity_level': analytics.get('activity_analysis', {}).get('activity_level', 'unknown'),
                'engagement_score': analytics.get('activity_analysis', {}).get('engagement_score', 0),
                'insights': analytics.get('insights', []),
                'generated_at': analytics.get('generated_at')
            }
            
            return dashboard
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения дашборда: {e}")
            return {'error': str(e)}
    
    async def get_chat_dashboard(self, chat_id: int) -> Dict[str, Any]:
        """💬 Получение дашборда чата"""
        
        if not self.analytics_service:
            return {'error': 'Аналитический сервис недоступен'}
        
        return await self.analytics_service.get_chat_analytics(chat_id)
    
    async def export_user_data(self, user_id: int, format: str = 'json') -> str:
        """📤 Экспорт данных пользователя"""
        
        try:
            dashboard = await self.get_user_dashboard(user_id)
            
            if format == 'json':
                import json
                return json.dumps(dashboard, indent=2, ensure_ascii=False)
            elif format == 'csv':
                # Простой CSV экспорт
                basic_stats = dashboard.get('basic_stats', {})
                csv_data = f"Пользователь,Сообщений,Средняя длина,Последняя активность\n"
                csv_data += f"{user_id},{basic_stats.get('message_count', 0)},{basic_stats.get('avg_message_length', 0)},{basic_stats.get('last_activity', 'N/A')}\n"
                return csv_data
            else:
                return str(dashboard)
                
        except Exception as e:
            logger.error(f"❌ Ошибка экспорта данных: {e}")
            return f"Ошибка экспорта: {e}"


__all__ = ["AnalyticsModule"]