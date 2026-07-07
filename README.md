# GTOBig

GTOBig 是一个分阶段推进的德州扑克辅助项目。  
当前仓库主要完成了两条主线：

1. 一个可运行的 Python 原型骨架
2. 一个可长期复用的静态图像视觉数据库流水线

这份 README 的目标不是展开所有设计细节，而是作为 GitHub 首页索引，帮助你快速回答这些问题：

- 现在做到哪个阶段了
- 每个版本标签对应什么里程碑
- 当前仓库已经实现了什么
- 下一步计划做什么

## 当前状态

- 当前开发阶段：`Phase 2 complete`
- 当前推荐下一阶段：`Phase 3 - crop extraction and sample labeling`
- 已发布里程碑标签：
  - `v0.1.0-alpha`
  - `v0.2.0-alpha`

## 路线图与版本里程碑

| 版本 | 阶段 | 状态 | 含义 |
| --- | --- | --- | --- |
| `v0.1.0-alpha` | Phase 1 | 已完成 | 原型骨架打通，主流程可用 mock 方式端到端运行 |
| `v0.2.0-alpha` | Phase 2 | 已完成 | 视觉数据库流水线完成，支持截图扫描、模板整理、压缩与元数据输出 |
| `v0.3.0-alpha` | Phase 3 | 计划中 | 裁剪提取与样本标注工作流 |
| `v0.4.0-alpha` | Phase 4 | 计划中 | 真实静态识别原型 |
| `v0.5.0-beta.1` | Phase 5 | 计划中 | 实时捕获链路接入 |
| `v0.6.0-beta.1` | Phase 6 | 计划中 | 状态机与引擎编排整合 |
| `v0.8.0-beta.1` | Phase 7 | 计划中 | 可用 GUI |
| `v1.0.0` | Final | 计划中 | 稳定可维护的端到端产品 |

## 当前已经实现的内容

### Phase 1：可运行的原型骨架

仓库已经具备一条最小可运行主路径：

`perception -> state machine -> engine -> console output`

已实现能力：

- 从 `config.yaml` 读取本地配置
- 一个最小版 `GameStateMachine`，可判断是否轮到自己行动
- 一个 mock `PerceptionModule`，返回示例快照
- 一个 mock GTO 引擎，返回固定策略结果
- 一个控制台渲染器，用于格式化输出策略建议
- 针对配置、状态机、感知模块和主循环的自动化测试

相关代码：

- [main.py](main.py)
- [core/config.py](core/config.py)
- [core/state_machine.py](core/state_machine.py)
- [perception/module.py](perception/module.py)
- [engine/mock_engine.py](engine/mock_engine.py)
- [ui/console_view.py](ui/console_view.py)

### Phase 2：静态图像视觉数据库流水线

仓库现在还包含了一个用于长期识别资产准备的静态图像预处理流水线，
用于从 `screenshots/` 中构建可复用的视觉数据库。

已实现能力：

- 创建 `data/vision_db/` 目录结构
- 扫描源截图目录
- 区分可信的 `*_raw.png` 模板种子与普通整图截图
- 解析模板标签，例如 `Ah_raw.png -> Ah / A / h`
- 保留整图原件到数据库结构中
- 对大图生成压缩副本，且不改变像素尺寸
- 输出 JSONL 元数据文件
- 遇到坏图时记录日志并继续处理
- 提供命令行入口构建视觉数据库

相关代码：

- [vision_db/layout.py](vision_db/layout.py)
- [vision_db/source_index.py](vision_db/source_index.py)
- [vision_db/image_ops.py](vision_db/image_ops.py)
- [vision_db/jsonl_store.py](vision_db/jsonl_store.py)
- [vision_db/pipeline.py](vision_db/pipeline.py)
- [scripts/build_vision_db.py](scripts/build_vision_db.py)

相关文档：

- [Phase 2 设计文档](docs/superpowers/specs/2026-07-07-vision-db-design.md)
- [Phase 2 执行计划](docs/superpowers/plans/2026-07-07-vision-db-phase2.md)
- [GitHub 上传策略](docs/github-upload-policy.md)

## 仓库结构

```text
gtobig/
├─ core/              # 配置与最小状态逻辑
├─ engine/            # Phase 1 的 mock 引擎接口
├─ perception/        # Phase 1 的 mock 感知模块
├─ ui/                # 控制台输出辅助
├─ vision_db/         # Phase 2 图像数据库流水线
├─ scripts/           # 命令行入口
├─ tests/             # pytest 自动化测试
├─ docs/              # plans / specs / upload policy
├─ config.yaml        # 本地运行配置
└─ main.py            # 原型主入口
```

## 快速开始

### 1. 安装依赖

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. 运行测试

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

### 3. 运行原型主流程

```powershell
.\.venv\Scripts\python.exe .\main.py
```

### 4. 构建视觉数据库

```powershell
.\.venv\Scripts\python.exe .\scripts\build_vision_db.py --source .\screenshots --db-root .\data\vision_db
```

## 数据与 Git 策略

仓库默认只追踪代码、测试、文档与小型配置，不把大批量图像资产直接放进普通 Git 历史。

默认保留在本地的数据包括：

- `screenshots/`
- `data/vision_db/`
- `.venv/`
- 各类缓存与 `__pycache__/`

这样做有两个好处：

1. 保持仓库体积稳定
2. 允许本地重复构建数据流水线，而不会污染 Git 历史

## 当前测试覆盖点

当前自动化测试已经覆盖：

- 配置加载
- 状态机构建 query
- mock 感知快照切换
- 主循环 smoke test
- 图像源扫描与模板标签解析
- 图片压缩行为
- vision database 端到端构建
- CLI 调用与摘要输出

## 下一步计划

下一阶段是 `Phase 3`，预计聚焦在：

- 从整图截图中提取牌面区域 crop
- 组织真实卡槽样本
- 建立第一版样本标注工作流

## 备注

- `v0.1.0-alpha` 表示项目第一次具备可运行骨架
- `v0.2.0-alpha` 表示 Phase 2 视觉数据库流水线完成
- `main` 可能会在阶段标签之后继续包含少量整理性提交，例如 `.gitignore`、发布收尾或文档更新

