---
name: sync-results-to-zentao
description: 禅道结果回写 - 读取 collect-results 产出的 collect_results.json，按用例标题(title)反查禅道用例，将测试脚本运行结果(passed/failed)逐条写入禅道执行结果。含认证复用、title反查、dry-run预览、写执行结果(端点探测→择优→降级)、幂等登记。⚠️ 写共享系统，必须先 dry-run 确认。
triggers:
  - "回写禅道"
  - "结果写禅道"
  - "同步结果到禅道"
  - "禅道执行结果"
  - "sync-results-to-zentao"
  - "用例执行结果"
---

# 禅道结果回写 (sync-results-to-zentao)

读取 `collect-results` 产出的 `collect_results.json`，**按用例标题(title)反查禅道用例**，把测试脚本运行结果
（`passed`/`failed`）**逐条写入禅道对应用例的执行结果**。

它是整条链路末端：`test-script-run-collect`（运行出报告）→ `collect-results`（整理成 collect_results.json）→ **本技能（回写禅道）**。

**重要**：这是**写共享系统**的操作。**必须先 dry-run 预览待写清单并经用户确认，才可实际写入**。

## 运行前提

- Node 环境 + **`zentao-cli`**（包名是 `zentao-cli`，不是 `zentao`）。
- 禅道连接信息：baseUrl、账号（已在 `~/.config/zentao/zentao.json` 存有 token 时优先复用，无需密码）。
- 输入：`collect-results` 产出的 `collect_results.json`（缺省取 `<批次>/collect_results.json`）。

## 关键事实与踩坑（务必先读）

| # | 事实 | 影响 |
|---|------|------|
| 1 | 存量 token 会过期（实测 `npx zentao-cli product list` 返 `error.code 1004 "所提供的 Token 已失效"`） | **每次先验证再复用**，失效才 `zentao-cli login`（需向用户索要账号密码） |
| 2 | 本实例 open API v2 数据端点多返 `{"status":"fail","message":"Not allowed"}`；v1 需有效 open-API token；**均无"写执行结果(run/testrun/createResult)"能力** | "写执行结果"不能用 CLI/open API 直接完成，走下"写执行结果优先级"的探测→择优→降级 |
| 3 | `testcase list` 返回 **`data` 包裹**，id 可能带 **`case_` 前缀** | 反查脚本统一剥前缀用纯数字 id |
| 4 | 按 title 反查可能**未命中/歧义**（禅道多产品/重名用例） | 精确→包含→候选→用户裁决，**绝不乱猜** |
| 5 | 原生 web action（`index.php?m=testcase&f=run` 等）需要**登录 session cookie 或已登录浏览器会话** | curl 直写需 cookie（从已登录浏览器导出）；Playwright 回写复用 `auth_state.json` |
| 6 | 原生执行表单字段随禅道版本变化 | 用 GET 解析表单字段，**不硬编码** |

## 认证与调用统一

| 用途 | 通道 | 说明 |
|------|------|------|
| 验证/复用 token | `~/.config/zentao/zentao.json` profiles[].token | 先读配置里已存 token 验证；有效直接用（无需密码） |
| 刷新登录 | `npx zentao-cli login` | 仅 token 失效时；需向用户索要账号密码 |
| 查产品/用例 | `npx zentao-cli product/testcase list ...` | id 剥 `case_` 前缀；list 有 `data` 包裹 |
| 写执行结果 | 见"写执行结果优先级" | 探测→择优→降级 |

## 处理流程

### 第一步 输入与目标确认
- 读 `collect_results.json`（默认 `<批次>/collect_results.json`，缺省取最近批次；或用户指定路径），展示统计（总数/通过/失败）。
- 拉产品并对齐目标：`npx zentao-cli product list --pick id,name --recPerPage 300 --format json` → 与用户确认 `productID`（⚠️ 传记问，用例可能分布多产品）。
- 询问执行上下文：默认"用例级执行记录"（`m=testcase&f=run`）；若用户指定挂某**测试单**，记 `taskID`（`m=testtask&f=runCase`）。

### 第二步 认证复用/刷新
```
# 验证存量 token（读 ~/.config/zentao/zentao.json 的 profiles[].token，不打印值）
npx zentao-cli testcase list --pick id --recPerPage 1 --format json
# 失效( code 1004 / Unauthorized ) → 刷新（需向用户要账号密码）
npx zentao-cli login -s <baseUrl> -u <账号> -p <密码>
# 仅当要跑 open API 探测时，另取临时 token
TOKEN=$(curl -sk -X POST "<base>/api.php/v2/users/login" -H "Content-Type: application/json" \
  -d '{"account":"<账号>","password":"<密码>"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])")
```

### 第三步 拉目标产品用例清单并反查
```
npx zentao-cli testcase list --product <productID> --pick id,title --recPerPage 300 --format json > /tmp/zentao_cases.json
python3 "<skill目录>/resolve_writeback.py" "<collect_results.json>" /tmp/zentao_cases.json \
  --productID <productID> -o "<批次>/writeback_plan.json"
```
`resolve_writeback.py` 按 title 反查并输出待写清单（含未找到/歧义标注）。核对打印的统计与待裁决条目。

### 第四步 dry-run 预览（写共享系统，必须先确认）
把 `writeback_plan.json` 的待写清单打印给用户：
```
| 本地用例ID | 状态 | 禅道caseID | 标题/候选 | 拟写状态 | 失败原因(截断) | 截图 |
```
附统计：将写通过 / 将写失败 / 未找到 / 歧义。**AskUserQuestion 确认后才进入写**；可提供选项"仅写失败项 / 全部 / 取消"。

### 第五步 写执行结果（⚠️ 核心，按优先级探测→择优→降级）
**A. 快检 open API 是否藏执行端点（成本最低，先做）**
```
# TOKEN=<步骤2 的 open-API token>
for ep in testruns testresults runs caseresult case-result testcase-result; do
  echo "$(curl -sk -o /dev/null -w '%{http_code}' "$BASE/api.php/v1/$ep" -H "Token: $TOKEN")  v1/$ep"
  echo "$(curl -sk -o /dev/null -w '%{http_code}' "$BASE/api.php/v2/$ep" -H "Token: $TOKEN")  v2/$ep"
done
```
判定：`200`+JSON=存在（undocumented，用但有风险）；`Not allowed`=禁用；`Unauthorized`=token 问题；`404/空体`=不存在。

**B. 原生 web action + session cookie（curl 直写）**
候选（按贴"逐条记录执行结果"排序）：
1. `index.php?m=testcase&f=run&caseID=<id>&version=<最新版本>`（首选）
2. `index.php?m=testcase&f=batchRun&caseID=<id1>,<id2>`
3. `index.php?m=testtask&f=runCase&taskID=<测试单id>&caseID=<id>`
4. `index.php?m=testrun&f=create`（新版测试单执行记录）

认证：用从已登录浏览器导出的 `cookies.txt`（`-b`/`-c`）。**运行时 GET 解析表单字段，不硬编码**：
```
curl -sk -b cookies.txt -c cookies.txt "$BASE/index.php?m=testcase&f=run&caseID=<id>&version=<v>" | grep -oE 'name="[^"]+"' | sort -u
curl -sk -b cookies.txt -c cookies.txt -X POST "$BASE/index.php?m=testcase&f=run&caseID=<id>&version=<v>" \
  -d 'status=fail&comment=<失败原因>&id=<id>&version=<v>&...'   # 字段以解析结果为准，可能含 CSRF token
```
判定成功：响应含"保存执行结果成功"/跳转执行记录页/无错误；否则记失败原因。

**C. Playwright UI 代填（复用 auth_state.json，最稳，可截图断言）**
```
# 用 run-collect 已导出的 auth_state.json
ctx = p.chromium.launch(headless=True).new_context(storage_state="auth_state.json")
page.goto(f"{BASE}/index.php?m=testcase&f=run&caseID={zid}&version=1")
page.locator("input[name='status'][value='pass']").check()   # 失败则 value='fail'
page.fill("textarea[name='comment']", error or "自动化测试")
page.click("button:has-text('保存')")
# 断言成功提示（如"保存执行结果成功"），失败截图
```

**D. 人工降级**：导出"待人工录入清单.csv/md"（用例ID/标题/禅道caseID/本地结果/失败原因/截图）+ 禅道 UI 指引（测试→用例→执行），供人工录入。

**择优顺序**：A 快检 → **按用户选定的 API/CLI 优先走 B(原生 action curl)**；B 需要 cookie 而不可得 → C(Playwright UI，需禅道登录态/auth_state)；仍不可 → D(人工)。每条写后尽力校验并**落本地 `sync_log.json`**。

### 第六步 完成状态
- 汇报：写成功数（分 passed/failed）、未找到/歧义待定数、写失败数、**使用的写渠道 + 该渠道的不稳定性风险**。
- 落 `sync_log.json`（case_id→zentaoID→status→time→channel）；重复执行对结果未变化条目默认跳过或提示覆盖。

## 幂等与安全
- dry-run + 用户确认后才写。
- `sync_log.json` 登记：结果未变化条目重复时跳过/提示覆盖，需确认。
- token 仅脚本内变量传递，不落盘。
- 只读命令（反查/列表/探测）在前，写仅发生在用户确认后。

## 输出
- `writeback_plan.json`（dry-run 待写清单）
- `sync_log.json`（实际写登记）
- 本次回写统计与失败清单。

## 校验清单
- [ ] 认证已就绪（token 复用或刷新），未向用户索要非必要密码
- [ ] collect_results.json 已正确读入，每条对应到目标产品
- [ ] 按 title 反查：未命中/歧义条目明确列出，未乱猜
- [ ] dry-run 清单已打印并经用户确认后才写
- [ ] 写执行结果已按探测到的渠道逐条执行并校验；渠道风险已向用户说明
- [ ] sync_log.json 已登记；未做重复覆盖共享数据
- [ ] 已汇报统计与失败清单