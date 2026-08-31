---
name: export-excel
description: 导出Excel - 将结构化测试用例导出为.xlsx文件，符合公司模板格式
triggers:
  - "导出Excel"
  - "导出用例"
  - "生成Excel"
  - "导出xlsx"
---

# 导出Excel

将结构化测试用例导出为 .xlsx 文件，符合公司模板格式。

## 输入

- 结构化测试用例（通常由"用例生成"技能产出）
- 可选：公司模板文件路径（默认使用 `./files/templates/用例模板.xlsx`，如用户指定则优先使用用户指定的路径）

## 处理规则

1. **确认Python环境**：检查是否安装了 `openpyxl` 库，未安装则先安装
2. **确定输出路径**：默认输出到 `./output/{当前日期}/{时间戳}_测试用例.xlsx`
3. **模板使用规则**（重要！）：
   - 模板文件（`./files/templates/用例模板.xlsx`）必须是**空白模板**，只包含表头和格式
   - 如模板中存在旧数据，**必须在写入新数据前清空所有旧数据**，只保留表头格式
   - 如无法确认模板是否干净，**优先创建全新工作簿**，而不是加载模板
4. **文本清理规则**：
   - 先处理HTML实体编码：`&lt;` → `<`，`&gt;` → `>`
   - 将所有 `<br>`、`<br/>` 替换为换行符
   - 移除多余转义字符：`\"` → `"`，`\\'` → `'`
   - 保留正常的步骤和预期结果格式
4. **默认表头格式**（如无模板或创建新文件时使用）：

| 列 | 表头名 | 说明 |
|----|--------|------|
| A  | 用例ID | TC-XXX-NNN |
| B  | 用例标题 | 不超过30字 |
| C  | 关联测试点 | TP编号 |
| D  | 所属产品 | 产品名称 |
| E  | 所属模块 | 功能模块名 |
| F  | 优先级 | P0/P1/P2 |
| G  | 前置条件 | 执行前需满足的条件 |
| H  | 操作步骤 | 具体操作描述（含步骤编号 1. xxx） |
| I  | 预期结果 | 期望的输出/状态 |

### 格式要求

- 表头行：加粗、居中、浅蓝底色
- 列宽自适应内容
- 用例之间用细边框分隔
- 每个用例一行，不拆分成多行
- 操作步骤保留原始的 "1. xxx\n2. xxx" 格式
- Sheet名称：`测试用例`

## 执行步骤

1. 解析输入的测试用例数据
2. 如用户提供模板路径，读取模板获取格式
3. 生成 .xlsx 文件到指定路径
4. 输出文件路径给用户确认

## 输出

- 文件路径：`./output/{当前日期}/testcases_{日期}.xlsx`
- 统计信息：用例总数、模块分布

## 注意事项

- 文件已存在时询问用户是否覆盖
- 导出完成后提示用户文件位置
- 如测试用例数据格式不符预期，提示用户先通过"用例生成"技能规范化

## 参考实现代码

以下是 `export_excel.py` 的完整实现模板：

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
导出测试用例到Excel
"""
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    from openpyxl import load_workbook, Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
except ImportError:
    print("正在安装openpyxl库...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "openpyxl"])
    from openpyxl import load_workbook, Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter


def clean_text(text):
    """清理文本中的换行标签和多余斜杠"""
    if not text:
        return text
    # 先处理HTML实体编码（如 &lt;br&gt; -> <br>）
    text = text.replace('&lt;', '<').replace('&gt;', '>')
    # 替换 <br> 为换行符
    text = re.sub(r'<br\s*/?>', '\n', text)
    # 移除多余的转义斜杠（如 \" -> "）
    text = text.replace('\\"', '"').replace("\\'", "'")
    return text.strip()


def parse_markdown_test_cases(md_file):
    """解析Markdown格式的测试用例"""
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()

    test_cases = []

    # 分割成模块
    module_pattern = r'### ([^\n]+)\s*\n([\s\S]*?)(?=### |$)'
    modules = re.findall(module_pattern, content)

    for module_name, module_content in modules:
        module_name = module_name.strip()

        # 查找表格
        table_pattern = r'\| 用例编号[^\n]*\n([\s\S]*?)(?=\n\n|\n---|\n## |$)'
        tables = re.findall(table_pattern, module_content)

        for table in tables:
            # 解析表格行
            rows = [row.strip() for row in table.split('\n') if row.strip() and '|' in row]

            for row in rows:
                # 跳过分隔行
                if re.match(r'^\|[\-\s:]+\|$', row.replace(' ', '')):
                    continue

                cells = [cell.strip() for cell in row.split('|') if cell.strip()]

                if len(cells) >= 8:
                    case_id = cells[0]
                    route_path = cells[1] if len(cells) > 1 else ''
                    product = cells[2] if len(cells) > 2 else '决策指挥系统'
                    module = cells[3] if len(cells) > 3 else module_name
                    title = cells[4] if len(cells) > 4 else ''
                    precondition = cells[5] if len(cells) > 5 else ''
                    steps = cells[6] if len(cells) > 6 else ''
                    expected = cells[7] if len(cells) > 7 else ''

                    # 确定优先级
                    priority = 'P1'  # 默认
                    if '重要' in title or '关键' in title:
                        priority = 'P0'
                    elif '边缘' in title or '异常' in title:
                        priority = 'P2'

                    # 提取关联测试点（如果有）
                    tp_match = re.search(r'TP\-\d+', title)
                    related_tp = tp_match.group(0) if tp_match else ''

                    test_cases.append({
                        'id': case_id,
                        'title': title,
                        'related_tp': related_tp,
                        'product': product,
                        'module': module,
                        'priority': priority,
                        'precondition': clean_text(precondition),
                        'steps': clean_text(steps),
                        'expected': clean_text(expected)
                    })

    return test_cases


def export_to_excel(test_cases, template_file, output_file):
    """导出到Excel - 始终创建干净的新文件，避免旧数据污染"""

    # 策略：优先创建全新的工作簿，而不是使用可能有旧数据的模板
    wb = Workbook()
    ws = wb.active
    ws.title = "测试用例"

    # 定义样式
    header_font = Font(name='微软雅黑', size=11, bold=True, color='FFFFFF')
    header_fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
    header_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    thin_border = Border(
        left=Side(style='thin', color='CCCCCC'),
        right=Side(style='thin', color='CCCCCC'),
        top=Side(style='thin', color='CCCCCC'),
        bottom=Side(style='thin', color='CCCCCC')
    )
    cell_alignment = Alignment(horizontal='left', vertical='top', wrap_text=True)

    # 创建表头
    headers = ['用例ID', '用例标题', '关联测试点', '所属产品', '所属模块', '优先级', '前置条件', '操作步骤', '预期结果']
    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(1, col_idx, header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = thin_border

    # 填充数据 - 每个用例一行
    current_row = 2
    for case in test_cases:
        ws.cell(current_row, 1, case['id'])
        ws.cell(current_row, 2, case['title'])
        ws.cell(current_row, 3, case['related_tp'])
        ws.cell(current_row, 4, case['product'])
        ws.cell(current_row, 5, case['module'])
        ws.cell(current_row, 6, case['priority'])
        ws.cell(current_row, 7, case['precondition'])
        ws.cell(current_row, 8, case['steps'])
        ws.cell(current_row, 9, case['expected'])

        # 应用样式
        for col_idx in range(1, 10):
            cell = ws.cell(current_row, col_idx)
            cell.alignment = cell_alignment
            cell.border = thin_border

        current_row += 1

    # 调整列宽
    for col_idx in range(1, 10):
        max_length = 0
        column = get_column_letter(col_idx)
        for row_idx in range(1, current_row):
            cell = ws.cell(row_idx, col_idx)
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 60)
        ws.column_dimensions[column].width = adjusted_width

    # 保存文件
    wb.save(output_file)
    print(f"[OK] 成功导出 {len(test_cases)} 条测试用例到: {output_file}")

    return len(test_cases)


def main():
    # 设置路径
    base_dir = Path(__file__).parent
    output_dir = base_dir / 'output' / datetime.now().strftime('%Y-%m-%d')
    output_dir.mkdir(parents=True, exist_ok=True)

    # 查找最新的测试用例文件
    md_files = list(output_dir.glob('完整测试用例.md'))
    if not md_files:
        md_files = list(output_dir.glob('测试用例*.md'))
    if not md_files:
        print("[ERROR] 未找到测试用例.md文件")
        return

    md_file = md_files[0]  # 使用第一个
    print(f"[INFO] 读取测试用例文件: {md_file}")

    # 解析测试用例
    test_cases = parse_markdown_test_cases(md_file)
    print(f"[INFO] 解析到 {len(test_cases)} 条测试用例")

    # 模板文件（保留引用但不再实际使用，为了向后兼容）
    template_file = base_dir / 'files/templates' / '用例模板.xlsx'

    # 输出文件
    timestamp = datetime.now().strftime('%H%M%S')
    output_file = output_dir / f'testcases_{datetime.now().strftime("%Y%m%d")}_{timestamp}.xlsx'

    # 导出
    count = export_to_excel(test_cases, template_file, output_file)

    # 统计模块分布
    module_stats = {}
    for case in test_cases:
        module = case['module'].split('-')[0]
        module_stats[module] = module_stats.get(module, 0) + 1

    print("\n[STATS] 用例统计:")
    for module, cnt in sorted(module_stats.items(), key=lambda x: -x[1]):
        print(f"  - {module}: {cnt}条")
    print(f"  总计: {count}条")


if __name__ == '__main__':
    main()
```
