#!/usr/bin/env python3
"""Parse Vietnam customs JSON files extracted by pdftext."""

import json, re, os, glob

BASE = os.path.dirname(os.path.abspath(__file__))
import sys
YEAR = int(sys.argv[1]) if len(sys.argv) > 1 else 2025

def load_json(path):
    with open(path) as f:
        return json.load(f)

def get_lines(data):
    """Extract all lines from pdftext JSON."""
    lines = []
    for page in data:
        for block in page['blocks']:
            for line in block['lines']:
                text = ' '.join(s['text'] for s in line['spans']).strip()
                if text:
                    lines.append(text)
    return lines

def parse_number(s):
    """Parse Vietnamese number format (dots as thousands separator)."""
    s = s.strip().replace('.', '').replace(',', '.')
    try:
        return float(s)
    except:
        return None

def parse_2x_2n(lines):
    """Parse 2X/2N (export/import by commodity). Extract Cao su and Sản phẩm từ cao su."""
    results = []
    for line in lines:
        # Cao su (rubber) - has Tấn (tons)
        m = re.search(r'Cao su\s+Tấn\s+(\d[\d.]*)\s+([\d,.]+)\s+([-\d,.]+)\s+([-\d,.]+)\s+(\d[\d.]*)\s+([\d,.]+)\s+([-\d,.]+)\s+([-\d,.]+)', line)
        if m:
            results.append({
                'category': 'Cao su',
                'unit': 'Tấn',
                'month_qty': parse_number(m.group(1)),
                'month_value': parse_number(m.group(2)),
                'yoy_qty': parse_number(m.group(3)),
                'yoy_value': parse_number(m.group(4)),
                'cum_qty': parse_number(m.group(5)),
                'cum_value': parse_number(m.group(6)),
                'mom_qty': parse_number(m.group(7)),
                'mom_value': parse_number(m.group(8)),
            })
        # Sản phẩm từ cao su (rubber products) - USD only
        m = re.search(r'Sản phẩm từ cao su\s+USD\s+([\d,.]+)\s+([-\d,.]+)\s+([\d,.]+)\s+([-\d,.]+)', line)
        if m:
            results.append({
                'category': 'Sản phẩm từ cao su',
                'unit': 'USD',
                'month_qty': None,
                'month_value': parse_number(m.group(1)),
                'yoy_qty': None,
                'yoy_value': parse_number(m.group(2)),
                'cum_qty': None,
                'cum_value': parse_number(m.group(3)),
                'mom_qty': None,
                'mom_value': parse_number(m.group(4)),
            })
    return results

def parse_5x_5n(lines):
    """Parse 5X/5N (export/import by country). Extract Cao su and Sản phẩm từ cao su per country."""
    countries = []
    country_re = re.compile(r'^([A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴĐÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸ\s]+)(?:\s+\d[\d.,\s]*)?$')
    
    current_country = None
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Detect country line: all caps, followed by a total number
        # Country lines look like: "TRUNG QUỐC 3.428.083.048 3.428.083.048"
        m = country_re.match(line)
        if m and not any(kw in line for kw in ['Cao su', 'Tấn', 'USD', 'Sản phẩm', 'Hàng', 'Điện thoại', 'Máy móc', 'Giày dép', 'Túi xách', 'Dệt', 'Vải', 'Gỗ', 'Sắt thép', 'Sản phẩm từ', 'Nguyên phụ', 'Phương tiện', 'Hàng hóa khác']):
            current_country = m.group(1).strip()
            continue
        
        if current_country is None:
            continue
        
        # Cao su line
        m = re.search(r'Cao su\s+Tấn\s+(\d[\d.]*)\s+([\d,.]+)\s+(\d[\d.]*)\s+([\d,.]+)', line)
        if m:
            countries.append({
                'country': current_country,
                'category': 'Cao su',
                'month_qty': parse_number(m.group(1)),
                'month_value': parse_number(m.group(2)),
                'cum_qty': parse_number(m.group(3)),
                'cum_value': parse_number(m.group(4)),
            })
        
        # Sản phẩm từ cao su line
        m = re.search(r'Sản phẩm từ cao su\s+USD\s+([\d,.]+)\s+([\d,.]+)', line)
        if m:
            countries.append({
                'country': current_country,
                'category': 'Sản phẩm từ cao su',
                'month_qty': None,
                'month_value': parse_number(m.group(1)),
                'cum_qty': None,
                'cum_value': parse_number(m.group(2)),
            })
    
    return countries

def main():
    all_results = {}
    
    months = [str(m).zfill(2) for m in range(1, 13)]
    
    for month in months:
        month_dir = os.path.join(BASE, str(YEAR), month)
        if not os.path.isdir(month_dir):
            print(f"Skipping month {month} (no directory)")
            continue
        
        month_data = {}
        
        for ftype in ['2x', '2n', '5x', '5n']:
            json_path = os.path.join(month_dir, f'{ftype}.json')
            if not os.path.exists(json_path):
                continue
            
            data = load_json(json_path)
            lines = get_lines(data)
            
            if ftype in ('2x', '2n'):
                month_data[ftype] = parse_2x_2n(lines)
            else:
                month_data[ftype] = parse_5x_5n(lines)
        
        all_results[month] = month_data
        print(f"Month {month}: " + ", ".join(f"{k}: {len(v)} records" for k, v in month_data.items()))
    
    out_path = os.path.join(BASE, 'parsed_results.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"\nSaved to {out_path}")

if __name__ == '__main__':
    main()
