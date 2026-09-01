---
name: import-to-zentao
description: 禅道用例导入 - 将测试用例文件(测试用例.md)结构化后自动批量录入禅道，含产品匹配、字段映射、dry-run、批量创建与校验。单 token 双用途：优先复用 ~/.config/zentao/zentao.json 已存 token（无需再要密码），统一认证头 Token:，模块走 v1 modules API、用例走 zentao-cli（steps/expects/stepType 三数组同位要点）
triggers:
  - "录入禅道"
  - "导入禅道"
  - "禅道用例"
  - "zentao导入"
  - "导入到禅道"
  - "测试用例录入"
---

# 禅道用例导入 (import-to-zentao)

将一份结构化测试用例文件（通常由 `workflow-prd-pipeline` / `test-case-generate` 产出，如 `output/{日期}/测试用例.md`）自动批量录入禅道。逐条创建用例，支持产品匹配、字段映射、导入前 dry-run、导入后校验。

**重要**：这是写共享系统的操作。**必须先给用户 dry-run 预览并经用户确认，才可实际创建**。产品名、模块策略均需与用户逐项确认。

## 运行前提

- Node 环境与 **`zentao-cli`**（⚠️ 包名是 `zentao-cli`，不是 `zentao`；`npx zentao` 会报 `No versions available`）。
  ```
  npm i -g zentao-cli          # 或直接 npx zentao-cli ...（自动缓存）
  ```
- 禅道连接信息：baseUrl、账号、密码。登录成功后将凭证（含 token）写入 `~/.config/zentao/zentao.json`。

## 输入

- 测试用例文件路径（用户提供；未提供时默认扫描 `output/*/测试用例.md` 下最新一份）。

## 关键事实与踩坑（务必先读）

| # | 事实 | 影响 |
|---|------|------|
| 1 | 包名 `zentao-cli` | 命令统一 `npx zentao-cli ...` |
| 2 | `create` 顶层键（`--productID 2` 等）**不被解析**，报"缺少必要参数 productID" | **必须用 `--data '<完整JSON>'` 传参** |
| 3 | 多步骤用例若只传 `steps`/`expects` 字符串数组，禅道**只保留第 1 条** | 必须**三数组同位**：`steps` + `expects` + `stepType`（每条 `"step"`） |
| 4 | 模块经 **v1 开放 API** 可读可建：`GET/POST http://<base>/api.php/v1/modules?type=case&id=<产品id>`。⚠️ **认证用动态登录临时 token**（见步骤1，走 `v2/users/login`），放 `Header: Token: <token>`（不带 token 返 `Unauthorized`）。**v2 的 `/api.php/v2/.../modules`、`tree` 端点一律 `Not allowed`**，务必走 v1 `/api.php/v1/modules` | 模块**可自动建**（无需独立 API key、无需界面手动建），作为模块策略默认首选 |
| 4b | 模块树的 `type` 字段总是 `story`，但接口 view 为 `case`，同一棵产品模块树同时供用例(测试)用 | 建模块时 type 传 `case` 即可挂到测试用例树；`GET modules` 返回顶级/子级 `children` 结构，按 `name` 匹配目标模块是否存在，重复则复用其 id |
| 5 | `testcase list --pick id` 返回的 id 可能带 **`case_` 前缀**（如 `case_8926`） | `get`/`delete` 前**去掉前缀**用纯数字 |
| 6 | `testcase get` 返回**扁平结构**（字段在顶层，无 `data` 包裹） | 取 `c.get('product')` 而非 `c.get('data',{}).get(...)` |
| 7 | 产品表很大（可达上百条）。`product list --search` 偶发不命中 | 用 `--recPerPage 300` 拉全量后本地筛选；目标**产品名务必直接与用户确认** |
| 8 | 禅道会自动给每行步骤显示行号。若步骤/预期文本内自带 `1.` `2.` 序号，会出现**双序号** | 导入前**剥离文本行首序号前缀**。`parse_case_md.py` 已内建 `strip_step_num()` 自动剥离；产出/手工构造 `steps` 时不要写入 `N. ` 前缀（steps[i]↔expects[i] 靠数组同位对齐，不靠文本序号） |
| 9 | `v2/users/login` 动态登录**需要账号密码**；若会话已经在 `~/.config/zentao/zentao.json` 存有有效 token，**无需再向用户要密码** | **优先读配置里已存 token**（`python3 -c "import sys,json;d=json.load(open(...));print([p['token'] for p in d['profiles'] if p['account']=='<账号>'][0])"`），它可直接通过 v1 modules API 认证；仅当该 token 失效（返 `Unauthorized`）才回退走 `v2/users/login` 或 `zentao-cli login` |

## 认证与调用统一（单 token 双用途）

禅道支持 v2，但 v2 **没有模块 CRUD 能力**（`POST /api.php/v2/tree` Not allowed、`/api.php/v2/modules` 空路由）。为统一，只从 **v2 `users/login` 拿一个临时 token**，三种用途共享同一 token、统一认证头 `Header: Token: <token>`：

| 用途 | 通道 | 端点 |
|------|------|------|
| 登录拿 token | v2 `users/login` | `POST /api.php/v2/users/login` |
| 建/读模块 | v1 modules API | `GET/POST /api.php/v1/modules` |
| 建/查/校验用例、产品 | zentao-cli | `npx zentao-cli ...` |

要点：
- **token 单源、优先复用**：首选从 `~/.config/zentao/zentao.json` 读已存 token（见踩坑表 #9）。**仅在它失效（v1 模块 API 返 `Unauthorized`）时才走 `v2/users/login`**——而后者需要账号密码，通常得向用户索要，故能复用就复用。该 token 同时满足 v1 接口认证（带 `Token:` 头成功，不带则返 `Unauthorized`）。
- 模块**必须走 v1 modules**（v2 无此能力）；用例走 zentao-cli（其内部即标准禅道开放 API）。
- token 为敏感态，仅脚本内变量传递，勿落盘/入库。

## 执行流程

### 步骤1 取 token（单 token 双用途，优先复用已有会话）
1. **首选：复用 `~/.config/zentao/zentao.json` 已存 token**（无需密码）：
   ```
   TOKEN=$(python3 -c "import sys,json;d=json.load(open('$HOME/.config/zentao/zentao.json'));print([p['token'] for p in d['profiles'] if p['account']=='<账号>'][0])")
   ```
   用它对模块 API 快速验证：`curl -sk "<baseUrl>/api.php/v1/modules?type=case&id=<某产品id>" -H "Token: $TOKEN"`。**能返回 JSON 即有效，直接进入步骤2**。
2. **仅当 token 失效（返 `Unauthorized` 或配置不存在）才重新登录**，此时需向用户索要账号密码：
   - `v2/users/login` 换临时 token（模块 API 认证用）：
     ```
     TOKEN=$(curl -sk -X POST "<baseUrl>/api.php/v2/users/login" \
          -H "Content-Type: application/json" -d "{\"account\":\"<账号>\",\"password\":\"<密码>\"}" \
          | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])")
     ```
   - `zentao-cli` 登录（建产品/查用例/校验用，凭证落到 `~/.config/zentao/zentao.json`）：
     ```
     npx zentao-cli login -s <baseUrl> -u <账号> -p <密码>
     ```
   - 实测：`v2/users/login` 密码错误会返 `{"status":"failed","reason":"登录失败…"}`，**此时不要反复试密码，优先走第 1 步复用配置 token**。

### 步骤2 解析用例文件
解析脚本在本 skill 目录 `parse_case_md.py`（生成 `cases.json`，含 products/modules/cases/stats）：
```
python3 "<skill目录>/parse_case_md.py" "<测试用例.md路径>" /tmp/zentao_cases.json
```
检查输出 `stats` 与"步骤/预期未对齐"告警；有未对齐需人工复核该批。

### 步骤3 确认 /（可选）建产品
- 查产品：`npx zentao-cli product list --pick id,name --recPerPage 300 --format json`。
- ⚠️ 用例文件"所属产品"列**未必是用户想要的目标**，往往要改导向某个现有产品或新建——**必须与用户确认**。
- 仅在用户明确要求新建时：
  ```
  npx zentao-cli product create --data '{"name":"<产品名>","acl":"open"}' --format json
  ```
- 记录 productID。

### 步骤4 模块（默认匹配现有模块树 → 缺失才自动建）
CLI **无 module 命令**（`unknown command 'module'`）；模块只能经 v1 开放 API 读/建（见踩坑表 #4）。**惯例：用户偏好复用现有模块树而非新建**，故先匹配、缺才建。

1. **建/查均需步骤1的 `$TOKEN`。查目标产品的用例模块树**：
   ```
   curl -sk "<baseUrl>/api.php/v1/modules?type=case&id=<产品id>" -H "Token: $TOKEN"
   ```
   返回模块 `children` 树（`id/name/parent/grade`），`root` 字段=产品 id。用脚本按路径段**逐级匹配**用例文件的`所属模块`（如路径 `板块/模块`：先找顶层名=板块的 id，再在其 `children` 里找名=模块的 id）。匹配到即得 `moduleID`，**复用，跳过创建**。

2. **确认目标模块归入哪个已验证模块**：先向用户确认"用现有模块树还是新建"（例如 AskUserQuestion）。若用户选"按用例文件所属模块匹配现有树"，直接落到匹配到的模块 id（本次 `首页`=1422）。

3. **对确切的缺失模块才逐个创建**：
   ```
   curl -sk -X POST "<baseUrl>/api.php/v1/modules" -H "Token: $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"id":"<产品id>","name":"<模块名>","type":"case","parent":"<父模块id,0为顶层>"}'
   ```
   - `id`=产品 id；`parent`=父模块 id，`0`=顶层；`type`=`case`（挂测试用例树）。
   - 创建后**再次 GET 模块树确认拿到新模块 id**。
   - 若 POST 返回非预期/超时，先 GET 确认是否已建（避免重复），再决定是否重试。

4. **回填映射**：得到 `<模块名> → moduleID` 映射，步骤6 用例 create 时写入 `module` 字段。
5. 若 v1 模块 API 不可用（最终降级），再问用户：**① 提供独立 API key 我建 ② 界面手动建、回填 moduleID ③ 模块留空（不传 `module` 字段）**。

### 步骤5 生成提交清单 + dry-run
把 `cases.json` 每条用例映射为提交对象（务必含三数组，见下）：
```json
{
  "productID": 2, "title": "用例标题", "pri": 2, "type": "feature",
  "module": <moduleID, 可选>, "precondition": "前置+测试数据",
  "steps":   ["步骤一", "步骤二"],    # 不要写 "1. " 前缀，禅道自动显示行号
  "expects": ["对应预期一", "对应预期二"],
  "stepType": ["step", "step"]
}
```
**将全部提交清单打印给用户确认**（总数、模块分布、示例几条），批准前不得真正创建。

### 步骤5.5 幂等预检（创建前先去重）
创建前先拉目标产品的现有用例标题集合，排除已存在用例，避免误重复：
```
npx zentao-cli testcase list --product <id> --pick id,title --recPerPage 300 --format json \
  | python3 -c "import sys,json;print(','.join(sorted({c['title'] for c in json.load(sys.stdin).get('data',[])})))"
```
把待建每个用例的 title 与该集合比对：已存在则标记"去重跳过"（除非用户允许重建），只在 dry-run 提交清单里列出状态；未存在的才进入步骤6 实际创建。用户批准后，跳过的用例不再创建。

### 步骤6 批量创建（⚠️ 三数组必须同位）
循环逐条提交，`--data` 传**完整 JSON**：
```
npx zentao-cli testcase create --data '{"productID":<id>,"title":"<标题>","pri":<1-4>,"type":"feature","precondition":"<前置>","steps":["步骤一","步骤二"],"expects":["对应预期一","对应预期二"],"stepType":["step","step"]}' --format json
```
- `steps`/`expects`/`stepType` **长度必须相等且同位**（steps[i]↔expects[i]↔stepType[i]），否则禅道只保留首条或错位。
- 幂等去重：同产品+标题已存在则跳过，避免重复；除非用户允许重建。
- 失败：逐条打印错误原因为准；可 `--batch-fail-fast`；修失败行后重试。

### 步骤7 校验
- 总数核对：`npx zentao-cli testcase list --product <id> --pick id,title --recPerPage 300 --format json`（注意 id 前缀，见踩坑表 #5）。
- 逐条抽查（注意扁平结构，见 #6）：
  ```
  npx zentao-cli testcase <纯数字id> --format json
  ```
  核对：`steps` 条数与文件一致、**每个 `steps[i].step` ↔ `steps[i].expect` 逐行对应**、`precondition`、`pri`、`type`、`product`。
- 输出导入结果汇总。

## 字段映射表

| 禅道字段 | 来源 | 处理 |
|----------|------|------|
| productID | 步骤3 确认/建的产品 | 必填 |
| module | 模块名 → moduleID | 步骤4 用 v1 API 自动建并回填；确无法建才留空（不传该字段） |
| title | 用例名称 | 原样 |
| pri | 优先级 | P0→1 / P1→2 / P2→3 / P3→4（禅道 1 最大） |
| type | 用例编号前缀 | TC-JIEKOU→interface，其余 feature |
| precondition | 前置条件 + 测试数据 | 测试数据并入："前置；测试数据：X" |
| steps / expects / stepType | 用例步骤 / 预期结果 / `"step"`×N | **三数组同位、等长、逐行对应**；`<br>` 拆行 |

不录入禅道的字段：route_path、关联测试点（禅道无对应字段；确需追溯可在标题加前缀或关联需求 D7）。

## 用例文件（模板）格式要求

解析脚本按**固定 11 列表格**逐行提取，列顺序不可变：

```
| 用例编号 | route_path | 所属产品 | 所属模块 | 用例名称 | 优先级 | 用例类型 | 前置条件 | 测试数据 | 用例步骤 | 预期结果 |
```

要点：
- **用例步骤 / 预期结果**：每行一条，建议带 `1.` `2.` 序号便于人工核对对齐，用 **`<br>`** 分隔；**步骤条数必须等于预期条数且逐行（同位）对应**，否则解析报未对齐告警，导入后步骤/预期会错配。序号仅用于 md 内对齐，导入时 `parse_case_md.py` 会**自动剥离行首序号**，避免禅道双序号。
- 测试数据无则填 `无`；有则导入时并入前置条件。
- 用例类型列供人类阅读，真实 type 以用例编号前缀为准（TC-JIEKOU→interface）。

## 错误与降级

- 已存 token 失效（v1 modules 返 `Unauthorized`）→ 回退走 `v2/users/login` 换临时 token；密码错误返 `login failed` 时**不要反复试密码**，优先复用 `~/.config/zentao/zentao.json` 里可能仍有效的其他 profile token。
- 模块无法建 → 步骤4 先匹配现有模块树，缺失才 v1 API 自动建；仍不可用再降级为 AskUserQuestion 三选项（独立 API key / 界面手动建回填 / 留空）。
- 步骤/预期未对齐 → 解析脚本告警，人工复核该条再提交；导入重点是保证 steps/expects/stepType 三数组等长。
- 用例已存在（同产品+标题）→ 默认跳过提示，避免重复；除非用户允许重建。
- 网络/超时：`--insecure` 跳过证书校验、`--timeout` 调大、失败行记录后重试。

## 完成状态
- 输出导入结果：成功条数、失败条数、失败用例 id、去重跳过数，附步骤/预期逐行对应的抽查结论。
- 若用户要求，本次视为"草稿"，未做删除；如需回滚用 `npx zentao-cli testcase delete <id>,<id>... --yes`。