#!/usr/bin/env python3
"""解析 test-script-run-collect 的产物，整理成结构化通过/失败清单 collect_results.json。

消费顺序（优先生成源）：测试报告.md → results/results.json → results.jsonl → 直接传 JSON。

解析源优先级：
1. tests_report.md —— 表格（用例ID|状态|名称|失败原因）4 列，状态为中文 通过/失败
2. results/results.json —— 旧版 run-collect 产物，顶层含 cases[]（id/name/status/error/screenshot）
3. results.jsonl —— TEST_RESULT_JSON 协议行，同 id 多条取末条
4. 用户直接传 JSON

用法：
    python3 parse_report.py <批次目录> [输出路径]
    输出路径缺省为 <批次目录>/collect_results.json
"""
import os
import re
import sys
import json
import glob
import datetime

CASE_ID_HEADERS = ("用例ID", "case_id", "用例编号", "id")
STATUS_NORM = {"通过": "passed", "失败": "failed", "passed": "passed", "failed": "failed", "pass": "passed", "fail": "failed"}


def norm_status(raw: str) -> str:
    """把 通过/失败/passed/failed 等归一化为 passed/failed；无法识别返回 'unknown'。"""
    key = (raw or "").strip().lstrip("*").rstrip("*").strip()
    if key in STATUS_NORM:
        return STATUS_NORM[key]
    if "通过" in key:
        return "passed"
    if "失败" in key:
        return "failed"
    return "unknown"


def clean_md(text: str) -> str:
    """清洗 markdown：去掉加粗/反引号，压缩空白。"""
    if not text:
        return ""
    t = text.replace("**", "").replace("`", "")
    return re.sub(r"\s+", " ", t).strip()


def find_screenshot_in_text(error: str) -> str:
    """从 error 文本里提取截图路径（相对批次目录）。"""
    m = re.search(r"([\w./\-_]+\.(?:png|jpg|jpeg|webp))", error or "")
    return m.group(1) if m else ""


def scan_screenshot_dir(batch_dir: str, case_id: str) -> str:
    """扫描 <批次>/screenshots/ 下以 case_id 开头的截图，按优先级返回。"""
    shots_dir = os.path.join(batch_dir, "screenshots")
    if not os.path.isdir(shots_dir):
        return ""
    pref = [f"{case_id}_", f"{case_id}.", case_id]
    found = []
    for f in os.listdir(shots_dir):
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            for p in pref:
                if f.startswith(p):
                    found.append(f)
                    break
    # 优先级：_failed_cli > _failed > _diag > 其它
    def rank(f):
        fl = f.lower()
        if "_failed_cli" in fl:
            return 0
        if "_failed" in fl:
            return 1
        if "_diag" in fl:
            return 2
        return 3
    if not found:
        return ""
    best = sorted(found, key=lambda f: (rank(f), f))[0]
    return os.path.join("screenshots", best)


# --------------------------------------------------------------------------
# 各解析源
# --------------------------------------------------------------------------
def parse_report_md(batch_dir: str) -> list:
    """解析 测试报告.md 的表格。表头自适应（按含 用例ID 的表头行定列序）。"""
    path = os.path.join(batch_dir, "测试报告.md")
    if not os.path.exists(path):
        return None
    results = []
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()

    header_idx = None
    cols = None
    for i, line in enumerate(lines):
        if "|" not in line:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        # 找到符合表头特征（含 用例ID）的行
        if any(h in cells for h in CASE_ID_HEADERS) and any(
            s in cells for s in ("状态", "通过", "结果")
        ):
            header_idx = i
            cols = cells
            break
    if header_idx is None:
        return None

    # 定位每列
    def col_idx(*names):
        for n in names:
            if n in cols:
                return cols.index(n)
        return None

    i_id = col_idx("用例ID", "case_id", "用例编号", "id")
    i_status = col_idx("状态")
    i_name = col_idx("名称")
    i_error = col_idx("失败原因", "原因", "备注")
    if i_id is None or i_status is None:
        return None

    n_cols = len(cols)
    for line in lines[header_idx + 1:]:
        ls = line.strip()
        if not ls or set(ls.strip("|")) <= {"-", ": "}:
            continue
        cells = [c.strip() for c in ls.strip("|").split("|")]
        if len(cells) < n_cols:
            cells = cells + [""] * (n_cols - len(cells))
        elif len(cells) > n_cols:
            # 多余段（如失败原因里含 |）归并回最后一列
            cells = cells[: n_cols - 1] + ["|".join(cells[n_cols - 1:])]
        case_id = cells[i_id].strip()
        if not case_id:
            continue
        status_raw = cells[i_status]
        status = norm_status(status_raw)
        if status == "unknown":
            continue  # 跳过统计/发现等非用例行
        error = clean_md(cells[i_error]) if i_error is not None else ""
        if error in ("——", "-", "无", "预期正确", ""):
            error = ""
        name = cells[i_name].strip() if i_name is not None else ""
        results.append(
            {"case_id": case_id, "name": name, "status": status,
             "error": error, "screenshot": find_screenshot_in_text(error)}
        )
    return results


def parse_results_json(batch_dir: str) -> list:
    """解析旧版 results/results.json。"""
    for cand in (os.path.join(batch_dir, "results", "results.json"),
                 os.path.join(batch_dir, "results.json")):
        if not os.path.exists(cand):
            continue
        try:
            data = json.load(open(cand, encoding="utf-8"))
        except Exception:
            continue
        cases = data.get("cases") if isinstance(data, dict) else data
        if not isinstance(cases, list):
            continue
        out = []
        for c in cases:
            if not isinstance(c, dict):
                continue
            case_id = str(c.get("id", c.get("case_id", ""))).strip()
            if not case_id:
                continue
            out.append({
                "case_id": case_id,
                "name": c.get("name", ""),
                "status": norm_status(c.get("status", "")),
                "error": (c.get("error") or ""),
                "screenshot": c.get("screenshot", "") or find_screenshot_in_text(c.get("error") or ""),
            })
        return out
    return None


def parse_results_jsonl(batch_dir: str) -> list:
    """解析 results.jsonl（TEST_RESULT_JSON 行）。同 id 取末条。"""
    for cand in (os.path.join(batch_dir, "results", "results.jsonl"),
                 os.path.join(batch_dir, "results.jsonl")):
        if not os.path.exists(cand):
            continue
        latest = {}
        with open(cand, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                m = re.search(r"TEST_RESULT_JSON:\s*(\{.*\})", line) or re.search(r"(\{.*\})", line)
                if not m:
                    continue
                try:
                    obj = json.loads(m.group(1))
                except Exception:
                    continue
                rid = str(obj.get("id", "")).strip()
                if rid:
                    latest[rid] = obj
        out = []
        for rid in sorted(latest):
            o = latest[rid]
            out.append({
                "case_id": rid,
                "name": o.get("name", ""),
                "status": norm_status(o.get("status", "")),
                "error": o.get("error", ""),
                "screenshot": o.get("screenshot", "") or find_screenshot_in_text(o.get("error") or ""),
            })
        return out
    return None


def parse_direct_json(text: str) -> list:
    """解析用户直接传的 JSON 列表/对象。"""
    try:
        data = json.loads(text)
    except Exception:
        return None
    cases = data.get("cases") if isinstance(data, dict) else data
    if not isinstance(cases, list):
        return None
    out = []
    for c in cases:
        if not isinstance(c, dict):
            continue
        case_id = str(c.get("case_id", c.get("id", ""))).strip()
        if not case_id:
            continue
        out.append({
            "case_id": case_id,
            "name": c.get("name", c.get("title", "")),
            "status": norm_status(c.get("status", "")),
            "error": c.get("error", ""),
            "screenshot": c.get("screenshot", "") or find_screenshot_in_text(c.get("error") or ""),
        })
    return out


# --------------------------------------------------------------------------
def main():
    if len(sys.argv) < 2:
        print("用法: python3 parse_report.py <批次目录> [输出路径]", file=sys.stderr)
        sys.exit(2)
    batch_dir = sys.argv[1].rstrip("/")
    out_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(batch_dir, "collect_results.json")

    source = ""
    results = None
    # 1. 尝试 md（但要求 md 与 json 都不存在时跳过）
    results = parse_report_md(batch_dir)
    if results is not None:
        source = os.path.join(batch_dir, "测试报告.md")
    else:
        results = parse_results_json(batch_dir)
        if results is not None:
            source = "results/results.json"
        else:
            results = parse_results_jsonl(batch_dir)
            if results is not None:
                source = "results.jsonl"

    if results is None:
        print(f"错误: <{batch_dir}> 下未找到可解析的产物(测试报告.md / results/results.json / results.jsonl)",
              file=sys.stderr)
        sys.exit(1)

    # 补充截图扫描（对未提取到截图且失败的）
    for r in results:
        if r["status"] == "failed" and not r["screenshot"]:
            r["screenshot"] = scan_screenshot_dir(batch_dir, r["case_id"])
        if r["status"] != "failed":
            r["screenshot"] = r.get("screenshot", "")

    total = len(results)
    passed = sum(1 for r in results if r["status"] == "passed")
    failed = sum(1 for r in results if r["status"] == "failed")
    unknown = total - passed - failed
    pass_rate = f"{passed / total * 100:.1f}%" if total else "0.0%"

    payload = {
        "source": source,
        "batch_dir": batch_dir,
        "collected_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "stats": {"total": total, "passed": passed, "failed": failed, "unknown": unknown, "pass_rate": pass_rate},
        "results": results,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"已生成: {out_path}")
    print(f"统计: 总数={total} 通过={passed} 失败={failed} 未知={unknown} 通过率={pass_rate}")
    print(f"解析源: {source}")
    for r in results:
        flag = "PASS" if r["status"] == "passed" else ("FAIL" if r["status"] == "failed" else "????")
        shot = f"  [{r['screenshot']}]" if r.get("screenshot") else ""
        print(f"  [{flag}] {r['case_id']} | {r['name']}{shot}")


if __name__ == "__main__":
    main()