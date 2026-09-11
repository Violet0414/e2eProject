#!/usr/bin/env python3
"""selfcheck.py - 生成后自检脚本。

供 test-script-generate-standalone 技能在第⑧步使用：脚本生成完毕、交付给用户前，
对输出目录做一轮自动化检查，把"脚本一跑就炸"的问题在生成阶段就拦住。

检查项（6 项）：
  1. 语法检查          — py_compile 逐文件编译
  2. viewport 字典语法  — 检测 viewport={{...}} 双层大括号的常见笔误
  3. 模板完整性        — 五层结构 / record_result / tid() / main() / if __name__ 等
  4. 定位器预检        — 用 auth_state 登录态打开目标页，抽样验证关键定位器能命中元素
  5. 断言方式检查      — input/select/date 类字段不该用 inner_text() 断言，应用 input_value()
  6. testid 元素类型推断 — 从 testids.json 读元素类型，生成断言时自动选对方式（本脚本只做报告，
                          具体修复由生成器在第⑥步结合 testids.json 完成）

用法：
  python3 selfcheck.py --script-dir <dir> [--base-url ...] [--auth-state ...] [--route-path ...]

退出码：
  0 = 全部通过 / 仅告警
  1 = 存在错误级问题（需要修复后再交付）
  2 = 参数错误
"""
import argparse
import json
import os
import re
import sys
import traceback
from pathlib import Path

# =============================================================================
# 检查项 1：语法检查
# =============================================================================
def check_syntax(script_dir: Path) -> list:
    """逐文件 py_compile，返回错误列表。"""
    issues = []
    import py_compile
    for f in sorted(script_dir.glob("*.py")):
        if f.name.startswith("_"):
            continue
        try:
            py_compile.compile(str(f), doraise=True)
        except py_compile.PyCompileError as e:
            issues.append(("error", f.name, f"语法错误: {e.msg}"))
    return issues


# =============================================================================
# 检查项 2：viewport 双层大括号笔误
# =============================================================================
def check_viewport_dict(script_dir: Path) -> list:
    """检测 viewport={{...}} 这类 .format() 转义后残留的双层大括号。"""
    issues = []
    pattern = re.compile(r"viewport\s*=\s*\{\{")
    for f in sorted(script_dir.glob("*.py")):
        if f.name.startswith("_"):
            continue
        text = f.read_text(encoding="utf-8")
        if pattern.search(text):
            issues.append(("error", f.name, "viewport 使用了双层大括号 {{...}}，应为单层 {...}"))
    return issues


# =============================================================================
# 检查项 3：模板完整性（五层结构）
# =============================================================================
REQUIRED_PATTERNS = {
    "配置区 CONFIG":        r"① 配置区|CONFIG",
    "辅助层 HELPER":        r"② 辅助层|HELPER",
    "页面层 PAGE OBJECT":   r"③ 页面层|PAGE OBJECT",
    "用例层 TEST CASE":     r"④ 用例层|TEST CASE",
    "驱动层 DRIVER":        r"⑤ 驱动层|DRIVER",
    "record_result 函数":    r"def record_result\(",
    "tid 函数":              r"def tid\(",
    "check 函数":            r"def check\(",
    "expect_toast 函数":     r"def expect_toast\(",
    "main 函数":             r"def main\(\)",
    "if __name__ 入口":      r'if __name__ == ["\']__main__["\']',
    "TEST_RESULT_JSON 协议": r"TEST_RESULT_JSON:",
}

def check_template_completeness(script_dir: Path) -> list:
    """检查每个脚本是否具备完整的五层结构和关键函数。"""
    issues = []
    for f in sorted(script_dir.glob("*.py")):
        if f.name.startswith("_"):
            continue
        text = f.read_text(encoding="utf-8")
        for name, pat in REQUIRED_PATTERNS.items():
            if not re.search(pat, text):
                issues.append(("error", f.name, f"缺少 {name}"))
    return issues


# =============================================================================
# 检查项 4：定位器预检（需真实浏览器 + auth_state）
# =============================================================================
def extract_locators_for_precheck(script_dir: Path) -> dict:
    """从所有脚本中抽取定位器候选，去重后用于预检。
    返回 {label: selector_str}，label 用于报告。
    """
    locators = {}  # key=标签(如 person-name), value=selector 字符串

    for f in sorted(script_dir.glob("*.py")):
        if f.name.startswith("_"):
            continue
        text = f.read_text(encoding="utf-8")

        # 去掉辅助函数 tid / rich_text 的定义体（避免抽到 f-string 里的 {testid} 模板变量）
        # 做法：只在 run_case / 页面类 __init__ 范围内抽
        text_for_extract = ""
        in_po_init = False
        in_run_case = False
        for line in text.split("\n"):
            if "def __init__(self" in line:
                in_po_init = True
            elif "def run_case" in line:
                in_run_case = True
                in_po_init = False
            elif in_po_init and line.strip() and not line.startswith("        ") and not line.startswith("\t"):
                in_po_init = False  # 出了 __init__
            if in_po_init or in_run_case:
                text_for_extract += line + "\n"

        if not text_for_extract:
            text_for_extract = text  # 兜底：没识别到就全量抽

        # tid(page, "xxx", "yyy")  → 抽 testid
        for m in re.finditer(r'tid\(page,\s*"([^"]+)"', text_for_extract):
            tid_val = m.group(1)
            if "{" in tid_val or "}" in tid_val:
                continue  # 跳过模板变量
            locators[f"testid:{tid_val}"] = f"[data-testid='{tid_val}']"

        # self.<name> = lambda: tid(page, "xxx", ...) 中的 testid
        for m in re.finditer(r'self\.\w+\s*=\s*lambda:\s*tid\(\s*page\s*,\s*"([^"]+)"', text_for_extract):
            tid_val = m.group(1)
            if "{" in tid_val:
                continue
            locators[f"testid:{tid_val}"] = f"[data-testid='{tid_val}']"

        # page.locator("...") 中含 placeholder 的定位
        for m in re.finditer(r'page\.locator\("([^"]*placeholder[^"]*)"\)', text_for_extract):
            sel = m.group(1)
            if "{" in sel or "}" in sel:
                continue
            locators[f"locator:{sel[:50]}"] = sel

        # [data-testid='xxx'] 字面量形式
        for m in re.finditer(r"\[data-testid='([^']+)'\]", text_for_extract):
            tid_val = m.group(1)
            if "{" in tid_val or "}" in tid_val:
                continue
            key = f"testid:{tid_val}"
            if key not in locators:
                locators[key] = f"[data-testid='{tid_val}']"

    return locators


def check_locators_live(script_dir: Path, base_url: str, route_path: str,
                        auth_state: str) -> list:
    """打开目标页面，抽样验证定位器能命中元素。
    返回 [(level, script, message), ...]
    """
    issues = []
    if not base_url or not route_path:
        return [("warn", "selfcheck", "定位器预检跳过：缺少 base_url 或 route_path")]

    auth_path = None
    if auth_state:
        auth_path = Path(auth_state)
        if not auth_path.is_absolute():
            auth_path = script_dir / auth_state
        if not auth_path.exists():
            return [("warn", "selfcheck", f"定位器预检跳过：auth_state 不存在 {auth_path}")]

    locators = extract_locators_for_precheck(script_dir)
    if not locators:
        return [("warn", "selfcheck", "定位器预检跳过：未抽取到任何定位器")]

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return [("warn", "selfcheck", "定位器预检跳过：未安装 playwright")]

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context(
                storage_state=str(auth_path) if auth_path and auth_path.exists() else None,
                viewport={"width": 1920, "height": 1080})
            page = ctx.new_page()
            page.goto(base_url + route_path, wait_until="domcontentloaded")
            try:
                page.wait_for_load_state("networkidle", timeout=3000)
            except Exception:
                pass
            page.wait_for_timeout(800)  # 等 SPA 动态组件挂载（比原 1500ms 短）

            hit = 0
            miss = 0
            sel_items = [(label, sel) for label, sel in locators.items()]
            # 一次性批量求值所有 selector 命中数，避免逐个 locator.count() 的往返开销
            counts = None
            if sel_items:
                try:
                    counts = page.evaluate(
                        """(sels) => sels.map(s => {
                            try { return document.querySelectorAll(s).length; } catch (e) { return -1; }
                        })""",
                        [sel for _, sel in sel_items],
                    )
                except Exception:
                    counts = None

            for i, (label, sel) in enumerate(sel_items):
                try:
                    cnt = counts[i] if counts is not None else None
                    if cnt in (None, -1):  # 批量求值不可用或 selector 不兼容（如 :has-text）
                        cnt = page.locator(sel).count()
                    if cnt == 0:
                        issues.append(("error", "定位器预检",
                                       f"定位器零命中: {label} -> {sel}"))
                        miss += 1
                    else:
                        hit += 1
                except Exception as e:
                    issues.append(("warn", "定位器预检",
                                   f"定位器查询异常: {label} -> {e}"))
                    miss += 1

            browser.close()
            issues.insert(0, ("info", "定位器预检",
                              f"共检查 {len(locators)} 个定位器，命中 {hit}，零命中 {miss}"))
    except Exception as e:
        issues.append(("error", "定位器预检",
                       f"打开页面失败: {e}"))

    return issues


# =============================================================================
# 检查项 5：断言方式检查
# =============================================================================
# 模式：check(page, "...", <locator_expr>, expect="...")
# 问题：locator 指向的是 input/select/date 类元素时，用 inner_text() 拿不到值
CHECK_PATTERN = re.compile(
    r'check\(\s*page\s*,\s*"[^"]*"\s*,\s*'
    r'(lambda:\s*pg\.\w+|\w+\(\)|[^,]+?)\s*,\s*expect="[^"]*"\s*\)'
)

# 判断 locator 是否指向 input 类字段（粗略判断：字段名包含 name/title/idcard/no/date/time
# 或 testids.json 中 type=input/date/other(容器内 input)）
INPUT_LIKE_NAMES = {
    "name", "idcard", "birth_date", "gender", "nation", "province", "city", "county",
    "death_type", "death_time", "found_time", "death_cause",
    "cert_no", "issue_date", "fam_name", "fam_idcard", "fam_phone", "fam_relation",
    "resident_addr", "death_addr", "title", "content", "source", "status", "type",
}

def _looks_like_input(locator_expr: str, testids_info: dict) -> bool:
    """判断一个定位器表达式是否指向 input/select/date 类（用 inner_text 断言会失败）。"""
    expr = locator_expr.strip()

    # 从 testids.json 查真实类型
    # 形如 lambda: pg.xxx  →  取 xxx 作为字段名
    m = re.search(r"pg\.(\w+)", expr)
    if m:
        field = m.group(1).lower().replace("_", "-")
        # 在 testids_info.index.by_label / by_testid 查
        for tid_val, info in testids_info.items():
            if tid_val.endswith(field) or field in tid_val:
                t = info.get("type", "")
                if t in ("input", "date", "readonly_input", "number"):
                    return True
                if t == "other":
                    # other 常是 select/date 容器，内部有 input
                    children = info.get("children", [])
                    if any(c.get("type") in ("input", "date", "textarea") for c in children):
                        return True
                    return True  # 保守认为 other 容器内有可输入元素

    # 关键字启发式
    expr_lower = expr.lower()
    for kw in ["input", "select", "date", "textarea", "placeholder", "input_value"]:
        if kw in expr_lower:
            return True

    # 字段名启发式
    for name in INPUT_LIKE_NAMES:
        if name in expr_lower:
            return True

    return False


def check_assertion_style(script_dir: Path, testids_path: str = None) -> list:
    """检查 check() 断言是否对 input 类字段用了 inner_text（应该用 input_value）。"""
    issues = []

    # 加载 testids.json（如果有）
    testids_info = {}
    if testids_path and os.path.exists(testids_path):
        try:
            with open(testids_path, encoding="utf-8") as f:
                data = json.load(f)
            for el in data.get("elements", []):
                testids_info[el.get("testid", "")] = el
        except Exception:
            pass

    for f in sorted(script_dir.glob("*.py")):
        if f.name.startswith("_"):
            continue
        text = f.read_text(encoding="utf-8")
        # 找 check(page, "desc", locator, expect="...") 形式
        for m in re.finditer(
            r'check\(\s*page\s*,\s*"([^"]*)"\s*,\s*(lambda:[^,]+|[^,]+?)\s*,\s*expect="',
            text
        ):
            desc = m.group(1)
            loc_expr = m.group(2).strip()
            if _looks_like_input(loc_expr, testids_info):
                issues.append((
                    "warn", f.name,
                    f"断言可能用错方式: 字段 [{desc}] 疑似 input 类，但用 inner_text() 断言。"
                    f"建议改用 input_value()。定位器: {loc_expr[:60]}"
                ))
    return issues


# =============================================================================
# 检查项 6：testid 元素类型推断（报告型，告诉生成器该怎么选断言方式）
# =============================================================================
def check_testid_type_report(script_dir: Path, testids_path: str = None) -> list:
    """读取 testids.json，输出每个 testid 的类型建议（input 用 input_value，
    div/span 用 inner_text，button 用 click）。仅作信息性报告。"""
    issues = []
    if not testids_path or not os.path.exists(testids_path):
        return [("info", "testid类型", "无 testids.json，跳过类型推断报告")]

    with open(testids_path, encoding="utf-8") as f:
        data = json.load(f)

    elements = data.get("elements", [])
    if not elements:
        return [("warn", "testid类型", "testids.json 中 elements 为空")]

    summary = f"共 {len(elements)} 个真实 testid："
    type_counts = {}
    for el in elements:
        t = el.get("type", "unknown")
        type_counts[t] = type_counts.get(t, 0) + 1
    summary += ", ".join(f"{k}={v}" for k, v in sorted(type_counts.items()))
    issues.append(("info", "testid类型", summary))

    # 建议：type=input/date 的字段，断言应使用 input_value()
    input_like = [el["testid"] for el in elements if el.get("type") in ("input", "date", "readonly_input", "number")]
    if input_like:
        issues.append(("info", "testid类型",
                       f"以下 testid 为输入类，断言应用 input_value(): {', '.join(input_like[:10])}"
                       + ("..." if len(input_like) > 10 else "")))

    return issues


# =============================================================================
# 主入口
# =============================================================================
def main() -> int:
    parser = argparse.ArgumentParser(description="自包含测试脚本生成后自检")
    parser.add_argument("--script-dir", required=True, help="脚本目录")
    parser.add_argument("--base-url", default="", help="目标系统基础地址（定位器预检用）")
    parser.add_argument("--route-path", default="", help="页面路由（定位器预检用）")
    parser.add_argument("--auth-state", default="", help="登录态 auth_state.json 路径（定位器预检用）")
    parser.add_argument("--testids", default="", help="testids.json 路径（断言方式检查用）")
    parser.add_argument("--no-live", action="store_true", help="跳过需要浏览器的定位器预检")
    args = parser.parse_args()

    script_dir = Path(args.script_dir).resolve()
    if not script_dir.is_dir():
        print(f"错误：脚本目录不存在: {script_dir}", file=sys.stderr)
        return 2

    testids_path = args.testids
    if not testids_path:
        default = script_dir / "testids.json"
        if default.exists():
            testids_path = str(default)

    all_issues = []

    print("=" * 60)
    print("【1/6】语法检查")
    issues = check_syntax(script_dir)
    all_issues.extend(issues)
    _print_issues(issues)

    print("\n【2/6】viewport 字典语法")
    issues = check_viewport_dict(script_dir)
    all_issues.extend(issues)
    _print_issues(issues)

    print("\n【3/6】模板完整性")
    issues = check_template_completeness(script_dir)
    all_issues.extend(issues)
    _print_issues(issues)

    print("\n【4/6】定位器预检")
    if args.no_live:
        print("  (已跳过 --no-live)")
    else:
        issues = check_locators_live(script_dir, args.base_url, args.route_path, args.auth_state)
        all_issues.extend(issues)
        _print_issues(issues)

    print("\n【5/6】断言方式检查")
    issues = check_assertion_style(script_dir, testids_path)
    all_issues.extend(issues)
    _print_issues(issues)

    print("\n【6/6】testid 元素类型推断")
    issues = check_testid_type_report(script_dir, testids_path)
    all_issues.extend(issues)
    _print_issues(issues)

    # 统计
    errors = sum(1 for lvl, _, _ in all_issues if lvl == "error")
    warns = sum(1 for lvl, _, _ in all_issues if lvl == "warn")
    infos = sum(1 for lvl, _, _ in all_issues if lvl == "info")

    print("\n" + "=" * 60)
    print(f"自检完成：错误 {errors} / 警告 {warns} / 信息 {infos}")
    if errors > 0:
        print("⚠️  存在错误级问题，建议修复后再交付。")
        return 1
    else:
        print("✅ 无错误级问题（可能有告警，请关注）。")
        return 0


def _print_issues(issues):
    if not issues:
        print("  ✓ 全部通过")
        return
    for lvl, src, msg in issues:
        icon = {"error": "❌", "warn": "⚠️ ", "info": "ℹ️ "}.get(lvl, "  ")
        print(f"  {icon} [{src}] {msg}")


if __name__ == "__main__":
    sys.exit(main())
