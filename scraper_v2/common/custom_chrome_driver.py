#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Author :  @fangwangme
Time   :  2023-04-19
Desc   :  
"""


import sys
import pathlib

from webdriver_manager.chrome import ChromeDriverManager
import undetected_chromedriver as uc

sys.path.append("{}/../".format(pathlib.Path(__file__).parent))


class CustomChromeDriver:
    def __init__(self, load_image=False):
        self.driver = None
        self.load_image = load_image

    def __enter__(self):
        self.start()
        return self.driver

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.quit()

    def start(self):
        self.driver = create_driver(self.load_image)

    def quit(self):
        self.driver.quit()


# another create driver with selenium
def create_driver(load_image=False):
    # other chrome options
    chrome_options = uc.ChromeOptions()

    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-application-cache")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-setuid-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--ignore-certificate-errors-spki-list")
    chrome_options.add_argument("--ignore-ssl-errors")
    # disable popup
    chrome_options.add_argument("--disable-popup-blocking")

    # page load strategy
    chrome_options.page_load_strategy = "normal"

    # disable save password
    chrome_options.add_argument("--password-store=basic")

    if load_image:
        image_flag = 1
    else:
        image_flag = 2

    chrome_options.add_experimental_option(
        "prefs",
        {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_setting_values.images": image_flag,
        },
    )

    driver = uc.Chrome(
        executable_path=ChromeDriverManager().install(),
        options=chrome_options,
    )

    return driver
