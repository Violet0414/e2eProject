---
name: explore-pipeline
description: 页面探索用例生成流水线 - 依次执行页面探索→探索转用例，每步独立子会话
triggers:
  - "探索流水线"
  - "探索流程"
  - "探索生成用例"
  - "页面探索用例"
---

# 页面探索用例生成流水线

按顺序自动执行页面探索和测试用例生成流程，每个步骤在独立子会话（Agent）中运行，避免上下文过长。

## 执行顺序

1. **页面探索** (explore-site)
2. **探索转用例** (generate-testcases-from-explore)

## 核心规则：每步独立子会话

每个步骤必须使用 Agent 工具开启独立子会话执行，**禁止**在主会话中直接执行技能逻辑。

### 子会话配置

- `subagent_type`: `"general-purpose"`
- 每个子会话的 prompt 必须包含：
  1. 要求子会话先读取对应技能的 SKILL.md 获取完整处理规则
  2. 明确告知输入信息（页面URL、登录凭据等）
  3. 明确要求将结果写入指定的输出文件
  4. 工作目录：`/home/mxr/e2eProject`

### 子会话 prompt 模板

每个子会话的 prompt 按以下模板构建：

```
请按以下要求执行任务：

1. 先读取技能定义文件：{SKILL.md路径}，理解其中的处理规则和输出格式
2. {根据步骤类型提供输入信息}
{如有参考文件}3. 读取参考文件：{参考文件路径}
4. 严格按照技能定义的处理规则执行
5. 将结果写入输出文件：{输出文件路径}（如目录不存在则先创建）
```

## 各步骤详细配置

### 步骤1：页面探索

- **技能文件**：`.claude/skills/explore-site/SKILL.md`
- **输入**：用户提供的页面URL（流水线启动时传入）、登录凭据（可选）
- **参考文件**：`./referenceDocument/testPointsRequirement.md`
- **输出目录**：`./exploreOutput/{当前日期}_{当前时间}/`
- **输出文件**：`./exploreOutput/{当前日期}_{当前时间}/explore_record.md`

子会话 prompt 示例：
```
请按以下要求执行任务：

1. 先读取技能定义文件：/home/mxr/e2eProject/.claude/skills/explore-site/SKILL.md，理解其中的处理规则和输出格式
2. 对以下页面进行探索：
   - 页面URL：{用户传入的页面URL}
   - 登录凭据：{用户传入的账号密码，如无则不填}
3. 读取参考文件：/home/mxr/e2eProject/referenceDocument/testPointsRequirement.md
4. 严格按照技能定义的处理规则执行页面探索，包括：
   - 初始化：创建输出目录，打开浏览器导航到目标页面
   - 主页面探索：列表查询、列表数据、列表翻页、列表操作、接口监测
   - 跳转子会话探索：新增/编辑/详情表单页
5. 将探索记录写入输出文件：/home/mxr/e2eProject/exploreOutput/{当前日期}_{当前时间}/explore_record.md（如目录不存在则先创建）
```

### 步骤2：探索转用例

- **技能文件**：`.claude/skills/generate-testcases-from-explore/SKILL.md`
- **输入文件**：`./exploreOutput/{日期时间文件夹}/explore_record.md`（步骤1产出）
- **参考文件**：`./referenceDocument/用例模板.xlsx`、`./referenceDocument/testPointsRequirement.md`
- **输出文件**：`./exploreOutput/{日期时间文件夹}/{时间戳}_测试用例.xlsx`

子会话 prompt：
```
请按以下要求执行任务：

1. 先读取技能定义文件：/home/mxr/e2eProject/.claude/skills/generate-testcases-from-explore/SKILL.md，理解其中的处理规则和输出格式
2. 读取输入文件：/home/mxr/e2eProject/exploreOutput/{日期时间文件夹}/explore_record.md
3. 读取用例模板：/home/mxr/e2eProject/referenceDocument/用例模板.xlsx
4. 读取参考文件：/home/mxr/e2eProject/referenceDocument/testPointsRequirement.md
5. 严格按照技能定义的处理规则，基于探索记录和参考文件生成测试用例
6. 将测试用例导出为Excel文件：/home/mxr/e2eProject/exploreOutput/{日期时间文件夹}/{时间戳}_测试用例.xlsx
```

## 流程控制规则

1. **顺序执行**：步骤1→2 严格按顺序执行，不可并行
2. **检查点**：步骤1完成后，检查 `explore_record.md` 是否成功生成再启动步骤2
3. **失败处理**：如果某步骤失败或输出文件未生成，停止流水线并向用户报告错误
4. **进度报告**：每个步骤开始前向用户报告当前进度，格式如：`正在执行步骤 1/2：页面探索...`
5. **探索确认**：步骤1（页面探索）完成后，向用户展示探索记录摘要（页面标题、探索模块数、字段数等），询问是否继续生成用例：
   - 用户确认继续：执行步骤2
   - 用户要求补充探索：根据用户反馈补充探索后重新确认
6. **完成报告**：全部步骤完成后，向用户汇报流水线执行结果，列出所有输出文件路径
