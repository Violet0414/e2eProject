---
name: test-script-run-collect
description: 测试脚本运行与结果收集 - 运行 generated_scripts 或用户指定目录下的自包含 Playwright 脚本，逐个执行，捕获 TEST_RESULT_JSON 协议行，聚合生成一份"测试报告.md"（脚本执行结果清单，写清通过与否）
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
逐个执行、捕获每个脚本按 `TEST_RESULT_JSON:` 协议行输出的结果，最终**只产出一份** `测试报告.md`：
可控的执行结果清单，写清每个脚本通过与否。

这些脚本**独立可运行**（`python 文件.py`），无需 pytest；本技能只负责批量执行 + 收集 + 聚合报告。

> **产物精简原则**：执行完毕**只保留 `测试报告.md` 一份结果文件**（失败截图可选），
> 不落盘 `results.jsonl`、`results.json`、每脚本 `.log`、批量运行日志等多余文件。

## 输入

1. **脚本目录**（必填）：
   - 默认：`e2eProject/generated_scripts/{目录}`（skill 1 的输出），若有多个由用户指定或选择最近一个
   - 也可由用户直接指定任意含自包含测试脚本的目录
2. **运行参数**（可选）：
   - `headless`：`True` 走无头模式，更快；缺省尊重脚本内 `HEADLESS` 配置
   - 单条筛选：如只想跑某 `case_id`，支持传入用例编号过滤

## 处理流程

### 第一步：确认脚本目录
- 列出 `generated_scripts/` 下各批次目录，请用户确认用哪个；若仅一个则直接使用
- 若脚本内配置区（BASE_URL 等）仍为空占位符，**提示用户**脚本会在登录/导航处失败并走 failed 分支，属预期行为；若已填则正常执行

### 第二步：会话准备 —— 确定登录态来源（真实系统关键步骤）

自包含脚本**用 `chromium.launch()` 起全新浏览器（无任何 cookie）**，若目标系统需登录，`goto` 编辑页会被
**弹回登录页** → 在输入框定位处超时失败。因此运行前必须先确定登录态来源，二选一：

**A. 复用已登录会话（推荐，真实系统常无法重登验证码/SSO）**
1. 判定/询问用户目标系统是否已在某浏览器登录（或当前 Playwright MCP 已登录）。可尝试导航看是否弹登录页判断。
2. 从已登录浏览器导出登录态 → `{脚本目录}/auth_state.json`（Playwright `storage_state` 格式）：
   - **cookie/localStorage 探测**：在已登录页面执行 `document.cookie` 读取 cookie、遍历 `localStorage`/`sessionStorage`
     提取 token（SPA 的 token 常在 cookie 或 localStorage，如 `xxx-token`）。注意：仅 `document.cookie` 能读非 httpOnly cookie；
     httpOnly 的需从浏览器 storage_state 导出）。
   - 组装 `auth_state.json`：`{"cookies":[{name,value,domain,path}...], "origins":[{origin,localStorage:[...]}]}`
     （domain 填目标 host，如 `192.168.200.67`，不带端口）。
3. 脚本配置区 `AUTH_STATE = "auth_state.json"` → 驱动层 `new_context(storage_state=...)` 复用该会话，跳过登录直接跑。

**B. 走脚本内 login()**：需填 BASE_URL/账号/密码/验证码，`AUTH_STATE` 留空。

> 提示：若脚本 `AUTH_STATE` 已填但其 json 缺失，会报 storage_state 错误；若登录态过期（token 失效），会再被弹回登录页，需重新导出。

### 第三步：逐个运行脚本并捕获结果
用 shell（或 Python 批量调用）顺序执行：

```bash
cd {脚本目录}
mkdir -p screenshots
for f in *.py; do
  echo "===== 运行 $f ====="
  python "$f" 2>&1   # 捕获 stdout 中的 TEST_RESULT_JSON: {...} 行
done
```

要点：
- **顺序执行**（按文件名排序），保证结果稳定、脚本不互相干扰
- **捕获 stdout 中的 `TEST_RESULT_JSON: {...}` 行**作为该脚本的权威结果，汇总到内存供最终聚合
- 若脚本崩溃/超时**没有任何协议行**，兜底为 `{"status": "failed", "error": "脚本异常退出，未输出结果协议行"}`
- **失败截图兜底（不依赖脚本内部截图）**：脚本自身截图可能因各种原因未落盘（`screenshots/` 空）。对跑出 failed/无协议行的用例，
  运行层用 playwright（复用同一 `auth_state.json`）打开该用例 `ROUTE_PATH` 补拍 `screenshots/{case_id}_failed_cli.png`，保证失败必有图。
- **偶发时序失败**：批量遇单条 failed 疑似时序抖动（toast 等待超时、单条重跑又能过）时，**重跑该条确认**；若确为偶发，报告中可标注"偶发重跑通过"。

### 第四步：生成单一"测试报告.md"
在脚本目录生成**一份** `测试报告.md`，结构与内容：

```
# 测试报告
运行时间 / 脚本目录 / 统计（总数/通过/失败/通过率）

## 执行结果
| 用例ID | 状态 | 名称 | 失败原因 |
|--------|------|------|----------|
```
- **状态列**：`通过` / `失败`（不写模糊描述），一眼可判断哪些脚本过、哪些没过
- **失败原因列**：
  - 系统实际行为与用例预期不符 → 如实写"系统实际 X vs 用例预期 Y"（作为测试发现，**不改用例预期**）
  - 脚本异常/超时 → 写脚本报错要点
  - 截图列如需保留：失败用例标注 `{case_id}_failed.png` 或 `{case_id}_failed_cli.png` 路径

> **判定原则**：**系统实际行为与用例预期不符 → 一律记失败，不改用例预期**。报告中对该类失败如实说明
> "系统实际 X vs 用例预期 Y"，作为测试发现/潜在缺陷（而非脚本误报）。

### 第五步：向用户汇报
- 运行统计：用例数 / 通过 / 失败 / 通过率
- 失败用例清单（id + 一句话原因，+ 截图路径若有）
- 产物路径：`测试报告.md`（仅此一份结果文件）
- 若存在占位符/需前置数据（如编辑目标 id、原文案）导致的失败，明确提示补齐后重跑
- 若某条疑似偶发时序失败，说明已重跑确认结果

## 校验清单
- [ ] 每个脚本被实际执行
- [ ] 结果协议行已捕获，统计与清单准确
- [ ] `测试报告.md` 已生成，含执行结果清单，每个脚本状态明确（通过/失败）
- [ ] 失败用例有原因说明（+ 截图路径若有）
- [ ] 会话准备已处理：已登录复用 `auth_state.json`，或填账号走 login()
- [ ] 不符合预期一律记为失败，未为凑通过改用例预期
- [ ] 除 `测试报告.md` 外未留多余结果文件（无 jsonl/json/每脚本 log/运行日志）
- [ ] 已向用户汇报统计与失败清单