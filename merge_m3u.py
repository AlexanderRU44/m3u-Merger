#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

def extract_url(line):
    """Извлекает URL из строки M3U"""
    line = line.strip()
    if line.startswith('#') or not line:
        return None
    
    url_pattern = r'https?://[^\s]+'
    match = re.search(url_pattern, line)
    if match:
        return match.group(0)
    return None

def has_catchup(info_line):
    """Проверяет, есть ли у канала поддержка архива"""
    if not info_line:
        return False
    
    catchup_patterns = [
        r'catchup="[^"]*"',
        r'catchup-days="\d+"',
        r'catchup-source="[^"]*"',
        r'catchup-type="[^"]*"',
        r' tvg-archive="\d+"',
    ]
    
    for pattern in catchup_patterns:
        if re.search(pattern, info_line, re.IGNORECASE):
            return True
    return False

def get_catchup_info(info_line):
    """Извлекает информацию об архиве из строки"""
    info = {
        'has_catchup': False,
        'catchup_type': None,
        'catchup_days': None,
        'catchup_source': None
    }
    
    match = re.search(r'catchup="([^"]*)"', info_line, re.IGNORECASE)
    if match:
        info['has_catchup'] = True
        info['catchup_type'] = match.group(1)
    
    match = re.search(r'catchup-days="(\d+)"', info_line, re.IGNORECASE)
    if match:
        info['has_catchup'] = True
        info['catchup_days'] = int(match.group(1))
    
    match = re.search(r'catchup-source="([^"]*)"', info_line, re.IGNORECASE)
    if match:
        info['has_catchup'] = True
        info['catchup_source'] = match.group(1)
    
    match = re.search(r'tvg-archive="(\d+)"', info_line, re.IGNORECASE)
    if match:
        info['has_catchup'] = True
        info['catchup_days'] = int(match.group(1))
    
    return info

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
                catchup_info = get_catchup_info(line)
                current_channel = {
                    'info': line,
                    'url': None,
                    'source': os.path.basename(file_path),
                    'has_catchup': catchup_info['has_catchup'],
                    'catchup_type': catchup_info['catchup_type'],
                    'catchup_days': catchup_info['catchup_days'],
                    'catchup_source': catchup_info['catchup_source']
                }
            elif current_channel and not line.startswith('#'):
                url = extract_url(line)
                if url:
                    current_channel['url'] = url
                    channels.append(current_channel)
                    current_channel = None
            elif line.startswith('#') and not line.startswith('#EXTINF'):
                if current_channel:
                    current_channel['info'] += '\n' + line
                    
    except Exception as e:
        print(f"⚠️ Ошибка при чтении {file_path}: {e}")
        
    return channels

def merge_m3u_files(input_dir, output_file, remove_duplicates=True, sort_channels=False):
    """Объединяет все M3U файлы из директории"""
    
    m3u_files = []
    for ext in ['*.m3u', '*.m3u8']:
        m3u_files.extend(Path(input_dir).glob(ext))
    
    if not m3u_files:
        print(f"❌ Не найдено M3U файлов в {input_dir}")
        return False, {}
    
    print(f"📂 Найдено {len(m3u_files)} файлов:")
    for f in m3u_files:
        size = f.stat().st_size
        print(f"  - {f.name} ({size} байт)")
    
    all_channels = []
    archive_channels = []
    seen_urls = set()
    duplicates_count = 0
    total_count = 0
    archive_count = 0
    sources = {}
    
    for file_path in m3u_files:
        print(f"📖 Чтение {file_path.name}...")
        channels = parse_m3u(file_path)
        sources[file_path.name] = len(channels)
        
        for channel in channels:
            if not channel['url']:
                continue
            
            total_count += 1
            
            if remove_duplicates:
                if channel['url'] in seen_urls:
                    duplicates_count += 1
                    continue
                seen_urls.add(channel['url'])
            
            # Если есть архив - добавляем в список архивных
            if channel.get('has_catchup', False):
                archive_count += 1
                # Копируем канал и добавляем группу "📺 АРХИВНЫЕ"
                archive_channel = channel.copy()
                # Добавляем group-title если его нет, или заменяем
                if 'group-title="' in archive_channel['info']:
                    # Заменяем существующую группу
                    archive_channel['info'] = re.sub(
                        r'group-title="[^"]*"',
                        'group-title="📺 АРХИВНЫЕ"',
                        archive_channel['info']
                    )
                else:
                    # Добавляем группу перед названием канала
                    archive_channel['info'] = archive_channel['info'].replace(
                        ',',
                        ' group-title="📺 АРХИВНЫЕ",'
                    )
                archive_channels.append(archive_channel)
                
            all_channels.append(channel)
    
    # Сортировка
    if sort_channels:
        all_channels.sort(key=lambda x: x.get('info', ''))
        archive_channels.sort(key=lambda x: x.get('info', ''))
    
    # Запись основного плейлиста
    write_m3u(all_channels, output_file)
    
    # Сохраняем архивные каналы в отдельный файл
    if archive_channels:
        archive_file = Path(output_file).parent / 'merged_archive.m3u'
        write_m3u(archive_channels, archive_file)
        print(f"📦 Архивные каналы сохранены в {archive_file}")
    
    # Статистика
    stats = {
        'generated': datetime.now().isoformat(),
        'input_dir': str(input_dir),
        'output_file': str(output_file),
        'total_files': len(m3u_files),
        'total_channels': total_count,
        'unique_channels': len(all_channels),
        'duplicates_removed': duplicates_count,
        'archive_channels': archive_count,
        'sources': sources,
        'file_sizes': {
            str(f): f.stat().st_size for f in m3u_files
        },
        'output_size': Path(output_file).stat().st_size if Path(output_file).exists() else 0
    }
    
    print("\n" + "="*50)
    print(f"📊 Статистика:")
    print(f"  Всего каналов: {total_count}")
    print(f"  Уникальных: {len(all_channels)}")
    print(f"  Удалено дубликатов: {duplicates_count}")
    print(f"  📺 Каналов с архивом: {archive_count}")
    print(f"  Источников: {len(m3u_files)}")
    print(f"✅ Результат сохранен в {output_file}")
    print("="*50)
    
    return True, stats

def write_m3u(channels, output_file):
    """Записывает каналы в M3U файл"""
    
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('#EXTM3U\n')
        f.write(f'# Создано: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
        f.write(f'# Всего каналов: {len(channels)}\n')
        
        archive_count = sum(1 for ch in channels if ch.get('has_catchup', False))
        if archive_count > 0:
            f.write(f'# Каналов с архивом: {archive_count}\n')
        f.write('\n')
        
        for channel in channels:
            if channel.get('info'):
                if channel.get('source'):
                    info = channel['info']
                    if not info.endswith(']') and not info.endswith(')'):
                        info = f'{info} [source: {channel["source"]}]'
                    
                    # Добавляем маркер архива
                    if channel.get('has_catchup', False):
                        days = channel.get('catchup_days', '?')
                        info = f'{info} 📺АРХИВ {days}д'
                    
                    f.write(info + '\n')
                else:
                    f.write(channel['info'] + '\n')
            if channel.get('url'):
                f.write(channel['url'] + '\n')

def main():
    parser = argparse.ArgumentParser(
        description='Объединение M3U плейлистов из GitHub'
    )
    
    parser.add_argument(
        '--input-dir',
        default='./playlists',
        help='Директория с исходными плейлистами'
    )
    
    parser.add_argument(
        '--output',
        default='./output/merged.m3u',
        help='Выходной файл'
    )
    
    parser.add_argument(
        '--keep-duplicates',
        action='store_true',
        help='Не удалять дубликаты'
    )
    
    parser.add_argument(
        '--sort',
        action='store_true',
        help='Сортировать каналы по названию'
    )
    
    parser.add_argument(
        '--generate-stats',
        action='store_true',
        help='Сгенерировать JSON со статистикой'
    )
    
    args = parser.parse_args()
    
    if not Path(args.input_dir).exists():
        print(f"❌ Директория {args.input_dir} не найдена")
        sys.exit(1)
    
    success, stats = merge_m3u_files(
        args.input_dir,
        args.output,
        remove_duplicates=not args.keep_duplicates,
        sort_channels=args.sort
    )
    
    if success and args.generate_stats and stats:
        stats_file = Path(args.output).parent / 'stats.json'
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        
        print(f"\n📊 Статистика сохранена в {stats_file}")
        print("="*50)
        print(json.dumps(stats, indent=2, ensure_ascii=False))
        print("="*50)
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
