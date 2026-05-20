"""自动化测试运行器主入口"""
import argparse
import sys
import os
from datetime import datetime
from pathlib import Path

# e2e_runner 目录路径
E2E_RUNNER_DIR = Path(__file__).parent
sys.path.insert(0, str(E2E_RUNNER_DIR))

from config.settings import settings
from common.logger import logs
from common.test_runner import TestRunner
from result_writer import ResultWriter


def main():
    parser = argparse.ArgumentParser(description="E2E自动化测试运行器")
    parser.add_argument("--env", choices=["test", "prod"], default="test",
                        help="指定测试环境（test/prod）")
    parser.add_argument("--date", type=str, default=None,
                        help="指定时间文件夹（如 2026-05-19），默认为当天")
    parser.add_argument("--test-type", choices=["all", "positive", "negative", "smoke"],
                        default="all", help="测试类型过滤")
    parser.add_argument("--username", type=str, default=None,
                        help="登录账号（默认为配置中的账号）")
    parser.add_argument("--password", type=str, default=None,
                        help="登录密码（默认为配置中的密码）")
    parser.add_argument("--sms-code", type=str, default=None,
                        help="短信验证码（默认为配置中的验证码）")
    parser.add_argument("--base-url", type=str, default=None,
                        help="系统基础URL（如 http://182.129.202.241:20051）")
    parser.add_argument("--login-url", type=str, default=None,
                        help="登录页面路径（如 /business/#/login）")

    args = parser.parse_args()

    date_folder = args.date or datetime.now().strftime("%Y-%m-%d")

    project_root = Path(__file__).parent.parent
    output_base = project_root / "output" / date_folder

    test_script_dir = output_base / "tests"
    if not test_script_dir.exists():
        logs.error(f"测试脚本目录不存在: {test_script_dir}")
        print(f"错误: 测试脚本目录不存在: {test_script_dir}")
        return

    # 创建必要的 output 目录结构（仅 results 和 screenshots）
    results_dir = output_base / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    screenshots_dir = output_base / "results" / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    # 复制 conftest.py 到 output/tests/，确保 fixture 对测试可见
    output_tests_conftest = output_base / "tests" / "conftest.py"
    if not output_tests_conftest.exists():
        import shutil
        shutil.copy(E2E_RUNNER_DIR / "conftest.py", output_tests_conftest)
        logs.info(f"已复制 conftest.py 到: {output_tests_conftest}")

    # 设置环境变量（登录凭证和URL）
    # 优先级：命令行参数 > settings.py 默认值
    if args.username:
        os.environ['E2E_LOGIN_USERNAME'] = args.username
    if args.password:
        os.environ['E2E_LOGIN_PASSWORD'] = args.password
    if args.sms_code:
        os.environ['E2E_LOGIN_SMS_CODE'] = args.sms_code
    if args.base_url:
        os.environ['E2E_BASE_URL'] = args.base_url
    if args.login_url:
        os.environ['E2E_LOGIN_URL'] = args.login_url

    # 设置 pytest 运行配置
    # 通过环境变量传递 PYTHONPATH，让测试脚本能导入 e2e_runner 中的模块
    # 优先从 output/{日期}/ 目录读取 pages 和 datas，其次使用 e2e_runner 目录
    output_pages = output_base / "pages"
    output_datas = output_base / "datas"
    python_path = f"{output_pages}:{output_datas}:{E2E_RUNNER_DIR}:{E2E_RUNNER_DIR / 'pages'}:{E2E_RUNNER_DIR / 'common'}:{E2E_RUNNER_DIR / 'config'}:{E2E_RUNNER_DIR / 'datas'}"
    if 'PYTHONPATH' in os.environ:
        os.environ['PYTHONPATH'] = python_path + ":" + os.environ['PYTHONPATH']
    else:
        os.environ['PYTHONPATH'] = python_path

    # 传递 output_base 路径给 conftest.py
    os.environ['E2E_OUTPUT_BASE'] = str(output_base)

    # 传递 conftest.py 路径
    os.environ['E2E_CONFTEST_PATH'] = str(E2E_RUNNER_DIR / "conftest.py")

    settings.current_env = args.env
    settings.TEST.test_type = args.test_type
    settings.REPORT.base_path = str(output_base / "results")

    logs.info("=" * 60)
    logs.info("E2E自动化测试运行器")
    logs.info("=" * 60)
    logs.info(f"测试环境: {args.env}")
    logs.info(f"时间文件夹: {date_folder}")
    logs.info(f"测试脚本目录: {test_script_dir}")
    logs.info(f"结果输出目录: {results_dir}")
    logs.info(f"测试类型: {args.test_type}")
    logs.info("=" * 60)

    test_runner = TestRunner()
    success = test_runner.run(
        results_dir=str(results_dir),
        case_dir=str(test_script_dir),
        test_type=args.test_type,
        conftest_path=str(output_tests_conftest)
    )

    result_writer = ResultWriter(str(results_dir))
    result_writer.parse_pytest_results(str(results_dir))
    result_writer.generate_summary_report()

    logs.info("=" * 60)
    logs.info("自动化测试流程全部完成!")
    logs.info("=" * 60)

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
