# data-testid 命名规范

> 适用范围:业务前端开发(生产 testid)与 E2E 测试工具链(explore-site 探索 / collect_testids.py 采集 / test-script-generate-standalone 脚本生成消费)。
> 工具链对 testid 的定位策略是**优先匹配真实 data-testid,缺失时回退语义定位器**。本规范保证 testid 命中率与定位稳定性,遵守规范 = 测试脚本质量上限最高。

## 一、硬性规则(MUST,违反即缺陷)

| # | 规则 | 说明 |
|---|------|------|
| 1 | **全小写 kebab-case**,格式 `^[a-z0-9]+(-[a-z0-9]+)*$` | 单词间用 `-` 分隔,禁止 camelCase/snake_case/中文/空格/大写 |
| 2 | **页面内唯一** | 同一 route_path 下不允许出现重复 testid;`collect_testids.py` 会自动检出重复项 |
| 3 | **禁止动态/随机值** | 禁止编译器生成的 hash(如 `css-x7f2a`)、时间戳、自增 id、UUID 等刷新后会变化的值;长十六进制串会被 lint 标记为疑似动态 |
| 4 | **表达业务语义,不表达实现** | 用 `user-name-input` 而非 `input-1`;语义与页面可见文案/placeholder 同源,便于工具按 label/placeholder 反查 |

## 二、推荐结构(SHOULD)

### 2.1 通用模式:`{语义}-{控件类型}`

| 控件类型 | 后缀/惯例 | 示例 |
|----------|-----------|------|
| 文本/数字输入框 | `-input` / `-textarea` | `user-name-input`、`remark-textarea` |
| 下拉选择 | `-select` | `district-select` |
| 级联选择 | `-cascader` | `region-cascader` |
| 单选(每选项一个) | `-radio-{选项}` | `gender-radio-yes` / `gender-radio-no` |
| 多选组容器 | `-checkbox-group` | `hobby-checkbox-group` |
| 多选选项 | `-checkbox-{选项}` | `hobby-checkbox-basketball` |
| 日期选择器 | `-date-picker`(挂在 el-date-editor 外层容器) | `birth-date-picker` |
| 数字输入 | `-input` | `count-input` |
| 开关 | `-switch` | `enable-switch` |
| 上传 | `-upload`(挂组件容器) | `attachment-upload` |
| 按钮 | `-btn` | `search-btn`、`reset-btn`、`add-btn` |
| 分页容器 | `pagination`(内部控件用子选择器,不逐个加) | `data-testid="pagination"` |
| Tab 容器/标签 | `-tabs` / `tab-{页签名}` | `detail-tabs` / `tab-basic` |
| 表格/表头 | `data-table` / `col-{字段名}` | `data-table` / `col-title` |
| 富文本 | `-editor`(挂**外层容器**,内部 contenteditable 由工具处理) | `content-editor` |

### 2.2 弹窗内元素:加弹窗/功能前缀

- 弹窗内按钮建议带弹窗语义前缀,如 `add-dialog-confirm-btn`、`edit-dialog-cancel-btn`
- 同页面存在多套同语义控件(如多处"确定"按钮)时,**必须**用前缀区分

### 2.3 组容器与选项的分层

- testid 标在组容器上时,选项通过容器+文本子选择器定位:
  `[data-testid="gender-radio"] .el-radio:has-text("是")`
- testid 直接标在选项上时,每选项一个:`[data-testid="gender-radio-yes"]`
- 二选一即可,不要混用造成冗余

## 三、特殊控件注意事项(与工具链约定)

| 控件 | 约定 |
|------|------|
| 日期选择器 | testid 挂在 `el-date-editor` **外层 div**,内部 input 由测试工具 `date_input()` 自动处理 |
| 富文本编辑器 | testid 挂在**外层容器**(如 el-form-item 的 div),内部 `[contenteditable=true]` 由工具 `rich_text()` 处理 |
| 下拉选项面板 | 面板通常渲染在 body 下(`el-select-dropdown`),**无需**给每个选项加 testid,工具按可见弹层+文本定位 |
| 只读展示字段 | 非交互元素**不必**加 testid,避免噪声;仅交互元素与断言目标需要 |

