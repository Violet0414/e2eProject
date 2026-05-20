"""pytest 配置和 fixtures"""
import pytest
import sys
from pathlib import Path
from datetime import datetime

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

    try:
        login_url = f"{settings.platform_side_url}{settings.current_env_config.platform_side.login_url}"
        logs.info(f"正在打开登录页: {login_url}")
        page.goto(login_url)
        page.wait_for_load_state("networkidle")

        page.wait_for_timeout(1000)

        page.fill("input[placeholder*='用户名'], input[name='username']", settings.current_account_config.username)
        page.wait_for_timeout(300)
        page.fill("input[placeholder*='密码'], input[name='password']", settings.current_account_config.password)
        page.wait_for_timeout(300)
        page.click("button[type='submit'], button:has-text('登录')")
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
    if call.when == "call" and call.failed:
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
