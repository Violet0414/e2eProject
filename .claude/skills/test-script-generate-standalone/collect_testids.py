#!/usr/bin/env python3
"""collect_testids.py - 采集页面真实 data-testid 生成 testids.json（含 index 反查索引）。

供 test-script-generate-standalone 技能在生成脚本前调用：打开目标页面，dump 其 DOM 树上
所有 [data-testid] 元素及相关上下文（label/placeholder/button_text/readonly/富文本等），
并自动点开"新增"弹窗二次采集，产出结构化 testids.json 缓存，供 SKILL 结合测试用例反查
真实 testid 生成脚本定位器。仅依赖 playwright，可脱离 MCP 环境独立运行。

用法：
  python3 collect_testids.py \
      --base-url "http://..." --route-path "/business/..." \
      --auth-state "auth_state.json" \
      --out "testids.json" [--no-dialog] [--headless] [--timeout-ms 20000]
退出码：0=成功；1=运行/采集失败（降级信号）；2=参数错误。
"""
import argparse
import hashlib
import json
import sys
from datetime import datetime

# =============================================================================
# ① 配置与登录（与生成脚本的 login() 保持一致）
# =============================================================================

def login(page, base_url, login_url_path, username, password, sms_code, auth_state) -> None:
    """复用 storage_state 则跳过登录；否则填账号密码登录。"""
    if auth_state:
        page.wait_for_load_state("networkidle")
        return
    page.goto(base_url + login_url_path)
    page.wait_for_load_state("networkidle")
    if username:
        page.fill("input[placeholder*='账号']", username)
    if password:
        page.fill("input[placeholder*='密码']", password)
    if sms_code:
        page.fill("input[placeholder*='验证码']", sms_code)
    page.click("button:has-text('登录')")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)


# =============================================================================
# ② DOM dump（page.evaluate 一次性遍历，JS 内联分类）
# =============================================================================

_DUMP_JS = r"""
(() => {
  const classify = (el) => {
    const tag = el.tagName;
    if (tag === 'INPUT') {
      switch ((el.type || '').toLowerCase()) {
        case 'checkbox': return 'checkbox';
        case 'radio': return 'radio';
        case 'date': case 'datetime-local': case 'time': return 'date';
        default:
          if (el.closest('.el-switch, .el-switch-core') !== null) return 'switch';
          if (el.closest('.el-input-number') !== null) return 'number';
          if (el.closest('.el-date-editor, .el-date-editor--date, .el-date-editor--datetime')
              !== null) return 'date';
          if (el.getAttribute('readonly') !== null) return 'readonly_input';
          return 'input';
      }
    }
    if (tag === 'TEXTAREA') return 'textarea';
    if (tag === 'SELECT') return 'select';
    if (tag === 'BUTTON') return 'button';
    if (el.querySelector('[contenteditable="true"]')) return 'rich_text';
    if (el.closest('.el-upload') !== null) return 'upload';
    return 'other';
  };

  const childrenSummaries = (el) => {
    const out = [];
    el.querySelectorAll('input[placeholder], textarea[placeholder]').forEach((inp) => {
      out.push({type: (inp.tagName === 'TEXTAREA' ? 'textarea' : inp.type || 'input'),
                placeholder: inp.getAttribute('placeholder') || ''});
    });
    return out;
  };

  const labelOf = (el) => {
    const item = el.closest('.el-form-item');
    if (item) {
      const lbl = item.querySelector(':scope > .el-form-item__label');
      if (lbl && lbl.textContent) return lbl.textContent.trim();
      const label = item.querySelector('.el-form-item__label');
      if (label && label.textContent) return label.textContent.trim();
    }
    return '';
  };

  const seen = new Set();
  const elements = [];
  document.querySelectorAll('[data-testid]').forEach((el) => {
    const testid = el.getAttribute('data-testid');
    if (!testid || seen.has(testid)) return;
    seen.add(testid);
    elements.push({
      testid: testid,
      scope: SCOPE,
      tag: el.tagName,
      type: classify(el),
      placeholder: (el.getAttribute('placeholder') || ''),
      label: labelOf(el),
      button_text: (el.textContent || '').trim(),
      value: (el.value !== undefined ? (el.value || '') : ''),
      readonly: el.hasAttribute('readonly') || (el.readOnly !== undefined && el.readOnly),
      disabled: el.disabled === true || el.getAttribute('aria-disabled') === 'true',
      has_contenteditable: el.querySelector('[contenteditable="true"]') !== null,
      visible: !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length),
      children: childrenSummaries(el),
    });
  });
  return elements;
})()
"""


def dump_testids(page, scope: str):
    """在 page 上执行 DUMP_JS 采集 [data-testid] 元素。scope 标记 main / add_dialog。"""
    return list(page.evaluate(_DUMP_JS.replace("SCOPE", json.dumps(scope))))

# =============================================================================
# ③ 新增弹窗采集
# =============================================================================

def find_add_button(page, main_elements) -> str | None:
    """按序定位'新增'按钮选择器：先 testid 命中，再 button-bar/primary 语义。"""
    for el in main_elements:
        if el["type"] == "button" and el["button_text"].strip() == "新增":
            return f"[data-testid='{el['testid']}']"
    for sel in ('.button-bar button:has-text("新增")',
                '.el-button--primary:has-text("新增")',
                'button:has-text("新增")'):
        if page.locator(sel).count() > 0:
            return sel
    return None


def open_add_dialog(page, timeout_ms: int) -> tuple[bool, str]:
    """点击新增按钮，等待弹窗（el-dialog / el-drawer）出现，返回 (是否打开, 弹窗标题)。"""
    loc = page.locator(".el-dialog:visible, .el-drawer:visible").last
    title = ""
    try:
        loc.wait_for(state="visible", timeout=timeout_ms)
        for sel in (".el-dialog__title", ".el-drawer__title"):
            t = page.locator(f"{sel}:visible").first
            if t.count() > 0 and t.inner_text().strip():
                title = t.inner_text().strip()
                break
    except Exception:
        pass
    return loc.count() > 0, title


# =============================================================================
# ④ 索引构建
# =============================================================================

def build_index(elements) -> dict:
    by_label, by_placeholder, by_button_text = {}, {}, {}

    def _append(table, key, testid):
        if not key:
            return
        table.setdefault(key, [])
        if testid not in table[key]:
            table[key].append(testid)

    for el in elements:
        if el["label"]:
            _append(by_label, el["label"], el["testid"])
        if el["placeholder"]:
            _append(by_placeholder, el["placeholder"], el["testid"])
        for c in el.get("children", []):      # 容器型 testid：子输入 placeholder 反查到容器 testid
            if c.get("placeholder"):
                _append(by_placeholder, c["placeholder"], el["testid"])
        if el["type"] == "button" and el["button_text"]:
            _append(by_button_text, el["button_text"].strip(), el["testid"])
    return {"by_label": by_label, "by_placeholder": by_placeholder, "by_button_text": by_button_text}


# =============================================================================
# ⑤ 缓存
# =============================================================================

def cache_key(base_url: str, route_path: str) -> str:
    return hashlib.sha1(f"{base_url}|{route_path}".encode("utf-8")).hexdigest()


# =============================================================================
# ⑥ 主流程
# =============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(description="采集页面真实 data-testid 生成 testids.json")
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--route-path", required=True)
    parser.add_argument("--auth-state", default="")
    parser.add_argument("--login-url-path", default="/business/#/login")
    parser.add_argument("--username", default="")
    parser.add_argument("--password", default="")
    parser.add_argument("--sms-code", default="")
    parser.add_argument("--out", default="")
    parser.add_argument("--no-dialog", action="store_true", help="不自动打开新增弹窗采集")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--timeout-ms", type=int, default=20000)
    args = parser.parse_args()

    if not args.out:
        print("[collect_testids] 错误: 缺少 --out 输出路径", file=sys.stderr)
        return 2

    from playwright.sync_api import sync_playwright

    page = None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=args.headless)
            context = browser.new_context(
                storage_state=args.auth_state if args.auth_state else None,
                viewport={"width": 1920, "height": 1080})
            page = context.new_page()
            login(page, args.base_url, args.login_url_path,
                  args.username, args.password, args.sms_code, args.auth_state)
            page.goto(args.base_url + args.route_path)
            page.wait_for_load_state("networkidle")

            main_elements = dump_testids(page, "main")

            add_dialog = {"opened": False, "title": ""}
            if not args.no_dialog:
                add_sel = find_add_button(page, main_elements)
                if add_sel and page.locator(add_sel).count() > 0:
                    page.locator(add_sel).first.click()
                    page.wait_for_timeout(600)
                    opened, title = open_add_dialog(page, args.timeout_ms)
                    add_dialog = {"opened": opened, "title": title}
                    if opened:
                        main_elements += dump_testids(page, "add_dialog")

            index = build_index(main_elements)
            payload = {
                "schema_version": 1,
                "cache_key": cache_key(args.base_url, args.route_path),
                "base_url": args.base_url,
                "route_path": args.route_path,
                "collected_at": datetime.now().isoformat(),
                "collector": "collect_testids.py",
                "page_title": page.title(),
                "add_dialog": add_dialog,
                "elements": main_elements,
                "index": index,
                "summary": {
                    "main_count": sum(1 for e in main_elements if e["scope"] == "main"),
                    "dialog_count": sum(1 for e in main_elements if e["scope"] == "add_dialog"),
                    "degraded": False,
                },
            }
            browser.close()

        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        s = payload["summary"]
        print(f"[collect_testids] OK {args.route_path} "
              f"-> main={s['main_count']} dialog={s['dialog_count']} "
              f"dialog_opened={add_dialog['opened']}")
        return 0

    except SystemExit:
        raise
    except KeyboardInterrupt:
        return 1
    except Exception as e:
        print(f"[collect_testids] 失败: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())