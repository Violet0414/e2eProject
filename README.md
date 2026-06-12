**技能目录**

requirement-split 需求拆分

test-point-extract 测试点提取

test-point-review 测试点审查

test-case-generate 测试用例生成

export-excel 导出Excel


explore-site 探索网页

generate-testcases-from-explore 根据探索结果生成测试用例

test-script-generate 测试脚本生成


WORK_FLOW_e2e-pipeline 根据需求文档自动生成测试用例工作流

WORK_FLOW_explore_pipeline 根据探索结果生成测试用例工作流



测试用例生成完成后可执行test-script-generate技能生成测试脚本

脚本生成完毕后可直接执行

python run.py \
      --env test \
      --date 2026-05-19 \
      --test-type all \
      --username Sn_admin \
      --password Smart@123456 \
      --sms-code 34287 \
      --base-url http://182.129.202.241:20051 \
      --login-url /business/#/login

使用现有框架运行测试脚本

参数说明：

date：测试脚本生成的文件夹名称

username：系统账号

password：系统密码

sms-code：验证码

base-url：测试系统地址

login-url：登录页面地址



