
## 🐍 Обновленный `merge_m3u.py` с сохранением статистики в output

```python
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
                    'source': os.path.basename(file_path)
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
    
    # Находим все M3U файлы
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
    seen_urls = set()
    duplicates_count = 0
    total_count = 0
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
                
            all_channels.append(channel)
    
    # Сортировка каналов по названию
    if sort_channels:
        all_channels.sort(key=lambda x: x.get('info', ''))
    
    # Запись результата
    write_m3u(all_channels, output_file)
    
    # Статистика
    stats = {
        'generated': datetime.now().isoformat(),
        'input_dir': str(input_dir),
        'output_file': str(output_file),
        'total_files': len(m3u_files),
        'total_channels': total_count,
        'unique_channels': len(all_channels),
        'duplicates_removed': duplicates_count,
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
    print(f"  Источников: {len(m3u_files)}")
    print(f"✅ Результат сохранен в {output_file}")
    print("="*50)
    
    return True, stats

def write_m3u(channels, output_file):
    """Записывает каналы в M3U файл"""
    
    # Создаем директорию если её нет
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('#EXTM3U\n')
        f.write(f'# Создано: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
        f.write(f'# Всего каналов: {len(channels)}\n\n')
        
        for channel in channels:
            if channel.get('info'):
                if channel.get('source'):
                    info = channel['info']
                    if not info.endswith(']') and not info.endswith(')'):
                        info = f'{info} [source: {channel["source"]}]'
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
        
        # Выводим JSON для GitHub Actions
        print("::set-output name=stats::" + json.dumps(stats))
        
        # Также выводим в читаемом виде
        print(f"\n📊 Статистика сохранена в {stats_file}")
        print("="*50)
        print(json.dumps(stats, indent=2, ensure_ascii=False))
        print("="*50)
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
