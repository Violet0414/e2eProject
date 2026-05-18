# ms-service-playwright 自动化测试脚本模板

> 本模板定义了该框架下可执行测试脚本的规范结构和编写模式，供测试脚本生成技能参考。所有模板内容均来自项目实际代码风格，生成脚本时必须严格遵循。

---

## 一、项目目录约定

```
ms-service-playwright/
├── pages/              # 页面对象（Page Object），按端分子目录
│   ├── base_page.py        # 基类 BasePage，所有页面对象必须继承
│   ├── login_page.py       # 登录页面对象
│   └── admin/              # 平台管理端页面对象
│       └── xxx.py              # 业务页面对象
├── datas/              # 测试数据，按端分子目录
│   ├── __init__.py         # 数据导出汇总
│   └── admin/              # 平台管理端测试数据
│       └── xxx_data.py         # Python 字典列表，不可用 YAML/JSON
├── tests/              # 测试用例脚本，按端分目录
│   └── admin/              # 平台管理端
├── common/             # 公共工具
│   ├── asserts.py          # AssertUtils 统一断言
│   ├── data_generation.py  # fake_data 数据生成器
│   ├── validation_mixin.py # ValidationMixin 字段验证混入类
│   ├── form_validator.py   # FormValidator 表单校验工具
│   ├── file_uploader.py    # FileUploader 文件上传工具
│   ├── table_operate.py    # TableOperate 列表搜索工具
│   ├── dropdown_selector.py# DropdownSelector 下拉选择工具
│   ├── message_tip.py      # MessageTip 提示消息工具
│   └── ...
├── conftest.py         # 全局 fixture 和钩子
├── config/settings.py  # 多环境配置（pydantic-settings）
└── test_files/         # 测试上传文件目录
```

---

## 二、生成文件清单

每生成一个模块的测试脚本，需要产出 **3 个文件**：

| 序号 | 文件 | 路径 | 说明 |
|------|------|------|------|
| 1 | 页面对象 | `pages/{端目录}/{module_name}.py` | 继承 BasePage，封装选择器和操作方法 |
| 2 | 测试数据 | `datas/{端目录}/{module_name}_data.py` | Python 字典列表，参数化驱动 |
| 3 | 测试用例 | `tests/{端目录}/test_{module_name}.py` | pytest + allure + ValidationMixin，参数化执行 |

---

## 三、文件模板

### 3.1 页面对象模板 `pages/{端目录}/{module_name}.py`

```python
"""{模块中文名}页面元素和操作"""
from pages.base_page import BasePage


class {PageClassName}(BasePage):
    """{模块中文名}页面元素和操作"""

    # region ======= {模块中文名}元素选择器 ========
    ADD_BUTTON = "text='新增'"
    SEARCH_BUTTON = "text='查询'"
    RESET_BUTTON = "text='重置'"
    DIALOG_CONFIRM_BUTTON = "text='确 定'"
    WIN_TITLE_NAME = "text='添加{实体中文名}'"

    # 表单字段选择器 —— 命名规则：SELECTOR_{字段大写英文}
    SELECTOR_{FIELD_NAME} = 'input[placeholder="请输入{字段中文名}"]'        # 文本输入框
    SELECTOR_{FIELD_STATUS} = 'input[placeholder="请选择{字段中文名}"]'      # 下拉选择框
    SELECTOR_{FIELD_TEXTAREA} = 'textarea[placeholder="请输入{字段中文名}"]'  # 文本域
    SELECTOR_UPLOAD_BTN = 'button:visible:has-text("点击上传")'              # 上传按钮

    # 搜索区域选择器
    SELECTOR_SEARCH_{FIELD_NAME} = 'input[placeholder="请输入{搜索字段中文名}"]'

    # endregion

    def _fill_{field_name}(self, value: str):
        """填写{字段中文名}"""
        if value is not None:
            self.fill(self.SELECTOR_{FIELD_NAME}, value)

    def _select_{field_name}(self, option_index, elem_index=None):
        """选择{字段中文名}下拉项"""
        if option_index is not None:
            if elem_index is not None:
                self.dropdown_selector.select_el_option_by_index(
                    self.SELECTOR_{FIELD_STATUS}, value=option_index, elem_index=elem_index
                )
            else:
                self.dropdown_selector.select_el_option_by_index(
                    self.SELECTOR_{FIELD_STATUS}, value=option_index
                )

    def upload_attachment(self, file_path):
        """上传附件"""
        if file_path is not None:
            self.file_uploader.upload_el_file(self.SELECTOR_UPLOAD_BTN, file_path, timeout=30000)

    def goto_module(self):
        """进入{模块中文名}模块"""
        self.navigate_menu(level1="{一级菜单名}", level2="{二级菜单名}"[, level3="{三级菜单名}"])
        return self

    def add_{entity}(self, {param_list}):
        """
        新增{实体中文名}
        :param {param_docs}
        """
        self.open_add_dialog("添加{实体中文名}")
        # 按表单字段顺序填写
        self._fill_{field_name_1}({field_1})
        self._select_{field_name_2}({field_2})
        # ... 其他字段

    def submit_form(self):
        """提交表单"""
        self.click(self.DIALOG_CONFIRM_BUTTON)

    def wait_win_closed(self):
        """等待新增窗口关闭"""
        self.wait_windows_closed(self.WIN_TITLE_NAME, timeout=20000)

    def is_column_exist(self, column_name: str, timeout: int = 15000) -> bool:
        """
        搜索验证{实体中文名}是否存在（用于新增后验证）
        Args:
            column_name: 搜索关键词
            timeout: 超时时间(毫秒)
        Returns:
            bool: 找到返回 True，否则返回 False
        """
        return self.table_operate.search_in_list(
            search_input_selector=self.SELECTOR_SEARCH_{FIELD_NAME},
            search_button_selector=self.SEARCH_BUTTON,
            search_keyword=column_name,
            timeout=timeout
        )
```

#### 页面对象编写要点

1. **选择器命名**：`SELECTOR_` 前缀 + 字段英文大写，如 `SELECTOR_CASE_TITLE`
2. **私有填充方法**：`_fill_{field}` 用于文本输入，内部判断 `if value is not None` 再填充
3. **私有选择方法**：`_select_{field}` 用于下拉选择，内部判断 `if option_index is not None` 再选择
4. **组合业务方法**：如 `fill_case_base_info()`、`add_reporter()` 等，按表单区域分组，内部调用私有方法
5. **菜单导航**：统一使用 `self.navigate_menu(level1=, level2=, level3=)`
6. **新增弹窗**：统一使用 `self.open_add_dialog("弹窗标题")`
7. **提交校验**：使用 `self.is_submit_success(use_tip=True, success_text="新增成功")`
8. **多元素索引**：使用 `elem_index` 参数，支持 `"first"` / `"last"` / 数字
9. **上传文件**：统一使用 `self.file_uploader.upload_el_file()`

---

### 3.2 测试数据模板 `datas/{端目录}/{module_name}_data.py`

```python
"""{模块中文名}测试数据"""
import os

from common.data_generation import fake_data
from config.settings import TEST_FILES_DIRECTORY_PATH
from pages.{端目录}.{module_name} import {PageClassName}


# 常量定义（反向-超长等特殊场景标题）
NAME_EXTRA_LONG = "反向-{字段中文名}超过长度限制"

# ==================== 新增{实体中文名}测试数据 ====================
{ENTITY}_ADD_TEST_DATA = [
    # ========== 冒烟测试 ==========
    {
        "title": "冒烟-完整填写所有字段提交成功",
        "type": "smoke",
        "expect_success": True,
        "data": {
            "{field_1}": f"测试{实体中文名}-{fake_data.random_4bit_str()}",
            "{field_2}": 1,
            "{field_3}_index": 0,
            "{field_4}_index": None,  # 非必填
            "file_path": os.path.join(TEST_FILES_DIRECTORY_PATH, "test_png.png"),
        }
    },  # 冒烟-完整填写

    # ========== 正向测试 ==========
    {
        "title": "正向-只填写必填字段提交成功",
        "type": "positive",
        "expect_success": True,
        "data": {
            "{field_1}": f"测试{实体中文名}-{fake_data.random_4bit_str()}",
            "{field_2}": 1,
            "{field_3}_index": 0,
            "{field_4}_index": None,  # 非必填
            "file_path": None,        # 非必填
        }
    },  # 正向-只填写必填字段

    # ========== 反向测试 ==========
    {
        "title": "反向-{字段中文名}为空",
        "type": "negative",
        "expect_success": False,
        "validation_info": {
            "selector": {PageClassName}.SELECTOR_{FIELD_NAME},
            "expected_error_text": "请输入{字段中文名}",
            "trigger": "blur"
        },
        "data": {
            "{field_1}": None,  # 目标字段用 None
            "{field_2}": 1,
            "{field_3}_index": 0,
            "{field_4}_index": None,
            "file_path": None,
        }
    },  # 反向-{字段中文名}为空

    {
        "title": "反向-{下拉字段中文名}为空",
        "type": "negative",
        "expect_success": False,
        "validation_info": {
            "selector": {PageClassName}.SELECTOR_{FIELD_DROPDOWN},
            "expected_error_text": "请选择{下拉字段中文名}",
            "trigger": "submit"
        },
        "data": {
            "{field_1}": f"测试{实体中文名}-{fake_data.random_4bit_str()}",
            "{field_2}": 1,
            "{field_3}_index": None,  # 目标字段用 None
            "{field_4}_index": None,
            "file_path": None,
        }
    },  # 反向-{下拉字段中文名}为空

    {
        "title": NAME_EXTRA_LONG,
        "type": "negative",
        "expect_success": False,
        "validation_info": {
            "selector": {PageClassName}.SELECTOR_{FIELD_NAME},
            "expected_error_text": "{字段名}长度超过限制",
            "trigger": "submit"
        },
        "data": {
            "{field_1}": f"测试{实体中文名}{fake_data.random_4bit_str()}" * 1000,
            "{field_2}": 1,
            "{field_3}_index": 0,
            "{field_4}_index": None,
            "file_path": None,
        }
    },  # 反向-name长度超过限制

    {
        "title": "反向-上传的附件格式不正确（txt）",
        "type": "negative",
        "expect_success": False,
        "validation_info": {
            "expected_error_text": "文件格式不正确",
            "trigger": "upload"
        },
        "data": {
            "{field_1}": None,
            "{field_2}": None,
            "{field_3}_index": None,
            "{field_4}_index": None,
            "file_path": os.path.join(TEST_FILES_DIRECTORY_PATH, "test_txt.txt"),
        }
    },  # 反向-上传附件格式不正确
]
```

#### 测试数据字典必填字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `title` | str | 是 | 用例中文标题，用于 Allure 报告展示和参数化ID。格式：`类型-场景描述`，如 `冒烟-完整填写所有字段`、`正向-只填写必填字段`、`反向-名称为空` |
| `type` | str | 是 | 用例类型，conftest 钩子依此过滤。可选值：`smoke` / `positive` / `negative` |
| `expect_success` | bool | 是 | 操作类用例预期结果。正向：`True`，反向：`False` |
| `data` | dict | 是 | 测试输入数据，所有业务字段放在此字典内 |
| `validation_info` | dict | 反向必填 | 字段验证信息，**仅在反向测试（字段为空/格式错误等）时使用** |

#### `validation_info` 字典结构（反向测试专用）

反向测试中，如果验证的是字段为空或格式错误，**必须**添加 `validation_info` 字典：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `selector` | str | blur/submit 必填 | 目标字段的页面选择器，引用页面对象类常量，如 `CaseRegistrationPage.SELECTOR_CASE_TITLE`。upload 类型不需要 |
| `expected_error_text` | str | 是 | 预期的错误提示文本，如 `"请输入案件标题"` |
| `trigger` | str | 是 | 验证触发方式：`"blur"`（失焦触发）/ `"submit"`（提交触发）/ `"upload"`（上传触发） |

**关键规则**：
- 反向测试中，**目标字段用 `None`**，非目标字段填写正常值
- `validation_info` 中的 `selector` 必须引用页面对象类常量，不要硬编码字符串
- upload 触发类型不需要 `selector` 字段，只需 `expected_error_text` 和 `trigger`
- blur 触发：文本输入框失焦后触发的校验（如"请输入XXX"）
- submit 触发：下拉框等点击提交后才触发的校验（如"请选择XXX"）
- upload 触发：上传不支持的文件格式触发的校验

#### 数据值约定

| 场景 | 写法 | 示例 |
|------|------|------|
| 需要唯一性的文本 | `f"前缀-{fake_data.random_4bit_str()}"` | `f"测试案件-{fake_data.random_4bit_str()}"` |
| 下拉框选项 | 整数索引，从 0 开始 | `0`（第一项） |
| 非必填字段不填 | `None` | `"file_path": None` |
| 文件上传路径 | `os.path.join(TEST_FILES_DIRECTORY_PATH, "文件名")` | `os.path.join(TEST_FILES_DIRECTORY_PATH, "test_png.png")` |
| 日期 | `fake_data.get_recent_date(N)` | `fake_data.get_recent_date(1)`（1天前） |
| 反向测试目标字段 | `None` | `"case_title": None` |

---

### 3.3 测试用例模板 `tests/{端目录}/test_{module_name}.py`

#### 3.3.1 使用 ValidationMixin 的测试模板（推荐，适用于有字段校验的场景）

```python
"""{模块中文名}测试用例"""
import allure
import pytest
import time
from common.asserts import AssertUtils
from common.validation_mixin import ValidationMixin
from pages.{端目录}.{module_name} import {PageClassName}
from datas.{端目录}.{module_name}_data import {ENTITY}_ADD_TEST_DATA

pytestmark = pytest.mark.{module_mark}


@allure.feature("{端中文名}-{模块中文名}")
class Test{PageClassName}(ValidationMixin):
    {entity_lower}_page: {PageClassName}

    @pytest.fixture(scope="class", autouse=True)
    def setup_class(self, {page_fixture}):
        """类前置：进入{模块中文名}模块"""
        self.__class__.{entity_lower}_page = {PageClassName}({page_fixture})
        yield

    def _validate_blur(self, selector, file_path, case_title):
        self.{entity_lower}_page.form_validator.blur_trigger_field_validation(selector, "blur")
        return self.{entity_lower}_page.form_validator.get_field_error_text(selector)

    def _validate_submit(self, selector, file_path, case_title):
        with allure.step("点击提交按钮触发验证"):
            self.{entity_lower}_page.submit_form()
            time.sleep(0.5)
            return self.{entity_lower}_page.form_validator.get_field_error_after_submit(selector)

    def _validate_upload(self, selector, file_path, case_title):
        with allure.step("上传不支持的文件格式"):
            self.{entity_lower}_page.upload_attachment(file_path)
        return self.{entity_lower}_page.form_validator.get_upload_error_text()

    def _handle_normal_test(self, test_case: dict):
        """处理正向测试"""
        expect_success = test_case["expect_success"]
        with allure.step("提交表单"):
            self.{entity_lower}_page.submit_form()

        with allure.step("验证提交结果"):
            is_success = self.{entity_lower}_page.is_submit_success(use_tip=True, success_text="新增成功")

            if expect_success:
                if is_success:
                    with allure.step("等待新增窗口关闭"):
                        self.{entity_lower}_page.wait_win_closed()

                    is_data_exist = self.{entity_lower}_page.is_column_exist(
                        column_name=test_case["data"]["{主键字段}"]
                    )
                    is_success = is_data_exist
                    allure.attach(
                        body=f"列表存在数据:{is_data_exist}",
                        name="列表搜索结果"
                    )

                AssertUtils.assert_submit_success(
                    is_success=is_success,
                    case_title=test_case["title"],
                    extra_msg="校验规则：提示成功 + 列表存在数据"
                )

    @allure.story("{实体中文名}新增功能验证")
    @pytest.mark.parametrize("test_case", {ENTITY}_ADD_TEST_DATA, ids=lambda x: x["title"])
    def test_{entity}_add(self, test_case):
        """{实体中文名}新增测试：正向+反向+前端校验"""
        allure.dynamic.title(test_case["title"])
        test_data = test_case["data"]
        validation_info = test_case.get("validation_info")
        file_path = test_data.get("file_path")

        with allure.step("进入{模块中文名}页面并刷新"):
            self.{entity_lower}_page.goto_module()
            self.{entity_lower}_page.page.reload()

        with allure.step("填写{实体中文名}信息"):
            self.{entity_lower}_page.add_{entity}(**test_data)

        with allure.step("填写附件信息"):
            self.{entity_lower}_page.upload_attachment(file_path)
            time.sleep(2)

        with allure.step("验证结果"):
            if validation_info is not None:
                with allure.step("验证字段"):
                    self._validate_field(test_case)
            else:
                with allure.step("处理普通测试"):
                    self._handle_normal_test(test_case)
```

#### 3.3.2 不使用 ValidationMixin 的简单测试模板（适用于简单CRUD场景）

```python
"""{模块中文名}测试用例"""
import allure
import pytest
import time
from common.asserts import AssertUtils
from common.data_generation import fake_data
from pages.{端目录}.{module_name} import {PageClassName}
from datas.{端目录}.{module_name}_data import (
    {ENTITY}_ADD_TEST_DATA,
    {ENTITY}_SEARCH_TEST_DATA,
    {ENTITY}_EDIT_TEST_DATA,
)

pytestmark = pytest.mark.{module_mark}


@allure.feature("{端中文名}-{模块中文名}")
class Test{PageClassName}ParamScenarios:
    """{模块中文名}参数化测试套件，覆盖正向/反向场景"""
    {entity_lower}_page: "{PageClassName}"

    @pytest.fixture(scope="class", autouse=True)
    def setup_class(self, {page_fixture}):
        """类前置：进入{模块中文名}模块"""
        self.__class__.{entity_lower}_page = {PageClassName}({page_fixture})
        self.__class__.{entity_lower}_page.goto_module()
        yield
        # 类后置：清理所有测试产生的数据
        try:
            test_data_prefix = "auto_"
            count = self.{entity_lower}_page.search(test_data_prefix)
            while count > 0:
                self.{entity_lower}_page.delete_first()
                count = self.{entity_lower}_page.search(test_data_prefix)
        except Exception:
            pass

    # ------------------------------ 新增{实体中文名}参数化场景 ------------------------------
    @pytest.mark.parametrize("test_case", {ENTITY}_ADD_TEST_DATA)
    @allure.story("{实体中文名}新增")
    def test_add_{entity}_param(self, test_case):
        """参数化测试新增{实体中文名}的各种场景"""
        time.sleep(1)
        allure.dynamic.title(test_case["title"])
        # 生成唯一名称避免重复
        unique_suffix = f"_{int(time.time())}"
        name = test_case["name"] + unique_suffix if test_case["name"] else test_case["name"]

        # 执行新增
        self.{entity_lower}_page.add_{entity}(name=name, ...)

        if test_case["expect_success"]:
            # 预期成功：验证能搜索到
            time.sleep(1)
            count = self.{entity_lower}_page.search(name)
            temp_test_case = test_case.copy()
            temp_test_case["expect_count"] = ">=1"
            AssertUtils.assert_search_result(count, temp_test_case, f"搜索新增的{实体中文名}：{{name}}")
            # 清理测试数据
            try:
                self.{entity_lower}_page.delete_first()
                time.sleep(1)
            except:
                pass
        else:
            # 预期失败：验证仍在对话框页面，或者搜索不到
            time.sleep(1)
            dialog_visible = self.{entity_lower}_page.page.locator(".el-dialog:visible").count() > 0
            if dialog_visible:
                self.{entity_lower}_page.page.keyboard.press("Escape")
                try:
                    self.{entity_lower}_page.page.locator(".el-dialog:visible").wait_for(state="hidden", timeout=3000)
                except:
                    pass
                AssertUtils.assert_operation_result(False, test_case, "前端校验已拦截非法输入")
            else:
                count = self.{entity_lower}_page.search(name)
                temp_test_case = test_case.copy()
                temp_test_case["expect_count"] = "==0"
                AssertUtils.assert_search_result(count, temp_test_case, "非法输入被后端拦截，未新增成功")

    # ------------------------------ 搜索功能参数化场景 ------------------------------
    @pytest.mark.parametrize("test_case", {ENTITY}_SEARCH_TEST_DATA)
    @allure.story("{实体中文名}搜索")
    def test_search_{entity}_param(self, test_case):
        """参数化测试搜索功能的各种场景"""
        time.sleep(1)
        allure.dynamic.title(test_case["title"])
        count = self.{entity_lower}_page.search(name=test_case["keyword"])
        AssertUtils.assert_search_result(count, test_case, f"搜索关键词：{{test_case['keyword']}}")

    # ------------------------------ 编辑功能参数化场景 ------------------------------
    @pytest.mark.parametrize("test_case", {ENTITY}_EDIT_TEST_DATA)
    @allure.story("{实体中文名}编辑")
    def test_edit_{entity}_param(self, test_case):
        """参数化测试编辑功能的各种场景"""
        time.sleep(1)
        allure.dynamic.title(test_case["title"])
        # 先新增一个测试{实体中文名}用于编辑
        test_data = fake_data.generate_test_data("edit_test")
        self.{entity_lower}_page.add_{entity}(**test_data)
        count = self.{entity_lower}_page.search(test_data["name"])
        assert count >= 1, "预新增测试数据失败"

        # 执行编辑
        result = self.{entity_lower}_page.edit_first(...)
        AssertUtils.assert_operation_result(result, test_case, f"编辑字段：{{test_case['field']}}")

        # 清理弹窗
        time.sleep(1)
        for _ in range(3):
            self.{entity_lower}_page.page.keyboard.press("Escape")
            time.sleep(0.2)
        try:
            self.{entity_lower}_page.page.locator(".el-dialog[aria-label*='修改']").wait_for(state="hidden", timeout=3000)
        except Exception:
            pass

        # 清理测试数据
        try:
            self.{entity_lower}_page.delete_first()
            time.sleep(1)
        except Exception:
            pass
```

---

## 四、模板占位符说明

| 占位符 | 含义 | 示例 |
|--------|------|------|
| `{端目录}` | 端子目录名 | `admin` / `company` / `citizen` |
| `{端中文名}` | 端中文名称 | `政策管理平台` / `欠薪监管平台` / `系统管理` |
| `{module_name}` | 模块英文标识（文件名用，下划线风格） | `labor_supervision_final` / `policy_management` |
| `{PageClassName}` | 页面对象类名（大驼峰） | `CaseRegistrationPage` / `ColumnManagementPage` |
| `{module_mark}` | pytest 标记名（小写+下划线） | `labor_supervision` / `policy_management` |
| `{模块中文名}` | 模块中文名称 | `案件登记管理` / `栏目管理` |
| `{实体中文名}` | 操作实体中文名 | `案件` / `栏目` |
| `{ENTITY}` | 实体英文大写（数据常量前缀） | `CASE` / `COLUMN` |
| `{entity}` | 实体英文（方法名用） | `case` / `column` |
| `{entity_lower}` | 同 entity，页面对象实例名 | `case_page` / `column_page` |
| `{page_fixture}` | conftest 中对应的页面 fixture | `admin_page` / `enterprise_page` / `citizen_page` |
| `{一级菜单名}` | 一级菜单文本 | `欠薪监管平台` / `政策管理` |
| `{二级菜单名}` | 二级菜单文本 | `劳动保障监察案件` / `栏目管理` |
| `{三级菜单名}` | 三级菜单文本（可选） | `案件登记管理` |
| `{主键字段}` | 测试数据中的主键字段名 | `case_title` / `name` |
| `{param_list}` | add 方法的参数列表 | `case_title, area_option, case_type_option` |
| `{param_docs}` | 参数文档 | `case_title: 案件标题, area_option: 所属区域选项` |

---

## 五、Fixture 选用规则

根据测试所属端选择对应的 fixture：

| 测试端 | fixture 名 | scope | 自动行为 |
|--------|-----------|-------|---------|
| 平台管理端（admin） | `admin_page` | class | 自动登录平台管理员 |
| 企业端 | `enterprise_page` | class | 自动登录企业账号 |
| 市民端 | `citizen_page` | class | 自动登录市民账号 |
| 需完全隔离的单用例 | `page` | function | 每个用例独立上下文，需手动登录 |

**fixture 使用模式**（class scope）：
```python
@pytest.fixture(scope="class", autouse=True)
def setup_class(self, admin_page):
    """类前置"""
    self.__class__.{entity_lower}_page = {PageClassName}(admin_page)
    yield
```

---

## 六、断言工具选用规则

| 场景 | 方法 | 关键参数 |
|------|------|---------|
| 新增/编辑/删除操作结果 | `AssertUtils.assert_operation_result(actual_result, test_case, msg)` | `test_case` 需含 `expect_success` |
| 搜索/查询结果数量 | `AssertUtils.assert_search_result(actual_count, test_case, msg)` | `test_case` 需含 `expect_count` |
| 表单提交成功 | `AssertUtils.assert_submit_success(is_success, case_title, extra_msg)` | `is_success` 为 bool |
| 字段验证错误提示 | `AssertUtils.assert_validation_error(field_name, actual_error_text, expected, case_title)` | `expected` 支持字符串精准包含或列表任意匹配 |
| 页面存在验证错误 | `AssertUtils.assert_has_validation_error(has_error, case_title, error_count)` | 反向测试使用 |

---

## 七、ValidationMixin 使用规则

当测试涉及字段校验（为空、格式错误等）时，测试类必须继承 `ValidationMixin`：

```python
from common.validation_mixin import ValidationMixin

class Test{PageClassName}(ValidationMixin):
```

**子类必须实现三个验证方法**：

| 方法 | 触发方式 | 实现逻辑 |
|------|---------|---------|
| `_validate_blur(self, selector, file_path, case_title)` | blur（失焦） | 调用 `form_validator.blur_trigger_field_validation()` + `get_field_error_text()` |
| `_validate_submit(self, selector, file_path, case_title)` | submit（提交） | 调用 `submit_form()` + `form_validator.get_field_error_after_submit()` |
| `_validate_upload(self, selector, file_path, case_title)` | upload（上传） | 调用 `upload_attachment()` + `form_validator.get_upload_error_text()` |

**父类自动提供**：
- `_validate_field(test_case)` —— 通用字段验证入口，根据 `validation_info` 的 `trigger` 自动分发
- `_check_required_params(trigger, selector, file_path)` —— 参数校验
- `_dispatch_validation(trigger, selector, file_path, case_title)` —— 分发逻辑

---

## 八、编码规范

1. **测试数据全部用 Python 字典列表**，存放在 `datas/` 目录，禁止 YAML/JSON
2. **每条测试数据必须包含 `type` 字段**（`positive`/`negative`/`smoke`），否则 conftest 钩子会跳过该用例
3. **页面对象必须继承 `BasePage`**，通过 `self.page` 访问 Playwright Page
4. **唯一数据用 `fake_data.random_4bit_str()`** 生成随机后缀，如 `f"测试案件-{fake_data.random_4bit_str()}"`
5. **反向测试必须添加 `validation_info`**，目标字段用 `None`，非目标字段填正常值
6. **`validation_info` 中的 `selector` 必须引用页面对象类常量**，如 `CaseRegistrationPage.SELECTOR_CASE_TITLE`
7. **页面对象私有方法内部判断 `if value is not None`** 再执行操作，保证 None 值不触发填充
8. **表单区域拆分为组合方法**：如 `fill_case_base_info()`、`fill_reported_unit()`、`fill_complaint_content()`
9. **菜单导航**：统一使用 `self.navigate_menu(level1=, level2=, level3=)`
10. **新增弹窗**：统一使用 `self.open_add_dialog("弹窗标题")`
11. **搜索操作前先点重置**：避免上一次搜索条件残留
12. **滚动到顶部**：操作列表前先 `self.page.evaluate("window.scrollTo(0, 0)")`
13. **弹窗清理**：用 ESC 键循环关闭弹窗，再 wait_for hidden，确保页面回到干净状态
14. **模块级标记**：文件顶部 `pytestmark = pytest.mark.{module_mark}`，方便 `pytest -m` 过滤运行
15. **参数化ID**：使用 `ids=lambda x: x["title"]`，以中文标题作为参数化ID
16. **优先使用 `wait_for_load_state`/`wait_for_selector`** 等待机制，避免硬编码 `time.sleep()`
17. **上传文件路径**：使用 `os.path.join(TEST_FILES_DIRECTORY_PATH, "文件名")`，不硬编码路径
18. **测试类命名**：大驼峰，如 `TestLaborCaseRegistration`、`TestPolicyColumnManagement`
19. **测试方法命名**：snake_case，如 `test_case_add`、`test_column_add`
20. **页面对象文件头**：使用 `"""{模块中文名}页面元素和操作"""` 格式的模块文档字符串
