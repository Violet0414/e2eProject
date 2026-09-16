#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bug-to-zentao: 解析 测试报告.md（test-script-run-collect 产出），收集失败用例并构建禅道 bug 提交清单。

用法:
  python3 build_bug_payload.py <测试报告.md路径> [输出.json路径] [--results-json <results.json路径>]
      [--screenshot-mode embed|attach|path] [--max-steps-html-kb 512]

输出 JSON 结构:
{
  "report": 报告路径, "batch_dir": 批次目录, "stats": {...},
  "bugs": [ { case_id, title, severity, pri, type, openedBuild, steps, steps_text,
              expectation, actual_result, classification, classification_reason,
              screenshot_path, screenshot_embedded } ]
}
不访问网络、不写禅道；创建动作由 SKILL.md 流程在 dry-run 确认后另行执行。
"""
import argparse
import base64
import json
import os
import re
import sys

# ---------- 脚本问题特征（默认排除，不提 bug） ----------
SCRIPT_ISSUE_PATTERNS = [
    r"waiting for locator", r"waiting for get_by", r"waiting for frame",
    r"Timeout.*exceeded", r"TimeoutError", r"timeout of \d+",
    r"net::ERR", r"503", r"Session closed", r"Target .* closed",
    r"locator\.count", r"未输出结果协议行", r"ENOTFOUND", r"ECONNREFUSED",
]
# 1 级缺陷特征（主要功能/数据/流程类）
SEV1_PATTERNS = [
    r"提交失败", r"保存失败", r"新增失败", r"编辑失败", r"删除失败",
    r"导入失败", r"导出失败", r"流程不通", r"数据丢失", r"统计数据?错误",
    r"列表没有显示", r"没有显示出", r"页面报错", r"系统报错", r"闪退",
    r"权限类", r"未授权.*(仍|未.*(显示|隐藏))",
]
# 3 级缺陷特征（格式/提示/展示效果/性能）
SEV3_PATTERNS = [
    r"格式", r"长度", r"提示文案", r"提示消息", r"展示效果", r"样式",
    r"性能", r"速度", r"对齐", r"间距", r"文案",
]

BUG_TYPE_MAP = [
    (r"性能|速度|加载慢|响应慢", "performance"),
    (r"设计|交互不合理|布局不合理", "designdefect"),
    (r"配置|字典|数据字典", "config"),
]


def md_cell(row: str, idx: int) -> str:
    cells = [c.strip() for c in row.strip().strip("|").split("|")]
    if idx < len(cells):
        return cells[idx]
    return ""


def parse_report(report_path: str):
    """解析测试报告.md，返回 (failed_rows, detail_tracebacks, report_meta)。兼容有/无'模块'列。"""
    with open(report_path, encoding="utf-8") as f:
        text = f.read()

    report_meta = {}
    m = re.search(r"\*\*运行时间\*\*：(.+)", text)
    if m:
        report_meta["run_time"] = m.group(1).strip()
    m = re.search(r"\*\*脚本目录\*\*：`?([^`\n]+)`?", text)
    if m:
        report_meta["batch_dir"] = m.group(1).strip()
    m = re.search(r"通过率\*\*：([\d.]+%)", text)
    if m:
        report_meta["pass_rate"] = m.group(1).strip()

    failed_rows = []
    detail_tracebacks = {}

    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        if "用例ID" in line or line.startswith("|---") or re.match(r"^\|[-\s|:]+\|$", line):
            # 表头或分隔行：记录列布局
            if "用例ID" in line:
                cells = [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", line.strip("|"))]
                failed_rows.append({"__header__": cells})
            continue
        cells = [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", line.strip("|"))]
        header = next((r["__header__"] for r in failed_rows if "__header__" in r), None)
        if header is None:
            continue
        row = dict(zip(header, cells))
        if row.get("状态") != "失败":
            continue
        screenshot = ""
        m = re.search(r"\(([^)]+\.png)\)", row.get("截图", ""))
        if m:
            screenshot = m.group(1)
        item = {
            "case_id": row.get("用例ID", ""),
            "module": row.get("模块", "") if "模块" in row else "",
            "name": row.get("名称", ""),
            "error": row.get("失败原因", ""),
            "screenshot": screenshot,
            # 新版报告（test-script-run-collect）已带 bug 字段列；旧格式报告这些键为空串
            "bug_title": row.get("bug标题", "") if "bug标题" in row else "",
            "steps_html": row.get("重现步骤", "") if "重现步骤" in row else "",
            "actual": row.get("结果", "") if "结果" in row else "",
            "expectation": row.get("预期", "") if "预期" in row else "",
            "severity": row.get("严重程度", "") if "严重程度" in row else "",
            "pri": row.get("优先级", "") if "优先级" in row else "",
        }
        failed_rows.append(item)

    # 失败用例详情段：### TC-XXX-001 标题 + ``` 代码块 + 截图：路径
    for m in re.finditer(
        r"###\s+(TC-[\w-]+)\s+([^\n]+)\n+```\n(.*?)```\n+截图：`?([^`\n]+)`?",
        text, re.S,
    ):
        detail_tracebacks[m.group(1)] = {
            "name": m.group(2).strip(),
            "traceback": m.group(3).strip(),
            "screenshot": m.group(4).strip(),
        }

    return failed_rows, detail_tracebacks, report_meta


def load_results_jsonl(path: str):
    """results.json（jsonl 格式）补充数据源，返回 case_id -> 记录。"""
    out = {}
    if not path or not os.path.exists(path):
        return out
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("status") == "failed":
                out[rec.get("id", "")] = rec
    return out


def classify(error_text: str, name: str):
    """返回 (classification, reason)。classification: defect | script_issue"""
    text = f"{name}\n{error_text}"
    for p in SCRIPT_ISSUE_PATTERNS:
        if re.search(p, text, re.I):
            return "script_issue", f"命中脚本/环境问题特征: {p}"
    return "defect", "断言失败，疑似业务缺陷（建议人工复核）"


def suggest_severity(error_text: str, name: str):
    text = f"{name}\n{error_text}"
    for p in SEV1_PATTERNS:
        if re.search(p, text):
            return 1, f"命中1级特征: {p}"
    for p in SEV3_PATTERNS:
        if re.search(p, text):
            return 3, f"命中3级特征: {p}"
    return 2, "默认2级（次要功能错误，不影响测试继续）"


def suggest_type(error_text: str, name: str):
    text = f"{name}\n{error_text}"
    for p, t in BUG_TYPE_MAP:
        if re.search(p, text):
            return t
    return "codeerror"


def build_title(name: str, module: str) -> str:
    """用例名称一般自带【模块-操作】前缀，直接使用；否则拼【模块】前缀。"""
    if name.startswith("【"):
        return name
    if module:
        return f"【{module.split('-')[-1]}】{name}"
    return name


def build_expectation(name: str) -> str:
    """从用例名称提取期望：取'验证'后文本，去掉（疑似缺陷）等尾注。"""
    m = re.search(r"验证(.+)", name)
    exp = m.group(1) if m else name
    exp = re.sub(r"（[^）]*(缺陷|场景)[^）]*）", "", exp).strip()
    return exp


def extract_assert_message(error_text: str) -> str:
    """从 traceback 提取最终断言消息行。"""
    m = re.findall(r"(?:AssertionError|Exception|Error):\s*(.+)", error_text)
    if m:
        return m[-1].strip()
    lines = [l.strip() for l in error_text.strip().splitlines() if l.strip()]
    return lines[-1] if lines else error_text.strip()


def short_traceback(traceback: str, max_lines: int = 6) -> str:
    """保留 traceback 尾部关键行（断言处）。"""
    lines = [l for l in traceback.strip().splitlines() if l.strip()]
    return "\n".join(lines[-max_lines:]) if len(lines) > max_lines else "\n".join(lines)


def build_steps_html(item: dict, report_meta: dict) -> str:
    """按规范拼装重现步骤富文本：[前置条件]/[重现步骤]/[结果]/[期望]。

    新版测试报告已带 bug 字段列（重现步骤/结果/预期），优先直接取用；
    旧格式报告（列为空）降级按用例名称拼接。
    """
    name = item["name"]
    actual = item.get("actual_result", "")
    pre = report_meta.get("run_time", "")
    steps_body = (item.get("steps_html") or "").strip()
    if not steps_body:
        mod = item.get("module") or ""
        tmod = re.match(r"【([^】]+)】", name)
        loc = mod or (tmod.group(1) if tmod else "目标模块")
        steps_body = f"1. 进入 {loc} 对应页面<br>2. 执行用例操作：{build_expectation(name)}"
    expectation = (item.get("expectation") or "").strip() or build_expectation(name)
    lines = [
        "<b>[前置条件]</b>",
        f"使用E2E自动化测试账号登录系统（批次运行时间：{pre}）",
        "<b>[重现步骤]</b>",
        steps_body,
        "<b>[结果]</b>",
        f"执行出现异常，实际结果：{actual}",
        "<b>[期望]</b>",
        expectation,
    ]
    return "<br>\n".join(lines)


def embed_screenshot(png_path: str, max_kb: int):
    """返回 (data_uri 或 None, 备注)。"""
    if not png_path or not os.path.exists(png_path):
        return None, "截图文件不存在"
    size_kb = os.path.getsize(png_path) / 1024
    if size_kb > max_kb:
        return None, f"截图 {size_kb:.0f}KB 超过 {max_kb}KB 上限，建议手动上传"
    with open(png_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return f"data:image/png;base64,{b64}", f"已内嵌（{size_kb:.0f}KB）"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("report", help="测试报告.md 路径")
    ap.add_argument("output", nargs="?", default="/tmp/zentao_bugs.json")
    ap.add_argument("--results-json", default="", help="results.json(jsonl) 路径，默认取报告同目录")
    ap.add_argument("--screenshot-mode", choices=["embed", "attach", "path"], default="attach")
    ap.add_argument("--max-steps-html-kb", type=int, default=512)
    args = ap.parse_args()

    report_path = args.report
    report_dir = os.path.dirname(os.path.abspath(report_path))
    # 报告文件可能被用户拷贝到桌面等位置，截图/results.json 仍以报告内"脚本目录"为准
    results_path = args.results_json or os.path.join(report_dir, "results.json")

    failed_rows, detail_tracebacks, report_meta = parse_report(report_path)
    if not os.path.exists(results_path) and report_meta.get("batch_dir"):
        alt_results = os.path.join(report_meta["batch_dir"], "results.json")
        if os.path.exists(alt_results):
            results_path = alt_results
    batch_dir_candidates = [report_dir]
    if report_meta.get("batch_dir"):
        batch_dir_candidates.append(report_meta["batch_dir"])
    results = load_results_jsonl(results_path)

    bugs = []
    for item in failed_rows:
        if "__header__" in item:
            continue
        cid = item["case_id"]
        tb = ""
        if cid in detail_tracebacks:
            tb = detail_tracebacks[cid]["traceback"]
        elif cid in results:
            tb = results[cid].get("error", "")
        screenshot = item["screenshot"] or detail_tracebacks.get(cid, {}).get("screenshot", "")
        error_text = tb or item["error"]

        classification, cls_reason = classify(error_text, item["name"])
        sev_raw = str(item.get("severity", "")).strip()
        if sev_raw.isdigit() and 1 <= int(sev_raw) <= 4:
            sev, sev_reason = int(sev_raw), "取自测试报告严重程度列"
        else:
            sev, sev_reason = suggest_severity(error_text, item["name"])
        actual = item.get("actual", "").strip() or extract_assert_message(error_text)
        expectation = item.get("expectation", "").strip() or build_expectation(item["name"])
        title = item.get("bug_title", "").strip() or build_title(item["name"], item["module"])
        png_abs = ""
        if screenshot:
            for cand in batch_dir_candidates:
                p = os.path.join(cand, screenshot)
                if os.path.exists(p):
                    png_abs = p
                    break
            else:
                png_abs = os.path.join(batch_dir_candidates[0], screenshot)

        embedded, embed_note = None, "未启用内嵌"
        if args.screenshot_mode == "embed" and classification == "defect":
            embedded, embed_note = embed_screenshot(png_abs, args.max_steps_html_kb)

        bug = {
            "case_id": cid,
            "title": title,
            "module_name": item["module"],
            "severity": sev,
            "pri": sev,  # 规范中严重级别与优先级对照基本一致，可后续单独调
            "severity_reason": sev_reason,
            "type": suggest_type(error_text, item["name"]),
            "openedBuild": "trunk",
            "steps": build_steps_html({**item, "actual_result": actual, "expectation": expectation}, report_meta),
            "steps_text": re.sub(r"<[^>]+>", "\n", build_steps_html({**item, "actual_result": actual, "expectation": expectation}, report_meta)).replace("\n\n", "\n"),
            "expectation": expectation,
            "actual_result": actual,
            "traceback_tail": short_traceback(error_text) if error_text else "",
            "classification": classification,
            "classification_reason": cls_reason,
            "screenshot_path": png_abs,
            "screenshot_embedded": embedded,
            "screenshot_note": embed_note,
        }
        bug["steps"] = build_steps_html({**item, "actual_result": actual}, report_meta)
        bugs.append(bug)

    defects = [b for b in bugs if b["classification"] == "defect"]
    script_issues = [b for b in bugs if b["classification"] == "script_issue"]
    payload = {
        "report": report_path,
        "batch_dir": report_meta.get("batch_dir") or batch_dir_candidates[0],
        "report_meta": report_meta,
        "stats": {
            "failed_total": len(bugs),
            "suggest_submit": len(defects),
            "suggest_exclude": len(script_issues),
        },
        "bugs": bugs,
    }
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"报告: {report_path}")
    print(f"失败项: {len(bugs)}（建议提交 {len(defects)} / 建议排除 {len(script_issues)}）")
    for b in bugs:
        tag = "提交" if b["classification"] == "defect" else "排除"
        print(f"  [{tag}] {b['case_id']} sev={b['severity']} {b['title'][:40]}")
    print(f"输出: {args.output}")


if __name__ == "__main__":
    main()
