---
name: test-script-generate
description: 测试脚本生成 - 根据测试用例.md和testScriptTemplate.md规范生成Playwright自动化测试脚本
triggers:
  - "生成测试脚本"
  - "测试脚本生成"
  - "生成脚本"
  - "写测试脚本"
---

# 测试脚本生成

将测试用例.md转化为符合 e2e_runner 项目规范的自动化测试脚本，严格遵循testScriptTemplate.md中定义的模板结构和编码规范。

## 核心要求

1. **输出目录结构与 e2e_runner 兼容**：生成的测试脚本必须输出到 `output/{日期}/tests/` 目录，供 e2e_runner 的 pytest 运行器读取执行
2. **跳转路径处理**：当测试用例需要跳转到非默认页面时，必须从测试用例中读取跳转路径（`route_path`）并写入测试数据，测试用例执行时使用该路径进行导航

## 输入

- **测试用例.md**：从以下位置搜索并由用户选择：
  - `./output/{当前日期}/` 文件夹下的 `.md` 文件
  - `./exploreOutput/{当前日期}/` 文件夹下的 `.md` 文件
- **测试脚本模板**：`./referenceDocument/testScriptTemplate.md`，定义脚本编写规范
- **输出目录**：`./output/{当前日期}/`（与测试用例.md同级目录，"当前日期"格式为YYYY-MM-DD，如2026-05-15）

## 输出文件结构

每个模块生成3个文件，按端类型分子目录：

| 序号 | 文件 | 路径 |
|------|------|------|
| 1 | 页面对象 | `output/{当前日期}/pages/{端目录}/{module_name}.py` |
| 2 | 测试数据 | `output/{当前日期}/datas/{端目录}/{module_name}_data.py` |
| 3 | 测试用例 | `output/{当前日期}/tests/{端目录}/test_{module_name}.py` |

**重要**：测试用例文件 `test_{module_name}.py` 最终被 e2e_runner 的 pytest 运行器在 `output/{日期}/tests/` 目录下执行，因此必须在文件开头正确设置 PYTHONPATH 导入路径。

## 跳转路径判断与处理

### 判断逻辑

在解析测试用例时，统一使用菜单导航 `goto_module()` 进入目标页面：

| 条件 | 处理方式 | 说明 |
|------|---------|------|
| 所有测试场景 | `goto_module()` | 统一使用菜单导航进入目标页面 |
| route_path字段 | 仅记录信息 | 用于日志追踪，不用于页面跳转 |

### 跳转路径读取

从测试用例文件中提取跳转路径，仅用于信息记录：

1. **测试用例表格中的 `route_path` 字段**（显式声明）
2. **测试用例表格中的 `页面URL` 或 `URL` 字段**
3. **探索记录中的"页面URL"字段**

### 测试用例中使用菜单导航

所有测试用例统一使用 `goto_module()` 通过菜单导航进入目标页面：

```python
def test_charging_pile_add(self, test_case):
    """充电桩新增测试"""
    test_data = test_case["data"]
    route_path = test_case.get("route_path")  # 仅用于日志记录

    with allure.step("进入充电桩页面"):
        # 统一使用菜单导航
        self.charging_pile_page.goto_module()
        self.charging_pile_page.page.reload()
```

## 处理流程

### 第一步：搜索并选择测试用例文件

执行以下命令搜索可用的 `.md` 文件：

```bash
# 搜索 output 目录下当前日期的 md 文件
find ./output -path "*/$(date +%Y-%m-%d)/*.md" -type f 2>/dev/null

# 搜索 exploreOutput 目录下当前日期的 md 文件
find ./exploreOutput -path "*/*$(date +%Y%m%d)*/*.md" -type f 2>/dev/null
```

使用 AskUserQuestion 工具让用户选择使用哪个文件：

```python
questions = [
    {
        "header": "选择用例文件",
        "question": "请选择要使用的测试用例文件：",
        "multiSelect": False,
        "options": [
            {"label": "文件1路径", "description": "文件描述"},
            {"label": "文件2路径", "description": "文件描述"},
        ]
    }
]
```

读取用户选择的测试用例 `.md` 文件，解析用例表格，提取：
- 模块路径（用于确定端类型和菜单结构）
- 用例编号、名称、步骤、预期
- 用例类型（正向/反向/UI验证）

### 第二步：读取模板文件

读取 `./referenceDocument/testScriptTemplate.md`，确认：
- 页面对象类结构和方法签名
- 测试数据字典必填字段
- 测试用例参数化模式
- ValidationMixin使用规则
- 编码规范和断言工具使用

### 第三步：创建输出目录

```bash
mkdir -p output/{当前日期}/pages/admin
mkdir -p output/{当前日期}/pages/company
mkdir -p output/{当前日期}/pages/citizen
mkdir -p output/{当前日期}/datas/admin
mkdir -p output/{当前日期}/datas/company
mkdir -p output/{当前日期}/datas/citizen
mkdir -p output/{当前日期}/tests/admin
mkdir -p output/{当前日期}/tests/company
mkdir -p output/{当前日期}/tests/citizen
```

### 第四步：生成页面对象

文件：`output/{当前日期}/pages/{端目录}/{module_name}.py`

根据模板中的页面对象模板生成，需要：

1. **文件头**：使用 `"""{模块中文名}页面元素和操作"""` 格式的模块文档字符串
2. **继承 BasePage**：`from pages.base_page import BasePage`
3. **元素选择器区域**（用 `# region` / `# endregion` 包裹）：
   - 按钮选择器：ADD_BUTTON、SEARCH_BUTTON、RESET_BUTTON、DIALOG_CONFIRM_BUTTON、WIN_TITLE_NAME
   - 表单字段选择器：命名规则 `SELECTOR_{字段大写英文}`
     - 文本输入框：`'input[placeholder="请输入{字段中文名}"]'`
     - 下拉选择框：`'input[placeholder="请选择{字段中文名}"]'`
     - 文本域：`'textarea[placeholder="请输入{字段中文名}"]'`
     - 上传按钮：`'button:visible:has-text("点击上传")'`
   - 搜索区域选择器：`SELECTOR_SEARCH_{字段大写英文}`
4. **私有填充方法**：`_fill_{field_name}(self, value: str)` —— 内部判断 `if value is not None` 再填充
5. **私有选择方法**：`_select_{field_name}(self, option_index, elem_index=None)` —— 内部判断 `if option_index is not None` 再选择，支持 `elem_index` 参数
6. **上传方法**：`upload_attachment(self, file_path)` —— 内部判断 `if file_path is not None`，使用 `self.file_uploader.upload_el_file()`
7. **菜单导航**：`goto_module()` —— 使用 `self.navigate_menu(level1=, level2=, level3=)`
8. **组合业务方法**：`add_{entity}(self, {param_list})` —— 内部调用 `self.open_add_dialog("弹窗标题")`，按表单字段顺序调用私有方法
9. **提交方法**：`submit_form()` —— 调用 `self.click(self.DIALOG_CONFIRM_BUTTON)`
10. **等待窗口关闭**：`wait_win_closed()` —— 调用 `self.wait_windows_closed(self.WIN_TITLE_NAME, timeout=20000)`
11. **搜索验证**：`is_column_exist(column_name, timeout=15000)` —— 调用 `self.table_operate.search_in_list()`

**渐进式生成策略**：先读取用例，识别所有需要的方法，每个方法单独实现。

### 第五步：生成测试数据

文件：`output/{当前日期}/datas/{端目录}/{module_name}_data.py`

根据模板中的测试数据模板生成：

1. **导入**：
   - `import os`
   - `from common.data_generation import fake_data`
   - `from config.settings import TEST_FILES_DIRECTORY_PATH`
   - `from pages.{端目录}.{module_name} import {PageClassName}`
2. **常量定义**：反向-超长等特殊场景标题
3. **数据组织**：按功能模块分组，如 `{ENTITY}_ADD_TEST_DATA`、`{ENTITY}_SEARCH_TEST_DATA`、`{ENTITY}_EDIT_TEST_DATA`
4. **每条数据必填字段**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `title` | str | 是 | 用例中文标题，格式：`类型-场景描述`，如 `冒烟-完整填写`、`正向-只填必填`、`反向-名称为空` |
| `type` | str | 是 | 可选值：`smoke` / `positive` / `negative` |
| `expect_success` | bool | 是 | 正向：`True`，反向：`False` |
| `route_path` | str | 否 | 跳转路径，仅记录信息用于日志追踪，测试用例执行时统一使用 `goto_module()` |
| `data` | dict | 是 | 所有业务字段放在此字典内 |
| `validation_info` | dict | 反向必填 | 仅在反向测试（字段为空/格式错误）时使用 |

5. **`route_path` 字段说明**：

| 场景 | 写法 | 说明 |
|------|------|------|
| 所有测试场景 | 不填或 `None` | 测试用例统一使用 `goto_module()` 通过菜单导航 |
| 记录跳转路径 | `/business/xxx/yyy` | 仅用于日志追踪，不用于实际页面跳转 |

6. **`validation_info` 字典结构**（反向测试专用）：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `selector` | str | blur/submit必填 | 引用页面对象类常量，如 `CaseRegistrationPage.SELECTOR_CASE_TITLE`。upload类型不需要 |
| `expected_error_text` | str | 是 | 预期的错误提示文本 |
| `trigger` | str | 是 | `"blur"`（失焦）/ `"submit"`（提交）/ `"upload"`（上传） |

7. **数据值约定**：

| 场景 | 写法 |
|------|------|
| 需要唯一性的文本 | `f"前缀-{fake_data.random_4bit_str()}"` |
| 下拉框选项 | 整数索引，从0开始 |
| 非必填字段不填 | `None` |
| 文件上传路径 | `os.path.join(TEST_FILES_DIRECTORY_PATH, "文件名")` |
| 日期 | `fake_data.get_recent_date(N)` |
| 反向测试目标字段 | `None`，非目标字段填正常值 |

**渐进式生成策略**：按用例模块分组，每组单独生成数据。

### 第六步：生成测试用例

文件：`output/{当前日期}/tests/{端目录}/test_{module_name}.py`

根据模板中的测试用例模板生成，根据场景选择模板：

#### 3.3.1 使用 ValidationMixin 的测试模板（推荐，适用于有字段校验的场景）

1. **导入**：
   - `import allure, pytest, time`
   - `from common.asserts import AssertUtils`
   - `from common.validation_mixin import ValidationMixin`
   - `from pages.{端目录}.{module_name} import {PageClassName}`
   - `from datas.{端目录}.{module_name}_data import {ENTITY}_ADD_TEST_DATA`
2. **模块标记**：`pytestmark = pytest.mark.{module_mark}`
3. **测试类继承 ValidationMixin**：`class Test{PageClassName}(ValidationMixin)`
4. **类属性**：`{entity_lower}_page: {PageClassName}`
5. **类前置fixture**：
   ```python
   @pytest.fixture(scope="class", autouse=True)
   def setup_class(self, {page_fixture}):
       self.__class__.{entity_lower}_page = {PageClassName}({page_fixture})
       yield
   ```
6. **必须实现三个验证方法**：
   - `_validate_blur(self, selector, file_path, case_title)` —— 调用 `form_validator.blur_trigger_field_validation()` + `get_field_error_text()`
   - `_validate_submit(self, selector, file_path, case_title)` —— 调用 `submit_form()` + `form_validator.get_field_error_after_submit()`
   - `_validate_upload(self, selector, file_path, case_title)` —— 调用 `upload_attachment()` + `form_validator.get_upload_error_text()`
7. **正向测试处理方法** `_handle_normal_test(self, test_case)`：
   - 提交表单 → `is_submit_success(use_tip=True, success_text="新增成功")` → 成功则 `wait_win_closed()` + `is_column_exist()` → `AssertUtils.assert_submit_success()`
8. **参数化测试方法**：
   ```python
   @allure.story("{实体中文名}新增功能验证")
   @pytest.mark.parametrize("test_case", {ENTITY}_ADD_TEST_DATA, ids=lambda x: x["title"])
   def test_{entity}_add(self, test_case):
   ```
   - **关键**：统一使用 `goto_module()` 进入页面 → 填写信息 → 填写附件 → 判断：有validation_info则调用 `_validate_field(test_case)`，否则调用 `_handle_normal_test(test_case)`

**菜单导航处理逻辑**：
```python
def test_{entity}_add(self, test_case):
    """{实体中文名}新增测试"""
    test_data = test_case["data"]
    route_path = test_case.get("route_path")  # 仅用于日志记录
    validation_info = test_case.get("validation_info")

    with allure.step("进入{模块中文名}页面"):
        # 统一使用菜单导航
        self.{entity_lower}_page.goto_module()
        self.{entity_lower}_page.page.reload()
    
    # ... 后续步骤
```

#### 3.3.2 不使用 ValidationMixin 的简单测试模板（适用于简单CRUD场景）

1. **测试类**：`class Test{PageClassName}ParamScenarios`
2. **类前置fixture**：进入模块 + 类后置清理测试数据（搜索前缀 + 循环删除）
3. **新增参数化**：`test_add_{entity}_param` —— 生成唯一名称 → 新增 → expect_success为True则搜索验证 + 清理，为False则验证弹窗/搜索不到
4. **搜索参数化**：`test_search_{entity}_param` —— 直接搜索 + `AssertUtils.assert_search_result()`
5. **编辑参数化**：`test_edit_{entity}_param` —— 先新增预置数据 → 编辑 → 弹窗清理(ESC循环) + 数据清理
6. **弹窗清理**：ESC键循环关闭 + `wait_for(state="hidden", timeout=3000)`

**渐进式生成策略**：按功能模块分批生成测试方法，每批不超过20个。

## 用例类型映射

| 用例类型 | 测试数据type | 断言方式 |
|----------|-------------|----------|
| UI验证类 | smoke | 验证元素存在/文本正确 |
| 正向操作类 | positive | expect_success=True |
| 反向操作类 | negative | expect_success=False + validation_info |

## 菜单路径与端类型映射

| 路径关键词 | 端目录 | 端中文名 | fixture | 测试目录 |
|-----------|--------|---------|---------|---------|
| 民生服务管理后台 | admin | 政策管理平台 | admin_page | tests/admin/ |
| 企业管理 | company | 欠薪监管平台 | enterprise_page | tests/company/ |
| 市民服务 | citizen | 系统管理 | citizen_page | tests/citizen/ |

## Fixture 选用规则

| 测试端 | fixture名 | scope | 自动行为 |
|--------|-----------|-------|---------|
| 平台管理端（admin） | `admin_page` | class | 自动登录平台管理员 |
| 企业端 | `enterprise_page` | class | 自动登录企业账号 |
| 市民端 | `citizen_page` | class | 自动登录市民账号 |
| 需完全隔离的单用例 | `page` | function | 每个用例独立上下文，需手动登录 |

## 断言工具选用规则

| 场景 | 方法 | 关键参数 |
|------|------|---------|
| 新增/编辑/删除操作结果 | `AssertUtils.assert_operation_result(actual_result, test_case, msg)` | `test_case`需含`expect_success` |
| 搜索/查询结果数量 | `AssertUtils.assert_search_result(actual_count, test_case, msg)` | `test_case`需含`expect_count` |
| 表单提交成功 | `AssertUtils.assert_submit_success(is_success, case_title, extra_msg)` | `is_success`为bool |
| 字段验证错误提示 | `AssertUtils.assert_validation_error(field_name, actual_error_text, expected, case_title)` | `expected`支持字符串或列表 |
| 页面存在验证错误 | `AssertUtils.assert_has_validation_error(has_error, case_title, error_count)` | 反向测试使用 |

## ValidationMixin 使用规则

当测试涉及字段校验（为空、格式错误等）时，测试类必须继承 `ValidationMixin`：

```python
from common.validation_mixin import ValidationMixin

class Test{PageClassName}(ValidationMixin):
```

子类必须实现三个验证方法：`_validate_blur`、`_validate_submit`、`_validate_upload`。

父类自动提供：`_validate_field(test_case)`（根据trigger自动分发）、`_check_required_params()`、`_dispatch_validation()`。

## 模板占位符说明

| 占位符 | 含义 | 示例 |
|--------|------|------|
| `{端目录}` | 端子目录名 | `admin` / `company` / `citizen` |
| `{端中文名}` | 端中文名称 | `政策管理平台` / `欠薪监管平台` / `系统管理` |
| `{module_name}` | 模块英文标识（下划线风格） | `labor_supervision_final` |
| `{PageClassName}` | 页面对象类名（大驼峰） | `CaseRegistrationPage` |
| `{module_mark}` | pytest标记名（小写+下划线） | `labor_supervision` |
| `{模块中文名}` | 模块中文名称 | `案件登记管理` |
| `{实体中文名}` | 操作实体中文名 | `案件` |
| `{ENTITY}` | 实体英文大写（数据常量前缀） | `CASE` |
| `{entity}` | 实体英文（方法名用） | `case` |
| `{entity_lower}` | 页面对象实例名 | `case_page` |
| `{page_fixture}` | 对应的页面fixture | `admin_page` |
| `{一级菜单名}` | 一级菜单文本 | `欠薪监管平台` |
| `{二级菜单名}` | 二级菜单文本 | `劳动保障监察案件` |
| `{三级菜单名}` | 三级菜单文本（可选） | `案件登记管理` |
| `{主键字段}` | 测试数据中的主键字段名 | `case_title` |
| `{param_list}` | add方法的参数列表 | `case_title, area_option, case_type_option` |
| `{param_docs}` | 参数文档 | `case_title: 案件标题, area_option: 所属区域选项` |
| `{route_path}` | 跳转路径（URL路径） | `/business/publicFacilities/chargingPile` |

## 编码规范

1. 测试数据全部用 Python 字典列表，禁止 YAML/JSON
2. 每条测试数据必须包含 `type` 字段（positive/negative/smoke），否则 conftest 钩子会跳过
3. 页面对象必须继承 BasePage，通过 `self.page` 访问 Playwright Page
4. 唯一数据用 `fake_data.random_4bit_str()` 生成随机后缀
5. 反向测试必须添加 `validation_info`，目标字段用 `None`，非目标字段填正常值
6. `validation_info` 中的 `selector` 必须引用页面对象类常量，不要硬编码字符串
7. 页面对象私有方法内部判断 `if value is not None` 再执行操作，保证 None 值不触发填充
8. 表单区域拆分为组合方法：如 `fill_case_base_info()`、`fill_reported_unit()`
9. 菜单导航：统一使用 `self.navigate_menu(level1=, level2=, level3=)`
10. 新增弹窗：统一使用 `self.open_add_dialog("弹窗标题")`
11. 搜索操作前先点重置，避免上一次搜索条件残留
12. 操作列表前先滚动到顶部：`self.page.evaluate("window.scrollTo(0, 0)")`
13. 弹窗清理：用 ESC 键循环关闭弹窗，再 wait_for hidden
14. 模块级标记：文件顶部 `pytestmark = pytest.mark.{module_mark}`
15. 参数化ID：使用 `ids=lambda x: x["title"]`，以中文标题作为参数化ID
16. 优先使用 `wait_for_load_state`/`wait_for_selector` 等待机制，避免硬编码 `time.sleep()`
17. 上传文件路径：使用 `os.path.join(TEST_FILES_DIRECTORY_PATH, "文件名")`，不硬编码
18. 测试类命名：大驼峰，如 `TestLaborCaseRegistration`
19. 测试方法命名：snake_case，如 `test_case_add`
20. 页面对象文件头：使用 `"""{模块中文名}页面元素和操作"""` 格式的模块文档字符串

## 渐进式读取策略

为防止上下文过长导致生成效果不理想：

1. **用例分段读取**：将测试用例按功能模块分段处理
2. **方法独立实现**：页面对象中的每个方法独立实现
3. **数据分组生成**：测试数据按功能模块分组
4. **测试方法分批**：每批测试方法不超过20个

## 注意事项

- 用例ID与测试方法名对应：如 TC-CASE-001 → test_tc_case_001
- 如果用例过于复杂或缺少关键信息，先列出疑问向用户确认
- 生成后统计产出文件数量和用例数量
- 页面对象的方法名使用 snake_case 风格
- fixture 选用根据端类型确定
- 涉及字段校验的测试类必须继承 ValidationMixin 并实现三个验证方法
- 简单CRUD场景使用不继承 ValidationMixin 的简单测试模板
- **跳转路径**：必须从测试用例中提取 `route_path` 或 `页面URL` 字段，仅记录到测试数据用于日志追踪，测试用例执行时统一使用 `goto_module()` 菜单导航
- **e2e_runner 兼容性**：生成的测试脚本放在 `output/{日期}/tests/` 目录，conftest.py 由 e2e_runner 自动复制，测试脚本只需正确设置导入路径

## 持久化

- 所有生成的文件输出到 `./output/{当前日期}/` 目录（与测试用例.md同级）
- 目录结构：
  ```
  output/{当前日期}/
  ├── 测试用例.md
  ├── pages/
  │   └── {端目录}/
  │       └── {module_name}.py
  ├── datas/
  │   └── {端目录}/
  │       └── {module_name}_data.py
  └── tests/
      └── {端目录}/
          └── test_{module_name}.py
  ```
- **重要**：`output/{当前日期}/tests/` 目录下的测试脚本由 e2e_runner 的 pytest 运行器执行，conftest.py 由 e2e_runner 自动复制到该目录，无需手动管理
