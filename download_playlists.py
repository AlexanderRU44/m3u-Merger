#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
import argparse
from pathlib import Path
from datetime import datetime

def download_playlist(url, output_path, timeout=30):
    """Скачивает плейлист по ссылке"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        print(f"📥 Скачивание: {url}")
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        # Сохраняем файл
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        print(f"✅ Сохранено: {output_path}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка скачивания {url}: {e}")
        return False

def main():
    # СПИСОК ВАШИХ ССЫЛОК НА ПЛЕЙЛИСТЫ
    playlists = [
        {
            'url': 'http://iptvshams.ru/ShamsTV.m3u8',
            'name': 'source1.m3u'
        },
        {
            'url': 'https://raw.githubusercontent.com/Dimonovich/TV/Dimonovich/FREE/TV',
            'name': 'source2.m3u8'
        },
        # ДОБАВЬТЕ СВОИ ССЫЛКИ ЗДЕСЬ
        {
            'url': 'ВАША_ССЫЛКА_1',
            'name': 'source1.m3u'
        },
        {
            'url': 'ВАША_ССЫЛКА_2',
            'name': 'source2.m3u8'
        },
    ]
    
    # Создаем папку playlists если её нет
    Path('./playlists').mkdir(exist_ok=True)
    
    print("="*50)
    print(f"📥 Загрузка плейлистов ({len(playlists)} источников)")
    print("="*50)
    
    success_count = 0
    for playlist in playlists:
        output_path = f"./playlists/{playlist['name']}"
        if download_playlist(playlist['url'], output_path):
            success_count += 1
    
    print("="*50)
    print(f"✅ Загружено: {success_count}/{len(playlists)}")
    print("="*50)

if __name__ == '__main__':
    main()
