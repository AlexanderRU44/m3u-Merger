#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta

# ═══════════════════════════════════════════════════════════════
# 🔽 СПИСОК КЛЮЧЕВЫХ СЛОВ ДЛЯ ИЗБРАННОГО
# ═══════════════════════════════════════════════════════════════
# Каналы, названия которых содержат эти слова, попадут в Избранное
# Группой будет полное название канала (например, "Россия 1")

FAVORITE_KEYWORDS = [
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
    'Мульт',
    'Детский',
    
    # === Музыка ===
    'Музыка',
    'Шансон',
    'Жара',
    
    # ⬇️ ДОБАВЬТЕ СВОИ КЛЮЧЕВЫЕ СЛОВА ЗДЕСЬ
    # 'Мой любимый канал',
]

# Настройка часового пояса (Москва UTC+3)
MOSCOW_TZ = timezone(timedelta(hours=3))

def get_moscow_time():
    return datetime.now(MOSCOW_TZ)

def is_favorite(info_line):
    """Проверяет, является ли канал избранным по ключевым словам"""
    if not info_line:
        return False
    
    info_lower = info_line.lower()
    
    for keyword in FAVORITE_KEYWORDS:
        if keyword.lower() in info_lower:
            return True
    
    return False

def get_channel_name(info_line):
    """Извлекает название канала из строки EXTINF"""
    # Ищем название после последней запятой
    match = re.search(r',([^,]*)$', info_line)
    if match:
        return match.group(1).strip()
    
    # Если не нашли, пробуем найти tvg-name
    match = re.search(r'tvg-name="([^"]*)"', info_line, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    return 'Без названия'

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

def write_m3u_with_groups(channels, output_file, update_time):
    """Записывает каналы в M3U файл с группировкой по названию"""
    
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Группируем каналы по названию
    groups = {}
    
    for ch in channels:
        name = get_channel_name(ch['info'])
        # Убираем всё после запятой (версии, HD, и т.д.)
        # Например: "Россия 1 HD" → "Россия 1"
        base_name = re.sub(r'\s*(HD|FHD|UHD|4K|\+.*|\(.*\))$', '', name, flags=re.IGNORECASE).strip()
        
        # Если название сильно изменилось, оставляем как есть
        if not base_name:
            base_name = name
        
        if base_name not in groups:
            groups[base_name] = []
        groups[base_name].append(ch)
    
    print(f"📂 Создано групп: {len(groups)}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('#EXTM3U\n')
        f.write(f'# ❤️ Избранное — {update_time.strftime("%Y-%m-%d %H:%M:%S")} MSK\n')
        f.write(f'# Всего каналов: {len(channels)}\n')
        f.write(f'# Групп: {len(groups)}\n\n')
        
        # Сортируем группы по названию
        for group_name in sorted(groups.keys()):
            channel_list = groups[group_name]
            
            # Добавляем комментарий-разделитель для группы
            f.write(f'# === ГРУППА: {group_name} ===\n')
            
            for ch in channel_list:
                # Изменяем или добавляем group-title
                info = ch['info']
                
                # Удаляем старый group-title, если есть
                info = re.sub(r'group-title="[^"]*"\s*', '', info)
                
                # Добавляем новый group-title
                if 'group-title="' not in info:
                    info = info.replace(
                        ',',
                        f' group-title="{group_name}",'
                    )
                
                f.write(info + '\n')
                f.write(ch['url'] + '\n')
            
            f.write('\n')  # Пустая строка между группами

def main():
    input_file = './output/merged.m3u'
    output_file = './output/favorites.m3u'
    
    print("="*50)
    print("❤️  СОЗДАНИЕ ПЛЕЙЛИСТА ИЗБРАННОЕ (С ГРУППАМИ)")
    print("="*50)
    
    if not Path(input_file).exists():
        print(f"❌ Файл {input_file} не найден")
        print("   Сначала запустите основной workflow merge-playlists.yml")
        return
    
    print(f"📖 Чтение: {input_file}")
    channels = parse_m3u(input_file)
    print(f"📊 Всего каналов в merged.m3u: {len(channels)}")
    
    # Фильтруем избранные каналы
    favorites = []
    for ch in channels:
        if is_favorite(ch['info']):
            favorites.append(ch)
    
    print(f"❤️ Найдено избранных каналов: {len(favorites)}")
    
    if not favorites:
        print("⚠️ Избранные каналы не найдены!")
        print("   Проверьте список FAVORITE_KEYWORDS в create_favorites.py")
        return
    
    # Показываем статистику по группам
    groups = {}
    for ch in favorites:
        name = get_channel_name(ch['info'])
        base_name = re.sub(r'\s*(HD|FHD|UHD|4K|\+.*|\(.*\))$', '', name, flags=re.IGNORECASE).strip()
        if base_name not in groups:
            groups[base_name] = 0
        groups[base_name] += 1
    
    print("\n📂 Группы каналов:")
    for group_name, count in sorted(groups.items()):
        print(f"  - {group_name}: {count} каналов")
    
    # Сохраняем с группировкой
    now = get_moscow_time()
    write_m3u_with_groups(favorites, output_file, now)
    
    print(f"\n✅ Плейлист Избранное сохранён: {output_file}")
    print(f"   Всего каналов: {len(favorites)}")
    print(f"   Групп: {len(groups)}")
    print("="*50)

if __name__ == '__main__':
    main()
