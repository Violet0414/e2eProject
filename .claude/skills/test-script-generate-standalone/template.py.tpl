"""用例: @@CASE_ID@@ @@CASE_NAME@@"""
import os
import traceback
from playwright.sync_api import sync_playwright

# =============================================================================
# ① 配置区 CONFIG —— 运行前在此填入目标系统信息与登录凭据（TODO 须补齐）
# =============================================================================
BASE_URL = "http://192.168.200.67:8080"   # 目标系统基础地址（可按运行环境修改），脚本内以 BASE_URL + ROUTE_PATH 拼接
LOGIN_URL_PATH = ""           # TODO: 登录页路由，如 /business/#/login（AUTH_STATE 为空时走 login()）
USERNAME = ""                 # TODO: 登录账号
PASSWORD = ""                 # TODO: 登录密码
SMS_CODE = ""                 # TODO: 短信验证码（已登录可留空）
AUTH_STATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".auth", "auth_state.json")  # 登录态文件路径，默认取脚本同目录下 .auth/auth_state.json（使用基于脚本位置的绝对路径，避免运行目录不同导致 FileNotFound）。为空字符串→走下方 login()。支持扩展字段 sessionStorage（Playwright 原生 storage_state 不包含，由 login() 手动恢复）
ROUTE_PATH = "@@ROUTE_PATH@@"   # 本用例页面路由（由用例表格 route_path 列自动填入）
HEADLESS = False              # True=无头运行，False=可视化

CASE_ID = "@@CASE_ID@@"
CASE_NAME = "@@CASE_NAME@@"
RESULT_FILE = __import__("os").environ.get("E2E_RESULT_FILE", "results.json")


# =============================================================================
# ② 辅助层 HELPER —— 与具体业务解耦的通用工具，通常无需改动
#    包含：结果上报 record_result / testid 定位 tid / 通用断言 check
# =============================================================================
def record_result(status: str, error: str = "", screenshot: str = "") -> None:
    """按统一协议记录结果：打印协议行 + 追加 JSONL。供 test-script-run-collect 聚合。"""
    import json, datetime
    entry = {
        "id": CASE_ID, "name": CASE_NAME, "status": status,
        "error": error, "screenshot": screenshot,
        "timestamp": datetime.datetime.now().isoformat(),
    }
    print(f"TEST_RESULT_JSON: {json.dumps(entry, ensure_ascii=False)}")
    with open(RESULT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def quick_load(page, url: str) -> None:
    """导航后快速等待：优先 domcontentloaded（马上往下执行），networkidle 仅做限时兜底。
    避免 SPA 长轮询/懒加载页面在 networkidle 上无限等待拖慢执行。"""
    page.goto(url, wait_until="domcontentloaded")
    try:
        page.wait_for_load_state("networkidle", timeout=3000)
    except Exception:
        page.wait_for_timeout(600)


def login(page) -> None:
    """已配置 AUTH_STATE 时复用该会话（跳过填账号登录）；否则走账号密码登录。
    真实系统常无法重登（验证码/SSO），优先用 AUTH_STATE 复用已登录会话。
    支持扩展字段 sessionStorage：Playwright 原生 storage_state 不包含 sessionStorage，
    若 auth_state.json 带 sessionStorage 字段则手动注入恢复。"""
    import os as _os, json as _json
    if AUTH_STATE and _os.path.exists(AUTH_STATE):
        with open(AUTH_STATE, "r", encoding="utf-8") as _f:
            _auth_data = _json.load(_f)
        # 恢复 sessionStorage（Playwright storage_state 不包含）
        if "sessionStorage" in _auth_data and _auth_data["sessionStorage"]:
            page.goto(BASE_URL, wait_until="domcontentloaded")
            page.evaluate("""data => {
                for (const [k, v] of Object.entries(data)) {
                    sessionStorage.setItem(k, v);
                }
            }""", _auth_data["sessionStorage"])
        page.wait_for_timeout(300)
        return
    quick_load(page, BASE_URL + LOGIN_URL_PATH)
    page.fill("input[placeholder*='账号']", USERNAME)
    page.fill("input[placeholder*='密码']", PASSWORD)
    page.fill("input[placeholder*='验证码']", SMS_CODE)
    page.click("button:has-text('登录')")
    page.wait_for_timeout(800)


def tid(page, testid: str, fallback: str = ""):
    """定位器工厂：返回值**优先匹配 data-testid**，未命中回退到 fallback 语义定位器，
    两者皆无才报错。testid 优先为 testids.json 采集到的真实 data-testid；未采集到
    （如编辑/详情弹窗字段）则为推断建议值。不符时改 fallback 或 base_testids 即可，无需改步骤代码。"""
    if testid and page.locator(f"[data-testid='{testid}']").count() > 0:
        return page.get_by_test_id(testid)
    if fallback:
        return page.locator(fallback)
    raise AssertionError(f"未找到元素: testid={testid!r}, fallback={fallback!r}")


def date_input(page, testid: str, fallback: str = ""):
    """日期选择器（el-date-picker / el-date-editor 等）定位器：data-testid 常标在**外层容器 div**上，
    真实可输入元素在其内部 `<input>`。直接对容器调用 .fill() 会报 "Element is not an input"。"""
    if testid and page.locator(f"[data-testid='{testid}']").count() > 0:
        el = page.locator(f"[data-testid='{testid}'] input").first
        if el.count() > 0:
            return el
    if fallback:
        return page.locator(fallback)
    raise AssertionError(f"未找到日期选择器输入元素: testid={testid!r}, fallback={fallback!r}")


def rich_text(page, testid: str, fallback: str = ""):
    """富文本编辑控件（wangEditor/Tinymce 等）定位器：data-testid 常标在**外层容器**（如 el-form-item）
    上，真实可编辑元素在其内部 `[contenteditable='true']`。区别于普通 input/textarea。"""
    if testid and page.locator(f"[data-testid='{testid}']").count() > 0:
        el = page.locator(f"[data-testid='{testid}'] [contenteditable='true']").first
        if el.count() > 0:
            return el
    if fallback:
        return page.locator(fallback)
    raise AssertionError(f"未找到富文本可编辑元素: testid={testid!r}, fallback={fallback!r}")


def select_dropdown(page, select_locator, option_text: str, nth: int = 0, timeout: int = 5000) -> None:
    """点击下拉选择器并选择指定选项。**只在当前可见的下拉弹层内查找**，避免页面上多组级联选择器
    （如户籍地址/死亡地点/家属住址的"船山区"）互相干扰导致匹配到 hidden 元素而超时卡死。
    select_locator 支持定位器对象或字符串。"""
    sel = page.locator(select_locator) if isinstance(select_locator, str) else select_locator
    sel.click()
    page.wait_for_timeout(300)
    items = page.locator('.el-select-dropdown:visible .el-select-dropdown__item').filter(has_text=option_text)
    items.nth(nth).wait_for(timeout=timeout)
    items.nth(nth).click()
    page.wait_for_timeout(300)


def check(page, desc: str, locator, expect: str = "", timeout: int = 5000) -> None:
    """通用断言：元素可见，并可选校验其文本包含期望值。locator 支持 string / 定位器 / **未调用的 lambda**（如 pg.title）。
    timeout 默认 5s：正向元素应尽快出现，失败（反向）打满也只 5s 而非 10s，压低批量执行耗时。"""
    if callable(locator):            # 兼容传 lambda（如 pg.title）而非已求值定位器
        locator = locator()
    el = page.locator(locator) if isinstance(locator, str) else locator
    el.wait_for(timeout=timeout)
    if expect:
        page.wait_for_timeout(200)
        assert expect in el.inner_text(), f"[{desc}] 实际文本不包含期望值: {expect}"
    print(f"  [OK] {desc}")


def expect_toast(page, text: str, timeout: int = 3000, retries: int = 1) -> None:
    """稳定等待 toast 短文提示（el-message 等）。toast 短暂、批量执行偶发超时，故做**短重试**。
    调用方在触发动作（点保存/发布）后可先 page.wait_for_timeout(300) 再调用本函数。
    仅用于正向用例（预期出现提示）；反向用例请用 expect_no_toast 负向断言。"""
    import time
    last = None
    for _ in range(retries + 1):
        try:
            page.locator(f"text={text}").first.wait_for(timeout=timeout)
            print(f"  [OK] 提示: {text}")
            return
        except Exception as e:
            last = e
            page.wait_for_timeout(300)
    raise last  # 重试仍失败 → 抛原始错误，走失败截图/上报


def expect_no_toast(page, text: str, timeout: int = 1500) -> None:
    """负向断言：确认指定 toast **不出现**（反向用例专用，短超时快速通过）。
    反向用例提交非法输入后，期望"不弹成功提示"，用短超时确认未出现即可，勿打满正向超时。"""
    try:
        page.locator(f"text={text}").first.wait_for(timeout=timeout)
        raise AssertionError(f"出现不应有的提示: {text}")
    except AssertionError:
        raise
    except Exception:
        print(f"  [OK] 未出现提示: {text}")


# =============================================================================
# ③ 页面层 PAGE OBJECT —— 按业务页面封装定位器与业务动作（增删改查等）
#    一个用例通常对应一个页面类；页面方法供用例层 run_case 调用。
# =============================================================================
class @@PAGE_NAME@@:
    """@@PAGE_DOC@@ 页面对象。"""

    def __init__(self, page) -> None:
        self.page = page
        # ---- 定位器集中定义（testid 取 testids.json 真实采集，缺失回退语义定位器）----
        # 例: self.save_btn  = lambda: tid(page, "{prefix}-save",  "button:has-text('保存')")
        #     self.title     = lambda: tid(page, "{prefix}-title", "input[placeholder*='公告标题']")
        #     self.add_btn   = lambda: tid(page, "{prefix}-add",   "button:has-text('新增')")
        # 富文本（内容/正文/富文本/长文本）用 rich_text()：data-testid 标在外层容器，可编辑区在内部 contenteditable。
        # 例: self.content   = lambda: rich_text(page, "{prefix}-content", "textarea[placeholder*='内容']")
        # 日期选择器（日期/时间/出生年月/死亡时间 等）用 date_input()：data-testid 常标在外层 div，内部才是 input。
        # 例: self.start_date = lambda: date_input(page, "{prefix}-start-date", ".el-form-item:has-text('开始日期') .el-date-editor input")
        ## placeholder:PAGE_OBJECT_ATTRS

    def open(self) -> None:
        """进入本用例页面。"""
        quick_load(self.page, BASE_URL + ROUTE_PATH)

    # ---- 业务动作（每个命名动作一个方法，对应一条增/删/改/查/其他操作）----
    ## placeholder:PAGE_OBJECT_METHODS


# =============================================================================
# ④ 用例层 TEST CASE —— 编排页面动作 + 断言预期，对应一条测试用例的"步骤/预期结果"
# =============================================================================
def run_case(page) -> None:
    """用例 @@CASE_ID@@ @@CASE_NAME@@：由'步骤'列转写，'页面动作'调用③，'断言'交给 check()。"""
    pg = @@PAGE_NAME@@(page)
    pg.open()
    # ---- 步骤转写（按'步骤'列逐条）----
    # 例: pg.add_btn().click()                                      # 点击新增
    #     pg.title().fill("测试公告")                                # 填写公告标题
    #     pg.save_btn().click()                                     # 点击保存
    #     check(page, "标题回显", pg.heading(), expect="测试公告")     # 断言:标题回显（input 类字段回显断言用 input_value）
    ## placeholder:CASE_STEPS


# =============================================================================
# ⑤ 驱动层 DRIVER —— 启动浏览器 → 登录 → 进入页面 → 执行用例 → 上报结果/失败截图
#    该层让整个脚本可 `python 文件.py` 独立运行（供 run-collect 批量执行）。
# =============================================================================
def main() -> None:
    page = None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=HEADLESS, args=["--disable-gpu"])
            # AUTH_STATE 非空→复用已登录会话(storage_state)；为空→全新上下文走 login() 填账号
            context = browser.new_context(
                storage_state=AUTH_STATE if AUTH_STATE else None)
            page = context.new_page()
            login(page)
            run_case(page)
            browser.close()
        record_result("passed")
    except Exception:
        screenshot = ""
        if page is not None:
            try:
                page.screenshot(path=f"screenshots/{CASE_ID}_failed.png", full_page=True)
                screenshot = f"screenshots/{CASE_ID}_failed.png"
            except Exception:
                pass
        record_result("failed", error=traceback.format_exc(), screenshot=screenshot)


if __name__ == "__main__":
    main()
