from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import os

def new_service():
    env_dict = os.environ
    driver_path = "%s/chromedriver" % env_dict.get("CHROME_DRIVER_BIN")
    service = Service(driver_path)
    return service

def get_browser_options():
    options = Options()
    options.add_argument('--no-sandbox')  # 解决DevToolsActivePort文件不存在的报错
    options.add_argument('--disable-gpu')  # 谷歌文档提到需要加上这个属性来规避bug
    options.add_argument('blink-settings=imagesEnabled=false')  # 不加载图片, 提升速度
    options.add_argument('--headless')  # 浏览器不提供可视化页面. linux下如果系统不支持可视化不加这条会启动失败

    # chrome_options.add_argument('window-size=1920x3000')  # 指定浏览器分辨率
    # chrome_options.add_argument('--hide-scrollbars')  # 隐藏滚动条, 应对一些特殊页面
    return options


def get_driver(options=None):
    if options is not None:
        driver = webdriver.Chrome(options=options)
    else:
        driver = webdriver.Chrome()
    return driver