# 自动化案例

自动化脚本合集。

## 周报自动化

丁二烯&合成周报 PPT 图表刷新和表格数据更新。

| 脚本 | 作用 |
|------|------|
| `refresh_weekly.ps1` | 刷新周度图表（25页） |
| `refresh_all.ps1` | 刷新全部53页图表 |
| `update_tables.ps1` | 更新19个表格数据 |
| `table_mapping.xlsx` | 表格映射配置（PPT页码→Excel区域） |

### 依赖

- PowerPoint（COM自动化）
- Excel（已打开日度.xlsx、周度数据库.xlsx）
- 坚果云同步目录
