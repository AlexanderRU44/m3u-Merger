#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import os
import sys
import time
import requests
from pathlib import Path
from datetime import datetime, timezone, timedelta

# ═══════════════════════════════════════════════════════════════
# 🔽 НАСТРОЙКИ
# ═══════════════════════════════════════════════════════════════

# Список ключевых слов для избранного
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
]

# Настройки проверки
CHECK_TIMEOUT = 5          # Таймаут на проверку канала (секунд)
CHECK_DELAY = 0.5          # Задержка между проверками (секунд)

# Настройка часового пояса (Москва UTC+3)
MOSCOW_TZ = timezone(timedelta(hours=3))

def get_moscow_time():
    return datetime.now(MOSCOW_TZ)

def check_stream(url, timeout=CHECK_TIMEOUT):
    """
    Проверяет, отвечает ли стрим-сервер.
    Возвращает True, если удалось получить данные.
    """
    if not url or not url.startswith(('http://', 'https://')):
        return False
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=timeout, stream=True)
        
        if response.status_code != 200:
            return False
        
        # Пробуем прочитать первые 1024 байта
        chunk = response.raw.read(1024)
        return bool(chunk)
        
    except Exception:
        return False

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
    match = re.search(r',([^,]*)$', info_line)
    if match:
        return match.group(1).strip()
    
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

def write_m3u_with_groups(channels, output_file, update_time, checked_count=None, dead_count=None):
    """Записывает каналы в M3U файл с группировкой по названию"""
    
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Группируем каналы по названию
    groups = {}
    
    for ch in channels:
        name = get_channel_name(ch['info'])
        base_name = re.sub(r'\s*(HD|FHD|UHD|4K|\+.*|\(.*\))$', '', name, flags=re.IGNORECASE).strip()
        
        if not base_name:
            base_name = name
        
        if base_name not in groups:
            groups[base_name] = []
        groups[base_name].append(ch)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('#EXTM3U\n')
        f.write(f'# ❤️ Избранное — {update_time.strftime("%Y-%m-%d %H:%M:%S")} MSK\n')
        f.write(f'# Всего каналов: {len(channels)}\n')
        f.write(f'# Групп: {len(groups)}\n')
        
        if checked_count is not None:
            f.write(f'# Проверено каналов: {checked_count}\n')
        if dead_count is not None:
            f.write(f'# Удалено нерабочих: {dead_count}\n')
        
        f.write('\n')
        
        for group_name in sorted(groups.keys()):
            channel_list = groups[group_name]
            f.write(f'# === ГРУППА: {group_name} ===\n')
            
            for ch in channel_list:
                info = ch['info']
                info = re.sub(r'group-title="[^"]*"\s*', '', info)
                
                if 'group-title="' not in info:
                    info = info.replace(
                        ',',
                        f' group-title="{group_name}",'
                    )
                
                f.write(info + '\n')
                f.write(ch['url'] + '\n')
            
            f.write('\n')

def main():
    input_file = './output/merged.m3u'
    output_file = './output/favorites.m3u'
    output_file_checked = './output/favorites_checked.m3u'
    
    print("="*50)
    print("❤️  СОЗДАНИЕ ПЛЕЙЛИСТА ИЗБРАННОЕ")
    print("="*50)
    
    if not Path(input_file).exists():
        print(f"❌ Файл {input_file} не найден")
        print("   Сначала запустите основной workflow merge-playlists.yml")
        return
    
    print(f"📖 Чтение: {input_file}")
    channels = parse_m3u(input_file)
    print(f"📊 Всего каналов в merged.m3u: {len(channels)}")
    
    # 1. Фильтруем избранные каналы
    favorites = []
    for ch in channels:
        if is_favorite(ch['info']):
            favorites.append(ch)
    
    total_favorites = len(favorites)
    print(f"❤️ Найдено избранных каналов: {total_favorites}")
    
    if not favorites:
        print("⚠️ Избранные каналы не найдены!")
        print("   Проверьте список FAVORITE_KEYWORDS в create_favorites.py")
        return
    
    # 2. Сохраняем все избранные (без проверки)
    now = get_moscow_time()
    write_m3u_with_groups(favorites, output_file, now)
    print(f"✅ Сохранены все избранные: {output_file}")
    
    # 3. Проверяем ВСЕ каналы на работоспособность
    print("\n" + "="*50)
    print("🔍 ПРОВЕРКА РАБОТОСПОСОБНОСТИ ВСЕХ КАНАЛОВ")
    print("="*50)
    print(f"📊 Всего к проверке: {total_favorites} каналов")
    print(f"⏱️  Примерное время: ~{round(total_favorites * (CHECK_TIMEOUT + CHECK_DELAY) / 60, 1)} минут")
    print("-"*50)
    
    working_channels = []
    dead_channels = []
    checked_count = 0
    
    for i, ch in enumerate(favorites, 1):
        # Показываем прогресс
        name = get_channel_name(ch['info'])
        sys.stdout.write(f"\r  [{i}/{total_favorites}] Проверка: {name[:35]}...")
        sys.stdout.flush()
        
        is_working = check_stream(ch['url'])
        checked_count += 1
        
        if is_working:
            working_channels.append(ch)
        else:
            dead_channels.append(ch)
        
        # Пауза между проверками
        time.sleep(CHECK_DELAY)
    
    print(f"\n\n📊 Результат проверки:")
    print(f"  ✅ Проверено: {checked_count}")
    print(f"  📺 Работает: {len(working_channels)}")
    print(f"  ❌ Не работает: {len(dead_channels)}")
    print(f"  📊 Процент рабочих: {round(len(working_channels)/checked_count*100, 1) if checked_count > 0 else 0}%")
    
    # 4. Сохраняем только рабочие каналы
    if working_channels:
        write_m3u_with_groups(
            working_channels, 
            output_file_checked, 
            now,
            checked_count=checked_count,
            dead_count=len(dead_channels)
        )
        print(f"\n✅ Сохранены только рабочие каналы: {output_file_checked}")
        print(f"   Всего рабочих каналов: {len(working_channels)}")
    else:
        print("\n❌ Нет рабочих каналов!")
    
    # 5. Показываем список нерабочих каналов (первые 10)
    if dead_channels:
        print("\n📋 Примеры нерабочих каналов (первые 10):")
        for i, ch in enumerate(dead_channels[:10], 1):
            name = get_channel_name(ch['info'])
            print(f"  {i}. {name[:50]}")
        if len(dead_channels) > 10:
            print(f"  ... и ещё {len(dead_channels) - 10} каналов")
    
    print("\n" + "="*50)
    print("✅ Готово!")
    print("="*50)

if __name__ == '__main__':
    main()
