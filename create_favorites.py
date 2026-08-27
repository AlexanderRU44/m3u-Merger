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

# ═══════════════════════════════════════════════════════════════
# 🔽 СПИСОК КАНАЛОВ ДЛЯ ДЕДУПЛИКАЦИИ (УДАЛЕНИЕ РЕГИОНАЛЬНЫХ ДУБЛЕЙ)
# ═══════════════════════════════════════════════════════════════
# Каналы, у которых нужно оставить только один экземпляр (без региона)

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

# ═══════════════════════════════════════════════════════════════
# 🔽 ГРУППЫ ДЛЯ ИЗВЛЕЧЕНИЯ ИЗ ФАЙЛА dimonovich_tv.m3u
# ═══════════════════════════════════════════════════════════════

EXTRACT_GROUPS = [
    'Wink (VPN 🇷🇺)',
    'Lime (VPN 🇷🇺)',
]

# Настройка часового пояса (Москва UTC+3)
MOSCOW_TZ = timezone(timedelta(hours=3))

def get_moscow_time():
    return datetime.now(MOSCOW_TZ)

def get_channel_brand(info_line):
    """
    Извлекает основное название канала (бренд) без региональных уточнений.
    Например: 'Россия 24 (Смоленск)' → 'Россия 24'
    Удаляет ТОЛЬКО регион в скобках. HD, FHD, +7, +2 и т.д. НЕ УДАЛЯЮТСЯ.
    """
    if not info_line:
        return None
    
    # Пробуем извлечь tvg-name или название после запятой
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
    
    # Удаляем ТОЛЬКО региональные уточнения в скобках: (Смоленск), (г. Москва) и т.д.
    # HD, FHD, 4K, +7, +2 и т.д. НЕ ТРОГАЕМ
    name = re.sub(r'\s*\([^)]*\)\s*', '', name).strip()
    
    return name

def extract_channels_from_groups(file_path, target_groups):
    """
    Извлекает каналы из указанных групп из M3U файла.
    Возвращает список каналов.
    """
    if not Path(file_path).exists():
        print(f"⚠️ Файл {file_path} не найден!")
        return []
    
    print(f"📖 Извлечение каналов из групп: {', '.join(target_groups)}")
    
    channels = []
    current_channel = None
    found_groups = set()
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith('#EXTINF'):
                # Проверяем, принадлежит ли канал нужной группе
                group_match = re.search(r'group-title="([^"]*)"', line, re.IGNORECASE)
                if group_match:
                    group_name = group_match.group(1)
                    for target_group in target_groups:
                        if target_group.lower() in group_name.lower():
                            found_groups.add(group_name)
                            current_channel = {
                                'info': line,
                                'url': None,
                                'source_group': group_name,
                            }
                            break
                    else:
                        current_channel = None
                else:
                    current_channel = None
                    
            elif current_channel and line.startswith(('http://', 'https://')):
                current_channel['url'] = line
                channels.append(current_channel)
                current_channel = None
    
    except Exception as e:
        print(f"⚠️ Ошибка при чтении {file_path}: {e}")
        return []
    
    print(f"✅ Найдено групп: {len(found_groups)}")
    for group in found_groups:
        print(f"   - {group}")
    print(f"📊 Извлечено каналов: {len(channels)}")
    
    return channels

def deduplicate_channels(channels):
    """
    Удаляет региональные дубли каналов, оставляя только один экземпляр для каждого бренда.
    Приоритет: сначала проверяем рабочие, потом выбираем с самым коротким названием (без региона).
    """
    if not channels:
        return []
    
    # Группируем каналы по бренду
    brand_groups = {}
    for ch in channels:
        brand = get_channel_brand(ch['info'])
        if not brand:
            # Если не удалось определить бренд, оставляем как есть
            brand_groups.setdefault(ch['info'], []).append(ch)
            continue
        
        # Проверяем, нужно ли дедуплицировать этот бренд
        brand_lower = brand.lower()
        should_dedup = False
        for dedup_channel in CHANNELS_TO_DEDUP:
            if dedup_channel.lower() in brand_lower:
                should_dedup = True
                break
        
        if should_dedup:
            brand_groups.setdefault(brand, []).append(ch)
        else:
            # Не дедуплицируем - оставляем все копии
            brand_groups.setdefault(f"_{brand}_{ch['info']}", []).append(ch)
    
    # Выбираем лучший канал из каждой группы
    result = []
    removed_count = 0
    
    for brand, group in brand_groups.items():
        if len(group) == 1:
            result.append(group[0])
            continue
        
        # Разделяем на "чистые" и "региональные"
        clean = []
        regional = []
        
        for ch in group:
            name = get_channel_name(ch['info'])
            if re.search(r'\([^)]*\)', name):
                regional.append(ch)
            else:
                clean.append(ch)
        
        # Если есть чистый канал - берём первый из них
        if clean:
            result.append(clean[0])
            removed_count += len(group) - 1
        else:
            # Иначе берём первый региональный
            result.append(regional[0])
            removed_count += len(group) - 1
    
    if removed_count > 0:
        print(f"🗑️ Удалено региональных дублей: {removed_count}")
    return result

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

def get_channel_name(info_line):
    match = re.search(r',([^,]*)$', info_line)
    if match:
        return match.group(1).strip()
    match = re.search(r'tvg-name="([^"]*)"', info_line, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return 'Без названия'

def write_m3u_with_groups(channels, output_file, update_time, dedup_count=None):
    """Записывает каналы в M3U файл с группировкой по категориям (БЕЗ ПРОВЕРКИ)"""
    
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Группируем каналы по новым категориям
    groups = {}
    
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
        if dedup_count is not None:
            f.write(f'# Удалено региональных дублей: {dedup_count}\n')
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
    dimonovich_file = './playlists/dimonovich_tv.m3u'
    output_file = './output/favorites.m3u'
    
    print("="*50)
    print("❤️  СОЗДАНИЕ ПЛЕЙЛИСТА ИЗБРАННОЕ (С КАТЕГОРИЯМИ)")
    print("="*50)
    
    # =============================================
    # 1. ИЗВЛЕКАЕМ КАНАЛЫ ИЗ DIMONOVICH_TV.M3U
    # =============================================
    print("\n📁 ИЗВЛЕЧЕНИЕ КАНАЛОВ ИЗ DIMONOVICH_TV.M3U")
    print("-"*50)
    
    channels = extract_channels_from_groups(dimonovich_file, EXTRACT_GROUPS)
    
    if not channels:
        print("⚠️ Каналы из указанных групп не найдены!")
        print(f"   Проверьте наличие групп: {', '.join(EXTRACT_GROUPS)}")
        return
    
    total_favorites = len(channels)
    print(f"📊 Всего каналов: {total_favorites}")
    
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
    # 3. СОХРАНЯЕМ ПЛЕЙЛИСТ (БЕЗ ПРОВЕРКИ)
    # =============================================
    print("\n" + "="*50)
    print("💾 СОХРАНЕНИЕ ПЛЕЙЛИСТА (БЕЗ ПРОВЕРКИ)")
    print("="*50)
    
    if channels:
        now = get_moscow_time()
        write_m3u_with_groups(
            channels, 
            output_file, 
            now,
            dedup_count=dedup_count
        )
        print(f"\n✅ Плейлист сохранён: {output_file}")
        print(f"   Всего каналов: {len(channels)}")
        
        # Показываем распределение по категориям
        print("\n📂 Распределение по категориям:")
        temp_groups = {}
        for ch in channels:
            group = get_new_group(ch['info']) or '📦 Прочее'
            temp_groups[group] = temp_groups.get(group, 0) + 1
        for group, count in sorted(temp_groups.items(), key=lambda x: -x[1]):
            print(f"  {group}: {count} каналов")
    else:
        print("\n❌ Нет каналов для сохранения!")
    
    print("\n" + "="*50)
    print("✅ Готово!")
    print("="*50)

if __name__ == '__main__':
    main()