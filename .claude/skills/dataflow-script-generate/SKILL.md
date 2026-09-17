---
name: dataflow-script-generate
description: 数据流转校验脚本生成（AC驱动）- 根据流程定义文件（Markdown，步骤 1.2.3. 平铺描述跨节点业务流程如 上报→审核→复核）生成可独立运行的 Playwright 自包含脚本：动作步骤执行填报/点击并捕获变量上下文，校验步骤引用上下文做跨节点数据一致性断言，失败输出字段级差异明细+步骤N定位（不截图），沿用 TEST_RESULT_JSON 协议供 test-script-run-collect 聚合
triggers:
  - "数据流转脚本生成"
  - "一致性校验脚本"
  - "根据流程定义生成脚本"
  - "AC流程脚本"
  - "dataflow-script-generate"
---

# 数据流转校验脚本生成（AC驱动）

把一份**流程定义文件**（按本目录 `template_flow.md` 语法编写）翻译成**一个可独立运行的
Playwright 自包含脚本**，沿流程步骤逐节点执行 UI 操作，并在校验步骤断言数据流转正确性。

与 `test-script-generate-standalone` 的差异定位：本技能是**"一流程一脚本"**（一条业务流程
跨多个页面/节点），不是"一用例一脚本+片段渲染"。**不使用 gen_script.py、不写 _specs 片段**，
由 LLM 按 `template.py.tpl` 五层结构手写全量脚本；testid 采集复用 collect_testids.py。

## 输入

- **流程定义文件**（必填）：按 `template_flow.md` 语法编写的 Markdown 文件路径
- **BASE_URL 与登录态**：流程定义元信息头中的 `BASE_URL`；登录态约定与
  test-script-generate-standalone 相同——落在批次目录 `{批次}/.auth/auth_state.json`，
  优先复用既有登录态（项目根 `.auth/` 或既有批次目录），否则导出当前会话，再无则走 `login()` 兜底

## 处理流程

### ① 解析流程定义

按 `template_flow.md` 的「语法约定」解析出：

1. **元信息**：流程ID（DF-XXX）、BASE_URL、优先级
2. **步骤序列**：动作步骤（打开页面/填写数据/点击按钮）与校验步骤（状态变更为/提示为/与第M步填写数据一致）
3. **占位符校验**：`${字段名}` 必须在此前某"填写数据"步骤中出现过，未注册的占位符**解析期报错**（不静默放行）
4. **一致性引用校验**："与第M步填写数据一致"的第M步必须是"填写数据"步骤，且字段名原文可匹配

### ② testid 批量采集

把流程涉及的全部去重 route_path 写入临时 routes.txt，一次登录遍历采集（缓存优先）：

```
python3 .claude/skills/test-script-generate-standalone/collect_testids.py \
    --base-url {BASE_URL} --auth-state {批次目录}/.auth/auth_state.json \
    --headless --route-paths {routes.txt} --out-dir generated_scripts/.testid_cache
```

采集不到的元素（如详情弹窗字段）在脚本中走语义 fallback 定位，不编造 testid。

### ③ 生成自包含脚本

输出到 `./generated_scripts/{流程名}_{YYYY-MM-DD}/DF-XXX.py`（单脚本平铺批次根，**无模块子目录**）。

脚本结构：沿用 `template.py.tpl` 五层骨架（配置/辅助/页面/用例/驱动），叠加 `flow_helpers.py.snippet`
中的数据流转辅助（复制进辅助层）：

| 层 | dataflow 脚本要求 |
|---|---|
| ① 配置区 | CASE_ID=流程ID，CASE_NAME=`{流程名}(数据流转)`；ROUTE_PATH 置首个步骤路由（实际导航由步骤转写控制） |
| ② 辅助层 | template.py.tpl 既有辅助 + **flow_helpers.py.snippet 全量复制**（CTX/capture/resolve/assert_dataflow_consistent/CURRENT_STEP） |
| ③ 页面层 | 每个涉及页面一个页面类，定位器集中定义（tid() testid 优先）；字段按 testids.json 类型选 date_input()/rich_text() 等 |
| ④ 用例层 | `run_case(page)` 按流程定义**逐步骤顺序转写**，规则见下 |
| ⑤ 驱动层 | 同 template.py.tpl，**去掉截图逻辑**，异常时注入 CURRENT_STEP 前缀 |

**用例层转写规则（核心）**：

1. **失败定位双保险**：实际步骤体写在 `_run_case_impl(page)` 内，每步执行前更新
   `CURRENT_STEP = "步骤N"`（`global CURRENT_STEP`）；`run_case(page)` 作为外层包装，
   捕获异常后按 `raise type(e)(f"[{CURRENT_STEP}] {e}") from e` 重抛。
   ⚠️ 必须在 run_case 层包装而非只在 main() 注入——run_collect.py 共享浏览器模式
   直接调用模块的 `run_case(page)`（不走脚本 main()），只在 main() 注入会使批量运行丢失步骤定位。
   main() 的异常处理**不再重复注入**前缀
2. `打开页面` → `quick_load(page, BASE_URL + route)`
3. `填写数据` → 组装 fields dict → 逐字段 `tid()/date_input()...` 定位并 fill（值先过 `resolve()`）→ `capture(fields)`
4. `点击按钮` → `tid(page, "", "button:has-text('{文本}')").click()`
5. `校验：状态变更为` → `check(page, "步骤N 状态变更", 定位器, expect="{期望状态}")`
6. `校验：提示为` → 触发动作后 `expect_toast(page, "{文本}")`
7. `校验：与第M步填写数据一致` → `assert_dataflow_consistent(page, [(字段名, 定位器, mode), ...])`，
   mode 按 testids.json 元素类型选 `"input"`/`"text"`（输入框一律 input_value，展示文本用 inner_text）
8. `${字段名}` 出现在任意步骤值中 → 先 `resolve()` 解析

**硬性约束**：

- **全程不截图**：`record_result()` 的 screenshot 恒传空字符串，main() 不调用 page.screenshot
- **收集全部差异再报错**：一致性断言一次 raise 带全部字段明细，不许逐字段 fail-fast
- 优先 wait 机制，避免硬 sleep

### ④ 自检

```
python3 .claude/skills/test-script-generate-standalone/selfcheck.py --script-dir {批次目录}
```

error 级问题必须修复后再交付。

### ⑤ 产出与汇报

- 产物：`{批次}/DF-XXX.py` + `{批次}/.auth/auth_state.json`（如采集/导出了登录态）+ README（记录流程定义路径与步骤数）
- 汇报：脚本路径、步骤总数（动作/校验各几条）、testid 真实覆盖度、自检结果、
  **`[via:api]` 降级声明**（如流程定义中出现该标注）

## 校验清单

- [ ] 流程定义已按 template_flow.md 语法解析；`${字段名}` 与"与第M步一致"的引用全部可解析，未静默放行
- [ ] 每个校验步骤均落为 check()/expect_toast()/assert_dataflow_consistent() 之一，无漏转
- [ ] 每步执行前更新 CURRENT_STEP；前缀注入在 **run_case 外层包装**（兼容 run_collect 共享模式直接调 run_case），main() 不重复注入
- [ ] 一致性断言一次 raise 带全部字段级差异明细（`字段=期望 vs 实际`）
- [ ] 全程无截图，screenshot 字段恒为空字符串
- [ ] 脚本通过 selfcheck.py 自检（error=0）
- [ ] testid 优先采自 testids.json，未采集到的走语义 fallback，不编造
