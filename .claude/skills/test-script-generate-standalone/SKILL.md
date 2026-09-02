---
name: test-script-generate-standalone
description: 测试脚本生成（自包含版）- 根据用户上传的测试用例 Markdown（含步骤/预期结果表格）为每个用例生成一个可独立运行的 Playwright 测试脚本，仅依赖 playwright 库，不依赖任何测试框架/基类
triggers:
  - "生成测试脚本"
  - "生成脚本"
  - "根据测试用例生成"
  - "生成自包含脚本"
  - "test-script-generate-standalone"
---

# 测试脚本生成（自包含版）

根据用户上传的**测试用例 Markdown 表格**（含 用例编号/route_path/用例名称/步骤/预期结果 等列），
为**每个用例**生成一个**自包含、可独立运行**的 Playwright 测试脚本（`.py`）。

生成的脚本**仅依赖 `playwright`**，自带浏览器启动、登录、断言、结果记录、失败截图逻辑，
**不依赖** `e2e_runner`、pytest、任何基类或页面对象框架，可整体复制到任意带 playwright 的环境运行。

## 与旧版 test-script-generate 的区别

| 维度 | 旧版（test-script-generate） | 本技能（自包含版） |
|------|------------------------------|--------------------|
| 运行方式 | 依赖 e2e_runner 框架 + pytest | 脚本自身 `python 文件.py` 直接运行 |
| 依赖 | ValidationMixin/BasePage/common 等 | 仅 playwright |
| 登录 | 复用 e2e_runner conftest fixture | 脚本内置 `login()` |
| 结果 | allure JSON | 脚本打印 `TEST_RESULT_JSON:` 协议行 + JSONL |
| 定位器 | record_operating_steps.py 优先 | 步骤为自然语言，定位器生成 TODO 占位，需人工补 |

## 输入

1. **测试用例文件**（必填）：用户上传的 Markdown，典型格式 `/mnt/c/Users/Violet/Desktop/测试用例.md`，
  含 `## 测试用例` 标题 + markdown 表格，表头形如：
  `用例编号 | route_path | 所属产品 | 所属模块 | 用例名称 | 优先级 | 关联测试点 | 前置条件 | 测试数据 | 步骤 | 预期结果`
  （步骤/预期结果单元格内用 `<br>` 分隔多条）
2. **关联需求名 / 模块名**（可选）：用于命名输出目录；缺省用 `auto`
3. **（可选）testid 命名约定**：默认不要求用户提供源码或 data-testid 清单。
   生成器**默认对所有交互节点生成"优先 data-testid"的定位代码**，testid 按下方"testid 推断命名规则"从业务词自动推断，
   每个定位都同时附一个**语义回退定位器**（如 placeholder/button 文本），运行时可拿到已埋 testid 的稳定定位、缺失时自动回退。
   - 若用户能告知实际使用的 testid 命名习惯（或提供少量示例），生成器将按该风格前缀推断，命中率更高

## 输出目录

```
e2eProject/generated_scripts/{关联需求名}_{YYYY-MM-DD}/
  ├── TC-XXX-001.py        # 每个用例一个自包含脚本
  ├── TC-XXX-002.py
  └── README.md            # 使用说明（如何填配置、如何运行）
```

运行 Skill 2（`test-script-run-collect`）时阅读的也正是这个 `generated_scripts/` 目录。

## 处理流程

### 第一步：定位并读取测试用例文件
- 优先使用用户明确提供的用例文件路径
- 否则询问用户给出用例 `.md` 路径

### 第二步：主会话直接执行，不拆子会话
本技能逻辑线性、体量小，**在主会话中直接完成**，无需 Agent 子会话。
若用例很多（如 >20 条），可分批生成，每次向用户报告进度。

### 第三步：解析 Markdown 表格
1. 读取用例文件全文
2. 定位表格表头行，确认列顺序（按关键词配对，不硬编码序号）
3. 逐行解析每个用例，提取：
   - `case_id`（用例编号，如 TC-ZHONGDIAN-002）
   - `case_name`（用例名称）
   - `route_path`（页面路由，如 /business/#/report/emphasis）
   - `priority`（优先级）
   - `test_data`（测试数据，可空）
   - `steps`（步骤列表，按 `<br>` 拆分）
   - `expected`（预期结果列表，按 `<br>` 拆分）
4. 忽略空行、分隔行（全 `---`）、非表格内容

### 第四步：确定输出目录
```
generated_scripts/{需求名}_{今天日期}
```
需求名用文件头部 `**关联需求**：XXX` 提取，否则用 module/产品名，再否则 `auto`。

### 第五步：为每个用例生成自包含脚本
使用下方**脚本模板**，将解析出的字段填入，并对步骤/预期做语义转写生成执行骨架。

### 第六步：生成 README.md
输出目录下写 `README.md`，说明：配置文件区位置、如何填 BASE_URL/账号、如何用 Skill 2 运行。

### 第七步：校验与汇报
1. 对生成的每个 `.py` 做 `python -m py_compile` 语法检查，失败则修复
2. 向用户汇报：生成脚本数、输出目录、每个脚本内需人工补充的 TODO 定位器数量

## 脚本模板（fill_template_string）

```python
"""用例: {case_id} {case_name}"""
import traceback
from playwright.sync_api import sync_playwright

# =============================================================================
# ① 配置区 CONFIG —— 运行前在此填入目标系统信息与登录凭据（TODO 须补齐）
# =============================================================================
BASE_URL = ""                 # TODO: 目标系统基础地址，如 https://example.com
LOGIN_URL_PATH = ""           # TODO: 登录页路由，如 /business/#/login（AUTH_STATE 为空时走 login()）
USERNAME = ""                 # TODO: 登录账号
PASSWORD = ""                 # TODO: 登录密码
SMS_CODE = ""                 # TODO: 短信验证码（已登录可留空）
AUTH_STATE = ""               # 复用已登录会话的 storage_state json（cookies/localStorage）。非空→跳过登录直接复用该会话；为空→走下方 login()
ROUTE_PATH = "{route_path}"   # 本用例页面路由（由用例表格 route_path 列自动填入）
HEADLESS = False              # True=无头运行，False=可视化

CASE_ID = "{case_id}"
CASE_NAME = "{case_name}"
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


def login(page) -> None:
    """已配置 AUTH_STATE 时复用该会话（跳过填账号登录）；否则走账号密码登录。
    真实系统常无法重登（验证码/SSO），优先用 AUTH_STATE 复用已登录会话。"""
    if AUTH_STATE:
        page.wait_for_load_state("networkidle")
        return
    page.goto(BASE_URL + LOGIN_URL_PATH)
    page.wait_for_load_state("networkidle")
    page.fill("input[placeholder*='账号']", USERNAME)
    page.fill("input[placeholder*='密码']", PASSWORD)
    page.fill("input[placeholder*='验证码']", SMS_CODE)
    page.click("button:has-text('登录')")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)


def tid(page, testid: str, fallback: str = ""):
    """定位器工厂：返回值**优先匹配 data-testid**，未命中回退到 fallback 语义定位器，
    两者皆无才报错。testid 为生成器推断建议值，实际不符时改 fallback 或 base_testids 即可，
    无需改任何步骤代码。"""
    if testid and page.locator(f"[data-testid='{testid}']").count() > 0:
        return page.get_by_test_id(testid)
    if fallback:
        return page.locator(fallback)
    raise AssertionError(f"未找到元素: testid={testid!r}, fallback={fallback!r}")


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


def check(page, desc: str, locator, expect: str = "") -> None:
    """通用断言：元素可见，并可选校验其文本包含期望值。locator 支持 string / 定位器 / **未调用的 lambda**（如 pg.title）。"""
    if callable(locator):            # 兼容传 lambda（如 pg.title）而非已求值定位器
        locator = locator()
    el = page.locator(locator) if isinstance(locator, str) else locator
    el.wait_for(timeout=10000)
    if expect:
        page.wait_for_timeout(500)
        assert expect in el.inner_text(), f"[{desc}] 实际文本不包含期望值: {expect}"
    print(f"  [OK] {desc}")


def expect_toast(page, text: str, timeout: int = 4000, retries: int = 1) -> None:
    """稳定等待 toast 短文提示（el-message 等）。toast 短暂、批量执行偶发超时，故做**短重试**。
    调用方在触发动作（点保存/发布）后可先 page.wait_for_timeout(300) 再调用本函数。"""
    import time
    last = None
    for _ in range(retries + 1):
        try:
            page.locator(f"text={text}").first.wait_for(timeout=timeout)
            print(f"  [OK] 提示: {text}")
            return
        except Exception as e:
            last = e
            page.wait_for_timeout(500)
    raise last  # 重试仍失败 → 抛原始错误，走失败截图/上报


# =============================================================================
# ③ 页面层 PAGE OBJECT —— 按业务页面封装定位器与业务动作（增删改查等）
#    一个用例通常对应一个页面类；页面方法供用例层 run_case 调用。
# =============================================================================
class {PageName}Page:
    """{模块名 / 页面名} 页面对象。"""

    def __init__(self, page) -> None:
        self.page = page
        # ---- 定位器集中定义（优先 data-testid，缺失回退语义定位器）----
        # 例: self.save_btn  = lambda: tid(page, "{prefix}-save",  "button:has-text('保存')")
        #     self.title     = lambda: tid(page, "{prefix}-title", "input[placeholder*='公告标题']")
        #     self.add_btn   = lambda: tid(page, "{prefix}-add",   "button:has-text('新增')")
        # 富文本（内容/正文/富文本/长文本）用 rich_text()：data-testid 标在外层容器，可编辑区在内部 contenteditable。
        # 例: self.content   = lambda: rich_text(page, "{prefix}-content", "textarea[placeholder*='内容']")
        ## placeholder:PAGE_OBJECT_ATTRS

    def open(self) -> None:
        """进入本用例页面。"""
        self.page.goto(BASE_URL + ROUTE_PATH)
        self.page.wait_for_load_state("networkidle")

    # ---- 业务动作（每个命名动作一个方法，对应一条增/删/改/查/其他操作）----
    ## placeholder:PAGE_OBJECT_METHODS


# =============================================================================
# ④ 用例层 TEST CASE —— 编排页面动作 + 断言预期，对应一条测试用例的"步骤/预期结果"
# =============================================================================
def run_case(page) -> None:
    """用例 {case_id} {case_name}：由'步骤'列转写，'页面动作'调用③，'断言'交给 check()。"""
    pg = {PageName}Page(page)
    pg.open()
    # ---- 步骤转写（按'步骤'列逐条）----
    # 例: pg.add_btn().click()                                      # 点击新增
    #     pg.title().fill("测试公告")                                # 填写公告标题
    #     pg.save_btn().click()                                     # 点击保存
    #     check(page, "公告标题回显", pg.title(), expect="测试公告")   # 断言:标题回显
    ## placeholder:CASE_STEPS


# =============================================================================
# ⑤ 驱动层 DRIVER —— 启动浏览器 → 登录 → 进入页面 → 执行用例 → 上报结果/失败截图
#    该层让整个脚本可 `python 文件.py` 独立运行（供 run-collect 批量执行）。
# =============================================================================
def main() -> None:
    page = None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=HEADLESS)
            # AUTH_STATE 非空→复用已登录会话(storage_state)；为空→全新上下文走 login() 填账号
            context = browser.new_context(
                storage_state=AUTH_STATE if AUTH_STATE else None,
                viewport={"width": 1920, "height": 1080})
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
```

### 模板中的步骤转写规则（填入两处 placeholder）

生成器把每条用例转写为 **①②③④⑤ 五层结构**（见上方模板）。步骤转写落在两处：

1. **③ 页面层 `## placeholder:PAGE_OBJECT_METHODS`**：把"增删改查"等**业务动作**生成为页面对象的一个方法，
   内含该动作涉及的元素定位（用 `tid()` 生成，优先 `data-testid`）。
2. **④ 用例层 `## placeholder:CASE_STEPS`**：按"步骤"列**逐条调用**这些页面方法 + 用 `check()` 断言"预期结果"。

#### 业务动作 → 页面层方法（③）
- 一条"新增/编辑/删除/查询/导入/导出…"动作 → 一个命名方法：`def create(...)` / `def edit(...)` / `def delete(...)` / `def query(...)` / `def open()`
- 动作内的每个交互节点统一用 `tid()` 生成定位器：
  ```
  self.<name> = lambda: tid(page, "<推断testid>", "<语义fallback>")
  ```
- `tid()` 运行逻辑：**优先**匹配 `[data-testid='<推断testid>']`（页面已埋定时最稳定）；未命中自动回退 `<语义fallback>`；两者皆无才报错。

#### 步骤 → 用例层调用（④）
- 对"步骤"列每条生成一行调用：`pg.<动作>.()`
  - 点击 → `.click()`
  - 填写（普通 input/textarea）→ `.fill("…")`
  - 填写（富文本 内容/正文/长文本）→ 页面方法内用 `click()` + `page.keyboard.type("…", delay=30)`（富文本 `.fill()` 会报 "Element is not an input/textarea/contenteditable"）
  - 勾选/选择 → `.click()`
- "预期结果"列 → 合并为 `check(page, "…", pg.<定位>(), expect="X")` 断言（同样优先 testid）；toast/提交提示断言用稳定版 `expect_toast(page, "提示文案")`

#### testid 推断命名规则（无源码时按业务词推断，前缀默认取页面/模块名）
- 前缀：取用例所属模块/页面业务名转小写 kebab。如"公告通知"→ `notice`，"用户管理"→ `user`。
- 按钮动作 → 后缀：保存`-save`、发布`-release`、取消`-cancel`、确定`-confirm`、新增`-add`、编辑`-edit`、删除`-delete`、查询`-query`、重置`-reset`、导入`-import`、导出`-export`、上一步/下一步`-prev/-next`。
- 输入框/字段 → 字段名 kebab：标题`-title`、内容`-content`、来源`-source`、名称`-name`、类型`-type`、时间`-time`、日期`-date`、状态`-status`。
- 规则：`{前缀}-{语义词}`，如保存公告 → `notice-save`，公告标题 → `notice-title`。
- 若用户提供实际 testid 命名习惯，按用户前缀与风格覆盖默认推断。

#### 语义定位 fallback 推断（作为 `tid` 第二参）
- 含 **打开/进入/跳转 …页面/报表/详情** → 不在定位内，由页面对象 `open()` 统一 `goto(BASE_URL + ROUTE_PATH)`（用用例 route_path），保留为已生效代码
- 含 **点击 …按钮/链接** → `button:has-text('…')`（如 `button:has-text('保存')`）
- 含 **填写/输入/录入 …** → `input[placeholder*='…']`（如 `input[placeholder*='公告标题']`）
- 含 **填写/输入…内容/正文/富文本/长文本**（字段名为内容类）→ 用 `rich_text(page, "{prefix}-{字段}", "textarea[placeholder*='…']")` 定位 + 页面方法内 `click()` 后 `keyboard.type("…")`（见上方③④规则）
- 含 **选择/勾选/展开 …** → 通用为 `text=…` 或按意图取 select/checkbox 定位符（无法精确时用 `page.locator("text=…")`）
- 含 **核对/检查/观察 …是否为/显示为 X** → `check(page, "…", pg.<定位>(), expect="X")`
- 无法明确映射的业务步骤 → 在用例层生成 `# stepN {原文}` 注释行，交给执行人员按界面补充

#### 脚本顶/页面层 base_testids 常量（可选的统一调整点）
生成脚本可在页面类的定位定义处补一个 `base_testids = {"保存": "notice-save", "公告标题": "notice-title", ...}` 映射，
作为 testid 推断结果的集中登记表，运行者发现实际 testid 不同时集中修改，步骤代码无需变动。（非强制；未生成也不影响 `tid()` 运行。）

### 脚本文件结构总览（README.md 中向用户说明）
每个生成的 `.py` 均由 5 个分层区块组成，便于阅读与维护：
1. **配置区**：BASE_URL/账号/密码/验证码/route_path/AUTH_STATE，运行前在此填真实信息。
   - **两种运行方式**：填入 `AUTH_STATE`（复用已登录会话 json）则跳过登录直接跑；留空则填 BASE_URL+账号走 `login()`。
   - 真实系统常无法重登（验证码/SSO），优先用 AUTH_STATE 复用已登录会话（cookies/localStorage 导出为 `auth_state.json`）。
2. **辅助层**：`record_result` / `tid` / `check`，通用工具，通常不动。
3. **页面层（Page Object）**：封装定位器与增删改查动作，对应被测业务页面。
4. **用例层**：`run_case()` 编排页面动作 + 断言，对应测试用例的"步骤/预期结果"。
5. **驱动层**：`main()` 启动浏览器 → 登录 → 执行用例 → 上报结果/失败截图，使脚本可 `python 文件.py` 独立运行。

## ⚠️ 诚实边界声明（务必告知用户）
- 生成脚本**不需要用户提供源码或 data-testid 清单**。生成器按业务词**推断**出 testid，并统一用 `tid()` **优先匹配 `data-testid`**，再回退语义定位器。
- **testid 是推断建议值**，若实际页面的 data-testid 命名不一致，运行时 `tid()` 会自动回退到语义定位器（placeholder/按钮文本），步骤仍能执行；
  若想拿到稳定的 testid 定位，改 `base_testids` 或 `tid()` 的 fallback 即可，无需改步骤代码。
- **富文本字段特殊**：data-testid 常标在外层容器，已用 `rich_text()` 定位内部 `[contenteditable=true]`，勿用 `.fill()`。
- **登录态二选一**：`AUTH_STATE` 复用已登录会话（真实系统常无法重登验证码/SSO，推荐）/ 填 BASE_URL+账号走 `login()`；结果协议、失败截图、toast 断言（稳定版）均可直接运行。

## 校验清单
- [ ] 每个 `.py` 通过 `python -m py_compile`
- [ ] 配置区占位符齐全（BASE_URL/LOGIN_URL_PATH/USERNAME/PASSWORD/SMS_CODE/**AUTH_STATE**）且带 TODO 注释
- [ ] 脚本为 ①②③④⑤ 五层结构（配置/辅助/页面PO/用例/驱动），`main()` 驱动 `run_case()`，页面动作归页面类方法
- [ ] record_result 打印 `TEST_RESULT_JSON:` 协议行
- [ ] 登录函数支持 AUTH_STATE 复用（非空则跳过填账号登录）、失败截图兜底齐全
- [ ] 脚本含 `tid()` 辅助，页面层所有定位节点用 `tid(page, "<testid>", "<fallback>")` 生成（优先 data-testid、缺失回退）；富文本字段（内容/正文）用 `rich_text()` + `click()/keyboard.type()` 输入
- [ ] `check()` 兼容未调用 lambda（含 `if callable(locator)`）；toast/提交提示断言用稳定版 `expect_toast()`（短重试）
- [ ] 无 `# TODO 定位器` 残留（已由语义 fallback 取代）
- [ ] `if __name__ == "__main__": main()` 存在，保证脚本可 `python 文件.py` 独立运行（供 test-script-run-collect 批量执行）
- [ ] README.md 已生成并说明配置（含 AUTH_STATE 两种运行方式）与后续运行方式