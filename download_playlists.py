#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import requests
import json
from pathlib import Path
from datetime import datetime

def remove_logos_from_line(line):
    """Удаляет атрибут tvg-logo из строки #EXTINF"""
    if line.startswith('#EXTINF'):
        return re.sub(r'\s*tvg-logo="[^"]*"', '', line)
    return line

def clean_m3u_content(content):
    """Очищает весь M3U контент от иконок"""
    lines = content.splitlines()
    cleaned_lines = []
    
    for line in lines:
        if line.startswith('#EXTINF'):
            cleaned_lines.append(remove_logos_from_line(line))
        else:
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)

def download_playlist(url, output_path, timeout=60):
    """Скачивает плейлист по ссылке и очищает от иконок"""
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
        
        # Очищаем от иконок
        cleaned_content = clean_m3u_content(content)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
        
        print(f"✅ Сохранено: {output_path} ({len(cleaned_content)} байт, иконки удалены)")
        return True, {'size': len(cleaned_content), 'status': 'success'}
        
    except requests.exceptions.Timeout:
        print(f"⏰ Таймаут: {url}")
        return False, {'status': 'timeout', 'error': 'Timeout'}
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False, {'status': 'error', 'error': str(e)}

def main():
    # ═══════════════════════════════════════════════════════════
    # 🔽 ВСЕ ИСТОЧНИКИ (7 ПЛЕЙЛИСТОВ)
    # ═══════════════════════════════════════════════════════════
    
    playlists = [
        # 1. Плейлист от Dimonovich
        {
            'url': 'https://raw.githubusercontent.com/Dimonovich/TV/Dimonovich/FREE/TV',
            'name': 'dimonovich_tv.m3u'
        },
        # 2. Плейлист ShamsTV
        {
            'url': 'http://iptvshams.ru/ShamsTV.m3u8',
            'name': 'shams_tv.m3u8'
        },
        # 3. Плейлист IPTVru (основной) - ИСПРАВЛЕНО: убран двойной слеш
        {
            'url': 'https://smolnp.github.io/IPTVru/IPTVru.m3u',
            'name': 'iptv_ru.m3u'
        },
        # 4. Плейлист IPTVstable (стабильная версия)
        {
            'url': 'https://raw.githubusercontent.com/smolnp/IPTVru/refs/heads/gh-pages/IPTVstable.m3u8',
            'name': 'iptv_stable.m3u8'
        },
        # 5. Плейлист Zabava
        {
            'url': 'https://raw.githubusercontent.com/CrocoUser/zabava-project/refs/heads/main/zabava-ef.m3u',
            'name': 'zabava_ef.m3u'
        },
        # 6. Плейлист от LoganetTV
        {
            'url': 'https://loganettv.github.io/playlists/all.m3u',
            'name': 'loganet_tv.m3u'
        },
        # 7. Плейлист от bugsfreeweb (много кино и познавательных каналов)
        {
            'url': 'https://raw.githubusercontent.com/bugsfreeweb/LiveTVCollector/refs/heads/main/LiveTV/Russia/LiveTV.m3u',
            'name': 'bugsfreeweb.m3u'
        },
    ]
    
    # ═══════════════════════════════════════════════════════════
    # Код ниже НЕ МЕНЯЙТЕ
    # ═══════════════════════════════════════════════════════════
    
    Path('./playlists').mkdir(exist_ok=True)
    
    # Удаляем старые файлы
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