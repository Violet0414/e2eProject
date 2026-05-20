"""自动化测试运行器主入口"""
import argparse
import sys
import shutil
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config.settings import settings
from common.logger import logs
from common.test_runner import TestRunner
from result_writer import ResultWriter


def ensure_output_structure(output_base: Path):
    """确保 output 目录结构完整"""
    # 创建必要的目录和 __init__.py 文件
    for dir_path in [
        output_base / "pages",
        output_base / "pages" / "admin",
        output_base / "datas",
        output_base / "datas" / "admin",
        output_base / "common",
    ]:
        dir_path.mkdir(parents=True, exist_ok=True)
        init_file = dir_path / "__init__.py"
        if not init_file.exists():
            init_file.touch()

    # 复制 base_page.py 到 output/pages/ 目录
    # 因为测试脚本中的页面对象依赖它
    src_base_page = Path(__file__).parent / "pages" / "base_page.py"
    dst_base_page = output_base / "pages" / "base_page.py"
    if src_base_page.exists() and not dst_base_page.exists():
        shutil.copy(src_base_page, dst_base_page)
        logs.info(f"已创建 base_page: {dst_base_page}")

    # 复制 common 模块到 output/common/ 目录
    src_common = Path(__file__).parent / "common"
    dst_common = output_base / "common"
    if src_common.exists():
        for py_file in src_common.glob("*.py"):
            if py_file.name != "__init__.py":
                dst_file = dst_common / py_file.name
                if not dst_file.exists():
                    shutil.copy(py_file, dst_file)
        logs.info(f"已同步 common 模块到 {dst_common}")


def main():
    parser = argparse.ArgumentParser(description="E2E自动化测试运行器")
    parser.add_argument("--env", choices=["test", "prod"], default="test",
                        help="指定测试环境（test/prod）")
    parser.add_argument("--date", type=str, default=None,
                        help="指定时间文件夹（如 2026-05-19），默认为当天")
    parser.add_argument("--test-type", choices=["all", "positive", "negative", "smoke"],
                        default="all", help="测试类型过滤")

    args = parser.parse_args()

    date_folder = args.date or datetime.now().strftime("%Y-%m-%d")

    project_root = Path(__file__).parent.parent
    output_base = project_root / "output" / date_folder

    test_script_dir = output_base / "tests" / "admin"
    if not test_script_dir.exists():
        logs.error(f"测试脚本目录不存在: {test_script_dir}")
        print(f"错误: 测试脚本目录不存在: {test_script_dir}")
        return

    # 确保 output 目录结构完整
    ensure_output_structure(output_base)

    pages_admin_dir = output_base / "pages" / "admin"
    datas_admin_dir = output_base / "datas" / "admin"

    # 设置 sys.path，优先从 output 目录导入
    # 注意：pytest 会重新设置 sys.path，所以需要通过环境变量传递
    import os
    python_path = f"{output_base}:{output_base / 'pages'}:{pages_admin_dir}:{datas_admin_dir}"
    if 'PYTHONPATH' in os.environ:
        os.environ['PYTHONPATH'] = python_path + ":" + os.environ['PYTHONPATH']
    else:
        os.environ['PYTHONPATH'] = python_path

    results_dir = output_base / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    screenshots_dir = output_base / "results" / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)

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
        test_type=args.test_type
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
