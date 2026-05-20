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
    def run(results_dir: str, case_dir: str, test_type: str = "all", conftest_path: str = None) -> bool:
        """
        执行测试用例

        :param results_dir: 测试结果目录
        :param case_dir: 测试用例目录
        :param test_type: 测试类型 (all/positive/negative/smoke)
        :param conftest_path: conftest.py 文件路径
        :return: 是否执行成功
        """
        logs.info("=" * 60)
        logs.info("开始执行测试...")
        logs.info(f"测试用例目录: {case_dir}")
        logs.info(f"结果输出目录: {results_dir}")
        logs.info(f"测试类型: {test_type}")
        logs.info("=" * 60)

        Path(results_dir).mkdir(parents=True, exist_ok=True)

        # 设置 PYTHONPATH，优先从 e2e_runner 目录导入模块
        # 注意：pytest 会重新设置 sys.path，所以通过环境变量传递
        if 'PYTHONPATH' not in os.environ:
            python_path = f"{E2E_RUNNER_DIR}:{E2E_RUNNER_DIR / 'pages'}:{E2E_RUNNER_DIR / 'common'}:{E2E_RUNNER_DIR / 'config'}:{E2E_RUNNER_DIR / 'datas'}"
            os.environ['PYTHONPATH'] = python_path
            logs.info(f"已设置 PYTHONPATH: {python_path}")

        pytest_args = [
            '-v',
            '-s',
            '--alluredir', results_dir,
            case_dir,
            '--tb=short',
            '-c', conftest_path,
        ]

        # 指定 conftest.py 位置（优先使用传入的路径）
        if conftest_path and Path(conftest_path).exists():
            logs.info(f"使用 conftest.py: {conftest_path}")

        if test_type != "all":
            pytest_args.extend(['-m', test_type])

        try:
            # 切换到 conftest.py 所在目录运行 pytest
            original_cwd = os.getcwd()
            os.chdir(Path(conftest_path).parent if conftest_path else E2E_RUNNER_DIR)

            exit_code = pytest.main(pytest_args)

            os.chdir(original_cwd)

            result_files = [f for f in os.listdir(results_dir) if f.endswith("-result.json")]
            logs.info(f"测试执行完成，共生成 {len(result_files)} 个结果文件")

            return exit_code == 0 or exit_code == 1
        except Exception as e:
            logs.error(f"测试执行异常: {e}")
            return False
