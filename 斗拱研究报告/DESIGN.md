# DESIGN.md · 斗拱研究报告

## 一、全局视觉约定

### ① 画布与安全区
- 画布 1280×720
- padding：上下 60 / 左右 60
- 内容区 1160×600
- 内容页母版：顶部深蓝标题条（1160×56）→ gap 24 → 主体区（1160×520）
- 页脚位于 y=670 带内（字号 14，深灰）

### ② 配色方案（学术宝蓝 + 木色图示）

| 槽位 | Hex | 用途 |
|---|---|---|
| 主色 | `#1E4FA8` | 标题条 / 编号 / 强调 / 图示结构线 |
| 辅色 | `#3D7BD9` / `#E8EFF8` | 图表第二色 / 浅底条 |
| 图示木色 | `#9C7A5B`（深）/ `#C9A882`（浅） | 斗拱构件填充——仅用于示意图，模拟测绘图纸的木色 |
| 强调色 | `#D9534F` | 关键发现、异常值、核心标注，全篇 ≤3% |
| 底色 | `#FFFFFF` | 主背景 |
| 正文色 | `#1A2230` / `#4A5568` / `#8B97A8` | 主 / 副 / 辅助 |
| 辅底 | `#F7F9FC` | 局部卡片底、表头底 |
| 分隔线 | `#D6DCE5` / `#E5E7EB` | 描边、表格线 |

纪律：蓝族 20-40%，白底 ≥60%，红 ≤3%，金色 0。

### ③ 字体系统
- 中文：`"Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif`
- 西文数字：`Arial, Helvetica, sans-serif`
- 字号阶梯：封面主标 64 / 章节大字 180 / 页主标 34 / 卡内小标 22 / 正文 20 / 表格 17 / 注 14

### ④ 视觉母题
**顶部深蓝标题条 + 右侧章节标识（`01 · 研究背景`）**，全篇内容页复用，位置字号完全一致。
**所有示意图统一为"测绘图纸"风格**：白底、1px 深蓝结构线、木色填充、红色标注点、细引线。

### ⑤ 配图清单（全部为内联矢量图，零版权风险）

| 编号 | 内容 | 生成方式 | 使用页 |
|---|---|---|---|
| F01 | 斗拱在柱顶的位置剖面示意 | SVG 手绘 | P7 |
| F02 | 一朵斗拱的分层爆炸示意（栌斗→华栱→横栱→昂→枋） | SVG 手绘 | P8 |
| F03 | 宋式/清式术语对照标注 | SVG 手绘 | P9 |
| F04 | 荷载传递路径图（屋面→槫→斗→栱→柱→础） | SVG 手绘 | P10 |
| F05 | 下昂杠杆原理示意 | SVG 手绘 | P11 |
| F06 | 三阶段斗拱体量对比（唐/宋/清） | SVG 手绘 | P13 |
| F07 | 七铺作出跳读法示意（四跳） | SVG 手绘 | P17 |
| F08 | 四实例横向对比柱图 | Chart | P18 |
| F09 | 封面斗拱剪影 | SVG 手绘 | P1 |

> 说明：本次所有图示均为据文献重绘的示意图，非实物照片。实物照片清单另附文件，逐张标注来源与许可，供后续替换。

## 二、逐页字段

| 页 | type | role | rhythm | layout | visual | visual_role | density |
|---|---|---|---|---|---|---|---|
| 01 | cover | hero | peak | 封面左侧标题 + 右侧剪影 | F09 | anchor | 字 60 / 图 1 |
| 02 | catalog | supporting | transition | 目录四章 | — | — | 字 80 |
| 03 | section | transition | transition | 章节扉页 01 | — | — | 字 20 |
| 04 | content | hero | peak | KPI 三数 + 问题陈述 | — | — | 字 200 |
| 05 | content | supporting | valley | 左文右图（大殿价值） | — | — | 字 230 |
| 06 | section | transition | transition | 章节扉页 02 | — | — | 字 20 |
| 07 | content | supporting | valley | 图左文右 | F01 | anchor | 字 200 |
| 08 | content | hero | peak | 满版爆炸图 + 底部六类标注 | F02 | anchor | 字 240 |
| 09 | content | supporting | valley | 术语对照表 | F03 | evidence | 字 260 |
| 10 | content | supporting | valley | 力流图 + 四段说明 | F04 | anchor | 字 220 |
| 11 | content | hero | peak | 大图 + 一句论断 | F05 | anchor | 字 170 |
| 12 | section | transition | transition | 章节扉页 03 | — | — | 字 20 |
| 13 | content | supporting | valley | 三阶段对比图 + 规律条 | F06 | anchor | 字 200 |
| 14 | content | supporting | valley | 唐宋特征四卡 | — | — | 字 240 |
| 15 | content | supporting | valley | 明清特征 + 数据对比 | — | — | 字 230 |
| 16 | section | transition | transition | 章节扉页 04 | — | — | 字 20 |
| 17 | content | hero | peak | 七铺作读法图 | F07 | anchor | 字 220 |
| 18 | content | supporting | valley | 四实例对比表 + 柱图 | F08 | evidence | 字 240 |
| 19 | content | hero | peak | 结论三条 + 转化路径 | — | — | 字 230 |
| 20 | content | supporting | valley | 文献与图示来源 | — | — | 字 300 |

anti_pattern（通用）：
- 禁等宽卡片横排堆砌
- 禁 emoji / 感叹号 / 卖点式标题
- 禁装饰性小图标贴片
- 禁金色与渐变
- 示意图禁用实物照片混搭（全篇统一为矢量测绘风格）
