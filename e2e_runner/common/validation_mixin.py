"""验证混入类"""
from common.asserts import AssertUtils


class ValidationMixin:
    """通用的字段验证方法"""

    @staticmethod
    def _check_required_params(trigger, selector, file_path):
        """检查必填参数"""
        if trigger in ("blur", "submit") and not selector:
            raise ValueError(f"{trigger} 验证必须指定 selector 字段")
        if trigger == "upload" and not file_path:
            raise ValueError("upload 验证必须指定 file_path")

    def _dispatch_validation(self, trigger, selector, file_path, case_title):
        """分发验证逻辑到对应的处理方法"""
        dispatch = {
            "blur": self._validate_blur,
            "submit": self._validate_submit,
            "upload": self._validate_upload,
        }

        if trigger not in dispatch:
            raise ValueError(f"不支持的验证触发方式: {trigger}")

        return dispatch[trigger](selector, file_path, case_title)

    def _validate_blur(self, selector, file_path, case_title):
        """失焦验证 - 子类需要实现"""
        raise NotImplementedError("子类必须实现 _validate_blur 方法")

    def _validate_submit(self, selector, file_path, case_title):
        """提交验证 - 子类需要实现"""
        raise NotImplementedError("子类必须实现 _validate_submit 方法")

    def _validate_upload(self, selector, file_path, case_title):
        """上传验证 - 子类需要实现"""
        raise NotImplementedError("子类必须实现 _validate_upload 方法")

    def _validate_field(self, test_case):
        """通用字段验证方法，支持blur/submit/upload三种触发方式"""
        validation = test_case.get("validation_info", {})
        test_data = test_case.get("data", {})
        case_title = test_case.get("title", "未知用例")

        selector = validation.get("selector", "")
        expected_error = validation.get("expected_error_text", "")
        trigger = validation.get("trigger", "")
        file_path = test_data.get("file_path", "")

        self._check_required_params(trigger, selector, file_path)

        actual_error = self._dispatch_validation(
            trigger=trigger,
            selector=selector,
            file_path=file_path,
            case_title=case_title
        )

        AssertUtils.assert_validation_error(
            field_name=selector if trigger != "upload" else "上传文件",
            actual_error_text=actual_error,
            expected=expected_error,
            case_title=case_title
        )
