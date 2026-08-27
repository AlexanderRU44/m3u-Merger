#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta

# ═══════════════════════════════════════════════════════════════
# 🔽 СПИСОК КАНАЛОВ ДЛЯ ИЗБРАННОГО
# ═══════════════════════════════════════════════════════════════
# Добавьте названия каналов, которые хотите видеть в Избранном
# (регистр не важен, достаточно части названия)

FAVORITE_CHANNELS = [
    # === Российские ===
    'Первый канал',
    'Россия 1',
    'Россия 24',
    'НТВ',
    'СТС',
    'ТНТ',
    'РЕН ТВ',
    'Пятый канал',
    'Матч ТВ',
    'Звезда',
    'ТВ Центр',
    'Мир',
    'Спас',
    'Карусель',
    
    # === Зарубежные ===
    'Discovery',
    'National Geographic',
    'Nat Geo',
    'History',
    'Animal Planet',
    'CNN',
    'BBC',
    'Deutsche Welle',
    'France 24',
    'CGTN',
    
    # === Кино ===
    'Amedia',
    'TV1000',
    'Viju',
    'Кинопремьера',
    'Кино ТВ',
    'Кинокомедия',
    'Кинохит',
    'Hollywood',
    'Bollywood',
    
    # === Спорт ===
    'Матч ТВ',
    'Eurosport',
    'Setanta',
    'Спорт',
    
    # === Познавательные ===
    'Наука 2.0',
    'Моя планета',
    'Охота и рыбалка',
    'Travel',
    'Приключения',
    
    # === Детские ===
    'Cartoon Network',
    'Карусель',
    'Мульт',
    'Детский',
    
    # === Музыка ===
    'Музыка',
    'Шансон',
    'Жара',
    
    # ⬇️ ДОБАВЬТЕ СВОИ КАНАЛЫ ЗДЕСЬ
    # 'Мой любимый канал',
    # 'Ещё один канал',
]

# Настройка часового пояса (Москва UTC+3)
MOSCOW_TZ = timezone(timedelta(hours=3))

def get_moscow_time():
    return datetime.now(MOSCOW_TZ)

def is_favorite(info_line):
    """Проверяет, является ли канал избранным"""
    if not info_line:
        return False
    
    info_lower = info_line.lower()
    
    for channel in FAVORITE_CHANNELS:
        if channel.lower() in info_lower:
            return True
    
    return False

def parse_m3u(file_path):
    """Парсит M3U файл и возвращает список каналов"""
    channels = []
    current_channel = None
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith('#EXTINF'):
                current_channel = {
                    'info': line,
                    'url': None,
                }
            elif current_channel and line.startswith(('http://', 'https://')):
                current_channel['url'] = line
                channels.append(current_channel)
                current_channel = None
    
    except Exception as e:
        print(f"⚠️ Ошибка при чтении {file_path}: {e}")
    
    return channels

def write_m3u(channels, output_file, update_time):
    """Записывает каналы в M3U файл"""
    
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('#EXTM3U\n')
        f.write(f'# ❤️ Избранное — {update_time.strftime("%Y-%m-%d %H:%M:%S")} MSK\n')
        f.write(f'# Всего каналов: {len(channels)}\n\n')
        
        for channel in channels:
            if channel.get('info'):
                f.write(channel['info'] + '\n')
            if channel.get('url'):
                f.write(channel['url'] + '\n')

def main():
    input_file = './output/merged.m3u'
    output_file = './output/favorites.m3u'
    
    print("="*50)
    print("❤️  СОЗДАНИЕ ПЛЕЙЛИСТА ИЗБРАННОЕ")
    print("="*50)
    
    if not Path(input_file).exists():
        print(f"❌ Файл {input_file} не найден")
        print("   Сначала запустите основной workflow merge-playlists.yml")
        return
    
    print(f"📖 Чтение: {input_file}")
    channels = parse_m3u(input_file)
    print(f"📊 Найдено каналов: {len(channels)}")
    
    # Фильтруем избранные каналы
    favorites = []
    for ch in channels:
        if is_favorite(ch['info']):
            favorites.append(ch)
    
    print(f"❤️ Найдено избранных каналов: {len(favorites)}")
    
    if not favorites:
        print("⚠️ Избранные каналы не найдены!")
        print("   Проверьте список FAVORITE_CHANNELS в create_favorites.py")
        return
    
    # Показываем найденные каналы
    print("\n📺 Найденные каналы:")
    for i, ch in enumerate(favorites[:20], 1):
        # Извлекаем название из строки
        match = re.search(r',([^,]*)$', ch['info'])
        name = match.group(1).strip() if match else 'Без названия'
        print(f"  {i}. {name}")
    
    if len(favorites) > 20:
        print(f"  ... и ещё {len(favorites) - 20} каналов")
    
    # Сохраняем
    now = get_moscow_time()
    write_m3u(favorites, output_file, now)
    
    print(f"\n✅ Плейлист Избранное сохранён: {output_file}")
    print(f"   Всего каналов: {len(favorites)}")
    print("="*50)

if __name__ == '__main__':
    main()
