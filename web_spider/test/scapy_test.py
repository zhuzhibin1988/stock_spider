from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from web_spider.spiders.tool import selenium_tools

headers = {'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate', 'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
           'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36'}


def get_browser_options():
    options = Options()
    options.add_argument('--no-sandbox')  # 解决DevToolsActivePort文件不存在的报错
    options.add_argument('--disable-gpu')  # 谷歌文档提到需要加上这个属性来规避bug
    options.add_argument('blink-settings=imagesEnabled=false')  # 不加载图片, 提升速度
    options.add_argument('--headless')  # 浏览器不提供可视化页面. linux下如果系统不支持可视化不加这条会启动失败

    # chrome_options.add_argument('window-size=1920x3000')  # 指定浏览器分辨率
    # chrome_options.add_argument('--hide-scrollbars')  # 隐藏滚动条, 应对一些特殊页面
    return options


def get_url_driver(url, options=None):
    if options is not None:
        driver = webdriver.Chrome(options=options)
    else:
        driver = webdriver.Chrome()
    driver.get(url)
    return driver


def fetch_stock_industry():
    url = 'http://data.eastmoney.com/bkzj/hy.html'
    service = selenium_tools.new_service()
    service.start()
    # 设置option方法1
    # option = webdriver.ChromeOptions()
    # option.headless = True  # 把chrome设置成无界面模式
    # driver = webdriver.Chrome(options=option)
    # driver.get(url)

    # 设置option方法2
    driver = selenium_tools.get_url_driver(url=url, options=selenium_tools.get_browser_options())

    xpath = "//table[@id='dt_1']/tbody/tr/td/a[starts-with(@href,'http://quote.eastmoney.com/center/')]"
    xpath = "//table[@id='dt_1']/tbody/tr"
    while True:
        industrys = driver.find_elements_by_xpath(xpath)
        for industry in industrys:
            stock_industry_url = industry.find_element_by_xpath("./td[2]/a").get_attribute("href")
            stock_industry = industry.find_element_by_xpath("./td[2]/a").text  # 行业名称
            stock_industry_code = parse_stock_industry_code(stock_industry_url)
            grow_rate = industry.find_element_by_xpath("./td[4]/span").text  # 涨跌幅
            capital_flow = industry.find_element_by_xpath("./td[5]/span").text  # 净流入
            print(
                "code: %s, name: %s, rate %s, flow %s" % (stock_industry_code, stock_industry, grow_rate, capital_flow))
        try:
            next_button_element = driver.find_element_by_xpath("//div[@id='PageCont']/a[text()='下一页']")
            attribute_class = next_button_element.get_attribute("class")
            if attribute_class == "nolink":
                next_button_element = None
        except Exception as e:
            next_button_element = None

        if next_button_element is None:
            break
        else:
            next_button_element.click()  # 模拟点击下一页
            time.sleep(2)
    driver.quit()
    service.stop()


def fetch_stock_news():
    url = "http://finance.eastmoney.com/news/csygc.html"
    service = selenium_tools.new_service()
    service.start()
    driver = selenium_tools.get_driver(selenium_tools.get_browser_options())
    driver.get(url)
    items = driver.find_elements_by_xpath("//div[@class='SubItemNav']/ul/li[2]")
    for item in items:
        element = item.find_element_by_xpath("./a")
        news_url = element.get_attribute("href")
        news = element.text
        print("news: %s, news_url: %s" % (news, news_url))
        fetch_category_news_list(driver, news_url)
    driver.quit()
    service.stop()


def fetch_category_news_list(driver, url):
    service = selenium_tools.new_service()
    service.start()
    driver.get(url)
    news_list = driver.find_elements_by_xpath("//ul[@id='newsListContent']/li")
    news_dict = {}
    for news in news_list:
        element = news.find_element_by_xpath("./div/p[@class='title']/a")
        news_url = element.get_attribute("href")
        news_title = element.text
        news_dict.setdefault(news_title, news_url)
    for news_key in news_dict.keys():
        news_title = news_key
        news_url = news_dict[news_title]
        news_content = fetch_news_content(driver, news_url)
        print("news_title: %s, news_url: %s" % (news_title, news_url))
        print(news_content)
    driver.quit()
    service.stop()


def fetch_news_content(driver, url):
    driver.get(url)
    news_content = ""
    paragraphs = driver.find_elements_by_xpath("//div[@id='ContentBody']/p")
    for paragraph in paragraphs:
        content = paragraph.text
        news_content += content + "\n"
    return news_content


def parse_stock_industry_code(url: str):
    """url：http://quote.eastmoney.com/center/list.html#28002732_0_2.html"""
    try:
        hash_key_idx = url.index("#")
        underline_idx = url.index("_")
    except ValueError as e:
        print(e)
        return None
    else:
        code = url[hash_key_idx + 1:underline_idx]
        return code


def fetch_stock_industry_detial():
    url = 'http://quote.eastmoney.com/center/list.html#28002422_0_2.html'
    service = selenium_tools.new_service()
    service.start()
    driver = get_url_driver(url=url, options=get_browser_options())
    try:
        while True:
            # driver.page_source
            elements = driver.find_elements_by_xpath("//table[@id='main-table']/tbody/tr/td[2]/a")
            for element in elements:
                print(element.text)
            try:
                next_button_element = driver.find_element_by_xpath("//span[@class='next paginate_button']")
                if next_button_element.text == "":  # ElementNotVisibleException
                    next_button_element = None
            except Exception as e:
                next_button_element = None

            if next_button_element is None:
                break
            else:
                next_button_element.click()  # 模拟点击下一页
                time.sleep(2)  # 等待加载页面
    finally:
        driver.quit()
        service.stop()


if __name__ == '__main__':
    fetch_stock_news()