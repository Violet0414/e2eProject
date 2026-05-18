# ms-service-playwright 自动化测试脚本模板

> 本模板定义了该框架下可执行测试脚本的规范结构和编写模式，供测试用例生成技能参考。

---

## 一、项目目录约定

```
ms-service-playwright/
├── pages/              # 页面对象（Page Object），每个模块一个文件
│   ├── base_page.py        # 基类 BasePage，所有页面对象必须继承
│   └── xxx_page.py         # 业务页面对象
├── datas/              # 测试数据，每个模块一个文件
│   └── xxx_data.py         # Python 字典列表，不可用 YAML/JSON
├── tests/              # 测试用例脚本，按端/模块分目录
│   ├── admin/              # 平台管理端
│   ├── company/            # 企业端
│   └── citizen/            # 市民端
├── common/             # 公共工具
│   ├── assert_utils.py     # AssertUtils 统一断言
│   ├── helpers.py          # generate_test_data 等辅助函数
│   └── ...
├── conftest.py         # 全局 fixture 和钩子
└── config/settings.py  # 多环境配置（pydantic-settings）
```

---

## 二、生成文件清单

每生成一个模块的测试脚本，需要产出 **3 个文件**：

| 序号 | 文件 | 路径 | 说明 |
|------|------|------|------|
| 1 | 页面对象 | `pages/{module_name}.py` | 继承 BasePage，封装元素定位和操作方法 |
| 2 | 测试数据 | `datas/{module_name}_data.py` | Python 字典列表，参数化驱动 |
| 3 | 测试用例 | `tests/{端目录}/test_{module_name}.py` | pytest + allure，参数化执行 |

---

## 三、文件模板

### 3.1 页面对象模板 `pages/{module_name}.py`

```python
"""{模块中文名}页面元素和操作"""
from pages.base_page import BasePage
import time


class {PageClassName}(BasePage):
    """{模块中文名}页面元素和操作"""

    # ==================== 菜单选择器 ====================
    PARENT_MENU = "text='{父级菜单名}'"
    SUB_MENU = "text='{子级菜单名}'"

    # ==================== 按钮选择器 ====================
    ADD_BUTTON = ".el-button--primary:first-child"
    SEARCH_BUTTON = "text='查询'"
    RESET_BUTTON = "text='重置'"
    DIALOG_CONFIRM_BUTTON = ".el-dialog__footer .el-button--primary"
    DELETE_CONFIRM_BUTTON = ".el-message-box__btns .el-button--primary"

    # ==================== 表单选择器 ====================
    SEARCH_INPUT = ".el-input__inner:first-child"
    DIALOG_INPUTS = ".el-dialog input:not([readonly])"
    DIALOG_REMARK = ".el-dialog textarea:first-child"

    # ==================== 列表选择器 ====================
    TABLE_ROWS = ".el-table__body tr"
    ROW_EDIT_BTN = ".el-table__body tr:first-child .el-button:nth-last-child(2)"
    ROW_DELETE_BTN = ".el-table__body tr:first-child .el-button:last-child"

    def goto_module(self):
        """进入{模块中文名}模块"""
        self.page.wait_for_selector(self.PARENT_MENU, timeout=10000)
        self.click(self.PARENT_MENU, force=True)
        self.page.wait_for_selector(self.SUB_MENU, timeout=10000)
        self.click(self.SUB_MENU, force=True)
        self.wait_for_table_loaded(timeout=10000)
        return self

    def search(self, keyword: str = "") -> int:
        """
        搜索{实体名}，返回结果数量
        :param keyword: 搜索关键词
        :return: 搜索结果条数
        """
        self.page.evaluate("window.scrollTo(0, 0)")
        self.page.locator("text='重置'").click(force=True)
        time.sleep(1)
        if keyword:
            search_input = self.page.locator(".el-input__inner:visible").first
            search_input.fill(keyword)
            search_input.press("Enter")
            self.wait_for_load_state("networkidle")
        return self.page.locator(self.TABLE_ROWS).count()

    def add_{entity}(self, {param_list}):
        """
        新增{实体名}
        :param {param_docs}
        """
        self.page.evaluate("window.scrollTo(0, 0)")
        # 清理可能存在的弹窗
        for _ in range(3):
            self.page.keyboard.press("Escape")
            time.sleep(0.2)
        # 点击新增按钮
        add_button = self.page.locator(".el-icon-plus").locator("..")
        add_button.click(force=True)
        # 等待新增对话框
        self.page.locator(".el-dialog[aria-label*='{对话框标题}']").wait_for(state="visible", timeout=20000)
        # 填写表单
        # TODO: 根据实际表单字段填写
        dialog_inputs = self.page.locator(".el-dialog input")
        dialog_inputs.nth(0).fill({first_field})
        # 点击确定
        self.page.locator(".el-dialog__footer .el-button--primary").last.click()
        self.wait_for_load_state("networkidle")
        return self

    def edit_first(self, new_value: str) -> bool:
        """
        编辑第一条搜索结果
        :param new_value: 新值
        :return: 编辑是否成功
        """
        self.page.evaluate("window.scrollTo(0, 0)")
        time.sleep(2)
        try:
            first_row = self.page.locator(self.TABLE_ROWS).first
            first_row.wait_for(state="visible", timeout=10000)
            action_buttons = first_row.locator(".el-button").all()
            edit_button = action_buttons[-2]
            edit_button.click(force=True)
            time.sleep(1)
            # 等待编辑对话框
            self.page.locator(".el-dialog[aria-label*='修改']").wait_for(state="visible", timeout=5000)
            # TODO: 填写编辑内容
            self.page.locator(self.DIALOG_REMARK).fill(new_value)
            self.page.get_by_role("button", name="确 定").click(force=True)
            self.wait_for_load_state("networkidle")
            time.sleep(2)
            dialog_visible = self.page.locator(".el-dialog[aria-label*='修改']").is_visible()
            return not dialog_visible
        except Exception as e:
            print(f"编辑失败: {e}")
            return False

    def delete_first(self) -> bool:
        """
        删除第一条搜索结果
        :return: 删除是否成功
        """
        self.page.evaluate("window.scrollTo(0, 0)")
        try:
            first_row = self.page.locator(self.TABLE_ROWS).first
            first_row.wait_for(state="visible", timeout=10000)
            first_row.scroll_into_view_if_needed()
            action_buttons = first_row.locator(".el-button").all()
            action_buttons[-1].click(force=True)
            self.page.locator(".el-message-box__btns .el-button--primary").click(force=True)
            self.wait_for_load_state("networkidle")
            return True
        except Exception as e:
            print(f"删除失败: {e}")
            return False
```

---

### 3.2 测试数据模板 `datas/{module_name}_data.py`

```python
# ------------------------------ {模块中文名}测试数据 ------------------------------
import random

# ==================== 新增{实体名}测试数据 ====================
{ENTITY}_ADD_TEST_DATA = [
    # ---------- 正向场景 ----------
    {{"name": "正向_常规名称", "sort": "480", "remark": "常规测试", "expect_success": True, "title": "常规合法参数", "type": "positive"}},
    {{"name": "正向_名称1字符", "sort": "48", "remark": "", "expect_success": True, "title": "名称最短1字符", "type": "positive"}},
    {{"name": "正向_名称30字符" + "x" * 20, "sort": "49", "remark": "最大长度名称", "expect_success": True, "title": "名称最大长度边界", "type": "positive"}},

    # ---------- 反向场景 ----------
    {{"name": "", "sort": "10", "remark": "", "expect_success": False, "title": "名称为空", "type": "negative"}},
    {{"name": "反向_超长名称" + "x" * 10000, "sort": "10", "remark": "", "expect_success": False, "title": "名称超过最大长度", "type": "negative"}},
]

# ==================== 搜索{实体名}测试数据 ====================
{ENTITY}_SEARCH_TEST_DATA = [
    {{"keyword": "存在关键词", "expect_count": ">0", "title": "搜索存在的{实体名}", "type": "positive"}},
    {{"keyword": "不存在的关键词_123456", "expect_count": "==0", "title": "搜索不存在的{实体名}", "type": "positive"}},
    {{"keyword": "", "expect_count": ">0", "title": "空关键词搜索返回所有", "type": "positive"}},
    {{"keyword": "模糊关键词", "expect_count": ">=1", "title": "模糊搜索匹配多个结果", "type": "positive"}},
]

# ==================== 编辑{实体名}测试数据 ====================
{ENTITY}_EDIT_TEST_DATA = [
    # ---------- 正向场景 ----------
    {{"field": "name", "new_value": "编辑后_新名称" + str(random.randint(1000, 9999)), "expect_success": True, "title": "修改名称", "type": "positive"}},
    {{"field": "remark", "new_value": "编辑后_新备注" + str(random.randint(1000, 9999)), "expect_success": True, "title": "修改备注", "type": "positive"}},

    # ---------- 反向场景 ----------
    {{"field": "name", "new_value": "", "expect_success": False, "title": "修改名称为空", "type": "negative"}},
]
```

#### 测试数据字典必填字段说明

| 字段 | 类型 | 说明 | 可选值 |
|------|------|------|--------|
| `title` | str | 用例中文标题，用于 Allure 报告展示 | 自定义 |
| `type` | str | 用例类型，**必须填写**，conftest 钩子依此过滤 | `positive` / `negative` / `smoke` |
| `expect_success` | bool | 操作类用例的预期结果（新增/编辑/删除） | `True` / `False` |
| `expect_count` | str | 搜索类用例的预期数量 | `">0"` / `"==0"` / `">=1"` / `">=0"` / 整数 |
| 业务字段 | str/dict | 测试输入数据（name, sort, remark 等） | 自定义 |

---

### 3.3 测试用例模板 `tests/{端目录}/test_{module_name}.py`

```python
"""{模块中文名}测试用例"""
import allure
import pytest
import time
from common.helpers import generate_test_data
from common.assert_utils import AssertUtils
from pages.{module_name} import {PageClassName}
from datas.{module_name}_data import (
    {ENTITY}_ADD_TEST_DATA,
    {ENTITY}_SEARCH_TEST_DATA,
    {ENTITY}_EDIT_TEST_DATA
)

pytestmark = pytest.mark.{module_mark}  # 模块标记，方便 pytest -m 单独运行


@allure.feature("{模块中文名}-参数化场景")
class Test{PageClassName}ParamScenarios:
    """{模块中文名}参数化测试套件，覆盖正向/反向场景"""
    {entity_lower}_page: "{PageClassName}"

    @pytest.fixture(scope="class", autouse=True)
    def setup_class(self, {page_fixture}):
        """类前置：进入{模块中文名}模块"""
        self.__class__.{entity_lower}_page = {PageClassName}({page_fixture})
        self.__class__.{entity_lower}_page.goto_module()
        yield
        # 类后置：清理测试数据
        try:
            test_data_prefix = "auto_"
            count = self.{entity_lower}_page.search(test_data_prefix)
            while count > 0:
                self.{entity_lower}_page.delete_first()
                count = self.{entity_lower}_page.search(test_data_prefix)
        except Exception:
            pass

    # ------------------------------ 新增{实体名}参数化场景 ------------------------------
    @pytest.mark.parametrize("test_case", {ENTITY}_ADD_TEST_DATA)
    @allure.story("{实体中文名}新增-参数化场景")
    def test_add_{entity}(self, test_case):
        """参数化测试新增{实体中文名}的各种场景"""
        time.sleep(2)
        allure.dynamic.title(test_case["title"])
        # 生成唯一名称避免重复
        unique_suffix = f"_{int(time.time())}"
        name = test_case["name"] + unique_suffix if test_case["name"] else test_case["name"]

        # 执行新增
        self.{entity_lower}_page.add_{entity}(
            name=name,
            sort=test_case["sort"],
            remark=test_case["remark"]
        )

        if test_case["expect_success"]:
            # 预期成功：验证能搜索到
            time.sleep(1)
            count = self.{entity_lower}_page.search(name)
            temp_test_case = test_case.copy()
            temp_test_case["expect_count"] = ">=1"
            AssertUtils.assert_search_result(count, temp_test_case, f"搜索新增的{实体中文名}：{{name}}")
        else:
            # 预期失败：验证对话框仍在或搜索不到
            time.sleep(1)
            dialog_visible = self.{entity_lower}_page.page.locator(".el-dialog[aria-label*='添加']").is_visible()
            if dialog_visible:
                self.{entity_lower}_page.page.keyboard.press("Escape")
                self.{entity_lower}_page.page.locator(".el-dialog[aria-label*='添加']").wait_for(state="hidden", timeout=3000)
                AssertUtils.assert_operation_result(False, test_case, "前端校验已拦截非法输入")
            else:
                count = self.{entity_lower}_page.search(name)
                temp_test_case = test_case.copy()
                temp_test_case["expect_count"] = "==0"
                AssertUtils.assert_search_result(count, temp_test_case, "非法输入被后端拦截，未新增成功")

    # ------------------------------ 搜索{实体名}参数化场景 ------------------------------
    @pytest.mark.parametrize("test_case", {ENTITY}_SEARCH_TEST_DATA)
    @allure.story("{实体中文名}搜索-参数化场景")
    def test_search_{entity}(self, test_case):
        """参数化测试搜索功能的各种场景"""
        time.sleep(2)
        allure.dynamic.title(test_case["title"])
        count = self.{entity_lower}_page.search(test_case["keyword"])
        AssertUtils.assert_search_result(count, test_case, f"搜索关键词：{{test_case['keyword']}}")

    # ------------------------------ 编辑{实体名}参数化场景 ------------------------------
    @pytest.mark.parametrize("test_case", {ENTITY}_EDIT_TEST_DATA)
    @allure.story("{实体中文名}编辑-参数化场景")
    def test_edit_{entity}(self, test_case):
        """参数化测试编辑功能的各种场景"""
        time.sleep(2)
        allure.dynamic.title(test_case["title"])
        # 先新增一个测试{实体名}用于编辑
        test_data = generate_test_data("edit_test")
        self.{entity_lower}_page.add_{entity}(**test_data)
        count = self.{entity_lower}_page.search(test_data["name"])
        assert count >= 1, "预新增测试数据失败"

        # 执行编辑
        new_value = test_case["new_value"]
        if test_case["field"] == "name":
            result = self.{entity_lower}_page.edit_first(new_value)
        elif test_case["field"] == "remark":
            result = self.{entity_lower}_page.edit_first(new_value)
        elif test_case["field"] == "all":
            result = self.{entity_lower}_page.edit_first(new_value["name"])
            if result:
                self.{entity_lower}_page.search(new_value["name"])
                result = self.{entity_lower}_page.edit_first(new_value["remark"])

        AssertUtils.assert_operation_result(result, test_case, f"编辑字段：{{test_case['field']}}")

        # 清理弹窗
        time.sleep(1)
        for _ in range(3):
            self.{entity_lower}_page.page.keyboard.press("Escape")
            time.sleep(0.2)
        try:
            self.{entity_lower}_page.page.locator(".el-dialog[aria-label*='编辑']").wait_for(state="hidden", timeout=3000)
        except Exception:
            pass

        # 清理测试数据
        if test_case["field"] == "name" and test_case["expect_success"]:
            self.{entity_lower}_page.search(new_value)
        elif test_case["field"] == "all" and test_case["expect_success"]:
            self.{entity_lower}_page.search(new_value["name"])
        else:
            self.{entity_lower}_page.search(test_data["name"])
        count = self.{entity_lower}_page.search("")
        if count > 0:
            self.{entity_lower}_page.delete_first()
```

---

## 四、模板占位符说明

| 占位符 | 含义 | 示例 |
|--------|------|------|
| `{module_name}` | 模块英文标识（文件名用，下划线风格） | `system_management` |
| `{PageClassName}` | 页面对象类名（大驼峰） | `PositionManagementPage` |
| `{module_mark}` | pytest 标记名（小写） | `system` |
| `{模块中文名}` | 模块中文名称 | `系统管理-职务管理` |
| `{实体中文名}` | 操作实体中文名 | `职务` |
| `{ENTITY}` | 实体英文大写（数据常量前缀） | `POSITION` |
| `{entity}` | 实体英文（方法名用） | `position` |
| `{entity_lower}` | 同 entity，页面对象实例名 | `position` |
| `{page_fixture}` | conftest 中对应的页面 fixture | `admin_page` / `enterprise_page` / `citizen_page` |
| `{父级菜单名}` | 一级菜单文本 | `系统管理` |
| `{子级菜单名}` | 二级菜单文本 | `职务管理` |
| `{对话框标题}` | 对话框 aria-label 关键词 | `添加职位` |
| `{param_list}` | add 方法的参数列表 | `name, sort, remark=""` |
| `{param_docs}` | 参数文档 | `name: 名称, sort: 排序` |
| `{first_field}` | 第一个表单字段变量 | `name` |

---

## 五、Fixture 选用规则

根据测试所属端选择对应的 fixture：

| 测试端 | fixture 名 | scope | 自动行为 |
|--------|-----------|-------|---------|
| 平台管理端（admin） | `admin_page` | class | 自动登录平台管理员 |
| 企业端 | `enterprise_page` | class | 自动登录企业账号 |
| 市民端 | `citizen_page` | class | 自动登录市民账号 |
| 需完全隔离的单用例 | `page` | function | 每个用例独立上下文，需手动登录 |

---

## 六、断言工具选用规则

| 场景 | 方法 | 关键参数 |
|------|------|---------|
| 新增/编辑/删除操作 | `AssertUtils.assert_operation_result(actual_result, test_case, msg)` | `test_case` 需含 `expect_success` |
| 搜索/查询操作 | `AssertUtils.assert_search_result(actual_count, test_case, msg)` | `test_case` 需含 `expect_count` |
| 文本包含验证 | `AssertUtils.assert_text_contains(actual_text, expect_text, title)` | — |
| 元素存在验证 | `AssertUtils.assert_element_exists(exists, name, title)` | — |

---

## 七、编码规范

1. **测试数据全部用 Python 字典列表**，存放在 `datas/` 目录，禁止 YAML/JSON
2. **每条测试数据必须包含 `type` 字段**（`positive`/`negative`/`smoke`），否则 conftest 钩子会跳过该用例
3. **页面对象必须继承 `BasePage`**，通过 `self.page` 访问 Playwright Page
4. **唯一数据用时间戳后缀**：`f"_{int(time.time())}"` 或 `generate_test_data(prefix)`
5. **清理测试数据**：setup_class 的 teardown 中删除 `auto_` 前缀数据；单条用例中也要清理自己创建的数据
6. **弹窗清理**：用 ESC 键循环关闭弹窗，再 wait_for hidden，确保页面回到干净状态
7. **避免硬编码 sleep**：优先使用 `wait_for_load_state("networkidle")`、`wait_for_selector()`、`smart_wait()`
8. **搜索操作前先点重置**：避免上一次搜索条件残留
9. **滚动到顶部**：操作列表前先 `self.page.evaluate("window.scrollTo(0, 0)")`
10. **模块级标记**：文件顶部 `pytestmark = pytest.mark.{module_mark}`，方便 `pytest -m` 过滤运行
