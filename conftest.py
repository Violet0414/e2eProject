"""pytest fixtures"""
import sys
import os
from pathlib import Path

# 获取项目根目录和 e2e_runner 目录
PROJECT_ROOT = Path(__file__).parent
E2E_RUNNER_DIR = PROJECT_ROOT / "e2e_runner"


def pytest_configure(config):
    """pytest 配置 hook - 在测试收集前执行"""
    # 设置 PYTHONPATH 环境变量
    output_base = PROJECT_ROOT / "output"
    if output_base.exists():
        for date_dir in output_base.iterdir():
            if date_dir.is_dir():
                pages_dir = date_dir / "pages"
                if pages_dir.exists():
                    python_path = f"{pages_dir}:{date_dir}"
                    if 'PYTHONPATH' in os.environ:
                        os.environ['PYTHONPATH'] = python_path + ":" + os.environ['PYTHONPATH']
                    else:
                        os.environ['PYTHONPATH'] = python_path
                    # 更新 sys.path
                    sys.path.insert(0, str(pages_dir))
                    sys.path.insert(0, str(date_dir))
                    break


# 重要：先将 e2e_runner 路径添加到 sys.path，确保 conftest 的导入正确
sys.path.insert(0, str(E2E_RUNNER_DIR))

# 添加 output 目录（用于测试脚本导入页面对象等）
OUTPUT_DIR = PROJECT_ROOT / "output"
sys.path.insert(0, str(OUTPUT_DIR))

import pytest
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
