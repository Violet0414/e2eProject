"""测试运行器模块"""
import pytest
import os
import sys
from pathlib import Path

# 在导入 pytest 之前设置 sys.path
E2E_RUNNER_DIR = Path(__file__).parent.parent
PROJECT_ROOT = E2E_RUNNER_DIR.parent
sys.path.insert(0, str(E2E_RUNNER_DIR))
sys.path.insert(0, str(PROJECT_ROOT))

from common.logger import logs


class TestRunner:
    """测试执行器"""

    @staticmethod
    def run(results_dir: str, case_dir: str, test_type: str = "all") -> bool:
        """
        执行测试用例

        :param results_dir: 测试结果目录
        :param case_dir: 测试用例目录
        :param test_type: 测试类型 (all/positive/negative/smoke)
        :return: 是否执行成功
        """
        logs.info("=" * 60)
        logs.info("开始执行测试...")
        logs.info(f"测试用例目录: {case_dir}")
        logs.info(f"结果输出目录: {results_dir}")
        logs.info(f"测试类型: {test_type}")
        logs.info("=" * 60)

        Path(results_dir).mkdir(parents=True, exist_ok=True)

        # 获取时间文件夹路径
        output_base = Path(case_dir).parent.parent.parent  # tests/admin -> output/{date}
        pages_dir = output_base / "pages"
        if pages_dir.exists():
            sys.path.insert(0, str(pages_dir))
            sys.path.insert(0, str(output_base))
            logs.info(f"已添加 pages 路径: {pages_dir}")

        pytest_args = [
            '-v',
            '-s',
            '--alluredir', results_dir,
            case_dir,
            '--tb=short'
        ]

        if test_type != "all":
            pytest_args.extend(['-m', test_type])

        try:
            exit_code = pytest.main(pytest_args)

            result_files = [f for f in os.listdir(results_dir) if f.endswith("-result.json")]
            logs.info(f"测试执行完成，共生成 {len(result_files)} 个结果文件")

            return exit_code == 0 or exit_code == 1
        except Exception as e:
            logs.error(f"测试执行异常: {e}")
            return False
