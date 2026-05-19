---
name: e2e-pipeline
description: E2E测试用例生成流水线 - 依次执行需求拆分→测试点提取→测试点评审→用例生成→导出Excel，每步独立子会话
triggers:
  - "E2E流水线"
  - "全流程"
  - "一键生成"
  - "端到端"
---

# E2E测试用例生成流水线

按顺序自动执行完整的测试用例生成流程，每个步骤在独立子会话（Agent）中运行，避免上下文过长。

## 执行顺序

1. **需求拆分** (requirement-split)
2. **测试点提取** (test-point-extract)
3. **测试点评审** (test-point-review)
4. **用例生成** (test-case-generate)
5. **导出Excel** (export-excel)

## 核心规则：每步独立子会话

每个步骤必须使用 Agent 工具开启独立子会话执行，**禁止**在主会话中直接执行技能逻辑。

### 子会话配置

- `subagent_type`: `"general-purpose"`
- 每个子会话的 prompt 必须包含：
  1. 要求子会话先读取对应技能的 SKILL.md 获取完整处理规则
  2. 明确告知输入文件路径，要求子会话读取该文件作为输入
  3. 明确要求将结果写入指定的输出文件
  4. 工作目录：`.`

### 子会话 prompt 模板

每个子会话的 prompt 按以下模板构建：

```
请按以下要求执行任务：

1. 先读取技能定义文件：{SKILL.md路径}，理解其中的处理规则和输出格式
2. 读取输入文件：{输入文件路径}
{如有参考文件}3. 读取参考文件：{参考文件路径}
4. 严格按照技能定义的处理规则处理输入内容
5. 将结果写入输出文件：{输出文件路径}（如目录不存在则先创建）
```

## 各步骤详细配置

### 步骤1：需求拆分

- **技能文件**：`.claude/skills/requirement-split/SKILL.md`
- **输入**：用户提供的需求数据（流水线启动时传入的内容）
- **输出文件**：`./output/{当前日期}/功能点列表.md`

子会话 prompt 示例：
```
请按以下要求执行任务：

1. 先读取技能定义文件：./.claude/skills/requirement-split/SKILL.md，理解其中的处理规则和输出格式
2. 对以下需求内容进行拆分：

{用户传入的需求内容}

3. 严格按照技能定义的处理规则处理
4. 将结果写入输出文件：./output/{当前日期}/功能点列表.md（如目录不存在则先创建）
```

### 步骤2：测试点提取

- **技能文件**：`.claude/skills/test-point-extract/SKILL.md`
- **输入文件**：`./output/{当前日期}/功能点列表.md`（步骤1产出）
- **参考文件**：`./referenceDocument/testPointsRequirement.md`
- **输出文件**：`./output/{当前日期}/测试点清单.md`

子会话 prompt：
```
请按以下要求执行任务：

1. 先读取技能定义文件：./.claude/skills/test-point-extract/SKILL.md，理解其中的处理规则和输出格式
2. 读取输入文件：./output/{当前日期}/功能点列表.md
3. 读取参考文件：./referenceDocument/testPointsRequirement.md
4. 严格按照技能定义的处理规则，基于功能点列表和参考文件提取测试点
5. 将结果写入输出文件：./output/{当前日期}/测试点清单.md（如目录不存在则先创建）
```

### 步骤3：测试点评审

- **技能文件**：`.claude/skills/test-point-review/SKILL.md`
- **输入文件**：`./output/{当前日期}/测试点清单.md`（步骤2产出）、`./output/{当前日期}/功能点列表.md`（步骤1产出）
- **参考文件**：`./referenceDocument/testPointsRequirement.md`
- **输出文件**：`./output/{当前日期}/测试点评审报告.md`

子会话 prompt：
```
请按以下要求执行任务：

1. 先读取技能定义文件：./.claude/skills/test-point-review/SKILL.md，理解其中的处理规则和输出格式
2. 读取输入文件：./output/{当前日期}/测试点清单.md
3. 读取功能点列表用于交叉比对：./output/{当前日期}/功能点列表.md
4. 读取参考文件：./referenceDocument/testPointsRequirement.md
5. 严格按照技能定义的处理规则进行评审
6. 将结果写入输出文件：./output/{当前日期}/测试点评审报告.md（如目录不存在则先创建）
```

### 步骤4：用例生成

- **技能文件**：`.claude/skills/test-case-generate/SKILL.md`
- **输入文件**：`./output/{当前日期}/测试点清单.md`（步骤2产出）
- **参考文件**：`./referenceDocument/testPointsRequirement.md`
- **输出文件**：`./output/{当前日期}/测试用例.md`

子会话 prompt：
```
请按以下要求执行任务：

1. 先读取技能定义文件：./.claude/skills/test-case-generate/SKILL.md，理解其中的处理规则和输出格式
2. 读取输入文件：./output/{当前日期}/测试点清单.md
3. 读取参考文件：./referenceDocument/testPointsRequirement.md
4. 严格按照技能定义的处理规则，基于测试点清单和参考文件生成测试用例
5. 将结果写入输出文件：./output/{当前日期}/测试用例.md（如目录不存在则先创建）
```

### 步骤5：导出Excel

- **技能文件**：`.claude/skills/export-excel/SKILL.md`
- **输入文件**：`./output/{当前日期}/测试用例.md`（步骤4产出）
- **输出文件**：`./output/{当前日期}/testcases_{日期}.xlsx`

子会话 prompt：
```
请按以下要求执行任务：

1. 先读取技能定义文件：./.claude/skills/export-excel/SKILL.md，理解其中的处理规则和输出格式
2. 读取输入文件：./output/{当前日期}/测试用例.md
3. 严格按照技能定义的处理规则，将测试用例导出为Excel文件
4. 将结果写入输出文件：./output/{当前日期}/testcases_{当前日期}.xlsx
```

## 流程控制规则

1. **顺序执行**：步骤1→2→3→4→5 严格按顺序执行，不可并行
2. **检查点**：每个步骤完成后，检查输出文件是否成功生成再启动下一步骤
3. **失败处理**：如果某步骤失败或输出文件未生成，停止流水线并向用户报告错误
4. **进度报告**：每个步骤开始前向用户报告当前进度，格式如：`正在执行步骤 2/5：测试点提取...`
5. **评审拦截**：步骤3（测试点评审）完成后，读取评审报告：
   - 如评审结论为"需修改"：暂停流水线，将问题清单展示给用户，询问是否继续执行后续步骤
   - 如评审结论为"通过"：继续执行步骤4
6. **完成报告**：全部步骤完成后，向用户汇报流水线执行结果，列出所有输出文件路径
