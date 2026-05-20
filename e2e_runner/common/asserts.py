"""断言工具模块"""
import allure


class AssertUtils:
    """断言工具类"""

    @staticmethod
    def assert_true(condition: bool, msg: str = ""):
        """断言条件为真"""
        assert condition, msg

    @staticmethod
    def assert_false(condition: bool, msg: str = ""):
        """断言条件为假"""
        assert not condition, msg

    @staticmethod
    def assert_equal(actual, expected, msg: str = ""):
        """断言相等"""
        assert actual == expected, f"{msg} 预期: {expected}, 实际: {actual}"

    @staticmethod
    def assert_not_equal(actual, expected, msg: str = ""):
        """断言不相等"""
        assert actual != expected, f"{msg} 预期不相等，但实际相等: {actual}"

    @staticmethod
    def assert_submit_success(is_success: bool, case_title: str = "", extra_msg: str = ""):
        """断言提交成功"""
        msg = f"用例[{case_title}]" if case_title else "用例"
        if extra_msg:
            msg += f", {extra_msg}"
        msg += f", 提交结果: {'成功' if is_success else '失败'}"
        assert is_success, msg

    @staticmethod
    def assert_operation_result(actual_result: bool, test_case: dict, extra_msg: str = ""):
        """统一断言操作结果"""
        expect_success = test_case.get("expect_success", True)
        case_title = test_case.get("title", "未命名用例")

        if expect_success:
            assert actual_result, f"用例[{case_title}]失败：预期操作成功，但实际失败。{extra_msg}"
        else:
            assert not actual_result, f"用例[{case_title}]失败：预期操作失败，但实际成功。{extra_msg}"

    @staticmethod
    def assert_search_result(actual_count: int, test_case: dict, extra_msg: str = ""):
        """统一断言搜索结果"""
        expect_count = test_case.get("expect_count")
        case_title = test_case.get("title", "未命名用例")

        if expect_count == ">0":
            assert actual_count > 0, f"用例[{case_title}]失败：预期结果>0，实际{actual_count}。{extra_msg}"
        elif expect_count == "==0":
            assert actual_count == 0, f"用例[{case_title}]失败：预期结果=0，实际{actual_count}。{extra_msg}"
        elif isinstance(expect_count, int):
            assert actual_count == expect_count, f"用例[{case_title}]失败：预期结果{expect_count}，实际{actual_count}。{extra_msg}"

    @staticmethod
    def assert_validation_error(actual_error_text: str, expected: str = "", field_name: str = "",
                                case_title: str = ""):
        """统一断言验证错误提示"""
        assert actual_error_text and actual_error_text.strip(), \
            f"用例[{case_title}]失败：{field_name} 未显示任何验证错误提示"

        if expected:
            assert expected in actual_error_text, \
                f"用例[{case_title}]失败：{field_name} 错误提示不匹配。期望「{expected}」，实际「{actual_error_text}」"

    @staticmethod
    def assert_has_validation_error(has_error: bool, case_title: str = "", error_count: int = 0):
        """统一断言页面存在验证错误"""
        assert has_error, f"用例[{case_title}]失败：预期应该有验证错误，但未检测到任何错误提示"

    @staticmethod
    def assert_no_success_message_when_error(no_success: bool, case_title: str = ""):
        """统一断言在有验证错误时不应出现成功提示"""
        assert no_success, f"用例[{case_title}]失败：预期不应该有成功提示，但检测到了成功消息"

    @staticmethod
    def attach_result(is_success: bool, case_title: str, extra_info: str = ""):
        """附加测试结果到报告"""
        status = "通过" if is_success else "失败"
        msg = f"用例[{case_title}] - {status}"
        if extra_info:
            msg += f", {extra_info}"
        allure.attach(msg, name="测试结果", attachment_type=allure.attachment_type.TEXT)
