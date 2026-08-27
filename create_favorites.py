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
# 🔽 СПИСОК КЛЮЧЕВЫХ СЛОВ ДЛЯ ИЗБРАННОГО
# ═══════════════════════════════════════════════════════════════
# Каналы, названия которых содержат эти слова, попадут в Избранное

FAVORITE_KEYWORDS = [
    # === Российские ===
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
    
    # === Зарубежные ===
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
    
    # === Кино ===
    'Amedia',
    'TV1000',
    'Viju',
    'Кинопремьера',
    'Кино ТВ',
    'Кинокомедия',
    'Кинохит',
    'Hollywood',
    'Bollywood',
    
    # === Спорт ===
    'Eurosport',
    'Setanta',
    'Спорт',
    
    # === Познавательные ===
    'Наука 2.0',
    'Моя планета',
    'Охота и рыбалка',
    'Travel',
    'Приключения',
    
    # === Детские ===
    'Cartoon Network',
    'Мульт',
    'Детский',
    
    # === Музыка ===
    'Музыка',
    'Шансон',
    'Жара',
]

# ═══════════════════════════════════════════════════════════════
# 🔽 ПРАВИЛА ПЕРЕГРУППИРОВКИ (ТОЛЬКО ДЛЯ ИЗБРАННОГО)
# ═══════════════════════════════════════════════════════════════
# Если в названии канала или его исходной группе есть слово из списка →
# канал попадает в новую категорию в плейлисте Избранное

GROUP_RULES = {
    '⌚ Архив': [
        'архив', 'archive', 'запись', 'record', 'повтор', 'replay',
        # Убраны общие слова: 'эфир', 'live', 'прямой эфир', 'трансляция', 'broadcast'
    ],
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

# Настройка часового пояса (Москва UTC+3)
MOSCOW_TZ = timezone(timedelta(hours=3))

def get_moscow_time():
    return datetime.now(MOSCOW_TZ)

def get_new_group(info_line):
    """
    Определяет, в какую новую группу поместить канал.
    Возвращает название новой группы или None (оставить как есть).
    """
    if not info_line:
        return None
    
    info_lower = info_line.lower()
    
    # Извлекаем текущую группу
    group_match = re.search(r'group-title="([^"]*)"', info_line, re.IGNORECASE)
    current_group = group_match.group(1).lower() if group_match else ''
    
    # ПРОВЕРКА НА АРХИВ В ПЕРВУЮ ОЧЕРЕДЬ
    for keyword in GROUP_RULES.get('⌚ Архив', []):
        if keyword.lower() in info_lower or keyword.lower() in current_group:
            return '⌚ Архив'
    
    # Проверяем по всем остальным правилам
    for new_group, keywords in GROUP_RULES.items():
        if new_group == '⌚ Архив':  # Пропускаем, так как уже проверили
            continue
        for keyword in keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in info_lower or keyword_lower in current_group:
                return new_group
    
    # Если ничего не подошло - отправляем в "Прочее"
    return '📦 Прочее'

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

def write_m3u_with_groups(channels, output_file, update_time, checked_count=None, dead_count=None):
    """Записывает каналы в M3U файл с группировкой по категориям"""
    
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Группируем каналы по новым категориям
    groups = {}
    ungrouped = []
    
    for ch in channels:
        new_group = get_new_group(ch['info'])
        if new_group:
            if new_group not in groups:
                groups[new_group] = []
            groups[new_group].append(ch)
        else:
            # Если группа не определена, оставляем исходную или создаём "Другие"
            current_group = re.search(r'group-title="([^"]*)"', ch['info'], re.IGNORECASE)
            if current_group:
                group_name = current_group.group(1)
            else:
                group_name = '📦 Прочее'
            
            # Очищаем старую группу и добавляем новую
            ch['info'] = re.sub(r'group-title="[^"]*"\s*', '', ch['info'])
            if 'group-title="' not in ch['info']:
                ch['info'] = ch['info'].replace(',', f' group-title="{group_name}",')
            
            if group_name not in groups:
                groups[group_name] = []
            groups[group_name].append(ch)
    
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
    
    # Добавляем остальные группы в алфавитном порядке
    other_groups = sorted([g for g in groups.keys() if g not in group_order])
    ordered_groups = [g for g in group_order if g in groups] + other_groups
    
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
        
        for group_name in ordered_groups:
            channel_list = groups[group_name]
            f.write(f'# === ГРУППА: {group_name} ===\n')
            
            for ch in channel_list:
                # Убеждаемся, что группа правильная
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
    print("❤️  СОЗДАНИЕ ПЛЕЙЛИСТА ИЗБРАННОЕ (С КАТЕГОРИЯМИ)")
    print("="*50)
    
    if not Path(input_file).exists():
        print(f"❌ Файл {input_file} не найден!")
        print("   Сначала запустите основной workflow merge-playlists.yml")
        return
    
    print(f"📖 Чтение: {input_file}")
    channels = parse_m3u(input_file)
    print(f"📊 Всего каналов в merged.m3u: {len(channels)}")
    
    # Фильтруем избранные каналы
    favorites = [ch for ch in channels if is_favorite(ch['info'])]
    total_favorites = len(favorites)
    print(f"❤️ Найдено избранных каналов: {total_favorites}")
    
    if not favorites:
        print("⚠️ Избранные каналы не найдены!")
        print("   Проверьте список FAVORITE_KEYWORDS в create_favorites.py")
        return
    
    # Параллельная проверка
    print("\n" + "="*50)
    print("🔍 ПРОВЕРКА КАНАЛОВ")
    print("="*50)
    
    working, dead = check_all_parallel(favorites)
    
    print(f"\n📊 Результат:")
    print(f"  ✅ Работает: {len(working)}")
    print(f"  ❌ Не работает: {len(dead)}")
    print(f"  📊 Процент рабочих: {round(len(working)/(len(working)+len(dead))*100, 1) if (len(working)+len(dead)) > 0 else 0}%")
    
    # Сохраняем только рабочие каналы с группировкой по категориям
    if working:
        now = get_moscow_time()
        write_m3u_with_groups(
            working, 
            output_file, 
            now,
            checked_count=len(working)+len(dead),
            dead_count=len(dead)
        )
        print(f"\n✅ Плейлист сохранён: {output_file}")
        print(f"   Всего каналов: {len(working)}")
        
        # Показываем распределение по категориям
        print("\n📂 Распределение по категориям:")
        # Временно пересчитываем группы для вывода
        temp_groups = {}
        for ch in working:
            group = get_new_group(ch['info']) or '📦 Прочее'
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
