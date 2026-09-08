---
name: test-script-fix-loop
description: 测试脚本失败反馈重写（闭环）- 读取 test-script-run-collect 保留的运行结果，对失败用例分类根因，自动重写脚本的定位/断言行并重跑，形成"生成→运行→失败→重写→重跑"闭环；真实测试发现与缺数据类永不自动重写
triggers:
  - "修复测试脚本"
  - "重跑失败用例"
  - "失败反馈重写"
  - "闭环修复"
  - "test-script-fix-loop"
---

# 测试脚本失败反馈重写（闭环）

承接 `test-script-generate-standalone`（生成）与 `test-script-run-collect`（运行收集），
把单向管道升级为反馈环：读取运行结果中的**失败用例**，分类根因，**自动重写脚本的定位/断言行**，再重跑，
直到通过或判定为"真实测试发现 / 需人工"。全流程只产出可追溯的 **`fix_feedbacks.md`** 与脚本修改，不破坏既有产物。

## 三条红线（务必遵守）

1. **绝不改预期结果来凑通过**：系统实际行为 ≠ 用例预期 → 这是**测试发现**，如实上报，**不重写脚本**。
2. **只改脚本自身问题**：仅当失败根因为定位器/断言方式等"脚本写错"时才重写，且**只动出问题的定位/断言行**，保持 ①②③④⑤ 五层结构不变。
3. **缺数据/缺会话不自动重写**：登录态过期、前置数据缺失、BASE_URL 空占位等属于**环境问题**，提示人工补齐后重跑，不进入自动改写。

## 定位与接缝

| 环节 | 输入 | 产出 |
|------|------|------|
| Skill1 `generate-standalone` | 测试用例.md | `generated_scripts/{需求名}_{日期}/` 下每个用例一个 `.py` + `testids.json` |
| Skill2 `run-collect` | 脚本目录 | `测试报告.md` + `screenshots/`（运行需 `--keep-results` 保留结果文件） |
| **本技能 fix-loop** | run-collect 保留的结果 | 分类 → 重写脚本 → 重跑 → `fix_feedbacks.md` + 修改说明 |

## 输入

1. **脚本批次目录**（必填）：`generated_scripts/{需求名}_{日期}/`，内含 `.py` 脚本与（运行预留的）`results.json` / `results.jsonl`。
2. **运行结果文件**：本技能需要机器可读的失败数据。若目录内**没有**结果文件，第一步需先用 `run_collect` 带 `--keep-results` 重跑生成（否则找不到失败信息）。
3. **登录态与会话**（重跑用）：`auth_state.json` 或脚本内 `login()` 配置，沿用 Skill2 第二步的处理方式。

## 处理流程

### 第一步：确保有机器可读的运行结果

- 若批次目录下有 `results.json` / `results.jsonl` → 直接用。
- 否则用 Skill2 带 `--keep-results` 重跑一次（可 `--filter` 缩小范围），把失败数据落到文件：
  ```
  cd e2eProject
  python3 .claude/skills/test-script-run-collect/run_collect.py \
      --script-dir "generated_scripts/{需求名}_{日期}" --keep-results
  ```
  > 没有 `results.json` 的，**务必**先跑这一步；不要凭口号/记忆猜测哪些失败。

### 第二步：生成失败反馈包

用本技能自带的 `build_feedbacks.py`，把失败用例的（错误 + 截图 + 脚本中疑似需改的定位/断言行）聚合成结构化反馈，供你逐条分类：
```
python3 .claude/skills/test-script-fix-loop/build_feedbacks.py \
    --script-dir "generated_scripts/{需求名}_{日期}" \
    --round 1 --max-rounds 2
```
- 产出 `{批次目录}/fix_feedbacks.md`（总览）+ `{批次目录}/fix_loop_work/{case_id}.json`（逐用例）。
- `--round`/`--max-rounds` 写进反馈，用于判断是否达到终止轮次。
- 无失败用例时脚本直接提示"无反馈需生成"，本技能到此结束。

### 第三步：逐失败用例分类根因

读 `fix_feedbacks.md` 中每个失败项的**错误信息 + 截图 + 疑似行**，判定根因（关键step，决定是否重写）：

| 根因类 | 典型错误特征 | 是否自动重写 |
|--------|--------------|--------------|
| `locator` | `locator(...) ... not found` / `waiting for` 元素超时 / `get_by_test_id` 无匹配 / `expect(...).to_be_visible` 失败 | ✅ 重写定位器 |
| `assertion_method` | 对 `input`/`select`/`date` 用了 `inner_text()` 导致取值空或断言错 | ✅ 改断言方式（`input_value()`） |
| `missing_data` / `env` | 编辑目标 id 为空 / 前置数据不存在 / 登录态过期被弹回登录页 / BASE_URL 空占位 | ❌ 不重写，提示人工 |
| `timeout` / `flaky` | 偶发时序抖动、toast 未捕获、加载慢 | ⚠️ 重跑确认（Skill2 `--max-retry` 已覆盖），不重写 |
| `real_bug` | **系统实际行为 = 用例预期不符，脚本本身运行成功** | ❌ 不重写，标记为测试发现 |

分类依据：脚本运行是否有异常（堆栈） vs 断言失败（值不符）。**运行异常走定位/断言类；值不符走 real_bug。**

### 第四步：按分类处置

**A. 可重写（locator / assertion_method）**——用生成器重写：
1. 只定位失败用例的脚本 `{case_id}.py` 与失败行；
2. 定位类：对照 `testids.json` 反查真实 `data-testid`（`index` 的 `by_label/by_placeholder/by_button_text`），优先换真实 testid；未命中则校正 `tid()` 的语义 fallback；保证 `tid(page, "<testid>", "<fallback>")` 结构不被打破。
3. 断言方式类：`input`/`select`/`date` 字段回显断言改用 `input_value()`，保留 `check()`/`expect_toast()` 既有约定；
4. **保持该脚本五层结构**，不引入新基类/新依赖，不动其它已通过用例。

**B. 不重写（missing_data / env / real_bug / flaky）**：
- `missing_data`/`env` → 在反馈中标注"需补齐：<具体缺失项>"，交人工；
- `real_bug` → 在反馈中标"测试发现：系统实际 X vs 用例预期 Y"（同 Skill2 第四步口径），交人工，**不改预期**；
- `flaky` → 说明"本轮不重写，重跑确认由 run_collect --max-retry 处理"。

### 第五步：重跑受影响用例

对**被重写**的用例，用 `run_collect` 定向重跑（`--keep-results` 保留本轮结果供下一轮）：
```
python3 .claude/skills/test-script-run-collect/run_collect.py \
    --script-dir "generated_scripts/{需求名}_{日期}" --filter <case_id> --keep-results
```

### 第六步：判定是否进入下一轮

- 被重写用例**已通过**，或无失败，且未达 `--max-rounds` → 关闭本轮。
- 仍有**可重写根因**（locator/assertion）失败，且轮次 < `--max-rounds` → 以 `--round <n+1>` 回到第二步再迭代。
- 剩余失败仅剩 `real_bug` / `missing_data` / 已达 `--max-rounds` → **停止自动重写**，将其转为需人工处理，如实汇报。

### 第七步：汇报与落盘

- 汇总本轮：重写了几条、每条改了什么（定位器 / 断言方式）、重跑结果、仍有几条待人工（含原因）。
- 在 `{批次目录}` 下更新/标注 `fix_feedbacks.md` 结论（可加"✅已修复 / ⏸待人工"列）。
- 向用户说明：哪些是脚本问题已自动修复，哪些是真实测试发现 / 缺数据需处理，产物路径。

## 与既有技能的关系

- **不接管生成与运行**：脚本仍由 Skill1 生成、Skill2 运行；本技能只做"失败→重写→重跑"那一环。
- **复用既有产物**：`testids.json`（定位反查）、`auth_state.json`（重跑会话）、`TEST_RESULT_JSON:` 协议行（结果判定）均沿用。
- **守护红线**：始终不为了凑通过对用预期 / 不加戏外断言；真实测试发现原样上抛。

## 校验清单

- [ ] `build_feedbacks.py` 通过 `python -m py_compile`；`--help` 输出参数完整；缺 `--script-dir` 有明确报错
- [ ] 第一步已确认有运行结果文件；若无已用 `run_collect --keep-results` 重跑生成
- [ ] `fix_feedbacks.md` + `fix_loop_work/{case_id}.json` 已生成，失败用例数与 `测试报告.md` 一致
- [ ] 每个失败用例已完成根因分类，分类有错误信息依据
- [ ] 重写仅发生在 `locator`/`assertion_method`，且只改定位/断言行，五层结构未破坏
- [ ] `real_bug` / `missing_data` 类**未被自动重写**，已如实标注并交人工
- [ ] 未为凑通过修改预期结果或断言含义
- [ ] 被重写用例已定向重跑（`--keep-results`），结果已更新
- [ ] 达到 `--max-rounds` 或无可重写项时已停止并转为人工
- [ ] 已向用户汇报：重写清单、每项修改内容、仍有几项待人工及原因