#!/usr/bin/env python3
"""Download 2024 Vietnam customs PDFs efficiently."""
import os, urllib.request, ssl

BASE = "/home/orange/.openclaw/workspace/data/vietnam-customs/2024"
ctx = ssl.create_default_context()

def try_download(url, dest):
    try:
        req = urllib.request.Request(url, method='HEAD')
        resp = urllib.request.urlopen(req, timeout=5, context=ctx)
        cl = int(resp.headers.get('Content-Length', 0))
        if cl > 5000:
            print(f"FOUND -> {url} ({cl})")
            urllib.request.urlretrieve(url, dest)
            return True
    except:
        pass
    return False

def build_urls(month, ftype):
    urls = []
    for suffix in ["vn-sb", "VN-SB", "TA-SB"]:
        for T in ["T", "t"]:
            for F in [ftype.upper(), ftype]:
                urls.append(f"2024-{T}{month}-{F}({suffix}).pdf")
    return urls

for m in range(1, 13):
    month = f"{m:02d}"
    os.makedirs(f"{BASE}/{month}", exist_ok=True)
    for ftype in ['2x', '2n', '5x', '5n']:
        dest = f"{BASE}/{month}/{ftype}.pdf"
        if os.path.exists(dest):
            print(f"EXISTS: {month} {ftype}")
            continue
        found = False
        filenames = build_urls(month, ftype)
        # Try pub month = month+1, month+2, then same month
        for pm in [m+1, m+2, m]:
            if pm > 12: continue
            for pd in range(4, 28):
                for fn in filenames:
                    url = f"https://files.customs.gov.vn/CustomsCMS/TONG_CUC/2024/{pm}/{pd}/{fn}"
                    if try_download(url, dest):
                        found = True; break
                if found: break
            if found: break
        if not found:
            print(f"MISSING: {month} {ftype}")

print("Done.")
