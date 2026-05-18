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

将测试用例.md转化为符合ms-service-playwright框架规范的自动化测试脚本。

## 输入

- **测试用例.md**：位于 `./output/{当前日期}/测试用例.md`，包含结构化测试用例
- **测试脚本模板**：`./referenceDocument/testScriptTemplate.md`，定义脚本编写规范
- **输出目录**：`./output/{当前日期}/`（"当前日期"格式为YYYY-MM-DD，如2026-05-15）

## 输出文件结构

每个模块生成3个文件：

| 序号 | 文件 | 路径 |
|------|------|------|
| 1 | 页面对象 | `output/{当前日期}/pages/{module_name}.py` |
| 2 | 测试数据 | `output/{当前日期}/datas/{module_name}_data.py` |
| 3 | 测试用例 | `output/{当前日期}/tests/{end}/test_{module_name}.py` |

## 处理流程

### 第一步：读取测试用例文件

读取 `./output/{当前日期}/测试用例.md`，解析用例表格，提取：
- 模块路径（用于确定端类型和菜单结构）
- 用例编号、名称、步骤、预期
- 用例类型（正向/反向/UI验证）

### 第二步：读取模板文件

读取 `./referenceDocument/testScriptTemplate.md`，确认：
- 页面对象类结构和方法签名
- 测试数据字典必填字段
- 测试用例参数化模式
- 编码规范和断言工具使用

### 第三步：创建输出目录

```bash
mkdir -p output/{当前日期}/pages
mkdir -p output/{当前日期}/datas
mkdir -p output/{当前日期}/tests/admin  # 或 enterprise/citizen
```

### 第四步：生成页面对象

文件：`output/{当前日期}/pages/{module_name}.py`

根据模板中的 `pages/{module_name}.py` 模板生成，需要：
1. 继承 BasePage
2. 定义菜单选择器（PARENT_MENU, SUB_MENU）
3. 定义按钮、表单、列表选择器
4. 实现 goto_module()、search() 等基础方法
5. 根据用例中的操作步骤，实现对应的业务方法

**渐进式生成策略**：
- 先读取用例，识别所有需要的方法（如 add_case, edit_case, assign_case 等）
- 每个方法单独实现，避免上下文过长

### 第五步：生成测试数据

文件：`output/{当前日期}/datas/{module_name}_data.py`

根据模板中的 `datas/{module_name}_data.py` 模板生成：
1. 按功能模块组织测试数据（如 TEXT_UNIFY_DATA, FIELD_VERIFY_DATA 等）
2. 每条数据包含必填字段：
   - `title`: 用例中文标题
   - `type`: positive/negative/smoke
   - `expect_success` 或 `expect_count`: 预期结果
3. 业务字段从用例的测试数据中提取

**渐进式生成策略**：
- 按用例模块分组，每组单独生成数据
- 使用时间戳或随机数保证数据唯一性

### 第六步：生成测试用例

文件：`output/{当前日期}/tests/{end}/test_{module_name}.py`

根据模板中的 `tests/{end}/test_{module_name}.py` 模板生成：
1. 使用 pytest.mark.parametrize 装饰器
2. 按功能模块组织测试类
3. 每个测试方法对应一条用例
4. 使用 AssertUtils 进行断言

**渐进式生成策略**：
- 按功能模块分批生成测试方法
- 每批不超过20个测试方法
- 使用 class 组织相关测试

## 用例类型映射

| 用例类型 | 测试数据type | 断言方式 |
|----------|-------------|----------|
| UI验证类 | smoke | 验证元素存在/文本正确 |
| 正向操作类 | positive | expect_success=True |
| 反向操作类 | negative | expect_success=False |

## 菜单路径与端类型映射

根据模块路径判断：

| 路径关键词 | 端类型 | fixture | 输出目录 |
|-----------|--------|---------|----------|
| 民生服务管理后台 | admin | admin_page | tests/admin/ |
| 企业管理 | enterprise | enterprise_page | tests/company/ |
| 市民服务 | citizen | citizen_page | tests/citizen/ |

## 渐进式读取策略

为防止上下文过长导致生成效果不理想，采用以下策略：

1. **用例分段读取**：将测试用例按功能模块分段处理
2. **方法独立实现**：页面对象中的每个方法独立实现
3. **数据分组生成**：测试数据按功能模块分组
4. **测试方法分批**：每批测试方法不超过20个

## 编码规范

1. 测试数据全部用 Python 字典列表，禁止 YAML/JSON
2. 每条测试数据必须包含 `type` 字段
3. 页面对象必须继承 BasePage
4. 唯一数据用时间戳后缀：`f"_{int(time.time())}"`
5. 操作前先点"重置"按钮
6. 使用 AssertUtils 断言
7. 弹窗清理用 ESC 键循环关闭

## 注意事项

- 用例ID与测试方法名对应：如 TC-CASE-001 → test_tc_case_001
- 如果用例过于复杂或缺少关键信息，先列出疑问向用户确认
- 生成后统计产出文件数量和用例数量
- 页面对象的方法名使用 snake_case 风格
- fixture 选用根据端类型确定

## 持久化

- 所有生成的文件输出到 `./output/{当前日期}/` 目录
- 目录结构：
  ```
  output/{当前日期}/
  ├── pages/
  │   └── {module_name}.py
  ├── datas/
  │   └── {module_name}_data.py
  └── tests/
      └── {end}/
          └── test_{module_name}.py
  ```
