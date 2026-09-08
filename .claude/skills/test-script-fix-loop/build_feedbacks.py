#!/usr/bin/env python3
"""build_feedbacks.py - 从测试运行结果提取失败用例的"反馈包"，供 test-script-fix-loop 重写脚本。

test-script-fix-loop 技能调用。读取批次目录下的 results.json / results.jsonl
（由 test-script-run-collect 用 --keep-results 保留的运行结果），筛出失败用例，
为每个失败用例生成一份结构化反馈 {case_id}.json，并汇总一份 fix_feedbacks.md 总览，
供生成器（Claude）据此分类根因并只改脚本的定位/断言行。

用法：
  python3 build_feedbacks.py --script-dir <批次目录> [--results results.json]
      [--out fix_loop_work] [--include-passed] [--round 1] [--max-rounds 2]

退出码：0 = 正常；1 = 参数/路径错误或找不到结果文件。
"""
import argparse
import json
import re
import sys
from pathlib import Path

# 定位/断言相关行（疑似需修改点）的识别模式
TARGET_LINE_RE = re.compile(
    r"tid\(|check\(|expect_toast\(|input_value\(|\.fill\(|\.click\(|data-testid|inner_text\(|RICH_TEXT|rich_text\("
)


def parse_args():
    p = argparse.ArgumentParser(description="从运行结果提取失败用例反馈包")
    p.add_argument("--script-dir", required=True, help="测试脚本批次目录（含 results.json/脚本）")
    p.add_argument("--results", default="", help="结果文件名；缺省自动找 results.json 或 results.jsonl")
    p.add_argument("--out", default="fix_loop_work", help="反馈包输出子目录，默认 fix_loop_work")
    p.add_argument("--include-passed", action="store_true", help="也写入已通过用例（默认只反馈失败）")
    p.add_argument("--round", type=int, default=1, help="当前重写轮次，写入反馈供终止判断")
    p.add_argument("--max-rounds", type=int, default=2, help="最多允许的重写轮数")
    return p.parse_args()


def load_results(path: Path) -> list:
    """读取结果文件。兼容 JSONL（每行一个 entry）与 JSON 数组。"""
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    # 优先当作 JSON array
    try:
        data = json.loads(text)
        return data if isinstance(data, list) else [data]
    except json.JSONDecodeError:
        pass
    # 退化为 JSONL
    entries = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries


def find_result_file(script_dir: Path, name: str) -> Path:
    if name:
        p = script_dir / name
        return p if p.exists() else None
    for cand in ("results.json", "results.jsonl"):
        p = script_dir / cand
        if p.exists():
            return p
    return None


def candidate_lines(script_text: str) -> list:
    """抽出脚本中与定位/断言相关的行（带行号），作为"疑似需修改点"。"""
    hits = []
    for idx, line in enumerate(script_text.splitlines(), 1):
        if TARGET_LINE_RE.search(line):
            hits.append({"line_no": idx, "line": line.strip()[:160]})
        if len(hits) >= 40:  # 避免反馈包过大
            break
    return hits


def truncate(text: str, limit: int = 1500) -> str:
    if not text:
        return ""
    return text if len(text) <= limit else text[:limit] + "\n...[截断]"


def main() -> int:
    args = parse_args()
    script_dir = Path(args.script_dir).resolve()
    if not script_dir.is_dir():
        sys.exit(f"错误：脚本目录不存在: {script_dir}")

    res_file = find_result_file(script_dir, args.results)
    if not res_file:
        print(f"⚠️ 未找到结果文件（results.json / results.jsonl）。请先用 ")
        print(f"   test-script-run-collect --keep-results 运行并保留结果，再运行本脚本。")
        return 1

    entries = load_results(res_file)
    if not entries:
        print(f"⚠️ 结果文件 {res_file.name} 无有效记录。")
        return 1

    failed = [e for e in entries if e.get("status") != "passed"]
    include = entries if args.include_passed else failed
    if not include:
        print("✅ 无失败用例（或已全部通过），无反馈需生成。")
        return 0

    out_dir = script_dir / args.out
    out_dir.mkdir(exist_ok=True)

    md_lines = []
    md_lines.append("# 失败反馈包（fix-loop）")
    md_lines.append("")
    md_lines.append(f"- **结果来源**：`{res_file.name}`")
    md_lines.append(f"- **当前轮次**：{args.round}（最大 {args.max_rounds} 轮）")
    md_lines.append(f"- **失败用例数**：{len(failed)} / {len(entries)}")
    md_lines.append(f"- **脚本目录**：`{script_dir}`")
    if len(failed) >= args.max_rounds:
        md_lines.append("")
        md_lines.append("> ⚠️ 达到最大轮次，本轮之后应停止自动重写，未通过项转为人工处理。")
    md_lines.append("")

    for e in sorted(failed, key=lambda x: x.get("id", "")):
        cid = e.get("id") or e.get("name") or "unknown"
        script = script_dir / f"{cid}.py"
        lines = candidate_lines(script.read_text(encoding="utf-8")) if script.exists() else []
        fb = {
            "id": cid,
            "name": e.get("name"),
            "status": e.get("status"),
            "error": truncate(e.get("error", "")),
            "screenshot": e.get("screenshot", ""),
            "script_abs": str(script),
            "script_exists": script.exists(),
            "candidate_lines": lines,
            "round": args.round,
            "max_rounds": args.max_rounds,
        }
        (out_dir / f"{cid}.json").write_text(json.dumps(fb, ensure_ascii=False, indent=2), encoding="utf-8")

        md_lines.append(f"## {cid} {e.get('name') or ''}")
        md_lines.append("")
        md_lines.append(f"- **状态**：`{e.get('status')}`")
        if e.get("screenshot"):
            md_lines.append(f"- **截图**：`{e.get('screenshot')}`")
        md_lines.append(f"- **脚本**：`{fb['script_abs']}`")
        md_lines.append("")
        md_lines.append("**疑似需检查的定位/断言行**：")
        md_lines.append("")
        if lines:
            for it in lines:
                md_lines.append(f"- `L{it['line_no']}`：`{it['line']}`")
        else:
            md_lines.append("- （未匹配到定位/断言行，或脚本缺失）")
        md_lines.append("")
        md_lines.append("**错误信息**：")
        md_lines.append("")
        md_lines.append("```")
        md_lines.append(fb["error"])
        md_lines.append("```")
        md_lines.append("")

    (script_dir / "fix_feedbacks.md").write_text("\n".join(md_lines), encoding="utf-8")
    print(f"已生成 {len(failed)} 份失败反馈包于 {out_dir}/")
    print(f"总览：{script_dir}/fix_feedbacks.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())