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
# 🔽 НАСТРОЙКИ ПРОВЕРКИ
# ═══════════════════════════════════════════════════════════════

CHECK_TIMEOUT = 3          # Таймаут на проверку (секунд)
MAX_WORKERS = 20           # Количество параллельных проверок
CHECK_DELAY = 0            # Задержка между проверками

# ═══════════════════════════════════════════════════════════════
# 🔽 ГРУППЫ, КОТОРЫЕ НЕ ПРОВЕРЯЕМ НА РАБОТОСПОСОБНОСТЬ
# ═══════════════════════════════════════════════════════════════

SKIP_CHECK_GROUPS = [
    'Wink (VPN 🇷🇺)',
]

# ═══════════════════════════════════════════════════════════════
# 🔽 ГРУППА, КОТОРУЮ ПЕРЕМЕЩАЕМ В АРХИВ
# ═══════════════════════════════════════════════════════════════

ARCHIVE_SOURCE_GROUP = 'Wink (VPN 🇷🇺)'

# ═══════════════════════════════════════════════════════════════
# 🔽 ПРАВИЛА ПЕРЕГРУППИРОВКИ
# ═══════════════════════════════════════════════════════════════

GROUP_RULES = {
    '📺 Федеральные каналы': [
        'первый канал', 'россия 1', 'россия-1', 'ртр', 'ntv', 'нтв',
        'рентв', 'рен тв', '5 канал', 'пятый канал', 'тв центр', 'твц',
        'звезда', 'mir', 'мир', 'отр', 'спас', 'союз', 'тнт', 'стс',
        'матч тв', 'карусель', 'звезда', 'тв центр', 'звезда',
        'ннтв', 'беларусь 5', 'курай-тв', 'матур тв', 'восток тв',
        'евразия', 'стс-мир', 'нтв-мир', 'мир 24', 'звезда плюс'
    ],
    '📰 Новости и познавательные': [
        'новости', 'news', 'рбк', 'известия', 'россия 24', 'russia 24',
        '360', 'euronews', 'bbc', 'cnn', 'rt', 'дождь', 'москва 24',
        'мир 24', 'инфо', 'информационный', 'деловой', 'бизнес', 'тасс',
        'cgtn', 'france 24', 'deutsche welle', 'discovery', 'national geographic',
        'nat geo', 'history', 'animal planet', 'наука 2.0', 'моя планета',
        'в мире животных', 'затерянный мир', 'путешествия', 'travel',
        'приключения', 'подводный мир', 'история', 'viasat history',
        'открытый мир', 'завораживающие пейзажи', 'мистика нацистской германии',
        'хрономиражи', 'тонкий мир', 'исчезнувший мир', 'вредный мир',
        'ядовитый мир', 'и треснул мир', 'мой мир', 'наука 2.0',
        'discovery science', 'investigation discovery'
    ],
    '🎬 Кино и сериалы': [
        'кино', 'tv1000', 'viju', 'viasat', 'amedia', 'fx', 'hollywood',
        'bollywood', 'кинопремьера', 'кинохит', 'киносвидание', 'киносемья',
        'киносерия', 'киномикс', 'кинокомедия', 'дом кино', 'киноужас',
        'сериал', 'serial', 'start', 'star cinema', 'star family', 'кинопоказ',
        'нтв сериал', 'viju+', 'кино тв', 'кинохит', 'мир сериала',
        'в гостях у сказки', 'капитан фантастика', 'супергерои',
        'bcu criminal', 'bcu history', 'bcu мультсериал', 'magic'
    ],
    '🎵 Музыкальные каналы': [
        'музыка', 'music', 'bridge', 'шансон', 'жара', 'muz', 'mtv',
        'europa plus', 'мегаполис', 'хит', 'рок', 'металл', 'русский хит',
        'classic', 'фон', 'меццо', 'mezzo', 'музсоюз', 'ностальгия',
        'ру.тв', 'ru.tv', 'мсм', 'tnt music', 'муз тв', 'радио шансон',
        'dance', 'techno', 'house', 'trance', 'stingray', 'vevo', 'xite',
        'music box', 'clubbing tv', 'deejay tv', 'kronehit', 'power tv',
        'baraza music', 'retro music', 'rock tv', 'dancehits', 'afrobeats',
        'afrobeat', 'deluxe', 'fresh music', 'best of dance', 'now 70',
        'now 80', 'now rock', 'retro music', 'спирит tv', 'страна fm',
        'радио шансон', 'музыка первого', 'музыка live', 'музыка кино',
        'сити эдем', '1hd music', '30a music', '7x music', '88 stereo',
        'afn music', 'aiva', 'city tv', 'company tv', 'radio love fm',
        'radio m2o', 'radio ibiza', 'reload radio', 'trance is star',
        'trt music', 'v2beat', 'vuemme tv', 'itv music', 'očko', 'm2o'
    ],
    '📺 Развлекательные и общие': [
        'тнт4', 'пятница', 'че', 'суббота', '2x2', 'домашний', 'ю тв',
        'квн', 'трк', 'стиль', 'право', 'загород', 'охота', 'рыбалка',
        'авто', 'кухня', 'еда', 'здоровье', 'усадьба', 'fashion', 'travel',
        'путешествие', 'поехали', 'время', 'доктор', 'продвижение',
        'телекафе', 'сарафан', 'ностальгия', 'русский бестселлер',
        'супергерои', 'типтоп', 'матур тв', 'эйфория', 'вредный мир',
        'отв екатеринбург', 'стов беларусь', 'on air tv', 'velari tv',
        'radiopadova', 'radio studio one', 'radio zeta', 'banovina tv',
        'kiss kiss', 'maidan tv', 'nazo', 'persiana', 'skay folk',
        'super six', 'super tv', 'this is bulgaria', 'ugra travel',
        'шурентий live', 'ля минор', 'амedia premium', 'амedia hit'
    ],
    '⚽ Спортивные каналы': [
        'матч', 'match', 'спорт', 'sport', 'футбол', 'football', 'хоккей',
        'khl', 'eurosport', 'setanta', 'arena sport', 'mma', 'бокс',
        'баскет', 'окко', 'старт', 'премьер', 'матч тв', 'match tv',
        'евроспорт', 'спорт', 'setanta sports', 'мир баскетбола'
    ],
    '👶 Детские и мультипликационные': [
        'карусель', 'мульт', 'cartoon', 'nickelodeon', 'nick jr', 'tiji',
        'gulli', 'disney', 'да винчи', 'da vinci', 'детский', 'baby',
        'мама', 'о!', 'солнце', 'радость моя', 'рыжий', 'смайл',
        'союзмультфильм', 'мультиландия', 'мультимания', 'чижик',
        'капитан фантастика', 'мультивселенная', 'детский мир', 'мультфильмы',
        'ani', 'стус kids', 'iptvplay мультсказки', 'mult'
    ],
    '📦 Прочее': [
        '4k удивительные животные', 'арабские эмираты 4k', 'гватемала 4k',
        'подводный мир в 4к', 'путешествие', 'приключения', 'дальше',
        'без названия', 'unknown', 'test', 'demo', 'sample'
    ]
}

# ═══════════════════════════════════════════════════════════════
# 🔽 СПИСОК КАНАЛОВ ДЛЯ ДЕДУПЛИКАЦИИ (УДАЛЕНИЕ РЕГИОНАЛЬНЫХ ДУБЛЕЙ)
# ═══════════════════════════════════════════════════════════════

CHANNELS_TO_DEDUP = [
    'россия 24',
    'россия 1',
    'россия-1',
    'ртр',
    'ntv',
    'нтв',
    'рентв',
    'рен тв',
    '5 канал',
    'пятый канал',
    'тв центр',
    'твц',
    'матч тв',
    'звезда',
    'мир',
    'otr',
    'отр',
    'спас',
    'союз',
    'карусель',
    'первый канал',
]

# Настройка часового пояса (Москва UTC+3)
MOSCOW_TZ = timezone(timedelta(hours=3))

def get_moscow_time():
    return datetime.now(MOSCOW_TZ)

def get_channel_brand(info_line):
    """
    Извлекает основное название канала (бренд) без региональных уточнений.
    """
    if not info_line:
        return None
    
    name = None
    match = re.search(r'tvg-name="([^"]*)"', info_line, re.IGNORECASE)
    if match:
        name = match.group(1).strip()
    else:
        match = re.search(r',([^,]*)$', info_line)
        if match:
            name = match.group(1).strip()
    
    if not name:
        return None
    
    # Удаляем ТОЛЬКО региональные уточнения в скобках
    name = re.sub(r'\s*\([^)]*\)\s*', '', name).strip()
    
    return name

def parse_m3u(file_path):
    """Парсит M3U файл и возвращает список каналов"""
    if not Path(file_path).exists():
        print(f"⚠️ Файл {file_path} не найден!")
        return []
    
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
        return []
    
    return channels

def deduplicate_channels(channels):
    """Удаляет региональные дубли каналов"""
    if not channels:
        return []
    
    brand_groups = {}
    for ch in channels:
        brand = get_channel_brand(ch['info'])
        if not brand:
            brand_groups.setdefault(ch['info'], []).append(ch)
            continue
        
        brand_lower = brand.lower()
        should_dedup = False
        for dedup_channel in CHANNELS_TO_DEDUP:
            if dedup_channel.lower() in brand_lower:
                should_dedup = True
                break
        
        if should_dedup:
            brand_groups.setdefault(brand, []).append(ch)
        else:
            brand_groups.setdefault(f"_{brand}_{ch['info']}", []).append(ch)
    
    result = []
    removed_count = 0
    
    for brand, group in brand_groups.items():
        if len(group) == 1:
            result.append(group[0])
            continue
        
        clean = []
        regional = []
        
        for ch in group:
            name = get_channel_name(ch['info'])
            if re.search(r'\([^)]*\)', name):
                regional.append(ch)
            else:
                clean.append(ch)
        
        if clean:
            result.append(clean[0])
            removed_count += len(group) - 1
        else:
            result.append(regional[0])
            removed_count += len(group) - 1
    
    if removed_count > 0:
        print(f"🗑️ Удалено региональных дублей: {removed_count}")
    return result

def get_new_group(info_line):
    """
    Определяет, в какую новую группу поместить канал.
    Если канал из группы Wink (VPN 🇷🇺) → отправляем в ⌚ Архив
    """
    if not info_line:
        return '📦 Прочее'
    
    info_lower = info_line.lower()
    
    # Извлекаем текущую группу
    group_match = re.search(r'group-title="([^"]*)"', info_line, re.IGNORECASE)
    current_group = group_match.group(1) if group_match else ''
    
    # Проверяем, из группы ли Wink (VPN 🇷🇺)
    if ARCHIVE_SOURCE_GROUP.lower() in current_group.lower():
        return '⌚ Архив'
    
    # Проверяем по остальным правилам
    current_group_lower = current_group.lower()
    for new_group, keywords in GROUP_RULES.items():
        for keyword in keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in info_lower or keyword_lower in current_group_lower:
                return new_group
    
    return '📦 Прочее'

def should_skip_check(info_line):
    """
    Проверяет, нужно ли пропускать проверку работоспособности для этого канала.
    """
    if not info_line:
        return False
    
    group_match = re.search(r'group-title="([^"]*)"', info_line, re.IGNORECASE)
    if not group_match:
        return False
    
    current_group = group_match.group(1)
    for skip_group in SKIP_CHECK_GROUPS:
        if skip_group.lower() in current_group.lower():
            return True
    
    return False

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
    """
    Проверяет все каналы параллельно.
    Каналы из SKIP_CHECK_GROUPS пропускаются и считаются рабочими.
    """
    total = len(channels)
    print(f"🚀 Параллельная проверка {total} каналов (потоков: {max_workers})")
    
    working = []
    dead = []
    skipped = []
    checked = 0
    
    start_time = time.time()
    
    # Сначала разделяем каналы на те, что нужно проверять, и те, что пропускаем
    to_check = []
    for ch in channels:
        if should_skip_check(ch['info']):
            skipped.append(ch)
            working.append(ch)  # Сразу считаем рабочими
        else:
            to_check.append(ch)
    
    if skipped:
        print(f"⏭️ Пропущено проверки: {len(skipped)} каналов (из {', '.join(SKIP_CHECK_GROUPS)})")
    
    if not to_check:
        print("✅ Все каналы пропущены проверки!")
        return working, dead
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_channel = {
            executor.submit(check_stream, ch['url']): ch 
            for ch in to_check
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

def get_channel_name(info_line):
    match = re.search(r',([^,]*)$', info_line)
    if match:
        return match.group(1).strip()
    match = re.search(r'tvg-name="([^"]*)"', info_line, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return 'Без названия'

def write_m3u_with_groups(channels, output_file, update_time, checked_count=None, dead_count=None, dedup_count=None, skipped_count=None):
    """Записывает каналы в M3U файл с группировкой по категориям"""
    
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Группируем каналы по новым категориям
    groups = {}
    
    for ch in channels:
        new_group = get_new_group(ch['info'])
        if new_group not in groups:
            groups[new_group] = []
        groups[new_group].append(ch)
    
    # Сортируем группы в нужном порядке
    group_order = [
        '⌚ Архив',
        '📺 Федеральные каналы',
        '📰 Новости и познавательные',
        '⚽ Спортивные каналы',
        '🎬 Кино и сериалы',
        '📺 Развлекательные и общие',
        '🎵 Музыкальные каналы',
        '👶 Детские и мультипликационные',
        '📦 Прочее',
    ]
    
    other_groups = sorted([g for g in groups.keys() if g not in group_order])
    ordered_groups = [g for g in group_order if g in groups] + other_groups
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('#EXTM3U\n')
        f.write(f'# ❤️ Плейлист — {update_time.strftime("%Y-%m-%d %H:%M:%S")} MSK\n')
        f.write(f'# Всего каналов: {len(channels)}\n')
        f.write(f'# Групп: {len(groups)}\n')
        if checked_count is not None:
            f.write(f'# Проверено: {checked_count}\n')
        if dead_count is not None:
            f.write(f'# Удалено нерабочих: {dead_count}\n')
        if dedup_count is not None:
            f.write(f'# Удалено региональных дублей: {dedup_count}\n')
        if skipped_count is not None:
            f.write(f'# Пропущено проверки: {skipped_count}\n')
        f.write('\n')
        
        for group_name in ordered_groups:
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
    input_file = './output/merged.m3u'
    output_file = './output/favorites.m3u'
    
    print("="*50)
    print("❤️  СОЗДАНИЕ ПЛЕЙЛИСТА ИЗ MERGED.M3U")
    print("="*50)
    
    # =============================================
    # 1. ЧИТАЕМ ВСЕ КАНАЛЫ ИЗ ФАЙЛА
    # =============================================
    print("\n📖 ЧТЕНИЕ ФАЙЛА merged.m3u")
    print("-"*50)
    
    channels = parse_m3u(input_file)
    
    if not channels:
        print("❌ Каналы не найдены!")
        return
    
    print(f"📊 Всего каналов: {len(channels)}")
    
    # =============================================
    # 2. УДАЛЯЕМ РЕГИОНАЛЬНЫЕ ДУБЛИ
    # =============================================
    print("\n" + "="*50)
    print("🗑️  УДАЛЕНИЕ РЕГИОНАЛЬНЫХ ДУБЛЕЙ")
    print("="*50)
    original_count = len(channels)
    channels = deduplicate_channels(channels)
    dedup_count = original_count - len(channels)
    print(f"📊 Было: {original_count}, стало: {len(channels)}, удалено: {dedup_count}")
    
    # =============================================
    # 3. ПРОВЕРКА КАНАЛОВ (С ПРОПУСКОМ ДЛЯ SKIP_CHECK_GROUPS)
    # =============================================
    print("\n" + "="*50)
    print("🔍 ПРОВЕРКА КАНАЛОВ")
    print("="*50)
    
    working, dead = check_all_parallel(channels)
    
    # Подсчитываем сколько пропущено проверки
    skipped_count = sum(1 for ch in working if should_skip_check(ch['info']))
    
    print(f"\n📊 Результат:")
    print(f"  ✅ Работает: {len(working)}")
    print(f"  ❌ Не работает: {len(dead)}")
    if skipped_count > 0:
        print(f"  ⏭️ Пропущено проверки: {skipped_count}")
    print(f"  📊 Процент рабочих: {round(len(working)/(len(working)+len(dead))*100, 1) if (len(working)+len(dead)) > 0 else 0}%")
    
    # =============================================
    # 4. СОХРАНЯЕМ ПЛЕЙЛИСТ
    # =============================================
    if working:
        now = get_moscow_time()
        write_m3u_with_groups(
            working, 
            output_file, 
            now,
            checked_count=len(working)+len(dead),
            dead_count=len(dead),
            dedup_count=dedup_count,
            skipped_count=skipped_count
        )
        print(f"\n✅ Плейлист сохранён: {output_file}")
        print(f"   Всего каналов: {len(working)}")
        
        # Показываем распределение по категориям
        print("\n📂 Распределение по категориям:")
        temp_groups = {}
        for ch in working:
            group = get_new_group(ch['info'])
            temp_groups[group] = temp_groups.get(group, 0) + 1
        for group, count in sorted(temp_groups.items(), key=lambda x: -x[1]):
            print(f"  {group}: {count} каналов")
    else:
        print("\n❌ Нет рабочих каналов!")
    
    print("\n" + "="*50)
    print("✅ Готово!")
    print("="*50)

if __name__ == '__main__':
    main()