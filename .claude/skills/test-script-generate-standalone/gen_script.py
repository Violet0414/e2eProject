#!/usr/bin/env python3
"""gen_script.py - 自包含测试脚本渲染器。

供 test-script-generate-standalone 技能在第⑥步使用：LLM 只产出"差异片段"
（页面层片段 + 每用例步骤片段），本脚本把片段机械拼装进固化模板
（template.py.tpl，①配置区/②辅助层/⑤驱动层等 250 行样板 100% 保真），
替代"LLM 逐个重写全量 300~400 行脚本"的慢速生成方式。

片段目录结构（_specs/ 保留在批次目录下供审计与重渲染）：
  _specs/
    pages/
      {PageName}.json        # {"page_name": "XxxPage", "page_doc": "模块/页面名"}
      {PageName}_page.py     # 页面层片段，两个段标记：
                             #   # ---- locators ----  → __init__ 内定位器（渲染缩进 8 空格）
                             #   # ---- methods ----   → class 内动作方法（渲染缩进 4 空格）
    cases/
      {case_id}/
        spec.json            # {"case_id","case_name","route_path","page_name"}
        steps.py             # run_case 内步骤代码，顶格写（渲染缩进 4 空格）

约定：片段代码一律顶格写，缩进由本脚本统一加；同页面多用例共享一份 page 片段。

用法：
  python3 gen_script.py --spec-dir <_specs目录> --out <输出目录> [--only TC-XXX-001 ...]

退出码：
  0 = 全部渲染成功且编译通过
  1 = 存在校验/渲染/编译失败（详见输出）
  2 = 参数错误
"""
import argparse
import json
import py_compile
import sys
from pathlib import Path

# placeholder 插入点 → (片段段标记, 渲染基准缩进)
SLOT_SPEC = {
    "PAGE_OBJECT_ATTRS":   ("locators", 8),
    "PAGE_OBJECT_METHODS": ("methods", 4),
    "CASE_STEPS":          (None, 4),   # None = 整个 steps.py 文件
}
LOCATORS_MARK = "# ---- locators ----"
METHODS_MARK = "# ---- methods ----"

# 元数据占位符 → spec/page 元数据键
META_FIELDS = ["case_id", "case_name", "route_path", "page_name", "page_doc"]


def _indent_block(lines: list, base_indent: int) -> str:
    """把顶格片段行统一加 base_indent 缩进；空行不加尾随空格。"""
    out = []
    for ln in lines:
        ln = ln.rstrip()
        if not ln.strip():
            out.append("")
        else:
            out.append(" " * base_indent + ln)
    return "\n".join(out)


def parse_page_fragments(text: str, src: str) -> dict:
    """解析页面层片段，按段标记切分为 {"locators": [...], "methods": [...]}。

    段标记行本身不输出（模板中已有注释标题）。段标记前的内容只允许空行/注释行。
    """
    frags = {"locators": [], "methods": []}
    seen = set()
    current = None
    for ln in text.split("\n"):
        stripped = ln.strip()
        if stripped == LOCATORS_MARK:
            current = "locators"
            seen.add(current)
            continue
        if stripped == METHODS_MARK:
            current = "methods"
            seen.add(current)
            continue
        if current is None:
            if stripped and not stripped.startswith("#"):
                raise ValueError(f"{src}: 段标记前存在代码行，片段必须在 "
                                 f"'{LOCATORS_MARK}' / '{METHODS_MARK}' 之后顶格书写")
            continue
        frags[current].append(ln)
    missing = [{"locators": LOCATORS_MARK, "methods": METHODS_MARK}[k]
               for k in frags if k not in seen]
    if missing:
        raise ValueError(f"{src}: 缺少段标记 {missing}，页面层片段须包含两个段标记")
    return frags


def render_case(template: str, spec: dict, page_meta: dict, page_frags: dict,
                steps_text: str) -> str:
    """渲染单个用例脚本：元数据 str.replace + 三个 placeholder 整行替换。"""
    out = template
    meta = {
        "case_id": spec["case_id"],
        "case_name": spec["case_name"],
        "route_path": spec["route_path"],
        "page_name": spec["page_name"],
        "page_doc": page_meta.get("page_doc", spec["page_name"]),
    }
    for field in META_FIELDS:
        out = out.replace(f"@@{field.upper()}@@", str(meta[field]))

    steps_lines = steps_text.split("\n")
    blocks = {
        "PAGE_OBJECT_ATTRS": _indent_block(page_frags["locators"], 8),
        "PAGE_OBJECT_METHODS": _indent_block(page_frags["methods"], 4),
        "CASE_STEPS": _indent_block(steps_lines, 4),
    }
    lines = out.split("\n")
    replaced = []
    for ln in lines:
        stripped = ln.strip()
        hit = None
        if stripped.startswith("## placeholder:"):
            hit = stripped.split("## placeholder:", 1)[1].strip()
        if hit in blocks:
            replaced.append(blocks[hit])
        else:
            replaced.append(ln)
    out = "\n".join(replaced)

    # 残留自检：占位符未填上说明片段缺失，直接失败比产出坏脚本好
    leftovers = [w for w in ["@@CASE_ID@@", "@@CASE_NAME@@", "@@ROUTE_PATH@@",
                             "@@PAGE_NAME@@", "@@PAGE_DOC@@", "## placeholder:"]
                 if w in out]
    if leftovers:
        raise ValueError(f"渲染后仍残留占位符: {leftovers}（片段为空或段标记缺失）")
    return out


def load_spec(case_dir: Path) -> dict:
    """读取并校验单个用例 spec.json。"""
    spec_path = case_dir / "spec.json"
    if not spec_path.exists():
        raise ValueError(f"缺少 {spec_path}")
    try:
        with open(spec_path, encoding="utf-8") as f:
            spec = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"{spec_path} 不是合法 JSON: {e}")
    required = ["case_id", "case_name", "route_path", "page_name"]
    missing = [k for k in required if not spec.get(k)]
    if missing:
        raise ValueError(f"{spec_path} 缺少必填字段: {missing}")
    if spec["case_id"] != case_dir.name:
        raise ValueError(f"{spec_path} 的 case_id '{spec['case_id']}' 与目录名 "
                         f"'{case_dir.name}' 不一致")
    return spec


def main() -> int:
    parser = argparse.ArgumentParser(
        description="自包含测试脚本渲染器（差异片段 + 固化模板拼装）",
        epilog="片段协议与段标记约定见脚本 docstring 及 SKILL.md「差异片段协议」",
    )
    parser.add_argument("--spec-dir", required=True, help="片段目录（批次下 _specs/）")
    parser.add_argument("--out", required=True, help="脚本输出目录")
    parser.add_argument("--only", nargs="*", default=None,
                        help="只渲染指定 case_id（重渲染/修复场景）")
    parser.add_argument("--template", default=str(Path(__file__).parent / "template.py.tpl"),
                        help="模板文件路径（默认取本脚本同目录 template.py.tpl）")
    args = parser.parse_args()

    spec_dir = Path(args.spec_dir).resolve()
    out_dir = Path(args.out).resolve()
    template_path = Path(args.template).resolve()
    if not spec_dir.is_dir():
        print(f"错误：片段目录不存在: {spec_dir}", file=sys.stderr)
        return 2
    if not template_path.exists():
        print(f"错误：模板文件不存在: {template_path}", file=sys.stderr)
        return 2
    template = template_path.read_text(encoding="utf-8")

    cases_root = spec_dir / "cases"
    if not cases_root.is_dir():
        print(f"错误：缺少用例片段目录: {cases_root}", file=sys.stderr)
        return 2
    case_dirs = sorted(d for d in cases_root.iterdir() if d.is_dir())
    if args.only is not None:
        want = set(args.only)
        case_dirs = [d for d in case_dirs if d.name in want]
        missed = want - {d.name for d in case_dirs}
        if missed:
            print(f"错误：--only 指定的用例无片段目录: {sorted(missed)}", file=sys.stderr)
            return 2
    if not case_dirs:
        print("错误：未发现任何用例片段目录（_specs/cases/*/）", file=sys.stderr)
        return 2

    out_dir.mkdir(parents=True, exist_ok=True)
    page_cache = {}   # page_name -> (meta, frags)
    pages_used = set()
    rendered, failures = [], []

    for case_dir in case_dirs:
        cid = case_dir.name
        try:
            spec = load_spec(case_dir)
            steps_path = case_dir / "steps.py"
            if not steps_path.exists():
                raise ValueError(f"缺少步骤片段: {steps_path}")
            steps_text = steps_path.read_text(encoding="utf-8").strip("\n")
            if not steps_text.strip():
                raise ValueError(f"步骤片段为空: {steps_path}")

            page_name = spec["page_name"]
            if page_name not in page_cache:
                page_meta_path = spec_dir / "pages" / f"{page_name}.json"
                page_py_path = spec_dir / "pages" / f"{page_name}_page.py"
                if not page_py_path.exists():
                    raise ValueError(f"缺少页面层片段: {page_py_path}")
                page_meta = {}
                if page_meta_path.exists():
                    with open(page_meta_path, encoding="utf-8") as f:
                        page_meta = json.load(f)
                frags = parse_page_fragments(
                    page_py_path.read_text(encoding="utf-8"), str(page_py_path))
                if not frags["locators"] and not frags["methods"]:
                    raise ValueError(f"页面层片段两个段均为空: {page_py_path}")
                page_cache[page_name] = (page_meta, frags)
            page_meta, frags = page_cache[page_name]
            pages_used.add(page_name)

            script = render_case(template, spec, page_meta, frags, steps_text)
            out_file = out_dir / f"{cid}.py"
            out_file.write_text(script, encoding="utf-8")
            py_compile.compile(str(out_file), doraise=True)
            rendered.append(cid)
        except Exception as e:
            failures.append((cid, str(e)))

    print("=" * 60)
    print(f"渲染完成：用例 {len(rendered)}/{len(case_dirs)}，涉及页面 {len(pages_used)} 个"
          f"（{', '.join(sorted(pages_used)) or '无'}）")
    print(f"输出目录: {out_dir}")
    if failures:
        print("\n以下用例渲染失败：")
        for cid, msg in failures:
            print(f"  ❌ [{cid}] {msg}")
        return 1
    print("✅ 全部渲染成功且 py_compile 通过。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
