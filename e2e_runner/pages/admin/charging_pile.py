"""充电桩页面对象"""
import time
from typing import Optional

from pages.base_page import BasePage


class ChargingPilePage(BasePage):
    """充电桩管理页面"""

    # region ======= 充电桩页面元素选择器 ========
    ADD_BUTTON = "button:has-text('新增')"
    EDIT_BUTTON = "button:has-text('编辑')"
    DELETE_BUTTON = "text='删除'"
    SUBMIT_BUTTON = ".el-dialog__footer button:has-text('确')"
    CANCEL_BUTTON = ".el-dialog__footer button:has-text('取消')"
    RESET_BUTTON = "button:has-text('重置')"
    SEARCH_BUTTON = "button:has-text('查询')"
    CONFIRM_BUTTON = "button:has-text('确定')"

    # 新增/编辑表单选择器
    SELECTOR_CHARGING_PILE_NAME = "input[placeholder*='点位']"
    SELECTOR_STREET = "input[placeholder*='街道']"
    SELECTOR_ADDRESS = "input[placeholder*='详细地址']"
    SELECTOR_PLACE_TYPE = "input[placeholder*='场所类型']"
    SELECTOR_OPERATOR = "input[placeholder*='运营商']"
    SELECTOR_SERVICE_PHONE = "input[placeholder*='服务电话']"
    SELECTOR_TOTAL_PILES = "input[placeholder*='充电桩总数']"
    SELECTOR_FAST_PILES = "input[placeholder*='快充桩数']"
    SELECTOR_SLOW_PILES = "input[placeholder*='慢充桩数']"
    SELECTOR_INTERFACE_STANDARD = "input[placeholder*='接口标准']"
    SELECTOR_PARKING_NATURE = "input[placeholder*='停车场性质']"
    SELECTOR_CHARGING_FEE = "input[placeholder*='充电费用']"
    SELECTOR_PAYMENT_METHOD = "input[placeholder*='支付方式']"
    SELECTOR_OPERATIONAL_STATUS = "input[placeholder*='运营状态']"
    SELECTOR_SERVICE_HOURS = "input[placeholder*='营业时间']"
    SELECTOR_FACILITIES = "input[placeholder*='配套设施']"
    SELECTOR_MAINTENANCE_CONTACT = "input[placeholder*='维护联系人']"

    # 搜索选择器
    SELECTOR_SEARCH_NAME = "input[placeholder*='点位']"

    # endregion

    def goto_module(self):
        """进入充电桩模块"""
        self.navigate_menu(level1="公共基础资源档案", level2="公用设施", level3="充电桩")
        self.page.wait_for_timeout(1000)
        return self

    def add_charging_pile(self, charging_pile_name: str = None, street_index: int = None,
                          address_index: int = None, place_type: str = None, operator: str = None,
                          service_phone: str = None, total_piles: str = None, fast_piles: str = None,
                          slow_piles: str = None, interface_standard: str = None,
                          parking_nature: str = None, charging_fee: str = None,
                          payment_method: str = None, operational_status: str = None,
                          service_hours: str = None, facilities: str = None,
                          maintenance_contact: str = None):
        """
        填写充电桩表单

        :param charging_pile_name: 点位/桩群名称
        :param street_index: 街道下拉索引
        :param address_index: 详细地址下拉索引
        :param place_type: 场所类型
        :param operator: 运营商/品牌
        :param service_phone: 服务电话
        :param total_piles: 充电桩总数
        :param fast_piles: 快充桩数
        :param slow_piles: 慢充桩数
        :param interface_standard: 接口标准
        :param parking_nature: 停车场性质
        :param charging_fee: 充电费用
        :param payment_method: 支付方式
        :param operational_status: 运营状态
        :param service_hours: 营业时间
        :param facilities: 配套设施
        :param maintenance_contact: 维护联系人
        """
        if charging_pile_name is not None:
            self.fill(self.SELECTOR_CHARGING_PILE_NAME, charging_pile_name)
            self.page.wait_for_timeout(200)

        if street_index is not None:
            self.dropdown_selector.select_el_option_by_index(self.SELECTOR_STREET, value=street_index)
            self.page.wait_for_timeout(200)

        if address_index is not None:
            self.dropdown_selector.select_el_option_by_index(self.SELECTOR_ADDRESS, value=address_index)
            self.page.wait_for_timeout(200)

        if place_type is not None:
            self._select_dropdown_option(self.SELECTOR_PLACE_TYPE, place_type)
            self.page.wait_for_timeout(200)

        if operator is not None:
            self.fill(self.SELECTOR_OPERATOR, operator)
            self.page.wait_for_timeout(200)

        if service_phone is not None:
            self.fill(self.SELECTOR_SERVICE_PHONE, service_phone)
            self.page.wait_for_timeout(200)

        if total_piles is not None:
            self.fill(self.SELECTOR_TOTAL_PILES, str(total_piles))
            self.page.wait_for_timeout(200)

        if fast_piles is not None:
            self.fill(self.SELECTOR_FAST_PILES, str(fast_piles))
            self.page.wait_for_timeout(200)

        if slow_piles is not None:
            self.fill(self.SELECTOR_SLOW_PILES, str(slow_piles))
            self.page.wait_for_timeout(200)

        if interface_standard is not None:
            self._select_dropdown_option(self.SELECTOR_INTERFACE_STANDARD, interface_standard)
            self.page.wait_for_timeout(200)

        if parking_nature is not None:
            self._select_dropdown_option(self.SELECTOR_PARKING_NATURE, parking_nature)
            self.page.wait_for_timeout(200)

        if charging_fee is not None:
            self.fill(self.SELECTOR_CHARGING_FEE, str(charging_fee))
            self.page.wait_for_timeout(200)

        if payment_method is not None:
            self._select_dropdown_option(self.SELECTOR_PAYMENT_METHOD, payment_method)
            self.page.wait_for_timeout(200)

        if operational_status is not None:
            self._select_dropdown_option(self.SELECTOR_OPERATIONAL_STATUS, operational_status)
            self.page.wait_for_timeout(200)

        if service_hours is not None:
            self.fill(self.SELECTOR_SERVICE_HOURS, service_hours)
            self.page.wait_for_timeout(200)

        if facilities is not None:
            self._select_dropdown_option(self.SELECTOR_FACILITIES, facilities)
            self.page.wait_for_timeout(200)

        if maintenance_contact is not None:
            self.fill(self.SELECTOR_MAINTENANCE_CONTACT, maintenance_contact)
            self.page.wait_for_timeout(200)

    def _select_dropdown_option(self, selector: str, value: str):
        """选择下拉选项"""
        try:
            dropdown = self.page.locator(selector)
            dropdown.click()
            self.page.wait_for_timeout(300)
            option = self.page.locator(f".el-select-dropdown__item:has-text('{value}')").first
            option.click()
            self.page.wait_for_timeout(200)
        except Exception:
            pass

    def open_edit_dialog(self):
        """打开编辑弹窗"""
        try:
            edit_btn = self.page.locator("button:has-text('编辑')").first
            if edit_btn.is_visible(timeout=3000):
                edit_btn.click()
                self.page.wait_for_timeout(500)
        except Exception:
            pass
        return self

    def upload_attachment(self, file_path: str):
        """上传附件"""
        if file_path is not None:
            self.file_uploader.upload_el_file("button:has-text('点击上传')", file_path)
        return self

    def submit_form(self):
        """提交表单"""
        try:
            submit_btn = self.page.locator(self.SUBMIT_BUTTON).first
            submit_btn.click()
            self.page.wait_for_timeout(500)
        except Exception:
            pass
        return self

    def close_dialog(self):
        """关闭弹窗"""
        try:
            self.page.keyboard.press("Escape")
            self.page.wait_for_timeout(300)
        except Exception:
            pass
        return self

    def reset_search(self):
        """重置搜索条件"""
        try:
            reset_btn = self.page.locator(self.RESET_BUTTON)
            if reset_btn.is_visible(timeout=3000):
                reset_btn.click()
                self.page.wait_for_timeout(300)
        except Exception:
            pass
        return self

    def search(self, **kwargs):
        """搜索"""
        for key, value in kwargs.items():
            if value is not None:
                try:
                    if key == "charging_pile_name":
                        selector = self.SELECTOR_SEARCH_NAME
                    else:
                        selector = f"input[placeholder*='{key}']"
                    self.page.locator(selector).fill(str(value))
                    self.page.wait_for_timeout(200)
                except Exception:
                    pass
        try:
            search_btn = self.page.locator(self.SEARCH_BUTTON).first
            search_btn.click()
            self.page.wait_for_timeout(500)
        except Exception:
            pass
        return self
