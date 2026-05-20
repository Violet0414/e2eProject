"""重点帮扶对象管理页面元素和操作"""
from pages.base_page import BasePage


class ObjectManagementPage(BasePage):
    """重点帮扶对象管理页面元素和操作"""

    # region ======= 重点帮扶对象管理元素选择器 ========
    ADD_BUTTON = "button:has-text('新增')"
    SEARCH_BUTTON = "button:has-text('查询')"
    RESET_BUTTON = "button:has-text('重置')"
    DIALOG_CONFIRM_BUTTON = ".el-dialog__footer button:has-text('确')"
    WIN_TITLE_NAME = "添加重点帮扶对象"

    # 新增/编辑表单字段选择器
    SELECTOR_OBJECT_NAME = 'input[placeholder="请输入对象名称"]'
    SELECTOR_OBJECT_NUMBER = 'input[placeholder="请输入对象号码"]'
    SELECTOR_ETHNICITY = 'input[placeholder="请选择民族"]'
    SELECTOR_GENDER = 'input[placeholder="请选择性别"]'
    SELECTOR_HIGHEST_EDUCATION = 'input[placeholder="请选择最高学历"]'
    SELECTOR_CONTACT_PHONE = 'input[placeholder="请输入联系手机"]'
    SELECTOR_UNEMPLOYMENT_TIME = 'input[placeholder="请选择失业时间"]'
    SELECTOR_UNEMPLOYMENT_INSURANCE = 'input[placeholder="请选择是否正在领取失业保险金"]'
    SELECTOR_DISTRICT = 'input[placeholder="请选择所属区域"]'
    SELECTOR_DETAILED_ADDRESS = 'input[placeholder="请选择地址"]'
    SELECTOR_PERSONNEL_TYPE = 'input[placeholder="请选择人员类型"]'
    SELECTOR_UNEMPLOYMENT_REASON = 'textarea[placeholder="请输入失业原因"]'
    SELECTOR_EMPLOYMENT_WISH = 'input[placeholder="请选择是否有就业意愿"]'
    SELECTOR_NEED_EMPLOYMENT_SERVICE = 'input[placeholder="请选择是否需要就业服务"]'
    SELECTOR_NEED_POLICY_CONSULT = 'input[placeholder="请选择是否需要就业创业政策咨询"]'
    SELECTOR_NEED_JOB_RECOMMEND = 'input[placeholder="请选择是否需要岗位推荐"]'
    SELECTOR_NEED_CAREER_GUIDANCE = 'input[placeholder="请选择是否需要职业指导"]'
    SELECTOR_NEED_EMPLOYMENT_TRAINING = 'input[placeholder="请选择是否需要就业培训"]'
    SELECTOR_NEED_ENTREPRENEUR_SERVICE = 'input[placeholder="请选择是否需要创业服务"]'
    SELECTOR_EMPLOYMENT_SERVICE_SITUATION = 'input[placeholder="请选择提供就业服务情况"]'
    SELECTOR_EMPLOYMENT_PROMOTION = 'input[placeholder="请选择促进实现就业情况"]'

    # 搜索区域选择器
    SELECTOR_SEARCH_OBJECT_NAME = 'input[placeholder="请输入对象名称"]'
    SELECTOR_SEARCH_OBJECT_NUMBER = 'input[placeholder="请输入对象号码"]'
    SELECTOR_SEARCH_DISTRICT = 'input[placeholder="请选择所属区划"]'
    SELECTOR_SEARCH_OBJECT_TYPE = 'input[placeholder="请选择对象类型"]'
    SELECTOR_SEARCH_EMPLOYMENT_STATUS = 'input[placeholder="请选择就业状态"]'
    SELECTOR_SEARCH_DATA_SOURCE = 'input[placeholder="请选择数据来源"]'
    SELECTOR_SEARCH_EMPLOYMENT_WISH = 'input[placeholder="请选择是否有就业愿望"]'
    SELECTOR_SEARCH_TASK_STATUS = 'input[placeholder="请选择任务状态"]'
    SELECTOR_SEARCH_UNEMPLOYMENT_INSURANCE = 'input[placeholder="请选择是否正在领取失业保险金"]'

    # endregion

    # region 私有填充方法

    def _fill_object_name(self, value: str):
        """填写对象名称"""
        if value is not None:
            self.fill(self.SELECTOR_OBJECT_NAME, value)

    def _fill_object_number(self, value: str):
        """填写对象号码"""
        if value is not None:
            self.fill(self.SELECTOR_OBJECT_NUMBER, value)

    def _fill_contact_phone(self, value: str):
        """填写联系手机"""
        if value is not None:
            self.fill(self.SELECTOR_CONTACT_PHONE, value)

    def _fill_unemployment_reason(self, value: str):
        """填写失业原因"""
        if value is not None:
            self.fill(self.SELECTOR_UNEMPLOYMENT_REASON, value)

    def _fill_detailed_address(self, value: str):
        """填写详细地址"""
        if value is not None:
            self.fill(self.SELECTOR_DETAILED_ADDRESS, value)

    def _select_ethnicity(self, option_index, elem_index=None):
        """选择民族下拉项"""
        if option_index is not None:
            if elem_index is not None:
                self.dropdown_selector.select_el_option_by_index(
                    self.SELECTOR_ETHNICITY, value=option_index, elem_index=elem_index
                )
            else:
                self.dropdown_selector.select_el_option_by_index(
                    self.SELECTOR_ETHNICITY, value=option_index
                )

    def _select_gender(self, option_index, elem_index=None):
        """选择性别下拉项"""
        if option_index is not None:
            if elem_index is not None:
                self.dropdown_selector.select_el_option_by_index(
                    self.SELECTOR_GENDER, value=option_index, elem_index=elem_index
                )
            else:
                self.dropdown_selector.select_el_option_by_index(
                    self.SELECTOR_GENDER, value=option_index
                )

    def _select_highest_education(self, option_index, elem_index=None):
        """选择最高学历下拉项"""
        if option_index is not None:
            if elem_index is not None:
                self.dropdown_selector.select_el_option_by_index(
                    self.SELECTOR_HIGHEST_EDUCATION, value=option_index, elem_index=elem_index
                )
            else:
                self.dropdown_selector.select_el_option_by_index(
                    self.SELECTOR_HIGHEST_EDUCATION, value=option_index
                )

    def _select_unemployment_insurance(self, option_index, elem_index=None):
        """选择是否正在领取失业保险金下拉项"""
        if option_index is not None:
            if elem_index is not None:
                self.dropdown_selector.select_el_option_by_index(
                    self.SELECTOR_UNEMPLOYMENT_INSURANCE, value=option_index, elem_index=elem_index
                )
            else:
                self.dropdown_selector.select_el_option_by_index(
                    self.SELECTOR_UNEMPLOYMENT_INSURANCE, value=option_index
                )

    def _select_personnel_type(self, option_index, elem_index=None):
        """选择人员类型下拉项"""
        if option_index is not None:
            if elem_index is not None:
                self.dropdown_selector.select_el_option_by_index(
                    self.SELECTOR_PERSONNEL_TYPE, value=option_index, elem_index=elem_index
                )
            else:
                self.dropdown_selector.select_el_option_by_index(
                    self.SELECTOR_PERSONNEL_TYPE, value=option_index
                )

    def _select_employment_wish(self, option_index, elem_index=None):
        """选择是否有就业意愿下拉项"""
        if option_index is not None:
            if elem_index is not None:
                self.dropdown_selector.select_el_option_by_index(
                    self.SELECTOR_EMPLOYMENT_WISH, value=option_index, elem_index=elem_index
                )
            else:
                self.dropdown_selector.select_el_option_by_index(
                    self.SELECTOR_EMPLOYMENT_WISH, value=option_index
                )

    def _select_need_employment_service(self, option_index, elem_index=None):
        """选择是否需要就业服务下拉项"""
        if option_index is not None:
            if elem_index is not None:
                self.dropdown_selector.select_el_option_by_index(
                    self.SELECTOR_NEED_EMPLOYMENT_SERVICE, value=option_index, elem_index=elem_index
                )
            else:
                self.dropdown_selector.select_el_option_by_index(
                    self.SELECTOR_NEED_EMPLOYMENT_SERVICE, value=option_index
                )

    def _select_need_policy_consult(self, option_index, elem_index=None):
        """选择是否需要就业创业政策咨询下拉项"""
        if option_index is not None:
            if elem_index is not None:
                self.dropdown_selector.select_el_option_by_index(
                    self.SELECTOR_NEED_POLICY_CONSULT, value=option_index, elem_index=elem_index
                )
            else:
                self.dropdown_selector.select_el_option_by_index(
                    self.SELECTOR_NEED_POLICY_CONSULT, value=option_index
                )

    def _select_need_job_recommend(self, option_index, elem_index=None):
        """选择是否需要岗位推荐下拉项"""
        if option_index is not None:
            if elem_index is not None:
                self.dropdown_selector.select_el_option_by_index(
                    self.SELECTOR_NEED_JOB_RECOMMEND, value=option_index, elem_index=elem_index
                )
            else:
                self.dropdown_selector.select_el_option_by_index(
                    self.SELECTOR_NEED_JOB_RECOMMEND, value=option_index
                )

    def _select_need_career_guidance(self, option_index, elem_index=None):
        """选择是否需要职业指导下拉项"""
        if option_index is not None:
            if elem_index is not None:
                self.dropdown_selector.select_el_option_by_index(
                    self.SELECTOR_NEED_CAREER_GUIDANCE, value=option_index, elem_index=elem_index
                )
            else:
                self.dropdown_selector.select_el_option_by_index(
                    self.SELECTOR_NEED_CAREER_GUIDANCE, value=option_index
                )

    def _select_need_employment_training(self, option_index, elem_index=None):
        """选择是否需要就业培训下拉项"""
        if option_index is not None:
            if elem_index is not None:
                self.dropdown_selector.select_el_option_by_index(
                    self.SELECTOR_NEED_EMPLOYMENT_TRAINING, value=option_index, elem_index=elem_index
                )
            else:
                self.dropdown_selector.select_el_option_by_index(
                    self.SELECTOR_NEED_EMPLOYMENT_TRAINING, value=option_index
                )

    def _select_need_entrepreneur_service(self, option_index, elem_index=None):
        """选择是否需要创业服务下拉项"""
        if option_index is not None:
            if elem_index is not None:
                self.dropdown_selector.select_el_option_by_index(
                    self.SELECTOR_NEED_ENTREPRENEUR_SERVICE, value=option_index, elem_index=elem_index
                )
            else:
                self.dropdown_selector.select_el_option_by_index(
                    self.SELECTOR_NEED_ENTREPRENEUR_SERVICE, value=option_index
                )

    def _select_employment_service_situation(self, option_index, elem_index=None):
        """选择提供就业服务情况下拉项"""
        if option_index is not None:
            if elem_index is not None:
                self.dropdown_selector.select_el_option_by_index(
                    self.SELECTOR_EMPLOYMENT_SERVICE_SITUATION, value=option_index, elem_index=elem_index
                )
            else:
                self.dropdown_selector.select_el_option_by_index(
                    self.SELECTOR_EMPLOYMENT_SERVICE_SITUATION, value=option_index
                )

    def _select_employment_promotion(self, option_index, elem_index=None):
        """选择促进实现就业情况下拉项"""
        if option_index is not None:
            if elem_index is not None:
                self.dropdown_selector.select_el_option_by_index(
                    self.SELECTOR_EMPLOYMENT_PROMOTION, value=option_index, elem_index=elem_index
                )
            else:
                self.dropdown_selector.select_el_option_by_index(
                    self.SELECTOR_EMPLOYMENT_PROMOTION, value=option_index
                )

    # endregion

    # region 搜索方法

    def search_by_object_name(self, object_name: str):
        """按对象名称搜索"""
        if object_name is not None:
            self.click(self.RESET_BUTTON)
            self.fill(self.SELECTOR_SEARCH_OBJECT_NAME, object_name)
            self.click(self.SEARCH_BUTTON)

    def search_by_object_number(self, object_number: str):
        """按对象号码搜索"""
        if object_number is not None:
            self.click(self.RESET_BUTTON)
            self.fill(self.SELECTOR_SEARCH_OBJECT_NUMBER, object_number)
            self.click(self.SEARCH_BUTTON)

    def search_by_object_type(self, option_index):
        """按对象类型搜索"""
        if option_index is not None:
            self.click(self.RESET_BUTTON)
            self._select_search_object_type(option_index)
            self.click(self.SEARCH_BUTTON)

    def search_by_employment_status(self, option_index):
        """按就业状态搜索"""
        if option_index is not None:
            self.click(self.RESET_BUTTON)
            self._select_search_employment_status(option_index)
            self.click(self.SEARCH_BUTTON)

    def search_by_task_status(self, option_index):
        """按任务状态搜索"""
        if option_index is not None:
            self.click(self.RESET_BUTTON)
            self._select_search_task_status(option_index)
            self.click(self.SEARCH_BUTTON)

    def reset_search(self):
        """重置搜索条件"""
        self.click(self.RESET_BUTTON)

    def _select_search_object_type(self, option_index, elem_index=None):
        """选择对象类型下拉项（搜索）"""
        if option_index is not None:
            if elem_index is not None:
                self.dropdown_selector.select_el_option_by_index(
                    self.SELECTOR_SEARCH_OBJECT_TYPE, value=option_index, elem_index=elem_index
                )
            else:
                self.dropdown_selector.select_el_option_by_index(
                    self.SELECTOR_SEARCH_OBJECT_TYPE, value=option_index
                )

    def _select_search_employment_status(self, option_index, elem_index=None):
        """选择就业状态下拉项（搜索）"""
        if option_index is not None:
            if elem_index is not None:
                self.dropdown_selector.select_el_option_by_index(
                    self.SELECTOR_SEARCH_EMPLOYMENT_STATUS, value=option_index, elem_index=elem_index
                )
            else:
                self.dropdown_selector.select_el_option_by_index(
                    self.SELECTOR_SEARCH_EMPLOYMENT_STATUS, value=option_index
                )

    def _select_search_task_status(self, option_index, elem_index=None):
        """选择任务状态下拉项（搜索）"""
        if option_index is not None:
            if elem_index is not None:
                self.dropdown_selector.select_el_option_by_index(
                    self.SELECTOR_SEARCH_TASK_STATUS, value=option_index, elem_index=elem_index
                )
            else:
                self.dropdown_selector.select_el_option_by_index(
                    self.SELECTOR_SEARCH_TASK_STATUS, value=option_index
                )

    # endregion

    # region 页面导航

    def goto_module(self):
        """进入重点帮扶对象管理模块"""
        self.navigate_menu(level1="重点帮扶", level2="重点帮扶对象管理")
        return self

    def navigate_to(self, route_path: str):
        """直接跳转到指定路径"""
        self.page.goto(route_path)
        return self

    # endregion

    # region 业务方法

    def open_add_dialog(self, dialog_title: str = "添加重点帮扶对象"):
        """打开新增弹窗"""
        self.click(self.ADD_BUTTON)
        self.wait_for_timeout(1000)

    def add_object(
        self,
        object_name: str = None,
        object_number: str = None,
        gender_index: int = None,
        contact_phone: str = None,
        personnel_type_index: int = None,
        ethnicity_index: int = None,
        highest_education_index: int = None,
        unemployment_insurance_index: int = None,
        unemployment_reason: str = None,
        employment_wish_index: int = None,
        need_employment_service_index: int = None,
        need_policy_consult_index: int = None,
        need_job_recommend_index: int = None,
        need_career_guidance_index: int = None,
        need_employment_training_index: int = None,
        need_entrepreneur_service_index: int = None,
        employment_service_situation_index: int = None,
        employment_promotion_index: int = None,
    ):
        """
        新增重点帮扶对象
        :param object_name: 对象名称
        :param object_number: 对象号码
        :param gender_index: 性别选项索引
        :param contact_phone: 联系手机
        :param personnel_type_index: 人员类型选项索引
        :param ethnicity_index: 民族选项索引
        :param highest_education_index: 最高学历选项索引
        :param unemployment_insurance_index: 是否正在领取失业保险金选项索引
        :param unemployment_reason: 失业原因
        :param employment_wish_index: 是否有就业意愿选项索引
        :param need_employment_service_index: 是否需要就业服务选项索引
        :param need_policy_consult_index: 是否需要就业创业政策咨询选项索引
        :param need_job_recommend_index: 是否需要岗位推荐选项索引
        :param need_career_guidance_index: 是否需要职业指导选项索引
        :param need_employment_training_index: 是否需要就业培训选项索引
        :param need_entrepreneur_service_index: 是否需要创业服务选项索引
        :param employment_service_situation_index: 提供就业服务情况选项索引
        :param employment_promotion_index: 促进实现就业情况选项索引
        """
        self._fill_object_name(object_name)
        self._fill_object_number(object_number)
        self._select_gender(gender_index)
        self._fill_contact_phone(contact_phone)
        self._select_personnel_type(personnel_type_index)
        self._select_ethnicity(ethnicity_index)
        self._select_highest_education(highest_education_index)
        self._select_unemployment_insurance(unemployment_insurance_index)
        self._fill_unemployment_reason(unemployment_reason)
        self._select_employment_wish(employment_wish_index)
        self._select_need_employment_service(need_employment_service_index)
        self._select_need_policy_consult(need_policy_consult_index)
        self._select_need_job_recommend(need_job_recommend_index)
        self._select_need_career_guidance(need_career_guidance_index)
        self._select_need_employment_training(need_employment_training_index)
        self._select_need_entrepreneur_service(need_entrepreneur_service_index)
        self._select_employment_service_situation(employment_service_situation_index)
        self._select_employment_promotion(employment_promotion_index)

    def submit_form(self):
        """提交表单"""
        self.click(self.DIALOG_CONFIRM_BUTTON)

    def wait_win_closed(self):
        """等待新增窗口关闭"""
        self.wait_windows_closed(self.WIN_TITLE_NAME, timeout=20000)

    def is_column_exist(self, column_name: str, timeout: int = 15000) -> bool:
        """
        搜索验证对象是否存在（用于新增后验证）
        Args:
            column_name: 搜索关键词
            timeout: 超时时间(毫秒)
        Returns:
            bool: 找到返回 True，否则返回 False
        """
        return self.table_operate.search_in_list(
            search_input_selector=self.SELECTOR_SEARCH_OBJECT_NAME,
            search_button_selector=self.SEARCH_BUTTON,
            search_keyword=column_name,
            timeout=timeout
        )

    def cancel_form(self):
        """取消表单"""
        self.click(".el-dialog__footer button:has-text('取消')")

    def close_detail_dialog(self):
        """关闭详情弹窗"""
        self.click(".el-dialog__footer button:has-text('返回')")

    # endregion
