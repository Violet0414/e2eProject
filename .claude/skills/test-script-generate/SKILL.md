---
name: test-script-generate
description: 测试脚本生成 - 根据"测试用例.md"、"record_operating_steps.py"生成符合项目规范的Playwright自动化测试脚本（⚠️ 必须优先使用record_operating_steps.py中的定位器）
triggers:
  - "生成测试脚本"
  - "测试脚本生成"
  - "生成脚本"
  - "写测试脚本"
  - "根据探索输出生成测试"
  - "test-script-generate"
---

# 测试脚本生成

将提供的"测试用例.md"、"record_operating_steps.py"转化为符合 pw-e2e-suite 项目规范的自动化测试脚本，严格遵循 files/templates/test_script_template.md 中定义的模板结构和编码规范。

## ⚠️【强制前置检查清单】—— 必须按顺序完成，不得跳过

在开始生成任何代码之前，必须完成以下检查和文件读取：

- [ ] **1. 完整扫描 files/templates 目录**：使用 Glob 工具扫描输出目录，列出所有发现的文件
- [ ] **2. 确认找到`record_operating_steps.py`**：必须优先查找并读取此文件（如果存在）
- [ ] **3. 提取`record_operating_steps.py`中所有定位器**：分析录制代码，提取所有 get_by_role、get_by_text、locator 的使用模式
- [ ] **4. 读取`测试用例.md`**：最后读取测试用例文件
- [ ] **6. 阅读模板文件**：完整阅读`files/templates/test_script_template.md`文件

**⚠️ 重要提示：如果发现 `record_operating_steps.py` 存在，必须优先使用其中的定位器，不得以任何理由忽略！**

## 核心要求

1. **输出目录结构与项目兼容**：生成的测试脚本直接输出到项目的 `pages/`、`datas/`、`tests/` 目录，供 pytest 运行器读取执行
2. **URL导航方式**：所有测试用例统一使用 `page_open_url()` 通过 URL 直接进入目标页面
3. **route_path 必须填写**：从`record_operating_steps.py`中提取 `route_path` 字段，写入页面对象
4. **⚠️ 元素定位器优先级（强制执行）**：当存在多个定位器来源时，必须严格按以下优先级使用：
   - **🔴 最高优先级（强制优先）**：`record_operating_steps.py` 中的定位器（实际录制的操作代码）—— 如果此文件存在，必须优先使用，不得绕过
   - **🟡 次优先级**：`explore_record.md` 中的定位器（探索记录）
   - **🟢 最后**：根据用例合理推断
5. **下拉选择方式**：根据实际情况选择合适的方式，参考`record_operating_steps.py`
6. **表单填充不区分新增/编辑选择器**：`fill_form_data` 方法中新增和编辑复用相同定位器（实际项目中新增编辑弹窗结构一致）
7. **严格按照模板格式生成**：生成的页面对象、测试数据、测试用例文件必须严格遵循 `files/templates/test_script_template.md` 中定义的结构和编码规范
8. **必须参考实际项目文件**：所有生成的文件必须严格遵循 `pages/population_map/community_management/community_service_facility_page.py`、`datas/population_map/community_management/community_service_facility_data.py`、`tests/population_map/community_management/test_community_service_facility.py` 的结构、命名规范和编码风格
9. **使用BaseCRUDTestTemplate基类**：测试用例类必须继承 `BaseCRUDTestTemplate` 基类，而不是直接使用 `ValidationMixin`

## 输入

- **测试用例文件**：从 `./output/{当天日期}/测试用例.md` 目录搜索最新的测试用例 `.md` 文件
- **探索记录文件**：`explore_record.md`（如果存在）
- **录制代码文件**：`./files/templates/record_operating_steps.py`（如果存在）—— **元素定位器优先使用此文件中的**
- **测试脚本模板**：`./files/templates/test_script_template.md`，定义脚本编写规范
- **输出目录**：项目根目录下对应的 `pages/`、`datas/`、`tests/` 目录

## 处理流程

### 第一步：强制扫描并确认所有输入文件（必须完成）

使用 Glob 工具扫描 output 目录，列出所有发现的文件：
```
例如输出：
- output/2026-07-21/测试用例.md
- output/2026-07-21/record_operating_steps.py  ⚠️ 必须标记此文件！
- output/2026-07-21/explore_record.md
```

**如果发现 record_operating_steps.py，必须立即读取并标记为"优先使用"！**

### 第二步：解析 record_operating_steps.py（如果存在 - 必须优先处理）

完整读取 record_operating_steps.py，提取并记录以下信息：
- 搜索区域使用的定位器模式
- 按钮点击使用的定位器
- 表单输入使用的定位器（注意 nth() 索引）
- 下拉选择使用的定位器
- 单选按钮使用的定位器
- 文本域使用的定位器

**⚠️ 提取示例**：
```python
# 从 record_operating_steps.py 中提取的定位器可以直接内联在 fill_form_data 方法中使用
page.get_by_role("textbox", name="请输入").nth(1)  # 项目名称
page.get_by_role("textbox", name="请选择区县").click()  # 区县下拉
page.get_by_role("listitem").filter(has_text="船山区").click()
```

### 第三步：解析其他输入文件

读取并解析以下关键信息：
- **route_path**：从 record_operating_steps.py 中提取
- **页面标题/模块中文名**：从页面标题或菜单路径获取
- **实体中文名**：从用例中提取（如"社区办公"、"项目"等）
- **字段信息**：表单字段、搜索字段、表格字段等，从 record_operating_steps.py 提取
- **元素定位器**：从 record_operating_steps.py 提取（⚠️ 优先使用 record_operating_steps.py 中的定位器，若不存在则使用 explore_record.md 中的定位器，若仍不存在则根据用例合理推断）

### 第四步：读取项目相关文件

读取以下项目文件以了解项目结构和规范：
1. **files/templates/test_script_template.md**：确认模板结构和编码规范
2. **pages/base_page.py**：了解基类提供的方法
3. **config/settings.py**：了解端配置和 fixture 配置
4. **common/constants.py**：了解常量定义
5. **tests/base_crud_template.py**：了解基类模板的结构和要求
6. **参考实际项目文件**：pages/population_map/community_management/community_service_facility_page.py、datas/population_map/community_management/community_service_facility_data.py、tests/population_map/community_management/test_community_service_facility.py

### 第五步：确定端类型和模块信息

根据页面URL或菜单路径确定端类型：

| 路径关键词    | 端目录 | 端中文名 | URL 特征 | Fixture |
|----------|-------|---------|---------|---------|
| 人口地图     | population_map | 人口地图 | aigc.cqzhgz.cn | population_map_page |
| 民生服务管理后台 | admin | 民生服务管理后台 | 民生服务相关 | ms_admin_page |
| 民生服务企业端  | company | 民生服务企业端 | 企业端相关 | ms_company_page |
| 决策指挥系统   | decision_command | 决策指挥系统 | 182.129.202.48 | decision_command_page |
| 默认       | population_map | 人口地图 | 未匹配任何路径 | population_map_page |

提取以下关键信息：
- `route_path`：页面路由路径
- `模块中文名`：如"项目管理"
- `实体中文名`：如"项目"
- `module_name`：模块英文标识（下划线风格），如 `community_office`、`project`
- `PageClassName`：页面对象类名（大驼峰），如 `CommunityOfficePage`、`ProjectPage`
- `ENTITY`：实体英文大写（数据常量前缀），如 `COMMUNITY_OFFICE`、`PROJECT`
- `NAME_FIELD`：名称字段，如 `community_office_name`、`project_name`
- `端目录`、`端中文名`：根据上表确定
- `page_fixture`：根据端类型确定

### 第六步：创建输出目录

如果目标目录不存在，先创建：

```bash
mkdir -p pages/{端目录}
mkdir -p datas/{端目录}
mkdir -p tests/{端目录}
```

### 第七步：生成页面对象

文件：`pages/{端目录}/{module_name}_page.py`

**页面对象结构**：参照模板文件 `files/templates/test_script_template.md`

1. **类定义与初始化**：
```python
class {PageClassName}(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.base_url = settings.{端类型}_side_url  # 如 population_map_side_url
        self.table_operate = TableOperate(page)
        self.dropdown_selector = DropdownSelector(page)
```

2. **定义 ROUTE_PATH 常量**：
```python
ROUTE_PATH: str = "/business/communityManagement/communityOffice"  # 从 record_operating_steps.py 获取
```

3. **元素选择器区域**（用 `# region` / `# endregion` 包裹）：
   - 弹窗标题常量：`DIALOG_TITLE_ADD`、`DIALOG_TITLE_EDIT`、`DIALOG_TITLE_DETAIL`（如果有）
   - 按钮：`BTN_*` 前缀，使用 lambda 定义（严格参考实际项目文件）
   - 表格操作：`TABLE_BODY_ROW`、`BTN_TABLE_EDIT`、`BTN_TABLE_DELETE`、`BTN_TABLE_DETAIL`
   - 搜索区域：`SEARCH_*` 前缀
   - 表单字段：`FORM_*` 前缀

4. **页面导航方法**：
```python
def page_open_url(self):
    """打开页面"""
    self.open_url(url=self.ROUTE_PATH)
    return self
```

5. **表单填充方法**：
```python
def fill_form_data(self, data: Dict) -> None:
    """
    批量填充新增/编辑表单，新增编辑复用定位器
    :param data: 表单键值对字典
    """
    # 对每个字段判断 if "field" in data and data["field"] is not None，再执行操作
    # 直接内联使用定位器，不通过 prefix 区分新增编辑
    # 严格参考实际项目文件中的实现方式
```

6. **submit_form 方法**：
```python
def submit_form(self, selector=None):
    """提交表单"""
    self.click(selector=selector, force=True)
    self.wait_for_load_state("domcontentloaded")
```

7. **业务操作方法**：
   - `search(search_data: Dict = None, timeout: int = 15000)`：搜索方法，返回数量
   - `add_data_operation(data: Dict)`：新增方法（点击新增、等待弹窗、填充表单）
   - `edit_first_row(edit_data: Dict)`：编辑第一行
   - `delete_first() -> bool`：删除第一行
   - `view_first_row_detail() -> None`：查看第一行详情
   - `get_form_field_values() -> dict`：获取表单字段值
   - `fill_search_fields(search_data: Dict) -> None`：填充搜索条件
   - `get_search_dropdown_locator_map() -> Dict`：获取搜索下拉定位器映射
   - `get_add_form_dropdown_locator_map() -> Dict`：获取新增表单下拉定位器映射
   - `wait_win_closed(dialog_name: str = None)`：等待弹窗关闭
   - `verify_search_fields_cleared(poll_timeout: int = 3000) -> list`：校验搜索条件已清空
   - `get_dropdown_options(dropdown_trigger_locator) -> list`：获取下拉框选项

### 第八步：生成测试数据

文件：`datas/{端目录}/{module_name}_data.py`

**数据结构**：参照模板文件 `files/templates/test_script_template.md` 和实际项目数据文件

1. **弹窗标题和期望常量**：
```python
{ENTITY}_NAME_FIELD = "{name_field}"
{ENTITY}_EXPECT_DIALOG_TITLE_ADD = "新增"
{ENTITY}_EXPECT_DIALOG_TITLE_EDIT = "编辑"
{ENTITY}_EXPECT_DIALOG_TITLE_DETAIL = "详情"
{ENTITY}_EXPECT_TABLE_HEADERS = [...]
{ENTITY}_EXPECT_DETAIL_FIELDS = [...]
{ENTITY}_EXPECT_FORM_PLACEHOLDERS = {{...}}
{ENTITY}_EXPECT_FORM_FIELD_LABELS = [...]
{ENTITY}_REQUIRED_FIELDS = [...]
{ENTITY}_TABLE_FIELD_MAPPING = {{...}}
{ENTITY}_DETAIL_FIELD_MAPPING = {{...}}
{ENTITY}_SEARCH_DROPDOWN_CONFIGS = [...]
{ENTITY}_ADD_FORM_DROPDOWN_CONFIGS = [...]
{ENTITY}_RESET_TEST_DATA = [...]
{ENTITY}_FIELD_LIMIT_CONFIG = [...]
{ENTITY}_INPUT_AUTO_CORRECTION_CONFIG = [...]
```

2. **新增测试数据** `{ENTITY}_ADD_TEST_DATA`：
   - 完整填写全部字段并提交
   - 只填写必填字段提交
   - 必填项不填写提交验证（期望失败）
   - 各种字段验证场景

3. **搜索测试数据** `{ENTITY}_SEARCH_TEST_DATA`：
   - 名称单条件精准搜索
   - 名称单条件模糊搜索
   - 组合条件搜索
   - 搜索不存在的数据

4. **编辑测试数据** `{ENTITY}_EDIT_TEST_DATA`：
   - 编辑全部字段
   - 编辑单字段
   - 编辑为空验证
   - 清空非必填字段

### 第九步：生成测试用例

文件：`tests/{端目录}/test_{module_name}.py`

**测试用例结构**：参照模板文件 `files/templates/test_script_template.md` 和实际项目测试文件

1. **测试类定义**：
```python
@allure.feature("{端中文名}-{模块中文名}")
class Test{PageClassName}(BaseCRUDTestTemplate):
    """{模块中文名}测试套件，覆盖正向/反向场景"""

    # region ====== 重写父类核心配置（必填） ======
    PAGE_CLASS = {PageClassName}  # 页面对象类
    ALLURE_FEATURE_NAME = "{端中文名}-{模块中文名}"  # allure feature名称

    ADD_TEST_DATA = {ENTITY}_ADD_TEST_DATA  # 新增测试数据
    SEARCH_TEST_DATA = {ENTITY}_SEARCH_TEST_DATA  # 搜索测试数据
    EDIT_TEST_DATA = {ENTITY}_EDIT_TEST_DATA  # 编辑测试数据

    EXPECT_TABLE_HEADERS = {ENTITY}_EXPECT_TABLE_HEADERS  # 表格预期列
    EXPECT_DETAIL_FIELDS = {ENTITY}_EXPECT_DETAIL_FIELDS  # 详情预期字段

    EXPECT_DIALOG_TITLE_ADD = {ENTITY}_EXPECT_DIALOG_TITLE_ADD  # 新增弹窗预期标题
    EXPECT_DIALOG_TITLE_EDIT = {ENTITY}_EXPECT_DIALOG_TITLE_EDIT  # 编辑弹窗预期标题
    EXPECT_DIALOG_TITLE_DETAIL = {ENTITY}_EXPECT_DIALOG_TITLE_DETAIL  # 详情弹窗预期标题

    EXPECT_FORM_PLACEHOLDERS = {ENTITY}_EXPECT_FORM_PLACEHOLDERS  # 新增表单默认提示
    EXPECT_FORM_FIELD_LABELS = {ENTITY}_EXPECT_FORM_FIELD_LABELS  # 新增表单字段标签
    REQUIRED_FIELDS = {ENTITY}_REQUIRED_FIELDS  # 新增表单必填项
    SEARCH_DROPDOWN_CONFIGS = {ENTITY}_SEARCH_DROPDOWN_CONFIGS  # 搜索下拉配置项
    ADD_FORM_DROPDOWN_CONFIGS = {ENTITY}_ADD_FORM_DROPDOWN_CONFIGS  # 新增表单下拉配置项
    RESET_TEST_DATA = {ENTITY}_RESET_TEST_DATA  # 重置测试数据
    FIELD_LIMIT_CONFIG = {ENTITY}_FIELD_LIMIT_CONFIG  # 输入框长度限制配置项
    INPUT_AUTO_CORRECTION_CONFIG = {ENTITY}_INPUT_AUTO_CORRECTION_CONFIG  # 输入框自动修正配置项

    TABLE_FIELD_MAPPING = {ENTITY}_TABLE_FIELD_MAPPING  # 表格字段映射配置
    DETAIL_FIELD_MAPPING = {ENTITY}_DETAIL_FIELD_MAPPING  # 详情字段映射配置

    NAME_FIELD = {ENTITY}_NAME_FIELD
    # 可选配置
    DYNAMIC_FIELDS = {{
        "id_card": fake_data.id_card(),
        "phone": fake_data.phone(),
    }}
    # endregion
```

2. **测试用例组织**：按照 story 分类
   - 全流程冒烟验证
   - 弹窗对话框交互验证
   - 新增表单规则与提交验证
   - 编辑表单回填与更新验证
   - 列表查询分页与表格交互验证
   - 详情弹窗字段显示验证
   - 删除操作逻辑验证

## 编码规范（严格遵循 - 基于实际项目）

⚠️ **核心优先原则（第0条）**：如果存在 `files/templates/record_operating_steps.py`，所有元素定位器必须优先使用录制代码中的内容，不得自行推断。特别注意：
   - `get_by_role()` 的 name 参数必须与录制一致
   - `nth()` 索引必须与录制一致
   - 下拉选择方式必须与录制一致

1. **测试数据全部用 Python 字典列表**，禁止 YAML/JSON
2. **每条测试数据必须包含 `type` 字段**（`POSITIVE`/`NEGATIVE`）
3. **页面对象必须继承 `BasePage`**，通过 `self.page` 访问 Playwright Page
4. **唯一数据用 `fake_data.random_4bit_str()`** 生成随机后缀
5. **异常测试使用 `expected_error_text` 列表或字符串**
6. **页面对象的按钮选择器使用 lambda 定义**：`BTN_ADD = lambda self: self.page.get_by_role("button", name="新增")  # noqa`
7. **页面对象的表单定位器可以定义为常量**，也可以直接内联在 `fill_form_data` 方法中使用
8. **页面对象方法内部判断 `if "field" in data and data["field"] is not None:` 再执行操作**
9. **URL导航统一使用 `page_open_url()` 方法**
10. **搜索操作前先点重置**：避免上一次搜索条件残留
11. **优先使用 `wait_for_load_state`/`wait_element_appear`/`wait_element_disappear`**，避免硬编码 `time.sleep()`
12. **测试类命名**：大驼峰，如 `TestCommunityServiceFacility`
13. **测试方法命名**：snake_case，如 `test_lifecycle_smoke`
14. **页面对象的方法名使用 snake_case 风格**
15. **测试类继承 `BaseCRUDTestTemplate`**，重写配置常量即可
16. **使用 `MARKER` 常量标记测试数据**，便于清理
17. **必须初始化 table_operate 和 dropdown_selector**：
    ```python
    self.table_operate = TableOperate(page)
    self.dropdown_selector = DropdownSelector(page)
    ```

## 输出文件清单

每个模块生成 3 个文件：

| 文件 | 路径 | 说明 |
|------|------|------|
| 页面对象 | `pages/{端目录}/{module_name}_page.py` | 继承 BasePage，封装选择器和操作方法 |
| 测试数据 | `datas/{端目录}/{module_name}_data.py` | Python 字典列表，参数化驱动 |
| 测试用例 | `tests/{端目录}/test_{module_name}.py` | pytest + allure + BaseCRUDTestTemplate |

## ⚠️ 最后验证（必须完成）

1. **验证定位器优先级（最重要）**：
   - 如果存在 files/templates/record_operating_steps.py，检查生成的页面对象中的定位器是否优先使用了录制的定位器模式
   - 特别检查 get_by_role 的使用顺序、nth() 索引是否与录制一致

2. **Python 语法检查**：使用 Python 语法检查生成的文件：`python -m py_compile file.py`

3. **检查导入语句是否正确**

4. **检查命名是否符合规范**

5. **向用户报告生成的文件清单**，并明确说明：
   - 是否使用了 files/templates/record_operating_steps.py 中的定位器
   - 哪些定位器是从录制代码中提取的
