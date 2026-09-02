---
name: collect-results
description: 结果收集 - 消费 test-script-run-collect 产出的 测试报告.md（或旧版 results/results.json(jsonl)），整理成结构化通过/失败清单 collect_results.json（case_id/name/status/error/screenshot），作为结果回写禅道(sync-results-to-zentao)的输入
triggers:
  - "收集结果"
  - "整理结果"
  - "结果清单"
  - "collect-results"
  - "汇总结果"
---

# 结果收集 (collect-results)

消费 `test-script-run-collect` 的产物（`测试报告.md`，或旧版批次目录下的 `results/results.json` / `results.jsonl`），
整理成**结构化通过的/失败清单** `collect_results.json`（`case_id/name/status/error/screenshot`），
作为下一个技能 `sync-results-to-zentao`（结果回写禅道）的输入。

它是整条链路的中间环：`test-script-run-collect`（运行+出报告）→ **本技能（整理成结构化清单）** → `sync-results-to-zentao`（回写禅道）。

## 输入

- **批次目录**（必填）：`e2eProject/generated_scripts/{需求名}_{日期}/`，含 run-collect 产物。缺省取最近一个，或用户指定。
- 也可直接传入一段 JSON（对象含 `cases` 或纯列表）。

## 关键事实与踩坑

| # | 事实 | 影响 |
|---|------|------|
| 1 | 现行 `测试报告.md` 是 4 列（用例ID/状态/名称/失败原因）；旧版 `results/results.json` 顶层含 `cases[]`(id/name/status/error/screenshot)、`stats` | 解析器按**表头列名自适应**，不写死列位；状态中文(通过/失败)归一化为 passed/failed |
| 2 | 失败原因可能带 `**`/反引号/多段文本，甚至含 `|` | 自动清洗 markdown；`split('|')` 多出的段归并回失败原因列 |
| 3 | 报告里“测试发现/待补项”等非表格正文行不应被当成用例 | 仅识别成功解析出 用例ID+状态 的行，状态无法归一化(unknown)的行跳过 |
| 4 | 失败截图不一定在失败原因里 | 截图优先从 error 文本提取；否则扫 `screenshots/{case_id}_*`（优先级 `_failed_cli > _failed > _diag`） |
| 5 | run-collect 精简产物只留 `测试报告.md` | 无 md 才回退 `results.json` → `results.jsonl`；三种都没有则报错 |

## 处理流程

### 第一步 确认批次目录
- 列出 `generated_scripts/` 下候选批次，用户选择或取最近一个。

### 第二步 解析并生成 collect_results.json
```
python3 "<skill目录>/parse_report.py" "<批次目录>" [输出路径]
```
- 输出路径缺省为 `<批次目录>/collect_results.json`。
- 内部自动按优先级选解析源：`测试报告.md` → `results/results.json` → `results.jsonl`。

### 第三步 校验并汇报
- 核对打印的统计与报告一致（总数/通过/失败/通过率），抽查失败的 `error`/`screenshot` 提取是否正确。
- 向用户汇报：统计 + 失败的 `case_id` 清单 + 产物路径 `collect_results.json`。

## 输出 collect_results.json（schema）

```json
{
  "source": "/…/公告管理_2026-09-02/测试报告.md",
  "batch_dir": "/home/mxr/e2eProject/generated_scripts/公告管理_2026-09-02",
  "collected_at": "2026-09-02T17:50:00",
  "stats": {"total": 7, "passed": 5, "failed": 2, "unknown": 0, "pass_rate": "71.4%"},
  "results": [
    {"case_id": "TC-NOTICE-001", "name": "新增公告-正常保存",
     "status": "passed", "error": "", "screenshot": ""},
    {"case_id": "TC-NOTICE-004", "name": "表单内容为空-校验拦截",
     "status": "failed",
     "error": "系统实际：内容留空点保存仍提示提交成功并跳转列表 vs 用例预期：提示公告内容不能为空并拦截",
     "screenshot": "screenshots/TC-NOTICE-004_diag.png"}
  ]
}
```

字段说明：
- `status`：`passed` / `failed`（已由中文“通过/失败”归一化）。
- `error`：失败原因（清洗后），通过为 `""`。
- `screenshot`：失败截图相对批次目录的路径，通过为 `""`。

## 校验清单

- [ ] `collect_results.json` 已生成，`stats` 与源报告一致（总数/通过/失败/通过率）
- [ ] 每条 `status` 正确归一化（通过→passed，失败→failed）
- [ ] 失败条目的 `error` 清洗干净且含失败原因
- [ ] 失败条目的 `screenshot` 已尽可能定位（error 文本提取或扫 `screenshots/`）