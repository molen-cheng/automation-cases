#!/usr/bin/env python3
"""合成橡胶装置日报 - Playwright 版（AB测试用）
直接用 Playwright API，单进程完成所有品种抓取，不经过 openclaw browser CLI"""
import asyncio, re, sys, json, time
from datetime import date
from pathlib import Path
from playwright.async_api import async_playwright

SECRETS_FILE = Path(os.environ.get("SECRETS_PATH", "")) if os.environ.get("SECRETS_PATH") else None
DATA_DIR = Path(os.environ.get("DATA_DIR", "./data"))

VARIANTS = [
    {
        "name": "SBS", "url": "https://rubb.oilchem.net/rubber/sbs.shtml",
        "link_text": "SBS生产企业装置一览表", "subdir": "sbs",
        "header": "| 企业性质 | 企业名称 | 产能（万吨/年） | SBS装置运行现状 |",
        "has_category": True,
    },
    {
        "name": "SBR", "url": "https://rubb.oilchem.net/361/43874/",
        "link_text": "丁苯橡胶企业装置一览表", "subdir": "sbr",
        "header": "| 企业性质 | 企业名称 | 产能（万吨/年） | 丁苯橡胶装置运行现状 |",
        "has_category": True,
    },
    {
        "name": "BR", "url": "https://list.oilchem.net/360/44347/",
        "link_text": "顺丁橡胶企业装置一览表", "subdir": "br",
        "header": "| 企业性质 | 企业名称 | 产能（万吨/年） | 装置运行现状 |",
        "has_category": False,
    },
]


def load_credentials():
    if not SECRETS_FILE.exists():
        return None, None
    data = json.loads(SECRETS_FILE.read_text())
    return data.get("username"), data.get("password")


def parse_tables(raw_text, variant_name, date_display, has_category):
    """解析 extract_body 返回的原始文本，生成 Markdown"""
    lines = raw_text.strip().splitlines()
    it = iter(lines)
    title, publish = "", ""
    for line in it:
        if line.startswith("TITLE:"):
            title = line[6:].strip()
        elif line.startswith("PUBLISH:"):
            publish = line[8:].strip()
        elif line.startswith("TABLES:"):
            break

    if not title:
        title = f"{variant_name}生产企业装置一览表（{date_display}）"

    all_rows = []
    for line in it:
        if line.startswith("---TABLE") or line.startswith("---ENDTABLE"):
            continue
        cells = [c.strip() for c in line.split("|")]
        if cells and any(c for c in cells):
            all_rows.append(cells)

    skip = {"企业性质", "企业名称", "产能", "装置运行", "SBS装置运行现状",
            "丁苯橡胶装置运行现状", "顺丁橡胶装置运行现状", "未来变动计划",
            "备注", "数据来源：隆众资讯", "中石化", "中石油", "其他企业"}
    data_rows = [r for r in all_rows if len([c for c in r if c and c not in skip]) >= 2
                 and not all(c in skip for c in r)]

    rows_out = []
    if has_category:
        cat = ""
        for r in data_rows:
            if r[0] in {"中石化", "中石油", "其他企业"}:
                cat = r[0]; continue
            while len(r) < 4: r.append("")
            rows_out.append((cat, r[0], r[1], r[2]))
    else:
        for r in data_rows:
            while len(r) < 4: r.append("")
            if r[0] == "-": continue
            rows_out.append(("", r[0], r[1], r[2]))

    md = [f"# {title}"]
    if publish:
        md += ["", publish]
    md += ["", "单位：万吨/年", "", variant_name and "" or "", variant_name and "" or ""]
    md.append("")  # clear above
    md = [f"# {title}"]
    if publish:
        md += ["", publish]
    md += ["", "单位：万吨/年", ""]

    # Use the header from variant config
    return md  # caller will add header


async def login_if_needed(page):
    """检查登录状态，未登录则自动登录"""
    text = await page.evaluate("document.body.innerText")
    if "会员中心" in text or "退出" in text:
        print("  Login OK (cached)")
        return True

    username, password = load_credentials()
    if not username or not password:
        print("  WARNING: No credentials, skipping login")
        return False

    print("  Logging in...")
    # 点击"点我登录"
    try:
        await page.click("text=点我登录", timeout=5000)
    except Exception:
        try:
            await page.click("a:has-text('点我登录')", timeout=3000)
        except Exception:
            print("  WARNING: Login link not found")
            return False

    await page.wait_for_timeout(2000)
    # 填写用户名密码
    inputs = await page.query_selector_all("input[type='text'], input[type='password'], input:not([type])")
    text_inputs = [i for i in inputs if await i.get_attribute("type") in (None, "", "text")]
    pass_inputs = [i for i in inputs if await i.get_attribute("type") == "password"]

    if len(text_inputs) >= 1 and len(pass_inputs) >= 1:
        await text_inputs[0].fill(username)
        await pass_inputs[0].fill(password)
        # 点击登录按钮
        btn = await page.query_selector("button:has-text('登录')")
        if btn:
            await btn.click()
            await page.wait_for_timeout(3000)
            print("  Login done")
            return True
    print("  WARNING: Login form not found")
    return False


async def fetch_variant(browser, variant):
    """抓取单个品种"""
    name = variant["name"]
    today_str = date.today().strftime("%Y%m%d")
    date_display = date.today().strftime("%Y%m%d")
    subdir = variant["subdir"]
    has_category = variant["has_category"]
    out_dir = DATA_DIR / subdir
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / (date.today().strftime("%Y-%m-%d") + ".md")

    print(f">>> [{name}] Opening {variant['url']}")
    page = await browser.new_page()
    try:
        await page.goto(variant["url"], wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_timeout(2000)
        await login_if_needed(page)

        # 查找并点击最新文章链接
        link_text = variant["link_text"]
        pattern = re.compile(re.escape(link_text) + r"（(\d{8})）")
        print(f">>> [{name}] Looking for article...")
        links = await page.query_selector_all("a")
        clicked = False
        for link in links:
            txt = (await link.inner_text()).strip()
            m = pattern.search(txt)
            if m:
                article_date = m.group(1)
                if article_date < today_str:
                    print(f">>> [{name}] Latest article is {article_date}, not today. Skipping.")
                    return None
                await link.click()
                clicked = True
                break

        if not clicked:
            print(f">>> [{name}] No matching article found. Skipping.")
            return None

        # 等待新标签页打开
        await page.wait_for_timeout(2000)
        pages = browser.contexts[0].pages
        # 最后一个页面应该是新打开的文章页
        article_page = pages[-1] if len(pages) > 1 else page
        await article_page.wait_for_timeout(2000)

        # 提取表格数据
        print(f">>> [{name}] Extracting table...")
        raw = await article_page.evaluate("""() => {
            const article = document.querySelector(".article-content") || document.body;
            const tables = article.querySelectorAll("table");
            const titleEl = article.querySelector("h1, .article-title");
            const title = titleEl ? titleEl.innerText.trim() : "";
            const publishEl = article.querySelector(".article-info, .pub-time");
            const publish = publishEl ? publishEl.innerText.trim() : "";
            let result = "TITLE:" + title + "\\n";
            result += "PUBLISH:" + publish + "\\n";
            result += "TABLES:" + tables.length + "\\n";
            tables.forEach((t, i) => {
                result += "---TABLE " + i + "---\\n";
                t.querySelectorAll("tr").forEach(tr => {
                    const cells = [];
                    tr.querySelectorAll("td, th").forEach(td => cells.push(td.innerText.trim()));
                    result += cells.join("|") + "\\n";
                });
                result += "---ENDTABLE---\\n";
            });
            return result;
        }""")

        # 关闭文章标签页
        if len(pages) > 1:
            await article_page.close()

        # 解析并生成 Markdown
        lines = raw.strip().splitlines()
        it = iter(lines)
        title, publish = "", ""
        for line in it:
            if line.startswith("TITLE:"): title = line[6:].strip()
            elif line.startswith("PUBLISH:"): publish = line[8:].strip()
            elif line.startswith("TABLES:"): break

        if not title:
            title = f"{variant['link_text'].split('企业')[0]}生产企业装置一览表（{date_display}）"

        all_rows = []
        for line in it:
            if line.startswith("---TABLE") or line.startswith("---ENDTABLE"): continue
            cells = [c.strip() for c in line.split("|")]
            if cells and any(c for c in cells): all_rows.append(cells)

        skip_headers = {"企业性质", "企业名称", "产能", "装置运行",
                        "SBS装置运行现状", "丁苯橡胶装置运行现状", "顺丁橡胶装置运行现状",
                        "未来变动计划", "备注", "数据来源：隆众资讯",
                        "中石化", "中石油", "其他企业"}
        data_rows = [r for r in all_rows
                     if len([c for c in r if c and c not in skip_headers]) >= 2
                     and not all(c in skip_headers for c in r)]

        rows_out = []
        if has_category:
            cat = ""
            for r in data_rows:
                if r[0] in {"中石化", "中石油", "其他企业"}:
                    cat = r[0]; continue
                while len(r) < 4: r.append("")
                rows_out.append((cat, r[0], r[1], r[2]))
        else:
            for r in data_rows:
                while len(r) < 4: r.append("")
                if r[0] == "-": continue
                rows_out.append(("", r[0], r[1], r[2]))

        md = [f"# {title}"]
        if publish: md += ["", publish]
        md += ["", "单位：万吨/年", "", variant["header"], "|---|---|---:|---|"]
        for cat, n, cap, st in rows_out:
            md.append(f"| {cat} | {n} | {cap} | {st} |")
        md += ["", "数据来源：隆众资讯", ""]

        out_file.write_text("\n".join(md), encoding="utf-8")
        print(f">>> [{name}] Saved: {out_file}")
        return str(out_file)

    except Exception as e:
        print(f">>> [{name}] Error: {e}")
        return None
    finally:
        await page.close()


async def main():
    t0 = time.time()
    targets = sys.argv[1:] if len(sys.argv) > 1 else ["sbs", "sbr", "br"]
    targets = [t.lower() for t in targets]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=[
            "--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"
        ])
        results = []
        for v in VARIANTS:
            if v["name"].lower() in targets or "all" in targets:
                r = await fetch_variant(browser, v)
                if r:
                    results.append(r)

        await browser.close()

    elapsed = time.time() - t0
    print(f"\nDone in {elapsed:.1f}s, {len(results)} variants saved.")
    return results


if __name__ == "__main__":
    asyncio.run(main())
