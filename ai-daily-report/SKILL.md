# AI日报 Skills

每天自动汇总AI领域的最新新闻，按板块分类呈现。

## 触发方式

- 手动触发：说"AI日报"、"生成AI日报"、"汇报AI新闻"等
- 定时任务：每天18:00自动执行

## 信息源（10个渠道）

### 中文AI资讯
- 知乎AI热榜：https://www.zhihu.com/topic/19550512/hot
- 36氪：https://www.36kr.com/information/AI/
- 机器之心：https://www.jiqizhixin.com/
- 量子位：https://www.qbitai.com/
- CSDN AI早间新闻：https://blog.csdn.net/nav/ai
- 新浪AI速递：https://k.sina.com.cn/channel/7857201856
- AIbase日报：https://aibase.cn/
- xix.ai实时：https://xix.ai/

### 英文AI资讯
- MIT Technology Review：https://www.technologyreview.com/ai/
- arXiv.org (AI论文)：https://arxiv.org/list/cs.AI/recent

## 输出格式要求

**固定七个板块（必须包含）：**
1. 🚀 **行业焦点** - 重大行业事件
2. 🧠 **大模型** - 大模型动态
3. 🤖 **产品&应用** - AI 产品发布、功能更新、应用落地相关
4. 💰 **资本市场** - 融资、市场表现
5. 📚 **研究&论文** - 论文、benchmark、研究突破、方法创新
6. 📜 **政策&产业动态** - 政策发布、产业趋势、企业动态
7. ⚠️ **风险&争议** - 安全、监管、争议事件

**可根据新闻内容酌情增加1-2个板块**

### 每条内容格式（必须包含）：

```markdown
**标题**
一句话总结：xxx
关键词：xxx
来源：[xxx](url)
```

### 每个板块要求
- 每个板块写 **3-5条** 内容
- 如果某板块当天没有足够新闻，至少保证2条

## 执行步骤

1. 使用 web-search-plus 搜索当天AI新闻
2. 从36氪、机器之心、量子位、新浪等渠道获取详细内容
3. 按上述七个固定板块分类整理
4. 每条新闻必须包含：标题、一句话总结、关键词、来源链接
5. 输出完整日报到文件：./AI日报-YYYY年M月D日.md
6. **创建飞书文档** — 使用 feishu_create_doc 将日报内容创建为飞书云文档，存入「OpenClaw 内容收录」知识库（导航页 node_token: YOUR_NODE_TOKEN）
7. **更新汇总索引** — 使用 feishu_update_doc 在汇总文档（doc_token=YOUR_DOC_TOKEN）最前面追加今日索引条目，格式：
   ```
   ## YYYY-MM-DD 星期X
   - [3-5条要点]概括当天最关键AI行业变化（每条15字内）
   - 🔗 [查看完整日报](今日日报文档链接)
   ```
8. **最后一步才输出文字** — 输出飞书文档链接和摘要，不要在中间步骤输出任何文字

## ⚠️ 重要提醒
- 步骤 6 和 7 **不可省略**！每次生成日报都必须创建飞书文档并更新汇总索引
- 全程不要输出中间状态，只在所有步骤完成后一次性输出结果

## 输出示例

```markdown
# 📰 AI日报 - 2026年3月3日

---

## 🚀 行业焦点

**标题**
一句话总结：xxx
关键词：xxx
来源：[xxx](url)

**标题2**
一句话总结：xxx
关键词：xxx
来源：[xxx](url)

---

## 🧠 大模型

...

## 🤖 产品&应用

...

## 💰 资本市场

...

## 📚 研究&论文

...

## 📜 政策&产业动态

...

## ⚠️ 风险&争议

...

---

*本日报由AI汇总 | 数据来源：36氪、机器之心、量子位、新浪、虎嗅等*
```

## 文件位置

- Skill文件：./skills/ai-daily-report/SKILL.md
- 日报输出：./AI日报-YYYY年M月D日.md
