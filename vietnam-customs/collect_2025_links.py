#!/usr/bin/env python3
"""
Automate Vietnam customs PDF link collection for all 12 months of 2025.
Usage: python3 collect_2025_links.py
Outputs: pdf_links_2025.json with all discovered PDF URLs organized by month.
"""
import json
import os
import subprocess
import sys
import time
import base64

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT = os.path.join(DATA_DIR, "pdf_links_2025.json")

# Country name mapping
COUNTRY_MAP = {
    "TRUNG QUỐC": "中国", "HOA KỲ": "美国", "NHẬT BẢN": "日本",
    "HÀN QUỐC": "韩国", "ẤN ĐỘ": "印度", "THÁI LAN": "泰国",
    "CAMPUCHIA": "柬埔寨", "MALAYSIA": "马来西亚", "INDONÊXIA": "印尼",
    "SINGAPORE": "新加坡", "ĐÀI LOAN": "台湾", "ÚC": "澳大利亚",
    "HÀ LAN": "荷兰", "ĐỨC": "德国", "PHÁP": "法国",
    "BỈ": "比利时", "Ý": "意大利", "ANH": "英国",
    "HỒNG KÔNG": "香港", "PHILIPPINES": "菲律宾",
}

def parse_vn_number(s):
    """Parse Vietnamese number format (dots as thousand separators, comma as decimal)"""
    if not s or s.strip() in ('', '-'):
        return 0
    s = s.strip().replace('.', '').replace(',', '.')
    try:
        return float(s)
    except:
        return 0

def extract_commodity_data(json_path, direction):
    """Extract rubber data from commodity PDF JSON.
    direction: 'X' for export, 'N' for import
    Returns dict with rubber and products data
    """
    import json as j
    with open(json_path) as f:
        data = j.load(f)
    
    pages = data if isinstance(data, list) else data.get('pages', [])
    
    result = {'rubber': None, 'products': None}
    
    for page in pages:
        texts = page if isinstance(page, list) else page.get('texts', [])
        
        # Build text lines for analysis
        lines = []
        current_line = ""
        for item in texts:
            if isinstance(item, dict):
                text = item.get('text', '')
                bbox = item.get('bbox', [])
                # Simple: just collect all text
                if text:
                    lines.append(text)
            elif isinstance(item, str):
                lines.append(item)
        
        full_text = ' '.join(lines)
        
        # Search for rubber line: "Cao su" with "Tấn"
        # Search for products line: "Sản phẩm từ cao su" with "USD"
        
        for i, line in enumerate(lines):
            if 'Cao su' in line and 'Tấn' not in line and 'Sản phẩm' not in line:
                # This might be a header or part of a line
                pass
            if 'Cao su' in line and 'Tấn' in line:
                # Rubber commodity line
                result['rubber'] = {'raw_line': line}
            if 'Sản phẩm từ cao su' in line and 'USD' in line:
                result['products'] = {'raw_line': line}
    
    return result

# This is a helper - main work will be done via browser automation
print("See collect_links_via_browser.js for the main collection logic.")
