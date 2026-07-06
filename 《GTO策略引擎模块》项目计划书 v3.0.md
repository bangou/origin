好的，以下是修订后的《GTO策略引擎模块》项目计划书 v3.0，已与主程序接口完全对齐。

---

# 《GTO策略引擎模块》项目计划书 (v3.0)

**版本**：3.0  
**日期**：2026-07-07  
**作者**：[你的名字]  
**关联文档**：《系统集成与显示主程序》v1.0

---

## 1. 项目定位

本模块是整个系统的 **“大脑”** ，提供标准翻后GTO策略的毫秒级查询服务。它被打包为一个独立的库或服务，仅通过明确的 API 与主程序交互。

**核心约定**：
- 接口完全符合主程序定义的 **v1.0 查询协议**。
- 提供两种调用方式供主程序选择：**Python绑定** 或 **本地HTTP服务**。
- 数据库路径等配置由主程序在初始化时注入，本模块不维护独立配置文件。

---

## 2. 与主程序的接口协议

### 2.1 初始化

主程序通过以下方式之一加载引擎：

**方式A：Python绑定（同进程，推荐）**
```python
import gto_engine
gto_engine.init(config={
    "data_path": "./engine/data/",
    "index_file": "./engine/data/index.bin"
})
```

**方式B：本地HTTP服务（独立进程）**
主程序使用前需先手动启动服务进程：
```bash
strategy_engine_server --data_path ./engine/data/ --port 9090
```
然后通过 `http://127.0.0.1:9090/query` 调用。

### 2.2 查询接口

**请求格式（JSON）**：
```json
{
  "version": "1.0",
  "hand": "AhKh",
  "board": "As7d2h",
  "history": "r200:c",
  "position": "BTN",
  "pot": 1500,
  "stack": 8500,
  "mode": "GTO",
  "options": {
    "include_ev": true,
    "include_tree": false
  }
}
```
- 此格式与主程序状态机 `build_query()` 生成的请求完全一致。
- `mode` 字段预留，当前仅支持 `"GTO"`，`"Exploit"` 模式返回相同 GTO 策略。
- `include_tree` 若为 `true`，响应中将包含子节点 ID，用于决策树浏览。

**响应格式（JSON）**：
```json
{
  "status": "ok",
  "node_id": "F184_042:a1b2c3",
  "actions": [
    {
      "type": "bet",
      "size": 0.33,
      "freq": 0.85,
      "ev": 12.5
    },
    {
      "type": "check",
      "freq": 0.15,
      "ev": 11.2
    }
  ],
  "recommendation": "bet33",
  "is_exact": true
}
```
- `status`：`"ok"` 精确命中，`"approx"` 近似值（需在 UI 标记），`"not_found"` 无数据。
- `recommendation`：可选，给出频率最高或 EV 最大的动作，供高亮显示。
- `is_exact`：`false` 时表示该结果来自插值或近似，非精确求解。

**Python 绑定调用示例**：
```python
result = gto_engine.query({
    "version": "1.0",
    "hand": "AhKh",
    "board": "As7d2h",
    "history": "r200:c",
    "position": "BTN",
    "pot": 1500,
    "stack": 8500,
    "mode": "GTO",
    "options": {"include_ev": True}
})
# result 为字典，结构与上述 JSON 一致
```

---

## 3. 内部架构

引擎内部结构保持不变，但移除了独立配置文件，所有路径由 `init()` 传入。

- **查询核心**：内存哈希索引 + mmap 节点文件，查询延迟 < 1ms。
- **未命中处理**：查找近似节点（相同纹理类），返回 `status: "approx"`。
- **数据生产**：离线使用 GTO+ 批量求解，生成节点文件和索引，与在线引擎解耦。

---

## 4. 部署与文件结构

在整体项目的 `engine/` 目录下：

```
engine/
├── gto_engine.pyd          # 编译好的Python绑定（C++扩展）
├── engine_server.exe       # HTTP服务可执行文件（可选）
├── data/
│   ├── index.bin           # 全局索引文件
│   └── nodes/              # 节点二进制文件
│       ├── F184_001/
│       │   ├── a1b2c3.node
│       │   └── ...
│       └── ...
└── tests/
    └── test_query.py
```

---

## 5. 开发计划

| 阶段 | 任务 | 预计时间 | 产出 |
|------|------|---------|------|
| **一：接口定义** | 明确查询、初始化 API，编写 mock 供主程序测试 | 1 周 | 可导入的空模块 |
| **二：查询核心** | 实现哈希索引、mmap 读取、查询逻辑 | 2 周 | 可查本地数据的引擎 |
| **三：接口封装** | Python 绑定、HTTP 服务（可选） | 1 周 | 两种调用方式 |
| **四：集成测试** | 与主程序联调，验证延迟与准确性 | 1 周 | 稳定版本 |
| **总计** | | **约 5 周** | |

---

## 6. 预算

- GTO+ 求解器：≈ $75（一次性，离线生成数据用）
- 其他软件库：免费
- 硬件：已有

---

