---
name: market-breadth-heatmap
description: "大盘云图市场宽度热力图生成。从 sckd.dapanyuntu.com 获取一级行业 MA20 站上率数据，按行业聚合后生成浅色系 3:4 比例热力图 PNG 图片。触发词：市场宽度、鱼盆热力图、大盘云图热力图、行业MA20站上率"
version: "2.0.0"
---

# 市场宽度热力图

大盘云图数据 → 浅色系热力图 PNG。一级行业 MA20 站上率变化追踪。

## 规则

- **数据来源**：`https://sckd.dapanyuntu.com/`，每日 16:00 更新
- **输出格式**：3:4 比例（690×920px）浅色系 PNG 图片
- **行业层级**：86 个二级行业 → 26 个一级行业大类聚合（取均值）
- **色阶**：0-100，浅色系渐变（淡紫 → 浅蓝 → 浅绿 → 浅黄 → 浅橙）
- **时间范围**：默认最近 31 个交易日（约 6 周）
- **数据聚合**：过滤 0 值（无数据），对有效值取算术平均
- **截图引擎**：Playwright Chromium（来自 ljg-card 的 capture.js）
- **质控标准**：
  - 26 个一级行业全部显示
  - 31 个日期列全部对齐
  - 颜色与数值对应准确
  - 底部统计正确（最强/最弱行业、全市场均值）
  - PNG 文件清晰、无截断、无渲染残留

## 工作流程

### Step 1：获取原始数据

读取 `<skill-base>/references/data-fetch.md`，按其步骤获取 API 数据。

数据结构：
```json
{
  "data": [[date_idx, industry_idx, value], ...],
  "dates": ["2026-02-24", ...],
  "industries": ["专业服务", "专用设备", ...],
  "page": 0,
  "start_date": "2026-02-23",
  "end_date": "2026-04-09"
}
```

### Step 2：按一级行业聚合

读取 `<skill-base>/references/industry-mapping.md`，将 86 个二级行业映射到 26 个一级行业大类。

聚合逻辑：
- 对每个 `(category, date)` 组合，收集所有子行业的有效值（>0）
- 计算算术平均值，保留 1 位小数
- 按最新日期的值降序排列行业

执行：
```bash
cd "<skill-base>" && python3 scripts/generate.py --mode aggregate --input <raw_data.json> --output aggregated_data.json
```

### Step 3：生成浅色系热力图 HTML

使用 `<skill-base>/assets/heatmap_template.html` 作为模板，注入聚合后的数据。

模板特点：
- 浅色背景：`#ffffff`
- 浅色系色阶：`#e0e7ff` → `#bae6fd` → `#bbf7d0` → `#fef08a` → `#fdba74`
- 3:4 比例：690×920px
- 响应式布局：flexbox + gap

执行：
```bash
cd "<skill-base>" && python3 scripts/generate.py --mode render --input aggregated_data.json --template assets/heatmap_template.html --output heatmap.html
```

### Step 4：HTML → PNG 截图

使用 Playwright 将 HTML 渲染为 PNG 图片。

截图工具：`<skill-base>/assets/capture.js`（来自 ljg-card）

```bash
cd "<skill-base>" && python3 scripts/generate.py --mode capture --input heatmap.html --output market_breadth_heatmap.png
```

依赖安装（首次使用）：
```bash
cd "<skill-base>" && npm install && npx playwright install chromium
```

### Step 5：质控检查

验证 PNG 输出：
1. 打开 PNG 文件，检查：
   - 26 个行业标签全部可见
   - 31 个日期列全部对齐
   - 颜色渐变平滑，数值与颜色对应
   - 底部统计正确
   - 图片清晰、无截断
2. 检查文件大小：约 50-200 KB
3. 确认 3:4 比例：690×920px

### Step 6：交付

报告文件路径：
```
[查看热力图](computer:///workspace/market_breadth_heatmap.png)
```

## 输出格式

最终交付物为单个 PNG 图片文件（690×920px），通过 HTML 中间产物渲染生成。

文件命名：`market_breadth_heatmap.png`

## 依赖

- Python 3（数据获取 + 聚合）
- Node.js + Playwright Chromium（HTML → PNG 截图）
- 依赖声明：`<skill-base>/package.json`
