---
name: workflow-dataflow-pipeline
description: 数据流转校验闭环流水线 - 依次执行 流程定义文件→dataflow-script-generate→test-script-run-collect，产出含字段级差异明细的测试报告.md，每步独立子会话，形成端到端数据流转校验闭环（不含禅道录入，如需提 bug 可后续单独调用 bug-to-zentao）
triggers:
  - "数据流转流水线"
  - "流程校验闭环"
  - "数据一致性闭环"
  - "dataflow-pipeline"
---

# 数据流转校验闭环流水线

把两个单点技能（dataflow-script-generate / test-script-run-collect）组装成一条可一键执行、
带检查点/人工确认点的**数据流转校验流水线**：输入一份流程定义文件（AC 步骤风格），
输出一份含字段级差异明细的 `测试报告.md`。

每个步骤在**独立子会话（Agent）**中运行，避免主会话上下文过长。

## 执行顺序（2 步）

1. **生成数据流转校验脚本** (dataflow-script-generate)
2. **运行收集** (test-script-run-collect)

> **终点为测试报告.md，不含禅道录入步骤**。报告失败行自带 bug 字段
> （bug标题/重现步骤/结果/预期），后续如需录入可单独调用 bug-to-zentao。

## 数据链路总览

| 步骤 | 技能 | 输出产物 | 供下一步 |
|------|------|----------|----------|
| 1 | dataflow-script-generate | `generated_scripts/{流程名}_{日期}/DF-XXX.py`（单脚本平铺批次根，含 `.auth/auth_state.json`） | 步骤2 输入 |
| 2 | test-script-run-collect（`--keep-results`） | `测试报告.md`（失败原因列为字段级差异明细，带 `[步骤N]` 定位） | 交付 |

## 核心规则：每步独立子会话

**禁止在 workflow 主会话中直接执行任何单点技能逻辑**，每个步骤用 Agent 打开独立子会话执行。

### 子会话配置

- `subagent_type`: `"general-purpose"`
- `working_directory`: 项目根目录（e2eProject）
- 每个子会话 prompt 必须包含：
  1. 要求子会话**先读取对应技能 `SKILL.md`** 获取完整处理规则
  2. 明确告知输入信息（流程定义文件路径 / BASE_URL / 登录态来源）
  3. 明确告知参考文件路径（`template_flow.md` / `flow_helpers.py.snippet`）
  4. 明确要求将结果写入指定的输出目录（不存在先创建）
  5. 完成后回传产物路径 + 关键统计

### 子会话 prompt 模板

```
请按以下要求执行任务：

1. 先读取技能定义文件：{SKILL.md路径}，理解其中的处理规则和输出格式
2. 读取输入：{流程定义文件路径 / 批次目录}
3. {如有}读取参考文件：{参考文件路径}
4. 严格按照技能定义的处理规则执行
5. 将结果写入输出：{输出路径}（如目录不存在则先创建）
6. 完成后向主会话汇报：产物路径 + 关键统计
```

## 各步骤详细配置

### 步骤1：生成数据流转校验脚本（dataflow-script-generate）

- **技能文件**：`.claude/skills/dataflow-script-generate/SKILL.md`
- **输入**：用户提供的流程定义文件路径（须符合 `template_flow.md` 语法）
- **参考文件**：`.claude/skills/dataflow-script-generate/template_flow.md`、`flow_helpers.py.snippet`
- **必填运行前置**：流程定义元信息头的 `BASE_URL` + 登录态（优先复用既有
  `.auth/auth_state.json`，来源确认放在流水线启动前，见流程控制规则 5）
- **输出目录**：`./generated_scripts/{流程名}_{YYYY-MM-DD}/`（单脚本 `DF-XXX.py` 平铺批次根）

子会话 prompt 示例：
```
1. 先读取技能定义文件：./.claude/skills/dataflow-script-generate/SKILL.md，理解其中的处理规则和输出格式
2. 读取输入文件：{流程定义文件路径}
3. BASE_URL：{流程定义元信息或用户提供}；登录态 auth_state.json：写入/复用 `{批次目录}/.auth/auth_state.json`（优先复用既有登录态）
4. 读取参考文件：template_flow.md（语法契约）与 flow_helpers.py.snippet（辅助函数，复制进脚本辅助层）
5. 严格按技能定义：解析流程定义 → testid 批量采集（collect_testids.py，缓存优先）→ 生成 DF-XXX.py → selfcheck.py 自检（error 级必须修复）
6. 全程不截图；校验步骤解析到 [via:api] 时降级为 UI 校验并在汇报中声明
7. 回传：脚本路径、步骤总数（动作/校验各几条）、testid 覆盖度、自检结果、[via:api] 降级声明
```

**人工确认点（步骤1 后，进入步骤2 前）**：向用户展示流程解析结果——
步骤总数（动作/校验各几条）、`${字段名}` 与"与第M步一致"引用可解析性、
testid 覆盖度、自检结果、[via:api] 降级声明。**确认后再运行**。

### 步骤2：运行收集（test-script-run-collect）

- **技能文件**：`.claude/skills/test-script-run-collect/SKILL.md`
- **输入**：`./generated_scripts/{流程名}_{日期}/`（步骤1 产出）
- **登录态**：沿用步骤1 的 `{批次目录}/.auth/auth_state.json`
- **输出文件**：`测试报告.md`（批次根目录）
- **关键**：**必须带 `--keep-results`**，保留 results.json 供后续排查/单独提 bug 使用。

运行命令（由子会话执行）：
```
python3 .claude/skills/test-script-run-collect/run_collect.py \
    --script-dir "generated_scripts/{流程名}_{日期}" --keep-results [--headless] [--max-retry 1]
```

**人工确认点**：沿用步骤1 已确认的登录态与 `BASE_URL`；仅当登录态缺失/过期时再补充确认。

## 流程控制规则

1. **顺序执行**：步骤1→2 严格按顺序，不可并行。
2. **检查点**：每步完成后校验输出文件存在再启动下一步。
3. **失败处理**：某步失败或输出未生成，停止流水线并向用户报告错误。
4. **进度报告**：每步开始前 `正在执行步骤 n/2：{步骤名}...`。
5. **人工确认点**：
   - **流水线启动前（硬前置）**：确认 `BASE_URL` 与登录态来源（复用 `auth_state.json` /
     填账号走 `login()`）——两者是 testid 采集与脚本生成的硬前置，确认前不得启动。
   - **步骤1 完成后**：展示流程解析结果（见步骤1 人工确认点），确认后再运行。
6. **完成报告**：列全部关键产物路径（流程定义 / 脚本 / 测试报告.md），报告失败项摘要
   （含 `[步骤N]` 定位与字段级差异明细条数）。
7. **不含禅道录入**：流水线以测试报告.md 为终点；用户如需提 bug，单独调用 bug-to-zentao
   （其消费本报告失败行的 bug 字段列，链路兼容）。

## 复用既有技能自带的工具/脚本

不重复实现，直接调用：
- `test-script-generate-standalone/collect_testids.py`：真实 data-testid 采集（含 `.testid_cache` 缓存）
- `test-script-generate-standalone/selfcheck.py`：生成后自检
- `test-script-run-collect/run_collect.py`：批量运行 + 聚合报告

## 校验清单

- [ ] 两个步骤已按子会话 prompt 模板分别配置，各含 技能文件/输入/参考/输出
- [ ] 流水线启动前已确认 BASE_URL 与登录态来源，确认前未启动 testid 采集与脚本生成
- [ ] 步骤1 产出单脚本 `DF-XXX.py` 平铺批次根；`${字段名}`/"与第M步一致"引用全部可解析；[via:api] 已降级声明
- [ ] 步骤2 命令带 `--keep-results`；报告失败原因列为字段级差异明细并带 `[步骤N]` 定位
- [ ] 全链路无截图产物
- [ ] 完成报告列出流程定义/脚本/测试报告.md 路径；未包含任何禅道录入步骤
