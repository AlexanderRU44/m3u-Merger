#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
import json
from pathlib import Path
from datetime import datetime

def download_playlist(url, output_path, timeout=60):
    """Скачивает плейлист по ссылке"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        print(f"📥 Скачивание: {url}")
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        content = response.text
        if not any(marker in content.lower() for marker in ['#extm3u', '#extinf']):
            print(f"⚠️ Предупреждение: возможно не M3U файл")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Сохранено: {output_path} ({len(content)} байт)")
        return True, {'size': len(content), 'status': 'success'}
        
    except requests.exceptions.Timeout:
        print(f"⏰ Таймаут: {url}")
        return False, {'status': 'timeout', 'error': 'Timeout'}
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False, {'status': 'error', 'error': str(e)}

def main():
    # ═══════════════════════════════════════════════════════════
    # 🔽 ВАШИ ССЫЛКИ НА ПЛЕЙЛИСТЫ (ДОБАВЛЕНЫ)
    # ═══════════════════════════════════════════════════════════
    
    playlists = [
        # 1. Плейлист от Dimonovich (с большим количеством каналов)
        {
            'url': 'https://raw.githubusercontent.com/Dimonovich/TV/Dimonovich/FREE/TV',
            'name': 'dimonovich_tv.m3u'
        },
        
        # 2. Плейлист ShamsTV
        {
            'url': 'http://iptvshams.ru/ShamsTV.m3u8',
            'name': 'shams_tv.m3u8'
        },
        
        # 3. Плейлист IPTVru
        {
            'url': 'https://smolnp.github.io/IPTVru//IPTVru.m3u',
            'name': 'iptv_ru.m3u'
        },
        
        # 4. Дополнительный плейлист (опционально)
        # {
        #     'url': 'https://iptv-org.github.io/iptv/index.m3u',
        #     'name': 'iptv_org.m3u'
        # },
    ]
    
    # ═══════════════════════════════════════════════════════════
    # Код ниже НЕ МЕНЯЙТЕ
    # ═══════════════════════════════════════════════════════════
    
    # Создаем папку
    Path('./playlists').mkdir(exist_ok=True)
    
    # Удаляем старые файлы (кроме README.md)
    for old_file in Path('./playlists').glob('*.m3u*'):
        if old_file.name != 'README.md':
            old_file.unlink()
            print(f"🗑️ Удален старый файл: {old_file.name}")
    
    print("="*60)
    print(f"📥 Загрузка плейлистов ({len(playlists)} источников)")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    if not playlists:
        print("❌ Нет ссылок для скачивания!")
        print("💡 Добавьте ссылки в массив 'playlists' в файле download_playlists.py")
        print("📝 Создаю тестовый файл для проверки...")
        
        # Создаем тестовый файл, чтобы скрипт не падал
        with open('./playlists/test.m3u', 'w', encoding='utf-8') as f:
            f.write('#EXTM3U\n')
            f.write('#EXTINF:-1,Test Channel\n')
            f.write('http://example.com/test\n')
        return
    
    success_count = 0
    results = {}
    
    for i, playlist in enumerate(playlists, 1):
        print(f"\n[{i}/{len(playlists)}]")
        output_path = f"./playlists/{playlist['name']}"
        success, info = download_playlist(playlist['url'], output_path)
        if success:
            success_count += 1
        results[playlist['name']] = {
            'url': playlist['url'],
            'success': success,
            'info': info
        }
    
    print("\n" + "="*60)
    print(f"📊 Результат: {success_count}/{len(playlists)} загружено")
    print("="*60)
    
    # Сохраняем статистику
    with open('./playlists/download_stats.json', 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total': len(playlists),
            'success': success_count,
            'results': results
        }, f, indent=2, ensure_ascii=False)
    
    # Сохраняем список источников
    with open('./playlists/sources.txt', 'w', encoding='utf-8') as f:
        f.write(f"# Источники плейлистов\n")
        f.write(f"# Обновлено: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Всего: {len(playlists)}, Загружено: {success_count}\n\n")
        for playlist in playlists:
            status = "✅" if results.get(playlist['name'], {}).get('success') else "❌"
            f.write(f"{status} {playlist['url']} -> {playlist['name']}\n")

if __name__ == '__main__':
    main()
