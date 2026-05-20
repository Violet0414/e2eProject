"""重点帮扶对象管理测试数据"""
import os

from common.data_generation import fake_data
from config.settings import TEST_FILES_DIRECTORY_PATH
from pages.admin.object_management import ObjectManagementPage


# ==================== 新增重点帮扶对象测试数据 ====================
OBJECT_ADD_TEST_DATA = [
    # ========== 冒烟测试 ==========
    {
        "title": "冒烟-完整填写所有字段提交成功",
        "type": "smoke",
        "expect_success": True,
        "route_path": "/emphaticAssistance/objectManagement",
        "data": {
            "object_name": f"测试对象-{fake_data.random_4bit_str()}",
            "object_number": "522723198504254146",
            "gender_index": 0,
            "contact_phone": "18545555555",
            "personnel_type_index": 0,
            "ethnicity_index": None,
            "highest_education_index": None,
            "unemployment_insurance_index": None,
            "unemployment_reason": None,
            "employment_wish_index": None,
            "need_employment_service_index": None,
            "need_policy_consult_index": None,
            "need_job_recommend_index": None,
            "need_career_guidance_index": None,
            "need_employment_training_index": None,
            "need_entrepreneur_service_index": None,
            "employment_service_situation_index": None,
            "employment_promotion_index": None,
        }
    },  # 冒烟-完整填写

    # ========== 正向测试 ==========
    {
        "title": "正向-只填写必填字段提交成功",
        "type": "positive",
        "expect_success": True,
        "route_path": "/emphaticAssistance/objectManagement",
        "data": {
            "object_name": f"测试对象-{fake_data.random_4bit_str()}",
            "object_number": "522723198504254146",
            "gender_index": 0,
            "contact_phone": "18545555555",
            "personnel_type_index": 0,
            "ethnicity_index": None,
            "highest_education_index": None,
            "unemployment_insurance_index": None,
            "unemployment_reason": None,
            "employment_wish_index": None,
            "need_employment_service_index": None,
            "need_policy_consult_index": None,
            "need_job_recommend_index": None,
            "need_career_guidance_index": None,
            "need_employment_training_index": None,
            "need_entrepreneur_service_index": None,
            "employment_service_situation_index": None,
            "employment_promotion_index": None,
        }
    },  # 正向-只填写必填字段

    # ========== 反向测试 ==========
    {
        "title": "反向-对象名称为空",
        "type": "negative",
        "expect_success": False,
        "route_path": "/emphaticAssistance/objectManagement",
        "validation_info": {
            "selector": ObjectManagementPage.SELECTOR_OBJECT_NAME,
            "expected_error_text": "请输入对象名称",
            "trigger": "blur"
        },
        "data": {
            "object_name": None,
            "object_number": "522723198504254146",
            "gender_index": 0,
            "contact_phone": "18545555555",
            "personnel_type_index": 0,
            "ethnicity_index": None,
            "highest_education_index": None,
            "unemployment_insurance_index": None,
            "unemployment_reason": None,
            "employment_wish_index": None,
            "need_employment_service_index": None,
            "need_policy_consult_index": None,
            "need_job_recommend_index": None,
            "need_career_guidance_index": None,
            "need_employment_training_index": None,
            "need_entrepreneur_service_index": None,
            "employment_service_situation_index": None,
            "employment_promotion_index": None,
        }
    },  # 反向-对象名称为空

    {
        "title": "反向-对象号码为空",
        "type": "negative",
        "expect_success": False,
        "route_path": "/emphaticAssistance/objectManagement",
        "validation_info": {
            "selector": ObjectManagementPage.SELECTOR_OBJECT_NUMBER,
            "expected_error_text": "请输入对象号码",
            "trigger": "blur"
        },
        "data": {
            "object_name": f"测试对象-{fake_data.random_4bit_str()}",
            "object_number": None,
            "gender_index": 0,
            "contact_phone": "18545555555",
            "personnel_type_index": 0,
            "ethnicity_index": None,
            "highest_education_index": None,
            "unemployment_insurance_index": None,
            "unemployment_reason": None,
            "employment_wish_index": None,
            "need_employment_service_index": None,
            "need_policy_consult_index": None,
            "need_job_recommend_index": None,
            "need_career_guidance_index": None,
            "need_employment_training_index": None,
            "need_entrepreneur_service_index": None,
            "employment_service_situation_index": None,
            "employment_promotion_index": None,
        }
    },  # 反向-对象号码为空

    {
        "title": "反向-性别为空",
        "type": "negative",
        "expect_success": False,
        "route_path": "/emphaticAssistance/objectManagement",
        "validation_info": {
            "selector": ObjectManagementPage.SELECTOR_GENDER,
            "expected_error_text": "请选择性别",
            "trigger": "submit"
        },
        "data": {
            "object_name": f"测试对象-{fake_data.random_4bit_str()}",
            "object_number": "522723198504254146",
            "gender_index": None,
            "contact_phone": "18545555555",
            "personnel_type_index": 0,
            "ethnicity_index": None,
            "highest_education_index": None,
            "unemployment_insurance_index": None,
            "unemployment_reason": None,
            "employment_wish_index": None,
            "need_employment_service_index": None,
            "need_policy_consult_index": None,
            "need_job_recommend_index": None,
            "need_career_guidance_index": None,
            "need_employment_training_index": None,
            "need_entrepreneur_service_index": None,
            "employment_service_situation_index": None,
            "employment_promotion_index": None,
        }
    },  # 反向-性别为空

    {
        "title": "反向-联系手机为空",
        "type": "negative",
        "expect_success": False,
        "route_path": "/emphaticAssistance/objectManagement",
        "validation_info": {
            "selector": ObjectManagementPage.SELECTOR_CONTACT_PHONE,
            "expected_error_text": "请输入联系手机",
            "trigger": "blur"
        },
        "data": {
            "object_name": f"测试对象-{fake_data.random_4bit_str()}",
            "object_number": "522723198504254146",
            "gender_index": 0,
            "contact_phone": None,
            "personnel_type_index": 0,
            "ethnicity_index": None,
            "highest_education_index": None,
            "unemployment_insurance_index": None,
            "unemployment_reason": None,
            "employment_wish_index": None,
            "need_employment_service_index": None,
            "need_policy_consult_index": None,
            "need_job_recommend_index": None,
            "need_career_guidance_index": None,
            "need_employment_training_index": None,
            "need_entrepreneur_service_index": None,
            "employment_service_situation_index": None,
            "employment_promotion_index": None,
        }
    },  # 反向-联系手机为空

    {
        "title": "反向-人员类型为空",
        "type": "negative",
        "expect_success": False,
        "route_path": "/emphaticAssistance/objectManagement",
        "validation_info": {
            "selector": ObjectManagementPage.SELECTOR_PERSONNEL_TYPE,
            "expected_error_text": "请选择人员类型",
            "trigger": "submit"
        },
        "data": {
            "object_name": f"测试对象-{fake_data.random_4bit_str()}",
            "object_number": "522723198504254146",
            "gender_index": 0,
            "contact_phone": "18545555555",
            "personnel_type_index": None,
            "ethnicity_index": None,
            "highest_education_index": None,
            "unemployment_insurance_index": None,
            "unemployment_reason": None,
            "employment_wish_index": None,
            "need_employment_service_index": None,
            "need_policy_consult_index": None,
            "need_job_recommend_index": None,
            "need_career_guidance_index": None,
            "need_employment_training_index": None,
            "need_entrepreneur_service_index": None,
            "employment_service_situation_index": None,
            "employment_promotion_index": None,
        }
    },  # 反向-人员类型为空

    {
        "title": "反向-对象名称超过长度限制",
        "type": "negative",
        "expect_success": False,
        "route_path": "/emphaticAssistance/objectManagement",
        "validation_info": {
            "selector": ObjectManagementPage.SELECTOR_OBJECT_NAME,
            "expected_error_text": "对象名称长度不能超过15",
            "trigger": "submit"
        },
        "data": {
            "object_name": "测试对象名称超过15字符的测试数据",
            "object_number": "522723198504254146",
            "gender_index": 0,
            "contact_phone": "18545555555",
            "personnel_type_index": 0,
            "ethnicity_index": None,
            "highest_education_index": None,
            "unemployment_insurance_index": None,
            "unemployment_reason": None,
            "employment_wish_index": None,
            "need_employment_service_index": None,
            "need_policy_consult_index": None,
            "need_job_recommend_index": None,
            "need_career_guidance_index": None,
            "need_employment_training_index": None,
            "need_entrepreneur_service_index": None,
            "employment_service_situation_index": None,
            "employment_promotion_index": None,
        }
    },  # 反向-对象名称超过长度限制

    {
        "title": "反向-失业原因超过长度限制",
        "type": "negative",
        "expect_success": False,
        "route_path": "/emphaticAssistance/objectManagement",
        "validation_info": {
            "selector": ObjectManagementPage.SELECTOR_UNEMPLOYMENT_REASON,
            "expected_error_text": "失业原因长度不能超过100",
            "trigger": "submit"
        },
        "data": {
            "object_name": f"测试对象-{fake_data.random_4bit_str()}",
            "object_number": "522723198504254146",
            "gender_index": 0,
            "contact_phone": "18545555555",
            "personnel_type_index": 0,
            "ethnicity_index": None,
            "highest_education_index": None,
            "unemployment_insurance_index": None,
            "unemployment_reason": "因企业倒闭导致失业，需要重新就业，这是一个很长的失业原因描述超过了100字符的限制范围",
            "employment_wish_index": None,
            "need_employment_service_index": None,
            "need_policy_consult_index": None,
            "need_job_recommend_index": None,
            "need_career_guidance_index": None,
            "need_employment_training_index": None,
            "need_entrepreneur_service_index": None,
            "employment_service_situation_index": None,
            "employment_promotion_index": None,
        }
    },  # 反向-失业原因超过长度限制

    {
        "title": "正向-所有就业意愿选项都填写",
        "type": "positive",
        "expect_success": True,
        "route_path": "/emphaticAssistance/objectManagement",
        "data": {
            "object_name": f"测试对象-{fake_data.random_4bit_str()}",
            "object_number": "522723198504254146",
            "gender_index": 0,
            "contact_phone": "18545555555",
            "personnel_type_index": 0,
            "ethnicity_index": 1,
            "highest_education_index": 1,
            "unemployment_insurance_index": 0,
            "unemployment_reason": "企业倒闭",
            "employment_wish_index": 0,
            "need_employment_service_index": 0,
            "need_policy_consult_index": 0,
            "need_job_recommend_index": 0,
            "need_career_guidance_index": 0,
            "need_employment_training_index": 0,
            "need_entrepreneur_service_index": 0,
            "employment_service_situation_index": 0,
            "employment_promotion_index": 0,
        }
    },  # 正向-所有就业意愿选项都填写
]

# ==================== 查询重点帮扶对象测试数据 ====================
OBJECT_SEARCH_TEST_DATA = [
    {
        "title": "正向-按对象名称精确查询",
        "type": "positive",
        "expect_success": True,
        "route_path": "/emphaticAssistance/objectManagement",
        "data": {
            "search_type": "object_name",
            "search_value": "1111",
        }
    },
    {
        "title": "正向-按对象号码精确查询",
        "type": "positive",
        "expect_success": True,
        "route_path": "/emphaticAssistance/objectManagement",
        "data": {
            "search_type": "object_number",
            "search_value": "522723198504254146",
        }
    },
    {
        "title": "正向-按对象类型查询",
        "type": "positive",
        "expect_success": True,
        "route_path": "/emphaticAssistance/objectManagement",
        "data": {
            "search_type": "object_type",
            "search_value": 0,  # 登记失业人员
        }
    },
    {
        "title": "正向-按就业状态查询",
        "type": "positive",
        "expect_success": True,
        "route_path": "/emphaticAssistance/objectManagement",
        "data": {
            "search_type": "employment_status",
            "search_value": 0,  # 已就业
        }
    },
    {
        "title": "正向-按任务状态查询",
        "type": "positive",
        "expect_success": True,
        "route_path": "/emphaticAssistance/objectManagement",
        "data": {
            "search_type": "task_status",
            "search_value": 0,  # 待帮扶
        }
    },
    {
        "title": "正向-多条件组合查询",
        "type": "positive",
        "expect_success": True,
        "route_path": "/emphaticAssistance/objectManagement",
        "data": {
            "search_type": "combined",
            "object_type": 1,  # 退役军人
            "employment_status": 1,  # 未就业
            "task_status": 2,  # 帮扶中
        }
    },
    {
        "title": "正向-重置查询条件",
        "type": "positive",
        "expect_success": True,
        "route_path": "/emphaticAssistance/objectManagement",
        "data": {
            "search_type": "reset",
        }
    },
    {
        "title": "反向-查询不存在的数据",
        "type": "negative",
        "expect_success": False,
        "route_path": "/emphaticAssistance/objectManagement",
        "data": {
            "search_type": "object_name",
            "search_value": "test_nonexist_12345",
            "expect_count": 0,
        }
    },
]

# ==================== 编辑重点帮扶对象测试数据 ====================
OBJECT_EDIT_TEST_DATA = [
    {
        "title": "正向-修改联系电话",
        "type": "positive",
        "expect_success": True,
        "route_path": "/emphaticAssistance/objectManagement",
        "data": {
            "object_name": "1111",
            "edit_field": "contact_phone",
            "new_value": "13800000000",
        }
    },
    {
        "title": "正向-清空非必填字段后保存",
        "type": "positive",
        "expect_success": True,
        "route_path": "/emphaticAssistance/objectManagement",
        "data": {
            "object_name": "1111",
            "edit_field": "optional_fields",
            "clear_fields": ["ethnicity", "highest_education", "unemployment_reason"],
        }
    },
]
