#!/usr/bin/env python3
"""Parse all Vietnam customs data (2019-2023) and output JSON for Feishu upload."""

import json, re, os

BASE = os.path.dirname(os.path.abspath(__file__))

COUNTRY_MAP_VI = {
    'TRUNG QUỐC': '中国', 'HOA KỲ': '美国', 'NHẬT BẢN': '日本', 'HÀN QUỐC': '韩国',
    'ẤN ĐỘ': '印度', 'THÁI LAN': '泰国', 'MALAIXIA': '马来西亚', 'INĐÔNÊXIA': '印尼',
    'ĐÀI LOAN': '台湾', 'SINGAPO': '新加坡', 'ANH': '英国', 'ĐỨC': '德国',
    'PHÁP': '法国', 'HÀ LAN': '荷兰', 'BỈ': '比利时', 'ITALIA': '意大利',
    'CAMPUCHIA': '柬埔寨', 'PHILIPPIN': '菲律宾', 'NGA': '尼日利亚', 'MỸ': '美国',
}

COUNTRY_MAP_EN = {
    'CHINA': '中国', 'USA': '美国', 'U.S.A.': '美国', 'JAPAN': '日本',
    'KOREA, REPUBLIC OF': '韩国', 'KOREA, SOUTH': '韩国', 'SOUTH KOREA': '韩国',
    'REPUBLIC OF KOREA': '韩国', 'INDIA': '印度', 'THAILAND': '泰国',
    'MALAYSIA': '马来西亚', 'INDONESIA': '印尼', 'TAIWAN': '台湾',
    'CHINESE TAIPEI': '台湾', 'SINGAPORE': '新加坡', 'UNITED KINGDOM': '英国',
    'UK': '英国', 'GERMANY': '德国', 'FRANCE': '法国', 'NETHERLANDS': '荷兰',
    'BELGIUM': '比利时', 'ITALY': '意大利', 'CAMBODIA': '柬埔寨',
    'PHILIPPINES': '菲律宾', 'NIGERIA': '尼日利亚',
}

COUNTRY_EN_VI = {
    'CHINA': 'TRUNG QUỐC', 'USA': 'HOA KỲ', 'JAPAN': 'NHẬT BẢN',
    'KOREA, REPUBLIC OF': 'HÀN QUỐC', 'SOUTH KOREA': 'HÀN QUỐC',
    'REPUBLIC OF KOREA': 'HÀN QUỐC', 'INDIA': 'ẤN ĐỘ', 'THAILAND': 'THÁI LAN',
    'MALAYSIA': 'MALAIXIA', 'INDONESIA': 'INĐÔNÊXIA', 'TAIWAN': 'ĐÀI LOAN',
    'SINGAPORE': 'SINGAPO', 'UNITED KINGDOM': 'ANH', 'GERMANY': 'ĐỨC',
    'FRANCE': 'PHÁP', 'NETHERLANDS': 'HÀ LAN', 'BELGIUM': 'BỈ',
    'ITALY': 'ITALIA', 'CAMBODIA': 'CAMPUCHIA', 'PHILIPPINES': 'PHILIPPIN',
    'NIGERIA': 'NGA',
}

def pn(s, lang='vi'):
    """Parse number. vi: dot=thousand, comma=decimal. en: comma=thousand, dot=decimal."""
    if s is None: return None
    s = s.strip()
    try:
        if lang == 'en':
            return float(s.replace(',', ''))
        else:
            return float(s.replace('.', '').replace(',', '.'))
    except:
        return None

def get_lines(data):
    lines = []
    for page in data:
        for block in page['blocks']:
            for line in block['lines']:
                text = ' '.join(s['text'] for s in line['spans']).strip()
                if text: lines.append(text)
    return lines

def load_json(path):
    with open(path) as f: return json.load(f)

def detect_lang(lines):
    for line in lines:
        if 'Cao su' in line: return 'vi'
        if 'Rubber' in line and 'Ton' in line: return 'en'
    return 'unknown'

def parse_2x_2n_vi(lines):
    results = []
    for line in lines:
        m = re.search(r'Cao su\s+Tấn\s+(\d[\d.]*)\s+([\d,.]+)\s+([-\d,.]+)\s+([-\d,.]+)\s+(\d[\d.]*)\s+([\d,.]+)\s+([-\d,.]+)\s+([-\d,.]+)', line)
        if m:
            results.append({'category': 'Cao su', 'mq': pn(m.group(1)), 'mv': pn(m.group(2)),
                           'yoy': pn(m.group(4)), 'cq': pn(m.group(5)), 'cv': pn(m.group(6))})
        m = re.search(r'Sản phẩm từ cao su\s+USD\s+([\d,.]+)\s+([-\d,.]+)\s+([\d,.]+)\s+([-\d,.]+)', line)
        if m:
            results.append({'category': 'Sản phẩm từ cao su', 'mq': None, 'mv': pn(m.group(1)),
                           'yoy': pn(m.group(2)), 'cq': None, 'cv': pn(m.group(3))})
    return results

def parse_2x_2n_en(lines):
    results = []
    for line in lines:
        m = re.search(r'Rubber\s+Ton\s+([\d.,]+)\s+([\d.,]+)\s+([-.\d,%]+)\s+([-.\d,%]+)\s+([\d.,]+)\s+([\d.,]+)\s+([-.\d,%]+)\s+([-.\d,%]+)', line)
        if m:
            results.append({'category': 'Rubber', 'mq': pn(m.group(1),'en'), 'mv': pn(m.group(2),'en'),
                           'yoy': pn(m.group(4),'en'), 'cq': pn(m.group(5),'en'), 'cv': pn(m.group(6),'en')})
        m = re.search(r'Rubber products\s+USD\s+([\d.,]+)\s+([-.\d,%]+)\s+([\d.,]+)\s+([-.\d,%]+)', line)
        if m:
            results.append({'category': 'Rubber products', 'mq': None, 'mv': pn(m.group(1),'en'),
                           'yoy': pn(m.group(2),'en'), 'cq': None, 'cv': pn(m.group(3),'en')})
    return results

def parse_5x_5n_vi(lines):
    results = []
    current_country = None
    skip_kw = ['Cao su', 'Tấn', 'USD', 'Sản phẩm', 'Hàng', 'Điện thoại', 'Máy móc', 'Giày dép',
               'Túi xách', 'Dệt', 'Vải', 'Gỗ', 'Sắt thép', 'Nguyên phụ', 'Phương tiện', 'Khác',
               'MINISTRY', 'GENERAL', 'CUSTOMS', 'STATISTICS', 'Table', 'Compared', 'Units',
               'Reporting', 'Year to date', 'Volume', 'Value', 'Main export', 'Main import',
               'Page', 'No.', 'Preliminary']
    country_re = re.compile(r'^([A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴĐÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸ\s]+)')
    for line in lines:
        line = line.strip()
        if not line: continue
        m = country_re.match(line)
        if m and not any(kw.lower() in line.lower() for kw in skip_kw):
            name = m.group(1).strip()
            if len(name) >= 3 and name not in ('T R U N G', 'Q U Ố C', 'H O A', 'K Ỳ', 'H À N', 'Q U Ố C'):
                current_country = name; continue
        if current_country is None: continue
        m = re.search(r'Cao su\s+Tấn\s+(\d[\d.]*)\s+([\d,.]+)\s+(\d[\d.]*)\s+([\d,.]+)', line)
        if m:
            results.append({'country': current_country, 'lang': 'vi', 'cat': 'Cao su',
                           'mq': pn(m.group(1)), 'mv': pn(m.group(2)), 'cq': pn(m.group(3)), 'cv': pn(m.group(4))})
        m = re.search(r'Sản phẩm từ cao su\s+USD\s+([\d,.]+)\s+([\d,.]+)', line)
        if m:
            results.append({'country': current_country, 'lang': 'vi', 'cat': 'Sản phẩm từ cao su',
                           'mq': None, 'mv': pn(m.group(1)), 'cq': None, 'cv': pn(m.group(2))})
    return results

def parse_5x_5n_en(lines):
    results = []
    current_country = None
    skip_kw = ['Rubber', 'Ton', 'USD', 'products', 'Handbags', 'Textiles', 'garments',
               'Foot-wears', 'Footwear', 'Iron', 'steel', 'Computers', 'electrical',
               'Telephones', 'mobile', 'phones', 'Machine', 'equipment', 'Other products',
               'Other means', 'Fishery', 'Fruits', 'vegetables', 'Cashew', 'Coffee',
               'Pepper', 'Yarn', 'Tyre', 'components', 'thereof', 'parts', 'spare-parts',
               'auxiliaries', 'materials', 'headgear', 'umbrellas', 'fabrics', 'technical',
               'MINISTRY', 'GENERAL', 'CUSTOMS', 'STATISTICS', 'Table', 'Compared', 'Units',
               'Reporting', 'Year to date', 'Volume', 'Value', 'Main export', 'Main import',
               'Page', 'No.', 'Preliminary', 'Country', 'Territory', 'base metals',
               'Crude oil', 'Coal', 'Transportation', 'accessories', 'Chemical', 'Plastic',
               'Resins', 'Paper', 'Ceramic', 'Wood', 'Cement', 'Pharmaceutical',
               'Fertilizer', 'Animal', 'feed', 'Copper', 'Aluminum', 'Zinc', 'Lead',
               'Tobacco', 'Wine', 'Beer', 'Cosmetic', 'Perfume', 'Jewelry', 'Gold',
               'Silver', 'Platinum', 'Glass', 'Optical', 'Photo', 'Cinema', 'Medical',
               'Aircraft', 'Ship', 'Boat', 'Railway', 'Tractor', 'Agricultural',
               'Knitted', 'Woven', 'Cotton', 'Synthetic', 'Silk', 'Hemp', 'Ramie',
               'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August',
               'September', 'October', 'November', 'December']
    for line in lines:
        line = line.strip()
        if not line: continue
        country_m = re.match(r'^([A-Z][A-Za-z\s,.\-]+?)\s+([\d.,]{7,})(?:\s+([\d.,]{7,}))?$', line)
        if country_m:
            name = country_m.group(1).strip()
            if (len(name) >= 3 and 'Ton' not in line and 'USD' not in line and
                'products' not in line.lower() and not any(kw.lower() in line.lower() for kw in skip_kw)):
                current_country = name.upper(); continue
        if current_country is None: continue
        m = re.search(r'Rubber\s+Ton\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)', line)
        if m:
            results.append({'country': current_country, 'lang': 'en', 'cat': 'Rubber',
                           'mq': pn(m.group(1),'en'), 'mv': pn(m.group(2),'en'),
                           'cq': pn(m.group(3),'en'), 'cv': pn(m.group(4),'en')})
        m = re.search(r'Rubber products\s+USD\s+([\d.,]+)\s+([\d.,]+)', line)
        if m:
            results.append({'country': current_country, 'lang': 'en', 'cat': 'Rubber products',
                           'mq': None, 'mv': pn(m.group(1),'en'), 'cq': None, 'cv': pn(m.group(2),'en')})
    return results

def normalize_vi_name(name):
    """Remove spurious spaces inside words from OCR artifacts (e.g. 'TRUNG QU Ố C' -> 'TRUNG QUỐC').
    Strategy: try the name as-is first; if not found, remove spaces adjacent to accented chars
    which are typical OCR artifacts in old PDFs."""
    return name  # actual normalization done in translate_country

def translate_country(name, lang):
    if lang == 'vi':
        # Try exact match first, then try removing spaces around accented chars (OCR artifacts)
        cn = COUNTRY_MAP_VI.get(name)
        norm = name
        if not cn:
            # Remove spaces adjacent to non-ASCII chars (OCR inserts spaces in accented letters)
            norm = re.sub(r'\s+([\x80-\uffff])', r'\1', name)
            norm = re.sub(r'([\x80-\uffff])\s+', r'\1', norm)
            cn = COUNTRY_MAP_VI.get(norm)
        vi = norm if cn else name
        return cn, vi
    return COUNTRY_MAP_EN.get(name), COUNTRY_EN_VI.get(name)

def parse_all():
    all_commodity, all_country = [], []
    for year in [2019, 2020, 2021, 2022, 2023]:
        year_dir = os.path.join(BASE, str(year))
        if not os.path.isdir(year_dir): continue
        months = ['10','11','12'] if year == 2022 else [str(m).zfill(2) for m in range(1, 13)]
        for month in months:
            month_dir = os.path.join(year_dir, month)
            if not os.path.isdir(month_dir): continue
            ms = f"{year}-{month}"
            for ftype, direction in [('2x','出口'),('2n','进口'),('5x','出口'),('5n','进口')]:
                json_path = os.path.join(month_dir, f'{ftype}.json')
                if not os.path.exists(json_path): continue
                data = load_json(json_path)
                lines = get_lines(data)
                lang = detect_lang(lines)
                if ftype in ('2x','2n'):
                    records = parse_2x_2n_en(lines) if lang == 'en' else parse_2x_2n_vi(lines)
                    for r in records:
                        cat = '天然橡胶' if r['category'] in ('Cao su','Rubber') else '橡胶制品'
                        all_commodity.append({
                            '月份': ms, '方向': direction, '品类': cat,
                            '当月数量(吨)': r['mq'],
                            '当月金额(万美元)': round(r['mv']/10000, 2) if r['mv'] else None,
                            '累计数量(吨)': r.get('cq'),
                            '累计金额(万美元)': round(r['cv']/10000, 2) if r.get('cv') else None,
                            '同比(%)': r.get('yoy'),
                        })
                else:
                    records = parse_5x_5n_en(lines) if lang == 'en' else parse_5x_5n_vi(lines)
                    for r in records:
                        cn, vi = translate_country(r['country'], r['lang'])
                        if not cn or not vi: continue
                        cat = '天然橡胶' if r['cat'] in ('Cao su','Rubber') else '橡胶制品'
                        all_country.append({
                            '月份': ms, '方向': direction, '国家(中文)': cn, '国家(越南语)': vi, '品类': cat,
                            '当月金额(万美元)': round(r['mv']/10000, 2) if r['mv'] else None,
                            '累计金额(万美元)': round(r['cv']/10000, 2) if r.get('cv') else None,
                            '当月数量(吨)': r['mq'], '累计数量(吨)': r.get('cq'),
                        })
    return all_commodity, all_country

if __name__ == '__main__':
    commodity, country = parse_all()
    print(f"Commodity: {len(commodity)}, Country: {len(country)}")
    with open(os.path.join(BASE, 'commodity_2019_2023.json'), 'w') as f:
        json.dump(commodity, f, ensure_ascii=False, indent=2)
    with open(os.path.join(BASE, 'country_2019_2023.json'), 'w') as f:
        json.dump(country, f, ensure_ascii=False, indent=2)
    # Verify 2023 China
    for r in country:
        if r['月份'] == '2023-01' and r['国家(中文)'] == '中国' and r['品类'] == '天然橡胶' and r['方向'] == '出口':
            print(f"VERIFY 2023-01 China export rubber: {r}")
