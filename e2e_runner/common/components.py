"""表单验证器"""
from playwright.sync_api import Page


class FormValidator:
    """表单字段验证工具"""

    def __init__(self, page: Page):
        self.page = page

    def blur_trigger_field_validation(self, selector: str, trigger: str = "blur"):
        """触发字段验证（blur/submit）"""
        try:
            element = self.page.locator(selector).first
            element.blur()
            self.page.wait_for_timeout(300)
        except Exception:
            pass

    def get_field_error_text(self, selector: str) -> str:
        """获取字段的错误提示文本"""
        try:
            # 常见的错误提示元素选择器
            error_selectors = [
                f"{selector}.el-form-item__error",
                f"{selector}-error",
                ".el-form-item__error",
                ".el-form-item__error:visible",
            ]
            for error_selector in error_selectors:
                try:
                    error_elem = self.page.locator(error_selector).first
                    if error_elem.is_visible(timeout=2000):
                        return error_elem.inner_text()
                except Exception:
                    continue
            return ""
        except Exception:
            return ""

    def get_field_error_after_submit(self, selector: str = None) -> str:
        """提交后获取字段错误文本"""
        try:
            self.page.wait_for_timeout(500)
            # 尝试多种错误提示选择器
            error_selectors = [
                ".el-form-item__error",
                ".el-form-item__error:visible",
                ".el-form-item.is-error .el-form-item__error",
            ]
            for error_selector in error_selectors:
                try:
                    error_elems = self.page.locator(error_selector)
                    if error_elems.count() > 0:
                        for i in range(error_elems.count()):
                            error_text = error_elems.nth(i).inner_text()
                            if error_text:
                                return error_text
                except Exception:
                    continue
            return ""
        except Exception:
            return ""

    def get_upload_error_text(self) -> str:
        """获取上传组件的错误提示"""
        try:
            error_selectors = [
                ".el-upload__tip",
                ".el-upload__tip:visible",
                ".el-form-item__error",
            ]
            for error_selector in error_selectors:
                try:
                    error_elem = self.page.locator(error_selector).first
                    if error_elem.is_visible(timeout=2000):
                        text = error_elem.inner_text()
                        if text:
                            return text
                except Exception:
                    continue
            return ""
        except Exception:
            return ""


class FileUploader:
    """文件上传工具"""

    def __init__(self, page: Page):
        self.page = page

    def upload_el_file(self, button_selector: str, file_path: str, timeout: int = 30000):
        """上传文件"""
        if file_path is None:
            return
        try:
            self.page.locator(button_selector).first.click()
            self.page.wait_for_timeout(500)
            # 设置文件到文件输入框
            file_input = self.page.locator("input[type='file']")
            file_input.set_input_files(file_path)
            self.page.wait_for_timeout(1000)
        except Exception as e:
            raise f"文件上传失败: {e}"


class DropdownSelector:
    """下拉选择器"""

    def __init__(self, page: Page):
        self.page = page

    def select_el_option_by_index(self, selector: str, value, elem_index: str = "first"):
        """通过索引选择下拉选项"""
        try:
            dropdown = self.page.locator(selector)
            if elem_index == "first":
                dropdown = dropdown.first
            elif elem_index == "last":
                dropdown = dropdown.last
            elif isinstance(elem_index, int):
                dropdown = dropdown.nth(elem_index)
            dropdown.click()
            self.page.wait_for_timeout(300)

            # 点击选项
            option_selector = f".el-select-dropdown__item:has-text('{value}')"
            option = self.page.locator(option_selector).first
            option.click()
            self.page.wait_for_timeout(200)
        except Exception:
            pass


class TableOperate:
    """表格操作工具"""

    def __init__(self, page: Page):
        self.page = page

    def search_in_list(self, search_button_selector: str, search_conditions: dict,
                        reset_button_selector: str = None, table_row_selector: str = ".el-table__body tr",
                        timeout: int = 15000) -> int:
        """在表格中搜索并返回结果数量"""
        try:
            # 填写搜索条件
            for key, condition in search_conditions.items():
                selector = condition.get("selector")
                value = condition.get("value")
                if selector and value:
                    self.page.locator(selector).fill(str(value))
                    self.page.wait_for_timeout(200)

            # 点击搜索按钮
            self.page.locator(search_button_selector).click()
            self.page.wait_for_timeout(1000)

            # 返回结果数量
            rows = self.page.locator(table_row_selector)
            return rows.count()
        except Exception:
            return 0


class MessageTip:
    """消息提示工具"""

    def __init__(self, page: Page):
        self.page = page

    def get_el_message(self) -> str:
        """获取 Element 消息提示"""
        try:
            message = self.page.locator(".el-message").first
            if message.is_visible(timeout=2000):
                return message.inner_text()
            return ""
        except Exception:
            return ""
