#!/usr/bin/env python3
"""按 title 反查禅道用例，生成"待回写清单"（dry-run 用，不写任何禅道数据）。

输入：collect_results.json（collect-results 的输出）+ 从 zentao-cli 拉出的用例清单 JSON。
输出：待回写清单 JSON（每项含 case_id/name/status/error→match 结果，matched 至少包含纯数字 caseID 或未命中标记）。

用法：
  npx zentao-cli testcase list --product <PID> --pick id,title --recPerPage 300 --format json > /tmp/zentao_cases.json
  python3 resolve_writeback.py <collect_results.json> <zentao_cases.json> [--productID <PID>] [-o 输出.json]

匹配策略（对本地结果的 name）：
  1. 规范化：去首尾空白/全角空格，把空白折成一个空格。
  2. 精确匹配禅道 title → 命中 1 → matched=True, caseID=纯数字id。
  3. 命中 0 → 退化"包含匹配"（本地 name 包含某禅道 title，或逆向），列出候选；仍无 → 未找到。
  4. 命中 >1 → 歧义，列出全部候选，取第一个选 caseID 并标记 ambiguous=True。

注意：
  - zentao-cli list 返回 {data:[...]} 包裹，id 可能带 case_ 前缀 → 一律剥为纯数字。
"""
import re
import sys
import json
import datetime

RE_CASE_PREFIX = re.compile(r"^case[_-]?")


def strip_case_prefix(v):
    return re.sub(RE_CASE_PREFIX, "", str(v)).strip()


def norm_title(t):
    t = (t or "").strip().replace("　", " ").replace(" ", " ")
    return re.sub(r"\s+", " ", t).strip()


def main():
    if len(sys.argv) < 3:
        print("用法: python3 resolve_writeback.py <collect_results.json> <zentao_cases.json> [-o 输出.json]", file=sys.stderr)
        sys.exit(2)
    collect_path, cases_path = sys.argv[1], sys.argv[2]
    out_path = None
    product_id = None
    if "-o" in sys.argv:
        out_path = sys.argv[sys.argv.index("-o") + 1]
    if "--productID" in sys.argv:
        product_id = sys.argv[sys.argv.index("--productID") + 1]

    with open(collect_path, encoding="utf-8") as f:
        collect = json.load(f)
    with open(cases_path, encoding="utf-8") as f:
        raw = json.load(f)
    zt_cases = raw.get("data") if isinstance(raw, dict) else raw
    if not isinstance(zt_cases, list):
        print("警告: zentao_cases.json 未解析为列表（非 {data:[]} 也非纯列表）", file=sys.stderr)
        zt_cases = []

    # 建 title 索引
    title_index = {}
    for c in zt_cases:
        if not isinstance(c, dict):
            continue
        t = norm_title(c.get("title"))
        case_id = strip_case_prefix(c.get("id"))
        if t:
            title_index.setdefault(t, []).append({"id": case_id, "title": t})

    weird = [i for i, v in enumerate(title_index.values()) if len(v) > 1]

    # 反向索引：每条结果
    plan = []
    for r in collect.get("results", []):
        local_name = norm_title(r.get("name"))
        status = r.get("status")
        case_id = strip_case_prefix(r.get("case_id"))
        entry = {
            "case_id": case_id,
            "name": local_name,
            "local_status": status,
            "status": status,  # 拟写状态 = 本地状态（passed → pass, failed → fail）
            "error": r.get("error", ""),
            "screenshot": r.get("screenshot", ""),
            "matched": False,
            "ambiguous": False,
            "caseID": "",
            "candidates": [],
            "resolve_note": "",
        }
        if not local_name:
            entry["resolve_note"] = "本地结果缺名称，无法反查"
            plan.append(entry)
            continue
        exact = title_index.get(local_name)
        if not exact:
            exact = title_index.get(local_name, []) if local_name in title_index else None
        if exact:
            entry["matched"] = True
            if len(exact) == 1:
                entry["caseID"] = exact[0]["id"]
            else:
                entry["ambiguous"] = True
                entry["candidates"] = [x["id"] for x in exact]
                entry["caseID"] = exact[0]["id"]  # 默认取第一个，待用户确认
                entry["resolve_note"] = f"标题命中多年用例(候选 ids: {', '.join(entry['candidates'])})，默认取 {entry['caseID']}"
        else:
            # 退化：包含匹配
            lower = local_name.lower()
            contains_hits = [
                (cid, t) for t, items in title_index.items()
                if lower in t.lower() or t.lower() in lower
                for cid in [items[0]["id"]]
            ]
            if contains_hits:
                entry["resolve_note"] = f"精确未命中，包含匹配候选: {json.dumps(contains_hits[:5], ensure_ascii=False)}"
                entry["candidates"] = [x[0] for x in contains_hits[:5]]
                if len(entry["candidates"]) == 1:
                    entry["matched"] = True
                    entry["caseID"] = entry["candidates"][0]
            else:
                entry["resolve_note"] = "禅道中未找到对应标题"
        plan.append(entry)

    stats = {
        "total": len(plan),
        "will_pass": sum(1 for p in plan if p["status"] == "passed" and p["matched"]),
        "will_fail": sum(1 for p in plan if p["status"] == "failed" and p["matched"]),
        "not_found": sum(1 for p in plan if not p["matched"]),
        "ambiguous": sum(1 for p in plan if p["ambiguous"]),
        "duplicate_title_in_zentao": len(weird),
    }
    payload = {
        "productID": product_id,
        "resolved_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "stats": stats,
        "plan": plan,
    }
    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f"已生成待回写清单: {out_path}")
    # 打印 dry-run 表
    print("-" * 100)
    hdr = f"{'本地用例ID':<14}{'状态':<8}{'禅道caseID':<12}{'标题/候选'} "
    print(hdr)
    print("-" * 100)
    for p in plan:
        cid = p["caseID"] if p["matched"] else ("?" if not p["matched"] else "-")
        note = p["resolve_note"] if not p["matched"] or p["ambiguous"] else p["name"]
        flag = "PASS" if p["status"] == "passed" else "FAIL"
        print(f"{p['case_id']:<14}{flag:<8}{str(cid):<12}{note[:70]}")
    print("-" * 100)
    print(f"统计: 总数={stats['total']} 将写通过={stats['will_pass']} 将写失败={stats['will_fail']} "
          f"未找到={stats['not_found']} 歧义={stats['ambiguous']} 禅道重标题组数={stats['duplicate_title_in_zentao']}")


if __name__ == "__main__":
    main()