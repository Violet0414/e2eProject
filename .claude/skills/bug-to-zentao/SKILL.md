---
name: bug-to-zentao
description: 禅道Bug自动录入 - 解析测试报告.md（test-script-run-collect产出）收集未通过用例，自动分拣真实缺陷/脚本问题，按《bug提交规范V1.0》构建bug（标题/截图/重现步骤/结果/预期/严重程度/优先级），dry-run确认后批量录入禅道。指派人固定为禅道当前登录人。复用 ~/.config/zentao/zentao.json 已存token，用例走 npx zentao-cli bug create --data
triggers:
  - "提bug"
  - "提禅道bug"
  - "录禅道bug"
  - "提交bug到禅道"
  - "bug录入禅道"
  - "失败用例提bug"
---

# 禅道Bug自动录入 (bug-to-zentao)

解析测试报告中的失败用例，按《bug提交规范V1.0》自动构建 bug 并录入禅道。

**重要**：写共享系统，**必须先 dry-run 展示全部提交草稿并经用户勾选确认，才可实际创建**。

## 输入

- **测试报告.md 路径**（用户提供；未提供时默认扫描 `generated_scripts/` 下最新批次的 `测试报告.md`，注意可能位于 `/mnt/e/e2eProject` 或本机路径）。
- 补充数据源：报告同目录 `results.json`（jsonl 格式，含完整 traceback）——脚本自动读取，无需用户干预。

## 关键事实与踩坑（务必先读）

| # | 事实 | 影响 |
|---|------|------|
| 1 | `bug create` 走 `npx zentao-cli bug create --data '<完整JSON>'`（POST /bugs） | 顶层键传参不被解析的问题与 testcase 相同，**必须 `--data` 传完整 JSON** |
| 2 | bug 必填：`productID`、`title`、`openedBuild`（trunk 或版本ID） | openedBuild 默认 `trunk` |
| 3 | `steps` 是**单个富文本字段**（非数组），支持 HTML（`<br>`/`<b>`/`<img>`） | 按规范用 `[前置条件]/[重现步骤]/[结果]/[期望]` 四段拼装 |
| 4 | 截图上传走原生 API：`POST /api.php/v1/files`，multipart 字段名**必须是 `imgFile`**（用 `file`/`files` 会误报"文件格式不在规定范围内"，实际是字段名不对）；zentao-cli file 模块确实无上传命令 | 见步骤7上传流程（已实测可用） |
| 5 | token 认证：统一 `Token: <token>` 头；优先复用 `~/.config/zentao/zentao.json` 已存 token，失效（`Unauthorized`）才重新登录 | 与 import-to-zentao 同一套，勿重复索要密码 |
| 6 | 测试报告的失败 ≠ 全是 bug | 必须先分拣：脚本问题（timeout/locator等待/503/网络错误）默认排除 |
| 7 | `severity`/`pri` 均为 1~4，**禅道 1 最大**；规范中两者对照基本一致 | 默认 sev=pri，特殊场景用户可单独调 |
| 8 | bug 类型枚举：codeerror代码错误/config配置/install部署/security安全/performance性能/standard规范/automation测试脚本/designdefect设计缺陷/others其他 | 默认 `codeerror` |
| 9 | 指派人 | **固定挂载禅道当前登录人**（zentao.json 的 account），不询问用户；`--data` 中 `assignedTo` 传该账号 |
| 10 | 新版测试报告（test-script-run-collect）执行结果表已含 `bug标题/重现步骤/结果/预期/严重程度/优先级/截图` 列（失败行填充、通过行"-"） | `build_bug_payload.py` 优先直接取用报告列：标题/步骤/预期原样复用、级别已按用例优先级映射（高→1/中→2/低→3）；**旧格式报告**（无这些列）自动降级为按用例名称拼接并自行判级 |
| 11 | `--data @文件` 语法**不被 zentao-cli 支持**，且失败时 stdout 为空、不报错（2026-09-16 实测 29 条全部静默失败） | 落盘后必须用 `--data "$(cat /tmp/bug_N.json)"`；**成功判定必须从返回 JSON 中解析到 `"id"`**，stdout 为空即失败 |
| 12 | steps 中截图 `img src` 必须用 **PATH_INFO 格式** `<baseUrl>/file-read-<fileID>.png`；GET 格式 `index.php?m=file&f=read&t=png&fileID=N` 浏览器端会因权限校验被重定向导致裂图；base64 data URI 内嵌会被编辑器过滤剥掉，**embed 模式不可用** | 步骤7 只用直传 + PATH_INFO 回填一种方式 |
| 13 | `npx zentao-cli bug <id>` 详情接口把 steps 的 HTML **转成 markdown 转义文本展示**（`<b>`→`**`、`[x]`→`\[x\]`），仅是展示层转换，存储仍是 HTML（curl GET /bugs/{id} 可验证） | ① 判断存储格式必须 curl 直查 v1 API；② **禁止把 CLI 详情取回的 steps 再 update 回去**（会把 markdown 字面量存库，页面显示源码） |

## 执行流程

### 步骤1 认证（复用已有 token）
1. 读已存 token（注意 baseUrl 字段名是 **`server`**，不是 baseUrl/url）：
   ```
   TOKEN=$(python3 -c "import json;d=json.load(open('$HOME/.config/zentao/zentao.json'));print(d['profiles'][0]['token'])")
   ACCOUNT=$(python3 -c "import json;d=json.load(open('$HOME/.config/zentao/zentao.json'));print(d['profiles'][0]['account'])")
   BASEURL=$(python3 -c "import json;d=json.load(open('$HOME/.config/zentao/zentao.json'));print(d['profiles'][0]['server'])")
   ```
2. 验证有效性：`curl -sk "<baseUrl>/api.php/v1/products?limit=1" -H "Token: $TOKEN"`，返回 JSON 即有效。
3. 失效（`Unauthorized`）→ 请用户在输入框执行 `! npx zentao-cli login -s <baseUrl> -u <账号> -p <密码>` 重新登录；**密码错误不要反复试**。

### 步骤2 解析报告 + 构建 bug 草稿
```
python3 "<本skill目录>/build_bug_payload.py" "<测试报告.md路径>" /tmp/zentao_bugs.json
```
脚本自动完成：失败项提取 → 真实缺陷/脚本问题分拣 → severity/pri/type 建议 → steps 四段拼装 → 截图路径解析。bug 标题/重现步骤/预期/级别**优先直接取自测试报告的 bug 字段列**（新版报告，见关键事实 #10），仅旧格式报告才降级为按用例名称拼接。检查输出的建议提交/排除清单。

截图模式（默认 `attach`，即清单中附本地路径由确认后上传环节处理）：
- `--screenshot-mode embed`：base64 内嵌。**实测会被禅道编辑器过滤剥掉，勿用**（见关键事实 #12），保留参数仅为脚本兼容。
- 截图相对路径解析：脚本先按报告所在目录找，找不到自动回退到报告头部"脚本目录"（batch_dir）下，报告被拷到桌面等位置也能正确定位截图。

### 步骤3 分拣复核（关键）
读取 `/tmp/zentao_bugs.json`，对每条：
- `classification=script_issue` → 默认排除，在清单中单独列出供用户勾选保留
- `classification=defect` → 默认提交
- **同步向用户展示报告中的"失败用例详情" traceback**，辅助用户判断

### 步骤4 确认产品/模块（一批确认一次）
1. `npx zentao-cli product list --pick id,name --recPerPage 300 --format json`，与报告批次名/系统名模糊匹配，**与用户确认目标产品**。
2. 模块树（v1 API，需 `$TOKEN`）：
   ```
   curl -sk "<baseUrl>/api.php/v1/modules?type=bug&id=<产品id>" -H "Token: $TOKEN"
   ```
   （bug 录入用 **`type=bug`**；`type=case` 是另一棵树，模块 id 不通用）
   按报告"模块"列/标题【】内模块名逐级匹配现有树；缺失则问用户（复用现有上级模块 / v1 API 自动建 / 留空）。bug 的 `module` 字段传匹配到的模块 id；不匹配则不传。

### 步骤5 dry-run（必须）
打印完整提交清单，逐条包含：
`case_id | title | severity | pri | type | 指派(=登录人$ACCOUNT) | 模块 | 截图(本地路径/内嵌状态) | steps全文预览`

用 AskUserQuestion 或表格让用户**逐条勾选提交/排除**，并可修改 severity/pri/type。批准前不得创建。

### 步骤5.5 幂等预检
拉产品现有 bug 标题集合去重（避免重复提交）。老产品 bug 可达近千条，**`--recPerPage` 用 1000 并核对返回 `pager.total` 是否拉全**：
```
npx zentao-cli bug list --product <id> --pick id,title --recPerPage 1000 --format json
```
同产品+同 title 已存在 → 默认跳过并在清单标注（用户允许重建除外）。

### 步骤6 批量创建
```
npx zentao-cli bug create --data '{"productID":<id>,"title":"<标题>","severity":<1-4>,"pri":<1-4>,"type":"codeerror","openedBuild":"trunk","assignedTo":"<登录人账号>","module":<可选>,"steps":"<四段HTML>"}' --format json
```
- 逐条提交；失败打印错误原因记录后继续，不中断整批。
- `steps` 内含引号/换行时注意 shell 转义，**必须**用 `--data "$(cat /tmp/bug_N.json)"` 逐条落盘后传文件内容；**禁止 `--data @文件`**（不被支持且静默失败，见关键事实 #11）。
- 成功判定：从返回 JSON 解析 `"id"`（如 `{"status":"success","data":{"message":"保存成功","id":29339,...}}`）；stdout 为空即失败，需检查 JSON 落盘内容与参数拼写后重试该条。

### 步骤7 截图上传（直传 + 手动兜底）

1. **API 直传（已实测可用，2026-09-15/16 两批次验证）**：
   ```
   curl -sk -X POST "<baseUrl>/api.php/v1/files" -H "Token: $TOKEN" \
     -F "imgFile=@<截图路径>;type=image/png"
   ```
   - 字段名必须 `imgFile`；成功返回 `{"id":<fileID>,"url":"..."}`。
   - 返回的 `url` 可能带重复前缀（如 `/zentao/zentao/index.php?...`），**不要直接用**，自行拼 **PATH_INFO 格式**地址：
     `<baseUrl>/file-read-<fileID>.png`
     （⚠️ GET 格式 `index.php?m=file&f=read&t=png&fileID=N` 浏览器端会被权限校验重定向导致裂图，勿用，见关键事实 #12）
   - 将 `<img src="<拼好的地址>">` 追加到 steps 再 update（`npx zentao-cli bug update <id> --data "$(cat /tmp/steps_up.json)"`）。
     ⚠️ **追加基准必须是本地构建的原始 HTML steps（/tmp/zentao_bugs.json 里的 `steps` 字段）**，绝不能从 `npx zentao-cli bug <id> --pick steps` 取回后追加——CLI 详情返回的是 markdown 转义文本，update 回去会把 markdown 字面量存进库，禅道页面就显示成 `**\[前置条件\]**` 源码（2026-09-16 实际踩坑，29 条被污染后全量重建修复）。该地址依赖查看者的禅道登录会话，与编辑器内贴图行为一致，浏览器已登录用户可正常显示。
   - 校验/取回二进制：`curl -sk "<baseUrl>/api.php/v1/files/<fileID>" -H "Token: $TOKEN"`。
   - 误传清理：`npx zentao-cli delete file <fileID> --yes`（v1 API 的 DELETE /files/{id} 无效）。
2. **标注手动处理**：直传异常或截图过大 → 汇总清单标注"该 bug 需手动补截图"，附本地截图绝对路径。（base64 内嵌会被编辑器过滤剥掉，不可用，勿尝试 embed 模式）

### 步骤8 校验与汇总
- **steps 的存储格式必须用 curl 直查 v1 API 核验**（CLI 详情接口会把 HTML 转 markdown 展示，不可作为判断依据）：
  ```
  curl -sk "<baseUrl>/api.php/v1/bugs/<bugID>" -H "Token: $TOKEN"
  ```
  核对：① 存储为 HTML（`<b>[前置条件]</b>` 原样存在，无 `**\[` 字面量）；② 四段完整；③ 含 `file-read-<fileID>.png` 的 `<img>`。
- 其余字段（title/severity/pri/type/module）可抽查 `npx zentao-cli bug <纯数字id> --format json`。
- 输出汇总：成功条数（含禅道bug id）、跳过（去重/用户排除）、失败原因、待手动补截图清单。

## 严重程度/优先级建议对照（摘自规范V1.0）

| 级别 | 典型场景（脚本失败原因→级别映射参考） |
|------|------|
| 1 | 提交/保存/删除/导入导出失败、列表无数据、流程不通、统计数据错误、权限错误、页面报错 |
| 2 | 必填/唯一性校验错误、字段值显示错误、查询/翻页结果不对、缺少确认提示、详情字段缺失（**默认**） |
| 3 | 格式/长度校验、不影响使用的展示效果、提示文案、性能速度 |
| 4 | 优化建议 |

## bug标题格式（规范要求）

- 简洁表明模块和问题点，用"不应""不符合需求"等词：`【XXX模块】-【新建】新建失败`
- 测试报告用例名称自带 `【模块-操作】` 前缀的直接使用，禁止二次拼接。

## steps 四段模板（规范要求）

```html
<b>[前置条件]</b><br>使用E2E自动化测试账号登录系统（批次运行时间：YYYY-MM-DD HH:MM:SS）<br>
<b>[重现步骤]</b><br>1. 进入 XX模块 对应页面<br>2. 执行用例操作：<用例名中"验证"后描述><br>
<b>[结果]</b><br>第2步出现异常，实际结果：<断言消息/关键traceback行><br>
<b>[期望]</b><br><用例名中"验证"后描述>
```

## 前后端判据（供用户询问时参考，摘自规范V1.0）

- 前端：界面/布局/兼容性/交互相关；没发请求、url错误、传参错误、响应对但页面显示错、UI类、页面写死内容
- 后端：业务逻辑/性能/数据/安全性相关；url和传参都对但响应内容不对
- 入参或出参少参数 → 前后端都要改，先提给后端

## 错误与降级

- token 失效 → 请用户重新登录，勿反复试密码
- 产品/模块匹配不到 → AskUserQuestion 降级（确认产品 / 换产品 / 模块留空）
- 全部失败项均为 script_issue → 告知用户"无疑似缺陷可提交"，展示分拣明细，不强行创建
- 禅道不可达/超时 → 记录后终止本批，输出已完成清单
