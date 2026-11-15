# 木构之间 · 项目入口

日常修改只需从下面五个目录中选择。历史备份收进 `archive/`，原始 Word 文档已放进 `docs/01-依据/原始文档/`。

| 你要做什么 | 去哪里 |
|---|---|
| 准备高职组人工智能赛道 PPT、四岗实操与讲解 | [竞赛演示](竞赛演示/README.md) |
| 改网页布局、交互和文字 | [web-exhibits](web-exhibits/README.md) |
| 查知识资料、写方案、看修改记录 | [docs](docs/README.md) |
| 在 Blender 中修改模型 | [models](models/README.md) |
| 添加现场照片、参考视频与图示 | [research](research/README.md) |
| 找已导出的离线网页、FBX、汇报文件 | [output](output/README.md) |
| 找旧自动备份或早期演示中间文件 | [archive](archive/README.md) |

## 四幕分别在哪里修改

| 页面 | 工作目录 | 常改内容 |
|---|---|---|
| 第一幕 · 历史 | `web-exhibits/act-01-history/` | 图文在 `materials-text-image/`；模型在 `materials-3d/` |
| 第二幕 · 木构图册 | `web-exhibits/act-02-globe/` | 条目 `data.json`；图片 `assets/buildings/`；交互 `js/`；样式 `css/` |
| 第三幕 · 斗拱拼装 | `web-exhibits/act-03-assembly/` | 页面 `index.html`；交互 `app.js`；材质 `wood-material.js`；模型 `assets/` |
| 第四幕 · 问答 | `web-exhibits/act-04-quiz/` | 见本幕 `README.md` |

新增建筑时，把条目和对应图片一起更新；修改模型时，编辑 `.blend` 后重新导出网页使用的 `.glb`；完成网页修改后重新生成离线包。`output` 是生成结果，不作为日常编辑入口。

`web-exhibits/shared/` 是各幕共用资源，移动前需核对引用。`act-01-history/node_modules/` 虽然较大，但第一幕开发和第三幕离线打包正在使用，已保留。

## 文件存放约定

- 新素材放所属幕的素材目录；只有调研原始媒体放 `research/`。
- 方案和知识文档遵循 `docs` 已有的「依据 / 内容 / 方案 / 记录 / 归档」分类。
- 新导出文件放 `output/`，同一用途优先更新现有包，避免“最终版2”“最终版3”。
- 老版本压缩后放 `archive/`，不要混在当前 `.blend` 旁。
- `斗拱研究报告/` 是现有汇报工程，保留原路径以兼容其素材和生成配置。

`.git/` 保存历史恢复能力，约占本项目一半体积。不要直接删除；拷去展厅运行只需要导出的离线包，不需要整个项目。
