#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import json
import argparse
import traceback
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Настройка часового пояса (Москва UTC+3)
MOSCOW_TZ = timezone(timedelta(hours=3))

def get_moscow_time():
    """Возвращает текущее время по Москве"""
    return datetime.now(MOSCOW_TZ)

def create_info_channel(update_time):
    """Создает информационный канал с датой обновления (без логотипа)"""
    info_line = f'#EXTINF:-1 group-title="📊 ИНФО",📅 Обновлено: {update_time.strftime("%d.%m.%Y %H:%M")} MSK'
    info_url = 'https://raw.githubusercontent.com/AlexanderRU44/m3u-Merger/main/output/info.m3u8'
    return {'info': info_line, 'url': info_url, 'source': 'M3U-Merger', 'has_catchup': False}

# Список групп, которые нужно исключить
EXCLUDED_GROUPS = [
    # Ранее добавленные группы
    '🔺 INFO 🔺',
    '- ИНФО -',
    'INFO',
    'Инфо',
    '↕️ Торрент ТВ ↕️',
    'Торрент ТВ',
    'Torrent TV',
    'Киргизия',
    'Узбекистан',
    'Наш Нет 🇺🇦',
    'Наш Нет',
    'Itv.uz (🇺🇿)',
    'Itv.uz',
    'ИНФОКАНАЛ',
    'Турция',
    'Туркменистан',
    'Германия',
    'Армения',
    'Болгария',
    'Украина',
    'Азербайжан',
    'Грузия',
    'XXX',
    'Сербия',
    'Словакия',
    'Хорватия',
    'Чехия',
    'Франция',
    'Италия',
    'Испания',
    'Индия',
    'Венгрия',
    'Великобритания',
    'USA',
    'Казахстан',
    'Республика Крым',  # Удаляем все каналы из этой группы
]

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

def get_group_title(info_line):
    """Извлекает название группы из строки EXTINF"""
    match = re.search(r'group-title="([^"]*)"', info_line, re.IGNORECASE)
    if match:
        return match.group(1)
    return None

def is_excluded_group(info_line):
    """Проверяет, нужно ли исключить канал по группе или названию"""
    group = get_group_title(info_line)
    if not group:
        # Если группы нет, проверяем название канала
        for excluded in EXCLUDED_GROUPS:
            if excluded.lower() in info_line.lower():
                return True
        return False
    
    for excluded in EXCLUDED_GROUPS:
        if excluded.lower() in group.lower():
            return True
    return False

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
        print(f"    🔍 Парсинг {file_path.name}...")
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        print(f"    📄 Прочитано {len(lines)} строк")
        line_count = 0
            
        for line in lines:
            line = line.strip()
            line_count += 1
            
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
        traceback.print_exc()
        
    print(f"    ✅ Найдено {len(channels)} каналов в {file_path.name}")
    return channels

def merge_m3u_files(input_dir, output_file, remove_duplicates=True, sort_channels=False):
    """Объединяет все M3U файлы из директории"""
    
    print(f"🔍 Проверка директории: {input_dir}")
    
    m3u_files = []
    for ext in ['*.m3u', '*.m3u8']:
        m3u_files.extend(Path(input_dir).glob(ext))
    
    if not m3u_files:
        print(f"❌ Не найдено M3U файлов в {input_dir}")
        print(f"📂 Содержимое {input_dir}:")
        for item in Path(input_dir).iterdir():
            print(f"  - {item.name}")
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
    excluded_count = 0
    sources = {}
    
    for file_path in m3u_files:
        print(f"📖 Чтение {file_path.name}...")
        channels = parse_m3u(file_path)
        sources[file_path.name] = len(channels)
        
        for channel in channels:
            if not channel.get('url'):
                continue
            
            if is_excluded_group(channel['info']):
                excluded_count += 1
                continue
            
            total_count += 1
            
            if remove_duplicates:
                if channel['url'] in seen_urls:
                    duplicates_count += 1
                    continue
                seen_urls.add(channel['url'])
            
            if channel.get('has_catchup', False):
                archive_count += 1
                archive_channel = channel.copy()
                if 'group-title="' in archive_channel['info']:
                    archive_channel['info'] = re.sub(
                        r'group-title="[^"]*"',
                        'group-title="📺 АРХИВНЫЕ"',
                        archive_channel['info']
                    )
                else:
                    archive_channel['info'] = archive_channel['info'].replace(
                        ',',
                        ' group-title="📺 АРХИВНЫЕ",'
                    )
                archive_channels.append(archive_channel)
                
            all_channels.append(channel)
    
    # Добавляем информационный канал с датой обновления (без логотипа)
    now = get_moscow_time()
    info_channel = create_info_channel(now)
    all_channels.insert(0, info_channel)  # Вставляем в начало
    
    if archive_channels:
        print(f"📺 Добавление {len(archive_channels)} архивных каналов в основной плейлист")
        all_channels.extend(archive_channels)
    
    if sort_channels:
        all_channels.sort(key=lambda x: x.get('info', ''))
        archive_channels.sort(key=lambda x: x.get('info', ''))
    
    try:
        print(f"💾 Запись основного плейлиста в {output_file}...")
        write_m3u(all_channels, output_file, now)
    except Exception as e:
        print(f"❌ Ошибка записи {output_file}: {e}")
        traceback.print_exc()
        return False, {}
    
    if archive_channels:
        try:
            archive_file = Path(output_file).parent / 'merged_archive.m3u'
            write_m3u(archive_channels, archive_file, now)
            print(f"📦 Архивные каналы сохранены в {archive_file}")
        except Exception as e:
            print(f"❌ Ошибка записи архивного файла: {e}")
            traceback.print_exc()
            return False, {}
    
    stats = {
        'generated': now.isoformat(),
        'input_dir': str(input_dir),
        'output_file': str(output_file),
        'total_files': len(m3u_files),
        'total_channels': total_count,
        'unique_channels': len(all_channels) - len(archive_channels) - 1,  # -1 за информационный канал
        'duplicates_removed': duplicates_count,
        'excluded_channels': excluded_count,
        'excluded_groups': EXCLUDED_GROUPS,
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
    print(f"  Уникальных: {len(all_channels) - len(archive_channels) - 1}")
    print(f"  Удалено дубликатов: {duplicates_count}")
    print(f"  🗑️ Исключено каналов: {excluded_count}")
    print(f"  📺 Каналов с архивом: {archive_count}")
    print(f"  📅 Обновлено: {now.strftime('%d.%m.%Y %H:%M')} MSK")
    print(f"  Источников: {len(m3u_files)}")
    print(f"✅ Результат сохранен в {output_file}")
    print("="*50)
    
    return True, stats

def write_m3u(channels, output_file, update_time):
    """Записывает каналы в M3U файл"""
    
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('#EXTM3U\n')
        f.write(f'# Создано: {update_time.strftime("%Y-%m-%d %H:%M:%S")} MSK\n')
        f.write(f'# Всего каналов: {len(channels)}\n')
        
        archive_count = sum(1 for ch in channels if ch.get('has_catchup', False))
        if archive_count > 0:
            f.write(f'# Каналов с архивом: {archive_count}\n')
        f.write('\n')
        
        for channel in channels:
            if channel.get('info'):
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
    
    try:
        args = parser.parse_args()
    except Exception as e:
        print(f"❌ Ошибка парсинга аргументов: {e}")
        traceback.print_exc()
        sys.exit(1)
    
    print("="*50)
    print("🚀 Запуск merge_m3u.py")
    print(f"📁 input-dir: {args.input_dir}")
    print(f"📁 output: {args.output}")
    print(f"🔧 keep-duplicates: {args.keep_duplicates}")
    print(f"🔧 sort: {args.sort}")
    print(f"🔧 generate-stats: {args.generate_stats}")
    print("="*50)
    
    if not Path(args.input_dir).exists():
        print(f"❌ Директория {args.input_dir} не найдена")
        print(f"📂 Текущая директория: {os.getcwd()}")
        sys.exit(1)
    
    try:
        success, stats = merge_m3u_files(
            args.input_dir,
            args.output,
            remove_duplicates=not args.keep_duplicates,
            sort_channels=args.sort
        )
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        traceback.print_exc()
        sys.exit(1)
    
    if not success:
        print("❌ Ошибка при объединении плейлистов")
        sys.exit(1)
    
    if args.generate_stats and stats:
        try:
            stats_file = Path(args.output).parent / 'stats.json'
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)
            
            print(f"\n📊 Статистика сохранена в {stats_file}")
            print("="*50)
            print(json.dumps(stats, indent=2, ensure_ascii=False))
            print("="*50)
        except Exception as e:
            print(f"⚠️ Не удалось сохранить статистику: {e}")
    
    print("✅ Скрипт успешно завершен")
    sys.exit(0)

if __name__ == '__main__':
    main()
