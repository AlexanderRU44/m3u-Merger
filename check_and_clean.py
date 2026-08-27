#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import re
import time
import requests
from pathlib import Path
from datetime import datetime

def check_stream(url, timeout=3):
    """Проверяет, отвечает ли стрим-сервер."""
    if not url or not url.startswith(('http://', 'https://')):
        return False
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=timeout, stream=True)
        if response.status_code != 200:
            return False
        chunk = response.raw.read(1024)
        return bool(chunk)
    except Exception:
        return False

def clean_playlist(input_file, output_file, max_checks=500):
    """
    Проверяет каналы в плейлисте и сохраняет только рабочие.
    max_checks — ограничение на количество проверяемых каналов (чтобы не превысить лимит времени).
    """
    if not Path(input_file).exists():
        print(f"❌ Файл {input_file} не найден")
        return

    print(f"📖 Чтение {input_file}...")
    with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    print(f"📊 Найдено {len(lines)} строк")
    
    working_channels = []
    dead_count = 0
    checked_count = 0
    
    # Заголовки плейлиста
    header = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('#EXTINF'):
            break
        header.append(line)
        i += 1

    # Обрабатываем каналы
    channels_to_check = []
    current_channel = None
    
    for i in range(i, len(lines)):
        line = lines[i].strip()
        if line.startswith('#EXTINF'):
            current_channel = {'info': line, 'url': None}
        elif current_channel and line.startswith(('http://', 'https://')):
            current_channel['url'] = line
            channels_to_check.append(current_channel)
            current_channel = None

    total = len(channels_to_check)
    print(f"📺 Найдено каналов для проверки: {total}")
    
    # Проверяем каналы
    for idx, ch in enumerate(channels_to_check):
        if checked_count >= max_checks:
            print(f"⏹️ Достигнут лимит проверок ({max_checks})")
            break
            
        sys.stdout.write(f"\r  [{idx+1}/{total}] Проверка...")
        sys.stdout.flush()
        
        is_working = check_stream(ch['url'])
        checked_count += 1
        
        if is_working:
            working_channels.append(ch)
        else:
            dead_count += 1
            
        time.sleep(0.3)  # Пауза, чтобы не перегружать серверы

    print(f"\n✅ Проверено: {checked_count}, 💀 Мертвых: {dead_count}, 📺 Живых: {len(working_channels)}")

    # Сохраняем результат
    with open(output_file, 'w', encoding='utf-8') as f:
        # Записываем заголовок
        for h in header:
            if h:
                f.write(h + '\n')
        # Записываем рабочие каналы
        for ch in working_channels:
            f.write(ch['info'] + '\n')
            f.write(ch['url'] + '\n')

    print(f"✅ Чистый плейлист сохранен в {output_file}")

if __name__ == '__main__':
    input_file = './output/merged.m3u'
    output_file = './output/merged_clean.m3u'
    
    # Проверяем максимум 300 каналов (около 2-3 минут работы)
    clean_playlist(input_file, output_file, max_checks=300)
