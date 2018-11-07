from web_spider.spiders.tool import *
from web_spider.spiders import *
from scrapy.http import TextResponse
from selenium import webdriver
import random


class StockSpider(scrapy.Spider):
    name = "stock"

    headers = {'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate', 'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
               'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36'}

    def __init__(self, name=None, **kwargs):
        super(StockSpider, self).__init__(name, **kwargs)
        self.db = None
        self.ip_pool = []
        os.chdir("/Users/zhuzhibin/Program/python/web_spider/proxy")
        with open("proxies.txt", "r") as proxies:
            for proxy in proxies.readlines():
                self.ip_pool.append(proxy)

    def start_requests(self):
        self.db = mysql_tools.connect()
        stock_urls = self.make_all_stock_urls()
        mysql_tools.close(self.db)
        begin = int(time.time())
        for stock_url in stock_urls:
            meta = {"proxy": random.choice(self.ip_pool).strip()}
            yield scrapy.Request(url=stock_url, callback=self.parse, headers=self.headers)
        end = int(time.time())
        print("cost time(s) : %d" % (end - begin))

    def get_cookies(self):
        url = "http://stockpage.10jqka.com.cn/realHead_v2.html"
        chrome_options = selenium_tools.get_browser_options()
        driver = webdriver.Chrome(chrome_options=chrome_options)
        driver.get(url)
        cookies = driver.get_cookies()

        cookies_dirt = {}
        for item in cookies:
            cookies_dirt.setdefault(item["name"], item["value"])
        driver.close()
        print(cookies_dirt)
        return cookies_dirt

    def make_all_stock_urls(self):
        stock_info_list = self.select_all_stock_info()

        stock_url_list = []
        for stock_info in stock_info_list:
            url = "https://gupiao.baidu.com/stock/%s%s.html" % (stock_info[2], stock_info[0])
            # url = "http://d.10jqka.com.cn/v2/realhead/hs_%s/last.js" % stock_info[0]
            stock_url_list.append(url)
        return stock_url_list

    def select_all_stock_info(self):
        cursor: Cursor = self.db.cursor()
        select_sql = "select * from t_stock limit 5"
        cursor.execute(select_sql)
        datas = cursor.fetchall()

        stock_info_list = []
        for data in datas:
            stock_code = data[0]
            stock_name = data[1]
            stock_type = data[2]
            stock_info_list.append((stock_code, stock_name, stock_type))
        return stock_info_list

    def parse(self, response: TextResponse):
        path = "/Users/zhuzhibin/Program/python/web_spider/stock"
        if not os.path.exists(path):
            os.mkdir(path)
        os.chdir(path)
        filename = "stock"

        line = {}
        stock_code = response.xpath("//a[@class='bets-name']/span/text()").extract_first()
        current_price = "--"
        different_value = "--"
        different_rate = "--"
        price_status_list = ["s-stop", "s-up", "s-down"]
        for price_status in price_status_list:
            current_price = response.xpath(
                "//div[@class='stock-bets']/div[@class='price %s ']/strong/text()" % price_status).extract_first()
            if current_price:
                values = response.xpath(
                    "//div[@class='stock-bets']/div[@class='price %s ']/span/text()" % price_status).extract()
                if values:
                    different_value = values[0]
                    different_rate = values[1]
                break

        line.setdefault("股票代码", stock_code)
        line.setdefault("当前价", current_price)
        line.setdefault("涨跌", different_value)
        line.setdefault("涨跌率", different_rate)

        index = 0
        title_selectors = response.xpath("//div[@class='bets-content']/div/dl/dt/text()").extract()
        value_selectors = response.xpath("//div[@class='bets-content']/div/dl/dd/text()").extract()
        for title_selector in title_selectors:
            title = title_selector.strip()
            value = value_selectors[index].strip()
            line.setdefault(title, value)
            index += 1
        with open(filename, "a") as f:
            if stock_code:
                f.write(str(line) + "\n")
                f.close()


if __name__ == '__main__':
    stockSpider = StockSpider()
    cookie = stockSpider.get_cookies()