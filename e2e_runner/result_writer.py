"""测试结果写入器"""
import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict

from common.logger import logs


class ResultWriter:
    """测试结果写入器"""

    def __init__(self, results_dir: str):
        self.results_dir = Path(results_dir)
        self.screenshots_dir = self.results_dir / "screenshots"
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)

        self.results_file = self.results_dir / "results.json"
        self.test_results: List[Dict] = []

    def add_test_result(self, name: str, status: str, error_msg: str = None,
                       screenshot_path: str = None, duration: float = None):
        """添加单个测试结果"""
        self.test_results.append({
            "name": name,
            "status": status,
            "error_msg": error_msg,
            "screenshot_path": screenshot_path,
            "duration": duration,
            "timestamp": datetime.now().isoformat()
        })

    def parse_pytest_results(self, results_dir: str):
        """解析 pytest 生成的 result.json 文件"""
        results_path = Path(results_dir)
        if not results_path.exists():
            logs.warning(f"结果目录不存在: {results_dir}")
            return

        for result_file in results_path.glob("*-result.json"):
            try:
                with open(result_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                test_name = data.get("name", result_file.stem.replace("-result", ""))
                status = data.get("status", "unknown").lower()

                error_msg = None
                if status == "failed":
                    status_details = data.get("statusDetails", {})
                    if isinstance(status_details, dict):
                        error_msg = status_details.get("message") or status_details.get("trace", "")
                    elif isinstance(status_details, str):
                        error_msg = status_details

                screenshot_path = None
                for screenshot_file in self.screenshots_dir.glob("*failed*.png"):
                    if test_name.replace("[", "_").replace("]", "_").replace(" ", "_") in str(screenshot_file):
                        screenshot_path = str(screenshot_file)
                        break

                duration = None
                if "start" in data and "stop" in data:
                    duration = (data["stop"] - data["start"]) / 1000

                self.add_test_result(
                    name=test_name,
                    status=status,
                    error_msg=error_msg,
                    screenshot_path=screenshot_path,
                    duration=duration
                )
            except Exception as e:
                logs.error(f"解析结果文件失败 {result_file}: {e}")

    def generate_summary_report(self) -> Dict:
        """生成测试结果汇总报告"""
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["status"] == "passed")
        failed = sum(1 for r in self.test_results if r["status"] == "failed")
        skipped = sum(1 for r in self.test_results if r["status"] == "skipped")
        broken = sum(1 for r in self.test_results if r["status"] == "broken")

        summary = {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "broken": broken,
            "pass_rate": f"{passed / total * 100:.2f}%" if total > 0 else "0%",
            "timestamp": datetime.now().isoformat(),
            "test_results": self.test_results
        }

        with open(self.results_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        logs.info("=" * 60)
        logs.info(f"测试结果汇总:")
        logs.info(f"  总计: {total}")
        logs.info(f"  通过: {passed}")
        logs.info(f"  失败: {failed}")
        logs.info(f"  跳过: {skipped}")
        logs.info(f"  异常: {broken}")
        logs.info(f"  通过率: {summary['pass_rate']}")
        logs.info(f"结果报告已生成: {self.results_file}")
        logs.info("=" * 60)

        return summary
