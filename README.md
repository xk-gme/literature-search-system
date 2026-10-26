# 文献搜索系统

通用的文献调研工具：输入一个研究问题，自动检索 arXiv、提取关键发现、按主题组织、生成结构化调研报告。

与研究想法系统的区别：
- **研究想法系统**：为特定科学问题生成研究想法/方法（S15→锦标赛→人工筛选→S16 格式化，产出可注入树搜索的方法卡）
- **文献搜索系统**：纯粹的文献调研工具（搜索→摘要→聚类→报告，产出可读的综述文档），不生成想法、不做锦标赛

## 使用方式

```powershell
cd D:\workspace\论文复现\文献搜索系统
$PY = "D:\workspace\论文复现\project\venv\Scripts\python.exe"

# 零成本试跑（不调 API）
& $PY -B -X utf8 -m src.pipeline survey --topic "你的研究问题" --dry-run

# 真实调用（约 5-10 次 API，视深度而定）
& $PY -B -X utf8 -m src.pipeline survey --topic "你的研究问题" --depth 2

# 指定输出目录
& $PY -B -X utf8 -m src.pipeline survey --topic "你的研究问题" --output-dir runs/my_survey
```

## 流水线

```text
输入：研究问题（一句话或多段描述）
  ↓
① 规划：LLM 生成搜索查询组（每组针对一个子方向）
  ↓
② 检索：arXiv API 逐组搜索，收集论文（标题+摘要+元数据）
  ↓
③ 提炼：LLM 阅读全部摘要，提取关键发现和方法学洞察
  ↓
④ 聚类：LLM 将论文按主题聚类，命名每个主题方向
  ↓
⑤ 报告：LLM 生成结构化中文调研报告（含文献清单、主题分析、方向建议）
  ↓
输出：Markdown 报告 + JSON 原始数据
```

## 与研究想法系统的关系

两个独立系统，共享基础设施（DeepSeek 客户端、arXiv 检索），但流水线和输出完全不同：

| | 研究想法系统 | 文献搜索系统 |
|---|---|---|
| 目的 | 为科学问题生成可执行的研究方法 | 为任意主题生成文献综述 |
| 输入 | 任务背景文件（S15 式） | 一句话研究问题 |
| 核心步骤 | 深研→锦标赛→人工筛选→格式化 | 搜索→提炼→聚类→报告 |
| 输出 | 方法卡（可注入树搜索） | 调研报告（Markdown） |
| LLM 调用 | ~52 次 | ~5-10 次 |
| Token 消耗 | ~25 万 | ~5-10 万 |

## 目录结构

```text
文献搜索系统/
├── README.md               本入口
├── config.yaml             配置（模型/搜索/深度）
├── src/
│   ├── __init__.py
│   ├── pipeline.py          CLI 入口
│   ├── searcher.py          arXiv 检索
│   ├── analyzer.py          提炼＋聚类＋报告生成
│   └── client.py            DeepSeek 客户端（复用研究想法系统的）
├── templates/               报告模板
└── runs/                    运行产物
```
