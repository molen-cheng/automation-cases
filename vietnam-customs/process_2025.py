#!/usr/bin/env python3
"""
Vietnam Customs 2025 Rubber Data - Complete Pipeline
Downloads PDFs, extracts text, parses data, writes to bitable.
"""

import json
import os
import subprocess
import sys
import re
import urllib.request
import ssl

BASE_DIR = os.environ.get("VIETNAM_DATA_DIR", "./data/vietnam-customs")
DATA_DIR = f"{BASE_DIR}/2025"
PDFTOOL = os.environ.get("PDFTOOL_PATH", "pdftext")
APP_TOKEN = os.environ.get("FEISHU_APP_TOKEN", "")
TABLE_TOTAL = os.environ.get("FEISHU_TABLE_TOTAL", "")
TABLE_COUNTRY = os.environ.get("FEISHU_TABLE_COUNTRY", "")

# All PDF links collected from website
PDF_LINKS = {
    "01": {
        "2x": "https://files.customs.gov.vn/CustomsCMS/TONG_CUC/2025/2/6/2025-t1-2x(vn-sb).pdf",
        "2n": "https://files.customs.gov.vn/CustomsCMS/TONG_CUC/2025/2/6/2025-t1-2n(vn-sb).pdf",
        "5x": "https://files.customs.gov.vn/CustomsCMS/TONG_CUC/2025/2/6/2025-t1-5x(vn-sb).pdf",
        "5n": "https://files.customs.gov.vn/CustomsCMS/TONG_CUC/2025/2/6/2025-t1-5n(vn-sb).pdf",
    },
    "02": {
        "2x": "https://files.customs.gov.vn/CustomsCMS/TONG_CUC/2025/3/6/2025-t2-2x(vn-sb).pdf",
        "2n": "https://files.customs.gov.vn/CustomsCMS/TONG_CUC/2025/3/6/2025-t2-2n(vn-sb).pdf",
        "5x": "https://files.customs.gov.vn/CustomsCMS/TONG_CUC/2025/3/6/2025-t2-5x(vn-sb).pdf",
        "5n": None,  # Not available on website
    },
    "03": {
        "2x": "https://files.customs.gov.vn/CustomsCMS/TONG_CUC/2025/4/4/2025-t3-2x(vn-sb).pdf",
        "2n": "https://files.customs.gov.vn/CustomsCMS/TONG_CUC/2025/4/4/2025-t3-2n(vn-sb).pdf",
        "5x": "https://files.customs.gov.vn/CustomsCMS/TONG_CUC/2025/4/4/2025-t3-5x(vn-sb).pdf",
        "5n": "https://files.customs.gov.vn/CustomsCMS/TONG_CUC/2025/4/4/2025-t3-5n(vn-sb).pdf",
    },
    "04": {
        "2x": "https://files.customs.gov.vn/CustomsCMS/TONG_CUC/2025/5/6/2025-t4-2x(vn-sb).pdf",
        "2n": "https://files.customs.gov.vn/CustomsCMS/TONG_CUC/2025/5/6/2025-t4-2n(vn-sb).pdf",
        "5x": "https://files.customs.gov.vn/CustomsCMS/TONG_CUC/2025/5/6/2025-t4-5x(vn-sb).pdf",
        "5n": "https://files.customs.gov.vn/CustomsCMS/TONG_CUC/2025/5/6/2025-t4-5n(vn-sb).pdf",
    },
    "05": {
        "2x": "https://files.customs.gov.vn/CustomsCMS/TONG_CUC/2025/6/6/2025-t5-2x(vn-sb).pdf",
        "2n": "https://files.customs.gov.vn/CustomsCMS/TONG_CUC/2025/6/6/2025-t5-2n(vn-sb).pdf",
        "5x": "https://files.customs.gov.vn/CustomsCMS/TONG_CUC/2025/6/6/2025-t5-5x(vn-sb).pdf",
        "5n": "https://files.customs.gov.vn/CustomsCMS/TONG_CUC/2025/6/6/2025-t5-5n(vn-sb).pdf",
    },
    "06": {
        "2x": "https://files.customs.gov.vn/CustomsCMS/TONG_CUC/2025/7/7/2025-t6-2x(vn-sb).pdf",
        "2n": "https://files.customs.gov.vn/CustomsCMS/TONG_CUC/2025/7/7/2025-t6-2n(vn-sb).pdf",
        "5x": "https://files.customs.gov.vn/CustomsCMS/TONG_CUC/2025/7/7/2025-t6-5x(vn-sb).pdf",
        "5n": "https://files.customs.gov.vn/CustomsCMS/TONG_CUC/2025/7/7/2025-t6-5n(vn-sb).pdf",
    },
    "07": {
        "2x": "https://files.customs.gov.vn/CustomsCMS/TONG_CUC/2025/8/6/2025-t7-2x(vn-sb).pdf",
        "2n": "https://files.customs.gov.vn/CustomsCMS/TONG_CUC/2025/8/6/2025-t7-2n(vn-sb).pdf",
        "5x": None,  # Not available
        "5n": None,  # Not available
    },
    "08": {
        "2x": "https://files.customs.gov.vn/CustomsCMS/TONG_CUC/2025/9/5/2025-t8-2x(vn-sb).pdf",
        "2n": "https://files.customs.gov.vn/CustomsCMS/TONG_CUC/2025/9/5/2025-t8-2n(vn-sb).pdf",
        "5x": "https://files.customs.gov.vn/CustomsCMS/TONG_CUC/2025/9/5/2025-t8-5x(vn-sb).pdf",
        "5n": "https://files.customs.gov.vn/CustomsCMS/TONG_CUC/2025/9/5/2025-t8-5n(vn-sb).pdf",
    },
    "09": {
        "2x": "https://files.customs.gov.vn/CustomsCMS/TONG_CUC/2025/10/6/2025-t9-2x(vn-sb).pdf",
        "2n": "https://files.customs.gov.vn/CustomsCMS/TONG_CUC/2025/10/6/2025-t9-2n(vn-sb).pdf",
        "5x": None,  # Not available
        "5n": "https://files.customs.gov.vn/CustomsCMS/TONG_CUC/2025/10/6/2025-t9-5n(vn-sb).pdf",
    },
    "10": {
        "2x": "https://files.customs.gov.vn/CustomsCMS/TONG_CUC/2025/11/6/2025-t10-2x(vn-sb).pdf",
        "2n": "https://files.customs.gov.vn/CustomsCMS/TONG_CUC/2025/11/6/2025-t10-2n(vn-sb).pdf",
        "5x": "https://files.customs.gov.vn/CustomsCMS/TONG_CUC/2025/11/6/2025-t10-5x(vn-sb).pdf",
        "5n": "https://files.customs.gov.vn/CustomsCMS/TONG_CUC/2025/11/6/2025-t10-5n(vn-sb).pdf",
    },
    "11": {
        "2x": "https://files.customs.gov.vn/CustomsCMS/TONG_CUC/2025/12/8/2025-t11-2x(vn-sb).pdf",
        "2n": "https://files.customs.gov.vn/CustomsCMS/TONG_CUC/2025/12/8/2025-t11-2n(vn-sb).pdf",
        "5x": "https://files.customs.gov.vn/CustomsCMS/TONG_CUC/2025/12/8/2025-t11-5x(vn-sb).pdf",
        "5n": "https://files.customs.gov.vn/CustomsCMS/TONG_CUC/2025/12/8/2025-t11-5n(vn-sb).pdf",
    },
    "12": {
        "2x": "https://files.customs.gov.vn/CustomsCMS/TONG_CUC/2026/1/7/2025-t12-2x(vn-sb).pdf",
        "2n": None,  # Not available
        "5x": "https://files.customs.gov.vn/CustomsCMS/TONG_CUC/2026/1/7/2025-t12-5x(vn-sb).pdf",
        "5n": "https://files.customs.gov.vn/CustomsCMS/TONG_CUC/2026/3/9/2025-t12-5n(vn-sb).pdf",
    },
}

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
    """Parse Vietnamese number: dots=thousands, comma=decimal"""
    if not s or s.strip() in ('', '-', '...'):
        return 0
    s = s.strip().replace('.', '').replace(',', '.')
    try:
        return float(s)
    except:
        return 0

def download_pdf(url, dest):
    """Download PDF using Python urllib (avoids proxy SSL issues)"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    # Disable proxy
    proxy_handler = urllib.request.ProxyHandler({})
    opener = urllib.request.build_opener(proxy_handler, urllib.request.HTTPSHandler(context=ctx))
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with opener.open(req, timeout=30) as resp:
            data = resp.read()
            if len(data) > 1000:  # Valid PDF
                with open(dest, 'wb') as f:
                    f.write(data)
                return True
            return False
    except Exception as e:
        print(f"  Download failed: {e}")
        return False

def extract_text(pdf_path):
    """Extract text from PDF using pdftext"""
    try:
        result = subprocess.run(
            [PDFTOOL, "--sort", "--json", pdf_path],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0 and result.stdout:
            return json.loads(result.stdout)
        return None
    except Exception as e:
        print(f"  pdftext failed: {e}")
        return None

def parse_commodity_pdf(data, direction):
    """
    Parse 2X/2N commodity PDF data.
    direction: '出口' (export) or '进口' (import)
    Returns list of dicts with rubber/product data.
    """
    results = []
    if not data:
        return results
    
    # Get all text content from all pages
    all_text = ""
    for page in data:
        if isinstance(page, dict):
            texts = page.get('texts', [])
            for item in texts:
                if isinstance(item, dict):
                    all_text += " " + item.get('text', '')
                elif isinstance(item, str):
                    all_text += " " + item
        elif isinstance(page, list):
            for item in page:
                if isinstance(item, dict):
                    all_text += " " + item.get('text', '')
    
    # Search for "Cao su" rubber line
    # Pattern: number Cao su Tấn month_qty month_usd yoy_qty% yoy_usd% cum_qty cum_usd ...
    # Search for "Sản phẩm từ cao su" products line  
    # Pattern: number Sản phẩm từ cao su USD month_usd yoy% cum_usd yoy%
    
    lines = all_text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Rubber commodity line
        if re.search(r'\bCao su\b', line) and 'Sản phẩm' not in line and 'Tấn' in line:
            # Parse: seq Cao su Tấn qty usd yoy_qty yoy_usd cum_qty cum_usd ...
            parts = line.split()
            try:
                # Find the index of "Tấn"
                tan_idx = -1
                for i, p in enumerate(parts):
                    if p == 'Tấn':
                        tan_idx = i
                        break
                if tan_idx >= 0:
                    # Next values after Tấn are: qty, usd, yoy_qty%, yoy_usd%, cum_qty, cum_usd, ...
                    vals = parts[tan_idx+1:]
                    nums = []
                    for v in vals:
                        v = v.replace(',', '.')
                        try:
                            nums.append(float(v))
                        except:
                            break
                    if len(nums) >= 4:
                        results.append({
                            'direction': direction,
                            'category': '橡胶',
                            'month_qty': nums[0] if len(nums) > 0 else 0,
                            'month_amt': nums[1] / 10000 if len(nums) > 1 else 0,  # USD -> 万美元
                            'cum_qty': nums[4] if len(nums) > 4 else 0,
                            'cum_amt': nums[5] / 10000 if len(nums) > 5 else 0,
                            'yoy': nums[2] if len(nums) > 2 else None,
                        })
            except Exception as e:
                print(f"  Parse rubber line error: {e}, line: {line[:100]}")
        
        # Products line
        if 'Sản phẩm từ cao su' in line and 'USD' in line:
            parts = line.split()
            try:
                usd_idx = -1
                for i, p in enumerate(parts):
                    if p == 'USD':
                        usd_idx = i
                        break
                if usd_idx >= 0:
                    vals = parts[usd_idx+1:]
                    nums = []
                    for v in vals:
                        v = v.replace(',', '.')
                        try:
                            nums.append(float(v))
                        except:
                            break
                    if len(nums) >= 2:
                        results.append({
                            'direction': direction,
                            'category': '橡胶制品',
                            'month_qty': 0,  # No quantity for products
                            'month_amt': nums[0] / 10000,
                            'cum_qty': 0,
                            'cum_amt': nums[2] / 10000 if len(nums) > 2 else 0,
                            'yoy': nums[1] if len(nums) > 1 else None,
                        })
            except Exception as e:
                print(f"  Parse products line error: {e}, line: {line[:100]}")
    
    return results

def parse_country_pdf(data, direction):
    """
    Parse 5X/5N country cross-tabulation PDF.
    Returns list of dicts with country-level data.
    """
    results = []
    if not data:
        return results
    
    all_text = ""
    for page in data:
        if isinstance(page, dict):
            texts = page.get('texts', [])
            for item in texts:
                if isinstance(item, dict):
                    all_text += " " + item.get('text', '')
    
    lines = all_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Look for country names at the start of a line, followed by numbers
        for vn_name, cn_name in COUNTRY_MAP.items():
            if line.upper().startswith(vn_name.upper()) or line.startswith(vn_name):
                # This line has a country name
                remaining = line[len(vn_name):].strip()
                parts = remaining.split()
                nums = []
                for p in parts:
                    p = p.replace(',', '.')
                    try:
                        nums.append(float(p))
                    except:
                        break
                
                if len(nums) >= 2:
                    # Determine if this is rubber or products based on line content
                    # Country lines typically have: rubber_month_amt, rubber_cum_amt, products_month_amt, products_cum_amt
                    # Or sometimes just rubber data
                    is_products = 'Sản phẩm' in line or 'sản phẩm' in line
                    
                    entry = {
                        'direction': direction,
                        'country_cn': cn_name,
                        'country_vn': vn_name,
                    }
                    
                    if len(nums) >= 4:
                        # Assume: rubber values, then products values
                        entry['category'] = '橡胶' if not is_products else '橡胶制品'
                        entry['month_amt'] = nums[0] / 10000
                        entry['cum_amt'] = nums[1] / 10000
                        entry['month_qty'] = nums[2] if not is_products else 0
                        entry['cum_qty'] = nums[3] if not is_products else 0
                    elif len(nums) >= 2:
                        entry['category'] = '橡胶制品' if is_products else '橡胶'
                        entry['month_amt'] = nums[0] / 10000
                        entry['cum_amt'] = nums[1] / 10000
                        entry['month_qty'] = 0
                        entry['cum_qty'] = 0
                    
                    results.append(entry)
    
    return results


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    
    total_records = []
    country_records = []
    
    for month, types in PDF_LINKS.items():
        month_str = f"2025-{month}"
        print(f"\n=== Processing month {month_str} ===")
        
        for type_key, url in types.items():
            if url is None:
                print(f"  {type_key}: SKIPPED (not available)")
                continue
            
            local_file = f"{DATA_DIR}/{month}/{type_key}.pdf"
            os.makedirs(os.path.dirname(local_file), exist_ok=True)
            
            # Download
            if not os.path.exists(local_file) or os.path.getsize(local_file) < 1000:
                print(f"  Downloading {type_key}...")
                if not download_pdf(url, local_file):
                    print(f"  FAILED to download {type_key}")
                    continue
                print(f"  Downloaded: {os.path.getsize(local_file)} bytes")
            else:
                print(f"  Already exists: {local_file}")
            
            # Extract text
            json_file = local_file.replace('.pdf', '.json')
            if not os.path.exists(json_file):
                print(f"  Extracting text...")
                data = extract_text(local_file)
                if data:
                    with open(json_file, 'w') as f:
                        json.dump(data, f, ensure_ascii=False)
                else:
                    print(f"  FAILED to extract text")
                    continue
            else:
                with open(json_file) as f:
                    data = json.load(f)
            
            # Parse data
            direction = '出口' if type_key in ('2x', '5x') else '进口'
            
            if type_key in ('2x', '2n'):
                results = parse_commodity_pdf(data, direction)
                for r in results:
                    r['month'] = month_str
                    total_records.append(r)
                print(f"  Commodity: found {len(results)} records")
            elif type_key in ('5x', '5n'):
                results = parse_country_pdf(data, direction)
                for r in results:
                    r['month'] = month_str
                    country_records.append(r)
                print(f"  Country: found {len(results)} records")
    
    # Save parsed data
    with open(f"{BASE_DIR}/total_records_2025.json", 'w') as f:
        json.dump(total_records, f, ensure_ascii=False, indent=2)
    with open(f"{BASE_DIR}/country_records_2025.json", 'w') as f:
        json.dump(country_records, f, ensure_ascii=False, indent=2)
    
    print(f"\n=== Summary ===")
    print(f"Total records: {len(total_records)}")
    print(f"Country records: {len(country_records)}")
    
    # Print sample records
    if total_records:
        print("\nSample total records:")
        for r in total_records[:4]:
            print(f"  {r}")
    if country_records:
        print("\nSample country records:")
        for r in country_records[:4]:
            print(f"  {r}")


if __name__ == '__main__':
    main()
