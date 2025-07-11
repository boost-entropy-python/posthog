import os
import tempfile
import time
import uuid
from datetime import timedelta
from typing import Literal, Optional

from posthog.schema_migrations.upgrade_manager import upgrade_query
import structlog
import posthoganalytics
from django.conf import settings
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

from posthog.api.services.query import process_query_dict
from posthog.exceptions_capture import capture_exception
from posthog.hogql.constants import LimitContext
from posthog.hogql_queries.query_runner import ExecutionMode
from posthog.models.exported_asset import (
    ExportedAsset,
    get_public_access_token,
    save_content,
)
from posthog.tasks.exporter import (
    EXPORT_SUCCEEDED_COUNTER,
    EXPORT_FAILED_COUNTER,
    EXPORT_TIMER,
)
from posthog.tasks.exports.exporter_utils import log_error_if_site_url_not_reachable
from posthog.utils import absolute_uri

logger = structlog.get_logger(__name__)

TMP_DIR = "/tmp"  # NOTE: Externalise this to ENV var

ScreenWidth = Literal[800, 1920]
CSSSelector = Literal[".InsightCard", ".ExportedInsight"]


# NOTE: We purposefully DON'T re-use the driver. It would be slightly faster but would keep an in-memory browser
# window permanently around which is unnecessary
def get_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless=new")  # Hint: Try removing this line when debugging
    options.add_argument("--force-device-scale-factor=2")  # Scale factor for higher res image
    options.add_argument("--use-gl=swiftshader")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")  # This flag can make things slower but more reliable
    options.add_experimental_option(
        "excludeSwitches", ["enable-automation"]
    )  # Removes the "Chrome is being controlled by automated test software" bar

    # Create a unique prefix for the temporary directory
    pid = os.getpid()
    timestamp = int(time.time() * 1000)
    unique_prefix = f"chrome-profile-{pid}-{timestamp}-{uuid.uuid4()}"

    # Use TemporaryDirectory which will automatically clean up when the context manager exits
    temp_dir = tempfile.TemporaryDirectory(prefix=unique_prefix)
    options.add_argument(f"--user-data-dir={temp_dir.name}")

    # Necessary to let the nobody user run chromium
    os.environ["HOME"] = temp_dir.name

    if os.environ.get("CHROMEDRIVER_BIN"):
        service = webdriver.ChromeService(executable_path=os.environ["CHROMEDRIVER_BIN"])
        return webdriver.Chrome(service=service, options=options)

    return webdriver.Chrome(
        service=Service(ChromeDriverManager(chrome_type=ChromeType.GOOGLE).install()),
        options=options,
    )


def _export_to_png(exported_asset: ExportedAsset) -> None:
    """
    Exporting an Insight means:
    1. Loading the Insight from the web app in a dedicated rendering mode
    2. Waiting for the page to have fully loaded before taking a screenshot to disk
    3. Loading that screenshot into memory and saving the data representation to the relevant Insight
    4. Cleanup: Remove the old file and close the browser session
    """

    image_path = None

    try:
        if not settings.SITE_URL:
            raise Exception(
                "The SITE_URL is not set. The exporter must have HTTP access to the web app in order to work"
            )

        image_id = str(uuid.uuid4())
        image_path = os.path.join(TMP_DIR, f"{image_id}.png")

        if not os.path.exists(TMP_DIR):
            os.makedirs(TMP_DIR)

        access_token = get_public_access_token(exported_asset, timedelta(minutes=15))

        screenshot_width: ScreenWidth
        wait_for_css_selector: CSSSelector

        if exported_asset.insight is not None:
            url_to_render = absolute_uri(f"/exporter?token={access_token}&legend")
            wait_for_css_selector = ".ExportedInsight"
            screenshot_width = 800
        elif exported_asset.dashboard is not None:
            url_to_render = absolute_uri(f"/exporter?token={access_token}")
            wait_for_css_selector = ".InsightCard"
            screenshot_width = 1920
        else:
            raise Exception(f"Export is missing required dashboard or insight ID")

        logger.info("exporting_asset", asset_id=exported_asset.id, render_url=url_to_render)

        _screenshot_asset(image_path, url_to_render, screenshot_width, wait_for_css_selector)

        with open(image_path, "rb") as image_file:
            image_data = image_file.read()

        save_content(exported_asset, image_data)

        os.remove(image_path)

    except Exception:
        # Ensure we clean up the tmp file in case anything went wrong
        if image_path and os.path.exists(image_path):
            os.remove(image_path)

        log_error_if_site_url_not_reachable()

        raise


# Newer versions of selenium seem to include the search bar in the height calculation.
# This is a manually determined offset to ensure the screenshot is the correct height.
# See https://github.com/SeleniumHQ/selenium/issues/14660.
HEIGHT_OFFSET = 85


def _screenshot_asset(
    image_path: str,
    url_to_render: str,
    screenshot_width: ScreenWidth,
    wait_for_css_selector: CSSSelector,
) -> None:
    driver: Optional[webdriver.Chrome] = None
    try:
        driver = get_driver()
        # Set initial window size with a more reasonable height to prevent initial rendering issues
        driver.set_window_size(screenshot_width, 600)
        driver.get(url_to_render)
        WebDriverWait(driver, 20).until(lambda x: x.find_element(By.CSS_SELECTOR, wait_for_css_selector))
        # Also wait until nothing is loading
        try:
            WebDriverWait(driver, 20).until_not(lambda x: x.find_element(By.CLASS_NAME, "Spinner"))
        except TimeoutException:
            logger.exception(
                "image_exporter.timeout",
                url_to_render=url_to_render,
                wait_for_css_selector=wait_for_css_selector,
                image_path=image_path,
            )
            with posthoganalytics.new_context():
                posthoganalytics.tag("url_to_render", url_to_render)
                try:
                    driver.save_screenshot(image_path)
                    posthoganalytics.tag("image_path", image_path)
                except Exception:
                    pass
                capture_exception()

        # Get the height of the visualization container specifically
        height = driver.execute_script(
            """
            const element = document.querySelector('.InsightCard__viz') || document.querySelector('.ExportedInsight__content');
            if (element) {
                const rect = element.getBoundingClientRect();
                return Math.max(rect.height, document.body.scrollHeight);
            }
            return document.body.scrollHeight;
        """
        )

        # For example funnels use a table that can get very wide, so try to get its width
        width = driver.execute_script(
            """
            tableElement = document.querySelector('table');
            if (tableElement) {
                return tableElement.offsetWidth * 1.5;
            }
        """
        )
        if isinstance(width, int):
            width = max(int(screenshot_width), min(1800, width or screenshot_width))
        else:
            width = screenshot_width

        # Set window size with the calculated dimensions
        driver.set_window_size(width, height + HEIGHT_OFFSET)

        # Allow a moment for any dynamic resizing
        driver.execute_script("return new Promise(resolve => setTimeout(resolve, 500))")

        # Get the final height after any dynamic adjustments
        final_height = driver.execute_script(
            """
            const element = document.querySelector('.InsightCard__viz') || document.querySelector('.ExportedInsight__content');
            if (element) {
                const rect = element.getBoundingClientRect();
                return Math.max(rect.height, document.body.scrollHeight);
            }
            return document.body.scrollHeight;
        """
        )

        # Set final window size
        driver.set_window_size(width, final_height + HEIGHT_OFFSET)
        driver.save_screenshot(image_path)
    except Exception as e:
        # To help with debugging, add a screenshot and any chrome logs
        with posthoganalytics.new_context():
            posthoganalytics.tag("url_to_render", url_to_render)
            if driver:
                # If we encounter issues getting extra info we should silently fail rather than creating a new exception
                try:
                    driver.save_screenshot(image_path)
                    posthoganalytics.tag("image_path", image_path)
                except Exception:
                    pass
        capture_exception(e)

        raise
    finally:
        if driver:
            driver.quit()


def export_image(exported_asset: ExportedAsset) -> None:
    with posthoganalytics.new_context():
        posthoganalytics.tag("team_id", exported_asset.team.pk if exported_asset else "unknown")
        posthoganalytics.tag("asset_id", exported_asset.id if exported_asset else "unknown")

        try:
            if exported_asset.insight:
                # NOTE: Dashboards are regularly updated but insights are not
                # so, we need to trigger a manual update to ensure the results are good
                with upgrade_query(exported_asset.insight):
                    process_query_dict(
                        exported_asset.team,
                        exported_asset.insight.query,
                        dashboard_filters_json=exported_asset.dashboard.filters if exported_asset.dashboard else None,
                        limit_context=LimitContext.QUERY_ASYNC,
                        execution_mode=ExecutionMode.CALCULATE_BLOCKING_ALWAYS,
                        insight_id=exported_asset.insight.id,
                        dashboard_id=exported_asset.dashboard.id if exported_asset.dashboard else None,
                    )

            if exported_asset.export_format == "image/png":
                with EXPORT_TIMER.labels(type="image").time():
                    _export_to_png(exported_asset)
                EXPORT_SUCCEEDED_COUNTER.labels(type="image").inc()
            else:
                raise NotImplementedError(
                    f"Export to format {exported_asset.export_format} is not supported for insights"
                )
        except Exception as e:
            team_id = str(exported_asset.team.id) if exported_asset else "unknown"
            capture_exception(e, additional_properties={"celery_task": "image_export", "team_id": team_id})

            logger.error("image_exporter.failed", exception=e, exc_info=True)
            EXPORT_FAILED_COUNTER.labels(type="image").inc()
            raise
