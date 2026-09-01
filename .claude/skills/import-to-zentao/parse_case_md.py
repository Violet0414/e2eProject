#!/usr/bin/env python3
"""
import-to-zentao: 解析测试用例.md → 生成禅道 testcase 提交所需的 JSON。
用法: python3 parse_case_md.py <测试用例.md路径> [输出cases.json路径]
"""
import json, re, sys
from collections import OrderedDict

PRI_MAP = {"P0": "1", "P1": "2", "P2": "3", "P3": "4"}
INTF_PREFIXES = ("TC-JIEKOU",)  # 这些前缀的用例视为接口测试
NUM_PREFIX = re.compile(r"^\s*\d+\s*[\.、．,，]?\s*")  # 行首 "1. " 等序号前缀（禅道自动显示行号，需剥离避免双序号）

def strip_step_num(s):
    """剥离每个步骤/预期文本行首的序号前缀，如 '1. 进入...' -> '进入...'。"""
    return "\n".join(NUM_PREFIX.sub("", ln, count=1) for ln in s.split("\n"))

def latest_md():
    import glob, os
    cands = []
    for p in glob.glob("output/*/测试用例.md"):
        cands.append((os.path.getmtime(p), p))
    if not cands:
        return None
    cands.sort(reverse=True)
    return cands[0][1]

def parse_lines(text):
    """按 <br> 拆行，保留每行与首序号供对齐。"""
    parts = [p.strip() for p in re.split(r"<br\s*/?>", text) if p.strip()]
    nums = []
    for p in parts:
        m = re.match(r"^(\d+)\s*[\.、．,，]?\s*", p)
        nums.append(int(m.group(1)) if m else None)
    return parts, nums

def build_steps_expects(step_raw, exp_raw):
    steps, _ = parse_lines(step_raw)
    exp_lines, exp_nums = parse_lines(exp_raw)
    if not steps:
        steps = ["执行用例"]
    first_offset = exp_nums[0] - 1 if exp_nums and exp_nums[0] else 0
    expects = [""] * len(steps)
    if exp_lines:
        perfect = len(steps) == len(exp_lines) and all(
            (n == i) for i, n in enumerate(exp_nums, start=1) if n is not None)
        if perfect:
            expects = exp_lines
        else:
            for idx, (line, num) in enumerate(zip(exp_lines, exp_nums)):
                if num is not None and 1 <= num <= len(steps) and first_offset == 0:
                    expects[num - 1] = line
                else:
                    expects[-1] = line if not expects[-1] else expects[-1] + "\n" + line
    return steps, expects

def main():
    md = sys.argv[1] if len(sys.argv) > 1 else latest_md()
    if not md:
        sys.exit("未找到测试用例文件，请提供路径: python3 parse_case_md.py <path>")
    out_json = sys.argv[2] if len(sys.argv) > 2 else "/tmp/zentao_cases.json"

    rows, warn = [], []
    with open(md, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line.startswith("|") or line.startswith("|---") or "用例编号" in line:
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) < 11:
                continue
            tc_id, route, product, module = cells[0], cells[1], cells[2], cells[3]
            title, pri, tp = cells[4], cells[5], cells[6]
            precond, data = cells[7], cells[8]
            steps, expects = build_steps_expects(cells[9], cells[10])
            steps = [strip_step_num(s) for s in steps]
            expects = [strip_step_num(e) for e in expects]
            if len(steps) != len(expects):
                warn.append(f"{tc_id}: steps={len(steps)} expects={len(expects)} 未对齐")
            precond_full = precond
            if data and data.lower() not in ("无", "n/a") and "测试数据：" not in precond:
                precond_full = (precond + "；测试数据：" + data) if precond else ("测试数据：" + data)
            rows.append(OrderedDict([
                ("tc_id", tc_id), ("module_name", module), ("product_name", product),
                ("title", title), ("pri", PRI_MAP.get(pri, "2")),
                ("type", "interface" if tc_id.startswith(INTF_PREFIXES) else "feature"),
                ("precondition", precond_full), ("steps", steps), ("expects", expects),
            ]))

    modules = list(OrderedDict.fromkeys(x["module_name"] for x in rows))
    stats = {"total": len(rows), "modules": {}, "by_type": {}}
    for x in rows:
        stats["modules"][x["module_name"]] = stats["modules"].get(x["module_name"], 0) + 1
        stats["by_type"][x["type"]] = stats["by_type"].get(x["type"], 0) + 1

    payload = {"source": md, "modules": modules, "products": list(OrderedDict.fromkeys(x["product_name"] for x in rows)), "stats": stats, "cases": rows}
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print("解析完成:", out_json)
    print("用例总数:", stats["total"], "| 类型:", stats["by_type"], "| 产品:", payload["products"])
    print("模块:", {m: stats["modules"][m] for m in modules})
    if warn:
        print("\n!! 步骤/预期未对齐用例:")
        for w in warn:
            print("   ", w)
    else:
        print("\n所有用例 steps/expects 已对齐")

if __name__ == "__main__":
    main()