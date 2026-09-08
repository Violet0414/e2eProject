#!/usr/bin/env python3
"""run_collect.py - 批量运行自包含 Playwright 测试脚本并聚合测试报告。

由 test-script-run-collect 技能调用。逐个执行目录下的自包含测试脚本（.py），
捕获每个脚本按 TEST_RESULT_JSON: 协议行输出的结果，生成一份 测试报告.md，
并在结束后清理临时产物，仅保留：测试脚本（.py）+ 测试报告.md + screenshots/。

用法：
  python3 run_collect.py --script-dir <目录> [--base-url ...] [--timeout 60]
      [--headless] [--filter TC-PERSON] [--max-retry 1] [--keep-results] [--no-live]

退出码：0 = 完成（可能含失败用例）；1 = 参数错误 / 目录无效。
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import traceback
from datetime import datetime
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent
GENERATED_ROOT = SRC_DIR.parents[2] / "generated_scripts"  # e2eProject/generated_scripts
PROTOCOL_RE = re.compile(r"TEST_RESULT_JSON:\s*(\{.*\})", re.S)


# =============================================================================
# ① 参数与目录解析
# =============================================================================
def parse_args():
    p = argparse.ArgumentParser(description="批量运行自包含测试脚本并生成测试报告")
    p.add_argument("--script-dir", default="", help="脚本批次目录；缺省自动选 generated_scripts/ 下最新批次")
    p.add_argument("--base-url", default="", help="截图补拍用基础地址；缺省从脚本内 BASE_URL= 提取")
    p.add_argument("--timeout", type=int, default=60, help="每个脚本执行超时秒数，默认 60")
    p.add_argument("--headless", action="store_true", help="强制无头运行（HEADLESS=True）")
    p.add_argument("--filter", default="", help="case_id 前缀过滤，只跑匹配用例，如 TC-PERSON")
    p.add_argument("--max-retry", type=int, default=1, help="偶发时序失败重跑次数，默认 1")
    p.add_argument("--keep-results", action="store_true", help="保留 results.json/jsonl 等临时产物（默认清理）")
    p.add_argument("--no-live", action="store_true", help="跳过失败用例截图补拍（无需浏览器）")
    return p.parse_args()


def resolve_script_dir(path: str) -> Path:
    if path:
        d = Path(path).resolve()
        if not d.is_dir():
            sys.exit(f"错误：脚本目录不存在: {d}")
        return d
    if not GENERATED_ROOT.is_dir():
        sys.exit(f"错误：缺省目录不存在: {GENERATED_ROOT}，请用 --script-dir 指定")
    batches = sorted((c for c in GENERATED_ROOT.iterdir() if c.is_dir()),
                     key=lambda c: c.stat().st_mtime, reverse=True)
    if not batches:
        sys.exit(f"错误：{GENERATED_ROOT} 下无批次目录")
    print(f"[run_collect] 未指定 --script-dir，自动选择最近批次: {batches[0].name}")
    return batches[0]


# =============================================================================
# ② 脚本元数据提取（route / base_url / case_id）
# =============================================================================
_ASSIGN_RE = re.compile(r'^\s*ROUTE_PATH\s*=\s*["\']([^"\']+)["\']', re.M)
_BASEURL_RE = re.compile(r'^\s*BASE_URL\s*=\s*["\']([^"\']+)["\']', re.M)


def extract_script_meta(py_path: Path) -> dict:
    """从脚本文本提取 case_id / route_path / base_url，供截图补拍使用。"""
    text = py_path.read_text(encoding="utf-8")
    m = _ASSIGN_RE.search(text)
    route = m.group(1) if m else ""
    m = _BASEURL_RE.search(text)
    base = m.group(1) if m else ""
    return {"id": py_path.stem, "route": route, "base_url": base}


# =============================================================================
# ③ 单个脚本运行
# =============================================================================
def run_one(script_dir: Path, fname: str, timeout: int, headless_flag: bool) -> dict:
    env = {**os.environ}
    if headless_flag:
        env["HEADLESS"] = "True"
    try:
        proc = subprocess.run(
            ["python3", fname], capture_output=True, text=True,
            timeout=timeout, env=env, cwd=str(script_dir),
        )
    except subprocess.TimeoutExpired:
        return {"status": "failed", "error": f"脚本执行超时（{timeout}s）", "retryable": True}
    except Exception as e:
        return {"status": "failed", "error": f"运行异常: {e}", "retryable": False}

    stdout = proc.stdout
    stderr = proc.stderr
    m = PROTOCOL_RE.search(stdout)
    if m:
        try:
            entry = json.loads(m.group(1))
        except json.JSONDecodeError:
            return {"status": "failed", "error": "协议行 JSON 解析失败", "retryable": True}
        status = entry.get("status", "unknown")
        err = entry.get("error", "")
        entry["retryable"] = (status != "passed")
        if not entry.get("timestamp"):
            entry["timestamp"] = datetime.now().isoformat()
        return entry
    err_msg = (stderr or stdout or "无输出")[-300:]
    return {"status": "failed",
            "error": f"脚本异常退出，未输出结果协议行\nstderr: {err_msg}",
            "retryable": True}


# =============================================================================
# ④ 主流程
# =============================================================================
def collect(full_meta: dict, o) -> dict:
    """合并脚本元数据与本次运行结果。name 优先取协议 entry 的名称，否则用 case_id。"""
    cid = full_meta["id"]
    return {"id": cid, "name": o.get("name") or cid, "status": o.get("status", "failed"),
            "error": o.get("error", ""), "screenshot": o.get("screenshot", ""),
            "timestamp": o.get("timestamp", datetime.now().isoformat()),
            "route": full_meta.get("route", ""), "base_url": full_meta.get("base_url", "")}


def main() -> int:
    args = parse_args()
    script_dir = resolve_script_dir(args.script_dir)
    os.chdir(script_dir)
    os.makedirs("screenshots", exist_ok=True)

    all_py = sorted(f for f in os.listdir(".") if f.endswith(".py") and not f.startswith("_"))
    if args.filter:
        py_files = [f for f in all_py if f.replace(".py", "").startswith(args.filter)]
    else:
        py_files = all_py

    print(f"共发现 {len(py_files)} 个测试脚本")
    print("=" * 60)

    metas = {f: extract_script_meta(Path(f)) for f in py_files}
    results = {}

    for i, f in enumerate(py_files, 1):
        print(f"\n[{i}/{len(py_files)}] 运行 {f} ...", flush=True)
        meta = metas[f]
        out = run_one(script_dir, f, args.timeout, args.headless)
        res = collect(meta, out)

        # 偶发时序失败重跑
        retried = False
        if res["status"] != "passed" and args.max_retry > 0 and out.get("retryable"):
            print(f"  ⚠️ 首次失败，重跑确认...", flush=True)
            out2 = run_one(script_dir, f, args.timeout, args.headless)
            retried = True
            if out2["status"] == "passed":
                out = out2
                res = collect(meta, out)
                res["retried_passed"] = True
                print(f"  ✅ 重跑通过", flush=True)
            else:
                res = collect(meta, out2)

        results[f] = res
        status = res["status"]
        if status == "passed":
            tag = "✅ 通过" if not retried else "✅ 通过(重跑)"
            print(f"  {tag}", flush=True)
        else:
            err_lines = [l for l in (res.get("error") or "").split("\n") if l.strip()]
            err_short = (err_lines[-1] if err_lines else "")[:120]
            print(f"  ❌ 失败: {err_short}", flush=True)

    # 统计
    total = len(results)
    passed = sum(1 for r in results.values() if r.get("status") == "passed")
    failed = total - passed
    rate = passed / total * 100 if total else 0
    print("\n" + "=" * 60)
    print(f"运行完成: 总数 {total} / 通过 {passed} / 失败 {failed} / 通过率 {rate:.1f}%")

    # 失败用例补拍截图（按各自 route）
    failed_cases = [r for r in results.values() if r.get("status") != "passed"]
    if failed_cases and not args.no_live:
        print(f"\n为 {len(failed_cases)} 个失败用例补拍截图（按各自 route）...")
        _shot_failed(script_dir, failed_cases)

    # 生成测试报告
    _write_report(script_dir, results, failed_cases, args)

    # 产物清理
    if not args.keep_results:
        _cleanup(script_dir)

    print(f"\n测试报告已生成: {script_dir}/测试报告.md")
    return 1 if failed else 0


def _shot_failed(script_dir: Path, failed_cases: list) -> None:
    from playwright.sync_api import sync_playwright
    auth = Path("auth_state.json")
    storage_state = str(auth) if auth.exists() else None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context(storage_state=storage_state,
                                      viewport={"width": 1920, "height": 1080})
            page = ctx.new_page()
            for r in failed_cases:
                cid = r["id"]
                shot_path = f"screenshots/{cid}_failed_cli.png"
                base = r.get("base_url") or ""
                route = r.get("route", "")
                if not base or not route:
                    print(f"  ⚠️  {cid} 无 base_url/route，跳过截图")
                    continue
                try:
                    page.goto(base + route)
                    page.wait_for_load_state("networkidle")
                    page.wait_for_timeout(1000)
                    page.screenshot(path=shot_path, full_page=True)
                    if not r.get("screenshot"):
                        r["screenshot"] = shot_path
                    print(f"  📸 {cid} -> {shot_path}")
                except Exception as e:
                    print(f"  ⚠️  {cid} 截图失败: {e}")
            browser.close()
    except Exception as e:
        print(f"  ⚠️  补拍截图整体失败: {e}")


def _write_report(script_dir: Path, results: dict, failed_cases: list, args) -> None:
    ordered = sorted(results.values(), key=lambda r: r["id"])
    report = []
    report.append("# 测试报告")
    report.append("")
    report.append(f"- **运行时间**：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"- **脚本目录**：`{script_dir}`")
    report.append("")
    total = len(ordered)
    passed = sum(1 for r in ordered if r.get("status") == "passed")
    failed = total - passed
    rate = passed / total * 100 if total else 0
    report.append(f"- **总数**：{total}")
    report.append(f"- **通过**：{passed}")
    report.append(f"- **失败**：{failed}")
    report.append(f"- **通过率**：{rate:.1f}%")
    report.append("")

    report.append("## 执行结果")
    report.append("")
    report.append("| 用例ID | 状态 | 名称 | 失败原因 | 截图 |")
    report.append("|--------|------|------|----------|------|")
    for r in ordered:
        cid = r["id"]
        status = r.get("status", "failed")
        if status == "passed":
            status_cn = "通过(重跑)" if r.get("retried_passed") else "通过"
        else:
            status_cn = "失败"
        name = r.get("name") or cid
        err = r.get("error", "") or ""
        err_short = ""
        if err:
            lines = [l for l in err.strip().split("\n") if l.strip()]
            err_short = lines[-1] if lines else err[:80]
            err_short = err_short.replace("|", "\\|")[:120]
        shot = r.get("screenshot", "") or ""
        shot_md = f"[{os.path.basename(shot)}]({shot})" if shot else ""
        report.append(f"| {cid} | {status_cn} | {name} | {err_short} | {shot_md} |")
    report.append("")

    if failed_cases:
        report.append("## 失败用例详情")
        report.append("")
        for r in sorted(failed_cases, key=lambda x: x["id"]):
            cid = r["id"]
            name = r.get("name") or cid
            err = r.get("error", "") or ""
            shot = r.get("screenshot", "") or ""
            report.append(f"### {cid} {name}")
            report.append("")
            report.append("```")
            report.append(err[-800:] if len(err) > 800 else err)
            report.append("```")
            if shot:
                report.append("")
                report.append(f"截图：`{shot}`")
            report.append("")

    (script_dir / "测试报告.md").write_text("\n".join(report), encoding="utf-8")


def _cleanup(script_dir: Path) -> None:
    for name in ("results.json", "results.jsonl"):
        p = script_dir / name
        if p.exists():
            p.unlink()
            print(f"  🧹 清理 {name}")
    for pat in ("*.log",):
        for p in script_dir.glob(pat):
            p.unlink()
            print(f"  🧹 清理 {p.name}")
    pycache = script_dir / "__pycache__"
    if pycache.is_dir():
        shutil.rmtree(pycache)
        print("  🧹 清理 __pycache__")


if __name__ == "__main__":
    sys.exit(main())