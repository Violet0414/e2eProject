"""pytest 配置和 fixtures"""
import pytest
import sys
import os
from pathlib import Path

# 在导入其他模块之前设置 sys.path
# conftest.py 可能位于 e2e_runner/ 或 output/.../tests/
_current_file = Path(__file__).resolve()

# 向上查找 e2e_runner 目录
# 可能的路径：
#   1. /path/to/e2eProject/e2e_runner/conftest.py
#   2. /path/to/e2eProject/output/YYYY-MM-DD/tests/conftest.py
E2E_RUNNER_DIR = _current_file.parent
if E2E_RUNNER_DIR.name == "tests":
    # 如果在 output/.../tests/ 目录下，向上两级到 e2eProject
    # tests -> 2026-05-19 -> output -> e2eProject
    E2E_RUNNER_DIR = E2E_RUNNER_DIR.parent.parent.parent / "e2e_runner"
elif E2E_RUNNER_DIR.name == "e2e_runner":
    # 已经在 e2e_runner 目录
    pass
else:
    # 回退到默认位置
    E2E_RUNNER_DIR = Path(__file__).parent

# 添加 e2e_runner 相关路径到 sys.path
for subdir in ["", "pages", "common", "config", "datas"]:
    if subdir:
        path = E2E_RUNNER_DIR / subdir
    else:
        path = E2E_RUNNER_DIR
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

# 添加 output/{日期}/ 目录下的 pages 和 datas 到 sys.path（优先使用）
output_base = os.environ.get('E2E_OUTPUT_BASE')
if output_base:
    output_path = Path(output_base)
    for subdir in ["pages", "datas"]:
        path = output_path / subdir
        if path.exists() and str(path) not in sys.path:
            sys.path.insert(0, str(path))

from playwright.sync_api import sync_playwright, Browser, Page

from config.settings import settings
from common.logger import logs


@pytest.fixture(scope="session")
def browser():
    """浏览器实例 - 全局共享"""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            slow_mo=100
        )
        yield browser
        browser.close()


@pytest.fixture(scope="class")
def admin_page(browser: Browser):
    """后台管理页面 - 每个测试类独立上下文"""
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080}
    )
    page = context.new_page()

    # 登录凭证：优先使用环境变量，其次使用 settings 默认值
    login_username = os.environ.get('E2E_LOGIN_USERNAME') or settings.current_account_config.username
    login_password = os.environ.get('E2E_LOGIN_PASSWORD') or settings.current_account_config.password
    login_sms_code = os.environ.get('E2E_LOGIN_SMS_CODE') or settings.current_account_config.sms_code

    # 登录 URL：优先使用环境变量，其次使用 settings 默认值
    base_url = os.environ.get('E2E_BASE_URL') or settings.platform_side_url
    login_url_path = os.environ.get('E2E_LOGIN_URL') or settings.current_env_config.platform_side.login_url
    login_url = f"{base_url}{login_url_path}"

    try:
        logs.info(f"正在打开登录页: {login_url}")
        page.goto(login_url)
        page.wait_for_load_state("networkidle")

        page.wait_for_timeout(1000)

        page.fill("input[placeholder='账号'], input[placeholder*='账号']", login_username)
        page.wait_for_timeout(300)
        page.fill("input[placeholder='密码'], input[placeholder*='密码']", login_password)
        page.wait_for_timeout(300)
        # 填写短信验证码
        page.fill("input[placeholder='请输入验证码']", login_sms_code)
        page.wait_for_timeout(300)
        page.click("button:has-text('登录')")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)
        logs.info("登录成功")
    except Exception as e:
        logs.error(f"登录失败: {e}")
        page.screenshot(path=str(Path(settings.REPORT.screenshots_dir) / "login_failed.png"))

    yield page

    page.close()
    context.close()


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_makereport(item, call):
    """失败时自动截图"""
    if call.when == "call" and call.excinfo is not None:
        page = None
        if "admin_page" in item.funcargs:
            page = item.funcargs["admin_page"]
        elif "page" in item.funcargs:
            page = item.funcargs["page"]

        if page:
            screenshot_dir = Path(settings.REPORT.screenshots_dir)
            screenshot_dir.mkdir(parents=True, exist_ok=True)

            test_name = item.name.replace("[", "_").replace("]", "_").replace(" ", "_")
            screenshot_path = screenshot_dir / f"{test_name}_failed.png"
            try:
                page.screenshot(path=str(screenshot_path), full_page=True)
                logs.info(f"失败截图已保存: {screenshot_path}")
            except Exception as e:
                logs.error(f"截图失败: {e}")


def pytest_collection_modifyitems(config, items):
    """根据测试类型过滤用例"""
    test_type = settings.TEST.test_type

    if test_type == "all":
        return

    filtered_items = []
    for item in items:
        test_case = item.obj
        test_case_type = getattr(test_case, "_test_type", None)
        test_case_marker = None

        if hasattr(item, 'get_closest_marker'):
            test_case_marker = item.get_closest_marker("positive") or \
                              item.get_closest_marker("negative") or \
                              item.get_closest_marker("smoke")

        should_run = False
        if test_type == "positive":
            should_run = test_case_type == "positive" or test_case_marker and test_case_marker.name == "positive"
        elif test_type == "negative":
            should_run = test_case_type == "negative" or test_case_marker and test_case_marker.name == "negative"
        elif test_type == "smoke":
            should_run = test_case_type == "smoke" or test_case_marker and test_case_marker.name == "smoke"

        if should_run:
            filtered_items.append(item)

    items[:] = filtered_items
