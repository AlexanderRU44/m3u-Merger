#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import argparse
from pathlib import Path
from urllib.parse import urlparse

def extract_url(line):
    """Извлекает URL из строки M3U"""
    line = line.strip()
    if line.startswith('#') or not line:
        return None
    
    # Ищем URL в строке
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
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        for line in lines:
            line = line.strip()
            
            if not line:
                continue
                
            if line.startswith('#EXTINF'):
                # Сохраняем информацию о канале
                current_channel = {
                    'info': line,
                    'url': None,
                    'source': file_path
                }
            elif current_channel and not line.startswith('#'):
                # Это URL
                url = extract_url(line)
                if url:
                    current_channel['url'] = url
                    channels.append(current_channel)
                    current_channel = None
            elif line.startswith('#') and not line.startswith('#EXTINF'):
                # Другие комментарии (например, #EXTM3U)
                if current_channel:
                    current_channel['info'] += '\n' + line
                    
    except Exception as e:
        print(f"Ошибка при чтении {file_path}: {e}")
        
    return channels

def merge_m3u_files(input_files, output_file, remove_duplicates=True):
    """Объединяет несколько M3U файлов"""
    
    all_channels = []
    seen_urls = set()
    duplicates_count = 0
    
    print(f"Обработка {len(input_files)} файлов...")
    
    for file_path in input_files:
        if not os.path.exists(file_path):
            print(f"Предупреждение: файл {file_path} не найден")
            continue
            
        print(f"  Чтение {file_path}...")
        channels = parse_m3u(file_path)
        
        for channel in channels:
            if not channel['url']:
                continue
                
            # Проверка на дубликаты
            if remove_duplicates:
                if channel['url'] in seen_urls:
                    duplicates_count += 1
                    continue
                seen_urls.add(channel['url'])
                
            all_channels.append(channel)
    
    print(f"Найдено каналов: {len(all_channels)}")
    if remove_duplicates:
        print(f"Удалено дубликатов: {duplicates_count}")
    
    # Запись результата
    write_m3u(all_channels, output_file)
    print(f"✅ Результат сохранен в {output_file}")

def write_m3u(channels, output_file):
    """Записывает каналы в M3U файл"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('#EXTM3U\n')
        
        for channel in channels:
            if channel.get('info'):
                f.write(channel['info'] + '\n')
            if channel.get('url'):
                f.write(channel['url'] + '\n')

def get_input_files(file_patterns):
    """Получает список файлов по шаблонам"""
    files = []
    for pattern in file_patterns:
        # Если это директория - берем все .m3u файлы
        if os.path.isdir(pattern):
            for root, _, filenames in os.walk(pattern):
                for filename in filenames:
                    if filename.endswith('.m3u') or filename.endswith('.m3u8'):
                        files.append(os.path.join(root, filename))
        else:
            # Если это файл или шаблон
            matched = list(Path('.').glob(pattern))
            if matched:
                files.extend([str(p) for p in matched])
            elif os.path.isfile(pattern):
                files.append(pattern)
                
    return sorted(set(files))

def main():
    parser = argparse.ArgumentParser(
        description='Объединение M3U плейлистов с удалением дубликатов'
    )
    
    parser.add_argument(
        'inputs',
        nargs='+',
        help='Входные файлы или директории (поддерживает wildcards)'
    )
    
    parser.add_argument(
        '-o', '--output',
        default='merged_playlist.m3u',
        help='Выходной файл (по умолчанию: merged_playlist.m3u)'
    )
    
    parser.add_argument(
        '--keep-duplicates',
        action='store_true',
        help='Не удалять дубликаты'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Подробный вывод'
    )
    
    args = parser.parse_args()
    
    # Получаем список файлов
    input_files = get_input_files(args.inputs)
    
    if not input_files:
        print("❌ Не найдено файлов для обработки")
        sys.exit(1)
    
    if args.verbose:
        print("Входные файлы:")
        for f in input_files:
            print(f"  {f}")
    
    # Объединяем
    merge_m3u_files(
        input_files,
        args.output,
        remove_duplicates=not args.keep_duplicates
    )

if __name__ == '__main__':
    main()
