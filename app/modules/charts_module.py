#!/usr/bin/env python3
"""
📈 CHARTS MODULE v2.0
Модуль создания графиков и визуализации данных
"""

import logging
from typing import Dict, Any, List
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


class ChartsModule:
    """📈 Модуль графиков"""
    
    def __init__(self, db_service):
        self.db = db_service
        self.charts_dir = Path('data/charts')
        self.charts_dir.mkdir(exist_ok=True)
        
        # Настройка matplotlib для русского языка
        plt.rcParams['font.family'] = 'DejaVu Sans'
        plt.rcParams['axes.unicode_minus'] = False
        
        logger.info("📈 Charts Module инициализирован")
    
    async def create_activity_chart(self, user_id: int) -> str:
        """📊 Создание графика активности"""
        
        try:
            # Генерируем тестовые данные активности
            dates = []
            activity = []
            
            for i in range(7):
                date = datetime.now() - timedelta(days=i)
                dates.append(date)
                # Имитируем активность
                activity.append(max(0, 10 + i * 2 + (i % 3) * 5))
            
            # Создаем график
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(dates, activity, marker='o', linewidth=2, markersize=6)
            ax.set_title(f'График активности пользователя {user_id}', fontsize=14, pad=20)
            ax.set_xlabel('Дата')
            ax.set_ylabel('Сообщений')
            ax.grid(True, alpha=0.3)
            
            # Форматирование дат
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m'))
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Сохраняем график
            chart_filename = f"activity_{user_id}_{int(datetime.now().timestamp())}.png"
            chart_path = self.charts_dir / chart_filename
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            return str(chart_path)
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания графика активности: {e}")
            return ""
    
    async def create_emotions_chart(self, user_id: int) -> str:
        """😊 Создание графика эмоций"""
        
        try:
            # Тестовые данные эмоций
            emotions = ['Радость', 'Грусть', 'Удивление', 'Гнев', 'Нейтральное']
            counts = [45, 12, 18, 8, 35]
            colors = ['#FFD700', '#87CEEB', '#FF69B4', '#FF4500', '#808080']
            
            # Создаем круговую диаграмму
            fig, ax = plt.subplots(figsize=(8, 8))
            wedges, texts, autotexts = ax.pie(counts, labels=emotions, colors=colors, 
                                            autopct='%1.1f%%', startangle=90)
            
            ax.set_title(f'Эмоциональный профиль пользователя {user_id}', 
                        fontsize=14, pad=20)
            
            # Сохраняем график
            chart_filename = f"emotions_{user_id}_{int(datetime.now().timestamp())}.png"
            chart_path = self.charts_dir / chart_filename
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            return str(chart_path)
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания графика эмоций: {e}")
            return ""
    
    async def create_crypto_chart(self, coin_name: str, price_data: List[float]) -> str:
        """₿ Создание графика криптовалюты"""
        
        try:
            if not price_data:
                return ""
            
            # Генерируем временные метки
            timestamps = []
            for i in range(len(price_data)):
                timestamp = datetime.now() - timedelta(hours=len(price_data)-i-1)
                timestamps.append(timestamp)
            
            # Создаем график цены
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.plot(timestamps, price_data, linewidth=2, color='#F7931A')
            ax.fill_between(timestamps, price_data, alpha=0.3, color='#F7931A')
            
            ax.set_title(f'График цены {coin_name.upper()}', fontsize=14, pad=20)
            ax.set_xlabel('Время')
            ax.set_ylabel('Цена (USD)')
            ax.grid(True, alpha=0.3)
            
            # Форматирование времени
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Сохраняем график
            chart_filename = f"crypto_{coin_name}_{int(datetime.now().timestamp())}.png"
            chart_path = self.charts_dir / chart_filename
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            return str(chart_path)
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания криптографика: {e}")
            return ""
    
    def cleanup_old_charts(self, max_age_hours: int = 24):
        """🧹 Очистка старых графиков"""
        
        try:
            current_time = datetime.now()
            removed_count = 0
            
            for chart_file in self.charts_dir.glob("*.png"):
                file_time = datetime.fromtimestamp(chart_file.stat().st_mtime)
                if current_time - file_time > timedelta(hours=max_age_hours):
                    chart_file.unlink()
                    removed_count += 1
            
            if removed_count > 0:
                logger.info(f"🧹 Удалено {removed_count} старых графиков")
                
        except Exception as e:
            logger.error(f"❌ Ошибка очистки графиков: {e}")


__all__ = ["ChartsModule"]