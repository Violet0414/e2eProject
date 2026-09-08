---
name: script-pipeline
description: 测试脚本闭环流水线 - 依次执行 页面探索→探索转用例→生成自包含脚本→运行收集→失败反馈重写，每步独立子会话+渐进式读取，形成完整测试脚本闭环
triggers:
  - "测试脚本流水线"
  - "探索生成脚本"
  - "端到端脚本"
  - "脚本闭环"
  - "一键跑测"
  - "script-pipeline"
---

# 测试脚本闭环流水线

按顺序自动执行完整的"页面探索 → 生成自包含测试脚本 → 运行收集 → 失败重写"闭环流程，
把四个单点技能（explore-site / test-script-generate-standalone / test-script-run-collect / test-script-fix-loop）
与用例生成技能（generate-testcases-from-explore）组装成一条可一键执行、带检查点/人工确认点的流水线。

每个步骤在**独立子会话（Agent）**中运行，避免主会话上下文过长；
对长文件（探索记录 / 用例md / 反馈）采用**渐进式读取**，分批/分块处理，进一步控制上下文溢出。

## 执行顺序（5 步）

1. **页面探索** (explore-site)
2. **探索转用例** (generate-testcases-from-explore)
3. **生成自包含脚本** (test-script-generate-standalone)
4. **运行收集** (test-script-run-collect)
5. **失败反馈重写** (test-script-fix-loop)

## 数据链路总览

| 步骤 | 技能 | 输出产物 | 供下一步 |
|------|------|----------|----------|
| 1 | explore-site | `explore_output/{日期_时间}/explore_record.md` + `recorded_code.py`（后者为探索附产物，闭环后续步骤不消费） | 步骤2 输入 |
| 2 | generate-testcases-from-explore | `explore_output/{日期_时间}/{时间戳}_测试用例.md` + `.xlsx` | 步骤3 输入 |
| 3 | test-script-generate-standalone | `generated_scripts/{需求}_{日期}/`（每用例一个 `.py` + `testids.json`） | 步骤4 输入 |
| 4 | test-script-run-collect | `测试报告.md` + `screenshots/`（用 `--keep-results` 保留 results.json） | 步骤5 输入 |
| 5 | test-script-fix-loop | 重写脚本 + `fix_feedbacks.md` + 最终 `测试报告.md` | 交付 |

> **`日期_时间`**：步骤1 初始化时生成的目录名，如 `2026-09-08_153000`，后续步骤沿用它。

## 核心规则：每步独立子会话 + 渐进式读取

**禁止在 `workflow` 主会话中直接执行任何单点技能逻辑**，每个步骤必须用 Agent 打开独立子会话执行。

### 子会话配置

- `subagent_type`: `"general-purpose"`
- `working_directory`: 流水的项目根目录（e2eProject）
- 每个子会话 prompt 必须包含：
  1. 要求子会话**先读取对应技能 `SKILL.md`** 获取完整处理规则
  2. 明确告知输入信息（页面URL / 输入文件路径 / 登录凭据等）
  3. 明确告知参考文件路径
  4. 明确要求将结果写入指定的输出文件（目录不存在先创建）
  5. 要求用**渐进式读取**处理长文件（见下）

### 渐进式读取约定（各子会话必须遵守）

- **探索记录 / 用例md / 反馈文件**等长文件：子会话用 `Read` 的 `offset + limit` 或按章节/按批次渐进读取，**不要**一次 `Read` 整文件载入自身上下文。
- **步骤3 用例多（≥20 条）时分批**：每批生成 N 条脚本，每批结束向主会话回传 `已完成 n/t`，主会话据此推进。
- 单点技能自身已内置"分批生成/缓存优先/`--max-rounds`"等防溢出机制，工作流应**沿用**，不重复实现。

### 子会话 prompt 模板

```
请按以下要求执行任务：

1. 先读取技能定义文件：{SKILL.md路径}，理解其中的处理规则和输出格式
2. 读取输入：{输入 URL / 输入文件路径}
{如有参考文件}3. 读取参考文件：{参考文件路径}
4. 严格按照技能定义的处理规则执行（可用渐进式读取分批处理长文件）
5. 将结果写入输出文件：{输出文件路径}（如目录不存在则先创建）
6. 完成后向主会话汇报：产物路径 + 关键统计
```

## 各步骤详细配置

### 步骤1：页面探索（explore-site）

- **技能文件**：`.claude/skills/explore-site/SKILL.md`
- **输入**：用户提供的页面URL（流水线启动时传入）、登录凭据（可选）
- **参考文件**：`./files/templates/test_points_requirement.md`
- **输出目录**：`./explore_output/{日期_时间}/`（由本步初始化创建）
- **输出文件**：`./explore_output/{日期_时间}/explore_record.md` + `recorded_code.py`
- **备注**：向主会话回传 `日期_时间` 目录名，供后续步骤指向。

子会话 prompt 示例：
```
1. 先读取技能定义文件：./.claude/skills/explore-site/SKILL.md，理解其中的处理规则和输出格式
2. 对以下页面进行探索：
   - 页面URL：{用户传入的页面URL}
   - 登录凭据：{用户传入的账号密码，如无则不填}
3. 读取参考文件：./files/templates/test_points_requirement.md
4. 严格按照技能定义执行，初始化时创建 ./explore_output/{日期_时间}/ 与 screenshots/ 子目录
5. 将探索记录写入：./explore_output/{日期_时间}/explore_record.md
6. 将元素操作代码写入：./explore_output/{日期_时间}/recorded_code.py
7. 回传：{日期_时间} 目录名、页面标题、探索模块数/字段数摘要
```

### 步骤2：探索转用例（generate-testcases-from-explore）

- **技能文件**：`.claude/skills/generate-testcases-from-explore/SKILL.md`
- **输入文件**：`./explore_output/{日期_时间}/explore_record.md`（步骤1 产出，工作流**直接指定**，不再让用户重选文件夹）
- **参考文件**：`./files/templates/用例模板.xlsx`、`./files/templates/test_points_requirement.md`
- **输出文件**：`./explore_output/{日期_时间}/{时间戳}_测试用例.md` + `.xlsx`
- **渐进式**：探索记录较长时，用 `Read` 的 offset+limit 按章渐进读取，不整文件载入。

子会话 prompt 示例：
```
1. 先读取技能定义文件：./.claude/skills/generate-testcases-from-explore/SKILL.md
2. 读取输入文件：./explore_output/{日期_时间}/explore_record.md（如较长请 offset+limit 渐进读取）
3. 读取用例模板：./files/templates/用例模板.xlsx
4. 读取参考文件：./files/templates/test_points_requirement.md
5. 严格按规则生成测试用例（用关键词配对列名，不硬编码序号）
6. 将结果写入：./explore_output/{日期_时间}/{时间戳}_测试用例.md 与 .xlsx
7. 回传：用例总数、各模块用例数、是否覆盖全部测试点、产出文件路径
```

**人工确认点**：步骤2 完成后，向用户展示用例统计（总数/各模块数/覆盖情况），
确认后再进入步骤3；用户要求补充探索则回到步骤1 后重跑步骤2。

### 步骤3：生成自包含脚本（test-script-generate-standalone）

- **技能文件**：`.claude/skills/test-script-generate-standalone/SKILL.md`
- **输入文件**：`./explore_output/{日期_时间}/{时间戳}_测试用例.md`（步骤2 产出）
- **必填运行前置**：`BASE_URL`（向用户索要）+ 登录态 `auth_state.json`
- **登录态统一约定**：`auth_state.json` 一律落在 `generated_scripts/{需求名}_{日期}/.auth/auth_state.json`（与生成脚本 `AUTH_STATE` 默认值 `.auth/auth_state.json` 一致，脚本独立运行即读此路径）。来源：优先复用已有登录态（项目根 `.auth/auth_state.json` 或既有批次目录），否则导出当前已登录会话后写入批次 `.auth/` 目录；仍无则走 `login()` 填账号兜底。
- **输出目录**：`./generated_scripts/{需求名}_{日期}/`（每用例一个 `.py` + `testids.json` + README）
- **渐进式**：用例 ≥ 20 条时**分批生成**，每批回传进度；步骤二数据采集按该技能缓存优先机制。
- **自检**：步骤3 子会话末尾用该技能自带 `selfcheck.py` 做 6 项检查，error 级必须修复后交付。

子会话 prompt 示例：
```
1. 先读取技能定义文件：./.claude/skills/test-script-generate-standalone/SKILL.md
2. 读取输入文件：{时间戳}_测试用例.md（文件较大时按批次渐进读取，逐批解析用例）
3. BASE_URL：{用户提供}；登录态 auth_state.json：写入/复用 `{批次目录}/.auth/auth_state.json`（见「登录态统一约定」）
4. 严格按规则为每个用例生成自包含脚本到 ./generated_scripts/{需求名}_{日期}/：按技能内「差异片段协议」先写 `_specs/` 差异片段（页面层片段每页面一份、每用例 spec.json+steps.py），再调 `gen_script.py --spec-dir ... --out ...` 渲染，**不要逐个手写全量脚本**
5. 用 ./generated_scripts/.testid_cache 采集真实 testid；未覆盖字段按语义 fallback 兜底
6. 用 selfcheck.py 做 6 项自检并修复 error 项（改片段后可用 gen_script.py `--only` 重渲该用例）
7. 回传：生成脚本数、自检结果（错误/警告数）、真实 testid 覆盖度、输出目录
```

### 步骤4：运行收集（test-script-run-collect）

- **技能文件**：`.claude/skills/test-script-run-collect/SKILL.md`
- **输入**：`./generated_scripts/{需求名}_{日期}/`（步骤3 产出）
- **登录态**：沿用步骤3 统一约定路径 `{批次目录}/.auth/auth_state.json`；缺失/过期则按步骤3 约定重新导出，或走 `login()` 兜底
- **输出文件**：`测试报告.md` + `screenshots/`
- **关键**：**必须带 `--keep-results`**，保留 `results.json` 供步骤5 闭环读取（否则 results 被默认清理）。

运行命令（由子会话执行）：
```
python3 .claude/skills/test-script-run-collect/run_collect.py \
    --script-dir "generated_scripts/{需求名}_{日期}" --keep-results \
    [--filter TC-XXX] [--headless] [--max-retry 1]
```

**人工确认点**：步骤4 沿用步骤3 已确认的登录态与 `BASE_URL`；仅当登录态缺失/过期时再补充确认。

### 步骤5：失败反馈重写（test-script-fix-loop）

- **技能文件**：`.claude/skills/test-script-fix-loop/SKILL.md`
- **输入**：`generated_scripts/{需求名}_{日期}/results.json`（步骤4 用 `--keep-results` 保留）
- **输出**：重写脚本 + `fix_feedbacks.md` + `{批次目录}/fix_loop_work/{case_id}.json`
- **迭代**：按 `--max-rounds`（默认 2）自动循环"重写→重跑"，直至通过或无可重写项。
- **三条红线**：不改预期凑通过；只改定位/断言行；缺数据/缺会话不自动重写。

子会话执行示例（第 1 轮）：
```
python3 .claude/skills/test-script-fix-loop/build_feedbacks.py \
    --script-dir "generated_scripts/{需求名}_{日期}" --round 1 --max-rounds 2
```
- 无失败用例 → 本步直接结束。
- 分类处置后，对被重写的用例用 run_collect 定向重跑：`--filter {case_id} --keep-results`。

## 流程控制规则

1. **顺序执行**：步骤1→2→3→4→5 严格按顺序，不可并行。
2. **检查点**：每步完成后校验输出文件存在再启动下一步。
3. **失败处理**：某步失败或输出未生成，停止流水线并向用户报告错误。
4. **进度报告**：每步开始前 `正在执行步骤 n/5：{步骤名}...`；步骤3/步骤5 内部阶段性进度也回传。
5. **人工确认点**：
   - 步骤2 完成后：展示用例统计，确认后再生成脚本。
   - 步骤3 前：确认 `BASE_URL` 与登录态来源（复用 `auth_state.json` / 填账号走 `login()`）—— 两者是步骤3 生成脚本与 testid 采集的硬前置，须先确认，避免采集降级。
6. **闭环终止**：步骤5 达到 `--max-rounds`，或剩余失败仅为 `real_bug`/`missing_data`/`env`，即停止自动重写，剩余项转人工。
7. **完成报告**：列全部关键产物路径（explore_record / 测试用例 / 脚本目录 / 测试报告 / fix_feedbacks）。

## 复用既有技能自带的工具/脚本

不重复实现，直接调用单点技能自带的可执行脚本：
- `test-script-generate-standalone/collect_testids.py`：真实 data-testid 采集（含 `.testid_cache` 缓存）
- `test-script-generate-standalone/selfcheck.py`：生成后 6 项自检
- `test-script-run-collect/run_collect.py`：批量运行 + 聚合报告
- `test-script-fix-loop/build_feedbacks.py`：失败反馈包生成

## 校验清单

- [ ] 五个步骤已按子会话 prompt 模板分别配置，各含 技能文件/输入/参考/输出
- [ ] 步骤2 自动指向步骤1 的 `{日期_时间}` 目录，不让用户重选
- [ ] 步骤3 需向用户索要 BASE_URL；登录态按「登录态统一约定」落位到 `{批次目录}/.auth/auth_state.json`
- [ ] 步骤4 明确带 `--keep-results` 保留 results.json 供步骤5 读取
- [ ] 步骤5 按 `--max-rounds` 自动迭代，遵守三条红线
- [ ] 渐进式读取约定写入各步与流程控制（长文件分批/分块、步骤3 用例批量生成）
- [ ] 流程控制规则齐全：顺序执行/检查点/失败处理/进度报告/人工确认点/闭环终止/完成报告