#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import os
import sys
import time
import requests
import concurrent.futures
from pathlib import Path
from datetime import datetime, timezone, timedelta

# ═══════════════════════════════════════════════════════════════
# 🔽 НАСТРОЙКИ
# ═══════════════════════════════════════════════════════════════

CHECK_TIMEOUT = 3          # Таймаут на проверку (секунд)
MAX_WORKERS = 20           # Количество параллельных проверок

# Список ключевых слов для избранного
FAVORITE_KEYWORDS = [
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
    'Amedia',
    'TV1000',
    'Viju',
    'Кинопремьера',
    'Кино ТВ',
    'Кинокомедия',
    'Кинохит',
    'Hollywood',
    'Bollywood',
    'Eurosport',
    'Setanta',
    'Наука 2.0',
    'Моя планета',
    'Охота и рыбалка',
    'Travel',
    'Приключения',
    'Cartoon Network',
    'Мульт',
    'Детский',
    'Музыка',
    'Шансон',
    'Жара',
]

MOSCOW_TZ = timezone(timedelta(hours=3))

def get_moscow_time():
    return datetime.now(MOSCOW_TZ)

def check_stream(url, timeout=CHECK_TIMEOUT):
    """Проверяет один канал"""
    if not url or not url.startswith(('http://', 'https://')):
        return False
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=timeout, stream=True)
        
        if response.status_code != 200:
            return False
        
        chunk = response.raw.read(1024)
        return bool(chunk)
        
    except Exception:
        return False

def check_all_parallel(channels, max_workers=MAX_WORKERS):
    """Проверяет все каналы параллельно"""
    total = len(channels)
    print(f"🚀 Параллельная проверка {total} каналов (потоков: {max_workers})")
    
    working = []
    dead = []
    checked = 0
    
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_channel = {
            executor.submit(check_stream, ch['url']): ch 
            for ch in channels
        }
        
        for future in concurrent.futures.as_completed(future_to_channel):
            ch = future_to_channel[future]
            checked += 1
            
            try:
                is_working = future.result(timeout=CHECK_TIMEOUT + 2)
                if is_working:
                    working.append(ch)
                else:
                    dead.append(ch)
            except:
                dead.append(ch)
            
            if checked % 10 == 0 or checked == total:
                elapsed = time.time() - start_time
                rate = checked / elapsed if elapsed > 0 else 0
                sys.stdout.write(f"\r  [{checked}/{total}] ✅ {len(working)} | ❌ {len(dead)} | {rate:.1f} каналов/сек")
                sys.stdout.flush()
    
    print()
    return working, dead

def is_favorite(info_line):
    if not info_line:
        return False
    info_lower = info_line.lower()
    for keyword in FAVORITE_KEYWORDS:
        if keyword.lower() in info_lower:
            return True
    return False

def get_channel_name(info_line):
    match = re.search(r',([^,]*)$', info_line)
    if match:
        return match.group(1).strip()
    match = re.search(r'tvg-name="([^"]*)"', info_line, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return 'Без названия'

def parse_m3u(file_path):
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

def write_m3u(channels, output_file, update_time, checked_count=None, dead_count=None):
    """Записывает каналы в M3U файл"""
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
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
            f.write(f'# Проверено: {checked_count}\n')
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
                    info = info.replace(',', f' group-title="{group_name}",')
                f.write(info + '\n')
                f.write(ch['url'] + '\n')
            f.write('\n')

def main():
    print("="*50)
    print("❤️  СОЗДАНИЕ ПЛЕЙЛИСТА ИЗБРАННОЕ")
    print("="*50)
    print(f"⚡ Параллельная проверка: {MAX_WORKERS} потоков")
    print(f"⏱️  Таймаут: {CHECK_TIMEOUT} сек")
    print("="*50)
    
    input_file = './output/merged.m3u'
    output_file = './output/favorites.m3u'
    
    if not Path(input_file).exists():
        print(f"❌ Файл {input_file} не найден!")
        sys.exit(1)
    
    print(f"📖 Чтение: {input_file}")
    channels = parse_m3u(input_file)
    print(f"📊 Всего каналов: {len(channels)}")
    
    # Фильтруем избранные
    favorites = [ch for ch in channels if is_favorite(ch['info'])]
    total_favorites = len(favorites)
    print(f"❤️ Найдено избранных каналов: {total_favorites}")
    
    if not favorites:
        print("⚠️ Избранные каналы не найдены!")
        print("   Проверьте список FAVORITE_KEYWORDS в create_favorites.py")
        sys.exit(0)
    
    # Параллельная проверка
    print("\n" + "="*50)
    print("🔍 ПРОВЕРКА КАНАЛОВ")
    print("="*50)
    
    working, dead = check_all_parallel(favorites)
    
    print(f"\n📊 Результат:")
    print(f"  ✅ Работает: {len(working)}")
    print(f"  ❌ Не работает: {len(dead)}")
    print(f"  📊 Процент рабочих: {round(len(working)/(len(working)+len(dead))*100, 1) if (len(working)+len(dead)) > 0 else 0}%")
    
    # Сохраняем только рабочие каналы
    if working:
        now = get_moscow_time()
        write_m3u(working, output_file, now, 
                 checked_count=len(working)+len(dead), 
                 dead_count=len(dead))
        print(f"\n✅ Плейлист сохранён: {output_file}")
        print(f"   Всего каналов: {len(working)}")
    else:
        print("\n❌ Нет рабочих каналов!")
    
    print("\n" + "="*50)
    print("✅ Готово!")
    print("="*50)

if __name__ == '__main__':
    main()
