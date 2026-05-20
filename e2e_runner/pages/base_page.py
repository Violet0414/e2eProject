"""页面对象基类"""
from playwright.sync_api import Page, Locator, expect
from typing import Optional

from config.settings import settings
from common.components import FormValidator, FileUploader, DropdownSelector, TableOperate, MessageTip


class BasePage:
    """所有页面对象的基类"""

    def __init__(self, page: Page):
        self.page: Page = page
        self.base_url = settings.platform_side_url
        self.timeout = settings.current_env_config.timeout * 1000
        self.form_validator = FormValidator(page)
        self.file_uploader = FileUploader(page)
        self.dropdown_selector = DropdownSelector(page)
        self.table_operate = TableOperate(page)
        self.message_tip = MessageTip(page)

    def navigate_to(self, path: str = ""):
        """导航到页面"""
        self.page.goto(f"{self.base_url}{path}")
        return self

    def navigate_url(self, url: str):
        """导航到完整URL"""
        self.page.goto(url)
        return self

    def click(self, selector: str, force: bool = False):
        """点击元素"""
        self.page.locator(selector).click(force=force)
        return self

    def fill(self, selector: str, value: str):
        """填充输入框"""
        self.page.locator(selector).fill(value)
        return self

    def clear(self, selector: str):
        """清空输入框"""
        self.page.locator(selector).clear()
        return self

    def get_text(self, selector: str) -> str:
        """获取元素文本"""
        return self.page.locator(selector).inner_text()

    def get_value(self, selector: str) -> str:
        """获取输入框值"""
        return self.page.locator(selector).input_value()

    def is_visible(self, selector: str) -> bool:
        """判断元素是否可见"""
        return self.page.locator(selector).is_visible()

    def is_enabled(self, selector: str) -> bool:
        """判断元素是否可用"""
        return self.page.locator(selector).is_enabled()

    def wait_for_selector(self, selector: str, timeout: int = None):
        """等待元素出现"""
        timeout = timeout or self.timeout
        self.page.wait_for_selector(selector, timeout=timeout)
        return self

    def wait_for_load_state(self, state: str = "networkidle"):
        """等待页面加载状态"""
        self.page.wait_for_load_state(state)
        return self

    def wait_for_timeout(self, timeout: int):
        """等待指定时间（毫秒）"""
        self.page.wait_for_timeout(timeout)
        return self

    def wait_win_closed(self, timeout: int = 5000):
        """等待弹窗关闭"""
        self.page.wait_for_timeout(500)
        try:
            close_btn = self.page.locator("button:has-text('取消'), button:has-text('关闭')").last
            if close_btn.is_visible(timeout=2000):
                close_btn.click()
                self.page.wait_for_timeout(300)
        except Exception:
            pass
        return self

    def close_dialog(self):
        """关闭弹窗"""
        try:
            esc_key = self.page.keyboard.press("Escape")
            self.page.wait_for_timeout(300)
        except Exception:
            pass
        return self

    def take_screenshot(self, name: str = None, full_page: bool = True) -> str:
        """截图"""
        from pathlib import Path
        from datetime import datetime

        screenshot_dir = Path(settings.REPORT.screenshots_dir)
        screenshot_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{name or datetime.now().strftime('%H%M%S')}.png"
        path = screenshot_dir / filename
        self.page.screenshot(path=str(path), full_page=full_page)
        return str(path)

    def submit_form(self):
        """提交表单"""
        try:
            submit_btn = self.page.locator("button:has-text('提交'), .el-dialog__footer button:has-text('确')").first
            submit_btn.click()
        except Exception:
            pass
        return self

    def is_submit_success(self, use_tip: bool = False, success_text: str = "操作成功",
                         use_url_wait: bool = False, wait_url: str = "",
                         use_url_check: bool = False, check_url: str = "") -> bool:
        """
        判断提交是否成功

        :param use_tip: 使用提示判断
        :param success_text: 成功提示文本
        :param use_url_wait: 使用URL等待判断
        :param wait_url: 等待的URL
        :param use_url_check: 使用URL检查判断
        :param check_url: 检查的URL
        :return: 是否成功
        """
        if use_tip:
            try:
                self.page.wait_for_timeout(1000)
                tip = self.page.locator(".el-message--success, .el-notification--success").first
                if tip.is_visible(timeout=3000):
                    tip_text = tip.inner_text()
                    return success_text in tip_text
            except Exception:
                pass

        if use_url_wait:
            try:
                self.page.wait_for_url(wait_url, timeout=self.timeout)
                return True
            except Exception:
                pass

        if use_url_check:
            current_url = self.page.url
            return check_url in current_url

        return False

    def is_column_exist(self, column_name: str, column_selector: str = ".el-table__body-wrapper tbody tr") -> bool:
        """判断列表中是否存在某条数据"""
        try:
            self.page.wait_for_timeout(1000)
            rows = self.page.locator(column_selector)
            count = rows.count()
            for i in range(count):
                row_text = rows.nth(i).inner_text()
                if column_name in row_text:
                    return True
            return False
        except Exception:
            return False

    def open_add_dialog(self):
        """打开新增弹窗"""
        try:
            add_btn = self.page.locator("button:has-text('新增'), button:has-text('添加')").first
            add_btn.click()
            self.page.wait_for_timeout(500)
        except Exception:
            pass
        return self

    def reset_search(self):
        """重置搜索"""
        try:
            reset_btn = self.page.locator("button:has-text('重置')")
            reset_btn.click()
            self.page.wait_for_timeout(300)
        except Exception:
            pass
        return self

    def search(self, **kwargs):
        """搜索"""
        for key, value in kwargs.items():
            if value is not None:
                selector = f"input[placeholder*='{key}'], input[placeholder*='{value}']"
                try:
                    self.page.locator(selector).fill(str(value))
                except Exception:
                    pass
        try:
            search_btn = self.page.locator("button:has-text('查询'), button:has-text('搜索')").first
            search_btn.click()
            self.page.wait_for_timeout(500)
        except Exception:
            pass
        return self

    def navigate_menu(self, level1: str = None, level2: str = None, level3: str = None):
        """
        通过菜单层级导航到指定模块

        :param level1: 一级菜单名称
        :param level2: 二级菜单名称
        :param level3: 三级菜单名称
        """
        import time

        def click_menu_item(text: str):
            """点击菜单项"""
            # 尝试多种选择器模式
            selectors = [
                f"text='{text}'",
                f"span:has-text('{text}')",
                f"li:has-text('{text}')",
                f".menu-wrapper:has-text('{text}')",
            ]
            for selector in selectors:
                try:
                    element = self.page.locator(selector).first
                    if element.is_visible(timeout=2000):
                        element.click()
                        time.sleep(0.3)
                        return True
                except Exception:
                    continue
            return False

        # 点击一级菜单
        if level1:
            click_menu_item(level1)
            self.page.wait_for_timeout(300)

        # 点击二级菜单
        if level2:
            click_menu_item(level2)
            self.page.wait_for_timeout(300)

        # 点击三级菜单
        if level3:
            click_menu_item(level3)
            self.page.wait_for_timeout(500)

        return self
