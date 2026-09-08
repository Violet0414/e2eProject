---
name: test-script-run-collect
description: 测试脚本运行与结果收集 - 用 run_collect.py 运行 generated_scripts 或用户指定目录下的自包含 Playwright 脚本，捕获 TEST_RESULT_JSON 协议行，聚合生成一份"测试报告.md"；自动清理临时产物
triggers:
  - "运行测试"
  - "执行测试脚本"
  - "收集测试结果"
  - "生成测试报告"
  - "跑测用例"
  - "test-script-run-collect"
---

# 测试脚本运行与结果收集

运行指定目录下的**自包含 Playwright 测试脚本**（由 `test-script-generate-standalone` 生成的 `.py`），
用本技能自带的 `run_collect.py` 逐个执行、捕获每个脚本按 `TEST_RESULT_JSON:` 协议行输出的结果，
最终**只产出一份** `测试报告.md`：可读的执行结果清单，写清每个脚本通过与否。

这些脚本**独立可运行**（`python 文件.py`），无需 pytest；本技能只负责批量执行 + 收集 + 聚合报告 + 清理。

> **产物精简原则（对齐"最终产物只留测试脚本+测试报告"）**：执行完毕由 `run_collect.py` 自动清理
> `results.json`、`results.jsonl`、运行日志、`__pycache__/`，**只保留**：
> 测试脚本（`*.py`）+ `测试报告.md` + `screenshots/`（失败截图，可溯源）。如需保留原始结果数据，
> 用 `--keep-results`。

## 输入

1. **脚本目录**（必填/可省）：
   - 缺省：`run_collect.py` 自动选 `generated_scripts/` 下**最近修改**的批次目录
   - 显式：`--script-dir <目录>`，也可指向任意含自包含脚本的目录
2. **运行参数**（可选）：
   - `--filter TC-PERSON`：只跑该 case_id 前缀（单条/单模块筛选）
   - `--headless`：强制无头；缺省尊重脚本内 `HEADLESS`
   - `--max-retry 1`：对疑似时序抖动的失败用例重跑确认，通过则标"通过(重跑)"
   - `--keep-results`：保留 `results.json`；默认清理
   - `--no-live`：跳过失败用例截图补拍（离线/CD 环境）

## 处理流程

### 第一步：确定脚本目录
- 先检查脚本配置区（BASE_URL 等）是否仍是空占位符：若是，告知用户"脚本会在登录/导航处失败并走 failed 分支，属预期"，建议先填齐配置（或提供有效 `auth_state.json` 复用登录态）。
- 用 `--script-dir` 指定批次，或用默认的自动选择（运行前会打印所选目录）。

### 第二步：会话准备 —— 确定登录态来源（真实系统关键步骤）

自包含脚本用 `chromium.launch()` 起全新浏览器（无 cookie），若目标系统需登录，页面会被弹回登录页导致超时。
运行前需确定登录态来源，二选一：

**A. 复用已登录会话（推荐，真实系统常无法重登验证码/SSO）**
1. 判定/询问目标系统是否已在某浏览器登录，可尝试导航看是否弹登录页判断。
2. 在 `{脚本目录}/auth_state.json` 导出已登录浏览器的 `storage_state`：
   - 用 Playwright（或 MCP）打开已登录页面，`context.storage_state(path="auth_state.json")` 一键导出；
     手拼 cookie/localStorage 兜底时注意：仅 `document.cookie` 能读非 httpOnly cookie，httpOnly 的必须走 storage_state 导出。
   - 标准样例：`{"cookies":[{name,value,domain,path}...],"origins":[{origin,localStorage:[...]}]}`（domain 填目标 host，不带端口）。
3. 脚本配置区 `AUTH_STATE = "auth_state.json"` → 驱动层 `new_context(storage_state=...)` 复用会话，跳过登录。

**B. 走脚本内 `login()`**：填 BASE_URL/账号/密码/验证码，`AUTH_STATE` 留空。

> 提示：`AUTH_STATE` 已填但 json 缺失会报 storage_state 错误；登录态过期会被弹回登录页，需重新导出。

### 第三步：运行并收集

```bash
cd e2eProject
python3 .claude/skills/test-script-run-collect/run_collect.py \
    --script-dir "generated_scripts/信息管理-逝者信息_2026-09-07" \
    [--filter TC-PERSON] [--headless] [--max-retry 1] [--keep-results] [--no-live]
```

`run_collect.py` 职责（无需手工 for 循环）：
- 逐个 `python3 文件.py` 执行，捕获 `TEST_RESULT_JSON: {...}` 协议行作为权威结果
- 崩溃/超时/无协议行 → 兜底 `failed`（"脚本异常退出，未输出结果协议行"）
- **偶发时序失败**：`failed` 用例按 `--max-retry` 重跑一次，二次通过则报告标"通过(重跑)"
- **失败截图补拍**：对失败用例，用 `auth_state.json` 打开**该用例自身的 `ROUTE_PATH`** 补拍
  `screenshots/{case_id}_failed_cli.png`（不依赖脚本内部截图，也非单一固定页面）
- 生成 `测试报告.md` 并清理临时产物（除非 `--keep-results`）

### 第四步：核对报告

`run_collect.py` 生成 `测试报告.md`：
```
# 测试报告
运行时间 / 脚本目录 / 统计（总数/通过/失败/通过率）

## 执行结果
| 用例ID | 状态 | 名称 | 失败原因 | 截图 |
## 失败用例详情
| 用例ID（错误堆栈 + 截图路径）
```
- 状态列：`通过` / `失败` / `通过(重跑)`，一眼判断。
- 失败原因列：系统实际行为 vs 用例预期 → 如实写"系统实际 X vs 用例预期 Y"（作测试发现，**不改用例预期**）；脚本异常/超时 → 写脚本报错要点。
- 若存在占位符/需前置数据（编辑目标 id、原文案）导致的失败，提示补齐后重跑。

### 第五步：向用户汇报
- 运行统计：用例数 / 通过 / 失败 / 通过率
- 失败用例清单（id + 一句话原因 + 截图路径）
- 产物路径：`测试报告.md`（+ `screenshots/`），确认已清理 `results.json`/运行日志等（或说明用了 `--keep-results`）
- 若某条疑似偶发时序失败，说明已重跑确认结果

## run_collect.py 参数

| 参数 | 默认 | 说明 |
|------|------|------|
| `--script-dir` | 最近批次 | 脚本目录 |
| `--base-url` | 脚本内提取 | 截图补拍基础地址 |
| `--timeout` | 60 | 每脚本超时秒数 |
| `--headless` | 脚本 HEADLESS | 强制无头 |
| `--filter` | 空 | case_id 前缀过滤如 TC-PERSON |
| `--max-retry` | 1 | 偶发失败重跑次数 |
| `--keep-results` | 关 | 保留 results.json/jsonl |
| `--no-live` | 关 | 跳过截图补拍 |

## 校验清单
- [ ] `run_collect.py` 通过 `python -m py_compile`；`--help` 参数完整
- [ ] 每个脚本被实际执行，结果协议行已捕获，统计与清单准确
- [ ] `测试报告.md` 已生成，含执行结果表，每脚本状态明确（通过/失败/通过(重跑)）+ 失败用例详情
- [ ] 失败用例有原因说明 + 截图路径（补拍图为该用例自身 route）
- [ ] 会话已处理：已登录复用 `auth_state.json`，或填账号走 `login()`
- [ ] 不符合预期一律记为失败，未为凑通过对用预期
- [ ] 临时产物已清理：仅留 `*.py` + `测试报告.md` + `screenshots/`（除非 `--keep-results`）
- [ ] 已向用户汇报统计与失败清单