"""全局配置管理"""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import Dict, List


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))
TEST_FILES_DIRECTORY_PATH = os.path.join(PROJECT_ROOT, "test_files")


class ServiceConfig(BaseSettings):
    """服务配置"""
    base_url: str
    login_url: str


class AccountConfig(BaseSettings):
    """账号配置"""
    username: str
    password: str
    sms_code: str = "34287"  # 测试用短信验证码


class EnvConfig(BaseSettings):
    """环境配置"""
    env_name: str
    timeout: int
    platform_side: ServiceConfig


class AccountEnvConfig(BaseSettings):
    """账号环境配置"""
    platform_side: AccountConfig


class ReportConfig(BaseSettings):
    """报告配置"""
    base_path: str = os.path.join(PROJECT_ROOT, "output")
    screenshot_on_failure: bool = True

    @property
    def results_dir(self) -> str:
        return os.path.join(self.base_path, "results")

    @property
    def screenshots_dir(self) -> str:
        return os.path.join(self.base_path, "screenshots")


class TestConfig(BaseSettings):
    """测试执行配置"""
    case_dir: str = "./tests"
    retry_count: int = 0
    retry_delay: int = 2
    test_type: str = "all"


class Settings(BaseSettings):
    """应用配置"""
    current_env: str = "test"

    ENV: Dict[str, EnvConfig] = {
        "test": EnvConfig(
            env_name="Test环境",
            timeout=35,
            platform_side=ServiceConfig(
                base_url="http://182.129.202.241:20051",
                login_url="/business/#/login"
            )
        ),
        "prod": EnvConfig(
            env_name="Prod环境",
            timeout=35,
            platform_side=ServiceConfig(
                base_url="https://msfw.sncitybrain.com",
                login_url="/business/#/login"
            )
        )
    }

    ACCOUNT: Dict[str, AccountEnvConfig] = {
        "test": AccountEnvConfig(
            platform_side=AccountConfig(
                username="Sn_admin",
                password="Smart@123456"
            )
        ),
        "prod": AccountEnvConfig(
            platform_side=AccountConfig(
                username="18606951794",
                password="5ykQU0ZpOP7oZRn1TWzZsQ=="
            )
        )
    }

    TEST: TestConfig = TestConfig()
    REPORT: ReportConfig = ReportConfig()

    @property
    def current_env_config(self) -> EnvConfig:
        return self.ENV[self.current_env]

    @property
    def current_account_config(self) -> AccountConfig:
        return self.ACCOUNT[self.current_env].platform_side

    @property
    def platform_side_url(self) -> str:
        return self.current_env_config.platform_side.base_url


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


settings = get_settings()
