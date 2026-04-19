#!/usr/bin/env python3
"""SHFE 仓单日报 - 通过Selenium抓取，支持多品种"""
import re, sys, time, json, hmac, hashlib, base64
from datetime import date, timedelta
from pathlib import Path
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

LOG_FILE = Path(__file__).parent / "shfe-br-warrant.log"
WEBHOOK_URL = os.environ.get("FEISHU_WEBHOOK_URL", "")
WEBHOOK_SECRET = os.environ.get("FEISHU_WEBHOOK_SECRET", "")
PAGE_TIMEOUT = 30  # 页面加载超时(秒)

# 品种别名 → (品种ID, 官方名称, 单位)
COMMODITY_MAP = {
    "br": ("br", "丁二烯橡胶", "吨"),
    "顺丁": ("br", "丁二烯橡胶", "吨"),
    "顺丁橡胶": ("br", "丁二烯橡胶", "吨"),
    "丁二烯": ("br", "丁二烯橡胶", "吨"),
    "丁二烯橡胶": ("br", "丁二烯橡胶", "吨"),
    "ru": ("ru", "天然橡胶", "吨"),
    "橡胶": ("ru", "天然橡胶", "吨"),
    "天然橡胶": ("ru", "天然橡胶", "吨"),
    "cu": ("cu", "铜", "吨"),
    "铜": ("cu", "铜", "吨"),
    "al": ("al", "铝", "吨"),
    "铝": ("al", "铝", "吨"),
    "zn": ("zn", "锌", "吨"),
    "锌": ("zn", "锌", "吨"),
    "pb": ("pb", "铅", "吨"),
    "铅": ("pb", "铅", "吨"),
    "ni": ("ni", "镍", "吨"),
    "镍": ("ni", "镍", "吨"),
    "sn": ("sn", "锡", "吨"),
    "锡": ("sn", "锡", "吨"),
    "au": ("au", "黄金", "千克"),
    "黄金": ("au", "黄金", "千克"),
    "金": ("au", "黄金", "千克"),
    "ag": ("ag", "白银", "千克"),
    "白银": ("ag", "白银", "千克"),
    "银": ("ag", "白银", "千克"),
    "rb": ("rb", "螺纹钢", "吨"),
    "螺纹": ("rb", "螺纹钢", "吨"),
    "螺纹钢": ("rb", "螺纹钢", "吨"),
    "hc": ("hc", "热轧卷板", "吨"),
    "热卷": ("hc", "热轧卷板", "吨"),
    "热轧卷板": ("hc", "热轧卷板", "吨"),
    "ss": ("ss", "不锈钢", "吨"),
    "不锈钢": ("ss", "不锈钢", "吨"),
    "sc": ("sc", "中质含硫原油", "桶"),
    "原油": ("sc", "中质含硫原油", "桶"),
    "bu": ("bu", "石油沥青", "吨"),
    "沥青": ("bu", "石油沥青", "吨"),
    "石油沥青": ("bu", "石油沥青", "吨"),
    "fu": ("fu", "燃料油", "吨"),
    "燃料油": ("fu", "燃料油", "吨"),
    "lu": ("lu", "低硫燃料油", "吨"),
    "低硫": ("lu", "低硫燃料油", "吨"),
    "低硫燃料油": ("lu", "低硫燃料油", "吨"),
    "sp": ("sp", "纸浆", "吨"),
    "纸浆": ("sp", "纸浆", "吨"),
    "ao": ("ao", "氧化铝", "吨"),
    "氧化铝": ("ao", "氧化铝", "吨"),
}

def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def send_feishu(msg):
    try:
        ts = str(int(time.time()))
        string_to_sign = f"{ts}\n{WEBHOOK_SECRET}"
        hmac_code = hmac.new(string_to_sign.encode("utf-8"), digestmod=hashlib.sha256).digest()
        sig = base64.b64encode(hmac_code).decode("utf-8")
        resp = requests.post(WEBHOOK_URL, json={
            "msg_type": "text",
            "content": {"text": msg},
            "timestamp": ts,
            "sign": sig,
        }, timeout=10)
        if resp.status_code != 200 or resp.json().get("code") != 0:
            log(f"推送失败: {resp.status_code} {resp.text}")
        else:
            log("  推送成功")
    except Exception as e:
        log(f"推送失败: {e}")

def create_driver():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    opts.page_load_strategy = "eager"  # 不等全部资源加载，DOM就绪即返回
    opts.timeout = PAGE_TIMEOUT
    return webdriver.Chrome(options=opts)

def pick_date(driver, wait, date_str):
    driver.get("https://www.shfe.com.cn/reports/tradedata/dailyandweeklydata/?query_params=dailystock")
    target_day = date_str.split("-")[2].lstrip("0")
    # 等待日历 td 出现（最多等10秒）
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "td")))
    except Exception:
        return "timeout"
    cells = driver.find_elements(By.TAG_NAME, "td")
    for cell in cells:
        cls = cell.get_attribute("class") or ""
        if "other_month" in cls:
            continue
        txt = cell.text.strip().lstrip("0")
        if txt == target_day:
            cell.click()
            # 等待数据表格出现（最多等15秒）
            try:
                wait.until(lambda d: "没有此日期的数据" in (d.find_element(By.TAG_NAME, "body").text or "") or
                           bool(d.find_elements(By.CSS_SELECTOR, "table")))
            except Exception:
                pass
            body = driver.find_element(By.TAG_NAME, "body").text
            if "没有此日期的数据" in body:
                return "no_data"
            m = re.search(r"(\d{4}-\d{2}-\d{2})", body)
            if m and m.group(1) != date_str:
                return "wrong_date"
            return "ok"
    return "not_found"

def parse_rows_from_html(table_html, cname, name_first=False):
    """通用解析表格行
    name_first=False: 仓库格式 [地区, 名称, 数量, 增减]
    name_first=True:  厂库格式 [名称, 地区, 数量, 增减]
    返回 (total_qty, total_change, detail_rows)
    """
    rows = []
    current_group = ""

    for tr in re.finditer(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL):
        raw = tr.group(1)
        tds = re.findall(r'<td[^>]*>(.*?)</td>', raw, re.DOTALL)
        cells = [re.sub(r'<[^>]+>', '', td).strip() for td in tds]

        if not cells:
            continue

        is_total_row = "isTotal" in raw
        has_colspan = 'colspan' in raw
        text_joined = ''.join(cells)
        is_grand_total = ('总计' in cells[0] if cells else False) or ('总计' in text_joined and has_colspan)

        if is_grand_total and len(cells) <= 4:
            nums = []
            for c in reversed(cells):
                try:
                    nums.insert(0, int(c))
                except ValueError:
                    pass
                if len(nums) == 2:
                    break
            if len(nums) == 2:
                return (nums[0], nums[1], rows)
            continue

        if len(cells) < 3:
            continue

        is_merged = len(cells) == 3
        first = cells[0]
        if first in ("地区", "厂库") or "单位" in first:
            continue
        # 跳过标题行（品种名）
        if name_first and first == f"{cname}(厂库)":
            continue

        try:
            if is_merged:
                qty = int(cells[1])
                change = int(cells[2])
            else:
                qty = int(cells[2])
                change = int(cells[3])
        except (ValueError, IndexError):
            continue

        if is_merged:
            if name_first:
                col1_name = current_group
                col2_group = cells[0] if cells[0] else cells[1]
            else:
                col1_name = cells[0]
                col2_group = current_group
        elif not first and current_group:
            if name_first:
                col1_name = current_group
                col2_group = cells[0] if cells[0] else cells[1]
            else:
                col1_name = cells[1] if len(cells) > 1 and cells[1] else cells[0]
                col2_group = current_group

        is_subtotal = is_total_row or first == "合计"

        if is_merged or (not first and current_group):
            pass
        elif name_first:
            col1_name = first
            col2_group = cells[1]
            if first not in ("合计", "总计"):
                current_group = first
        else:
            col1_name = cells[1]
            col2_group = first
            if first not in ("合计", "总计"):
                current_group = first

        rows.append({
            "group": current_group,
            "sub_group": col2_group if name_first else "",
            "name": col1_name,
            "qty": qty,
            "change": change,
            "is_subtotal": is_subtotal,
        })

    return (0, 0, rows)

def format_result(wh_total, wh_change, wh_rows, fc_total, fc_change, fc_rows, unit="吨"):
    lines = []

    wh_changes = [r for r in wh_rows if r["change"] != 0 and not r["is_subtotal"]]
    fc_changes = [r for r in (fc_rows or []) if r["change"] != 0 and not r["is_subtotal"]]

    if not wh_changes and not fc_changes:
        lines.append("今日无变化")
    else:
        if wh_changes:
            lines.append("仓库变化量明细：")
            region_changes = {}
            for r in wh_changes:
                region_changes.setdefault(r["group"], []).append(r)
            wh_subtotal = 0
            for region, items in region_changes.items():
                region_total = sum(r["change"] for r in items)
                wh_subtotal += region_total
                for r in items:
                    lines.append(f"{region} {r['name']} {r['change']:+d}")
            lines.append(f"仓库小计：{wh_subtotal:+d}")

        if fc_changes:
            lines.append("厂库变化量明细：")
            factory_changes = {}
            for r in fc_changes:
                factory_changes.setdefault(r["group"], []).append(r)
            fc_subtotal = 0
            for factory, items in factory_changes.items():
                factory_total = sum(r["change"] for r in items)
                fc_subtotal += factory_total
                for r in items:
                    lines.append(f"{factory} {r['sub_group']} {r['change']:+d}")
            lines.append(f"厂库小计：{fc_subtotal:+d}")

    total_qty = wh_total + fc_total
    total_change = wh_change + fc_change

    lines.append("汇总：")
    if fc_total:
        lines.append(f"仓单总量：{total_qty:,} {unit}（仓库 {wh_total:,} + 厂库 {fc_total:,}）")
    else:
        lines.append(f"仓单总量：{total_qty:,} {unit}")
    lines.append(f"当日总变化量：{total_change:+,} {unit}")
    return "\n".join(lines)

def resolve_commodity(name):
    if not name:
        return None, None, None
    key = name.strip().lower()
    return COMMODITY_MAP.get(key, (None, None, None))

def list_commodities():
    seen = set()
    result = []
    for cid, cname, unit in COMMODITY_MAP.values():
        if cid not in seen:
            seen.add(cid)
            result.append(f"  {cid} - {cname}（{unit}）")
    return "\n".join(result)

def main():
    args = sys.argv[1:]
    commodity_input = None
    target_date = None

    if args:
        if args[0] in ("--list", "-l", "list"):
            print(list_commodities())
            return
        cid, cname, cunit = resolve_commodity(args[0])
        if cid:
            commodity_input = args[0]
            if len(args) > 1:
                target_date = args[1]
        else:
            target_date = args[0]

    if not commodity_input:
        commodity_input = "br"
    cid, cname, cunit = resolve_commodity(commodity_input)
    if not cid:
        log(f"未知品种: {commodity_input}")
        print(f"未知品种: {commodity_input}\n支持的品种:\n{list_commodities()}")
        return

    today = date.today()
    dates = [target_date] if target_date else [today, today - timedelta(days=1)]

    for d in dates:
        date_str = d.strftime("%Y-%m-%d") if isinstance(d, date) else d

        driver = create_driver()
        wait = WebDriverWait(driver, PAGE_TIMEOUT)
        try:
            log(f"获取 {date_str} {cname}仓单数据...")
            result = pick_date(driver, wait, date_str)
            if result != "ok":
                log(f"  {date_str}: {result}")
                driver.quit()
                continue

            html = driver.page_source

            # 解析仓库表
            wh_label = f"{cname}(仓库)"
            wh_idx = html.find(wh_label)
            if wh_idx == -1:
                log(f"  未找到{cname}仓库数据")
                driver.quit()
                continue
            wh_table = html[html.rfind("<table", 0, wh_idx):html.find("</table>", wh_idx) + 8]
            wh_total, wh_change, wh_rows = parse_rows_from_html(wh_table, cname, name_first=False)

            # 解析厂库表
            fc_label = f"{cname}(厂库)"
            fc_idx = html.find(fc_label)
            fc_total, fc_change, fc_rows = 0, 0, []
            if fc_idx != -1:
                fc_table = html[html.rfind("<table", 0, fc_idx):html.find("</table>", fc_idx) + 8]
                fc_total, fc_change, fc_rows = parse_rows_from_html(fc_table, cname, name_first=True)

            text = format_result(wh_total, wh_change, wh_rows, fc_total, fc_change, fc_rows, unit=cunit)
            msg = f"{cname}仓单日报 {date_str}\n\n{text}"
            log(msg)
            send_feishu(msg)
            driver.quit()
            return
        except Exception as e:
            import traceback
            log(f"  错误: {e}\n{traceback.format_exc()}")
            driver.quit()
            continue

    log("所有日期均无数据")

if __name__ == "__main__":
    main()
