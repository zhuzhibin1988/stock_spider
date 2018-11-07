from web_spider.spiders.tool import *
from web_spider.spiders import *


class StockSpider(scrapy.Spider):
    name = "stock_news"

    headers = {'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate', 'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
               'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36'}

    def __init__(self, name=None, **kwargs):
        super(StockSpider, self).__init__(name, **kwargs)
        self.db = None

    def start_requests(self):
        self.db = mysql_tools.connect()
        self.create_stock_news_table()
        begin = int(time.time())
        url = "http://finance.eastmoney.com/news/csygc.html"
        yield scrapy.Request(url=url, callback=self.parse, headers=self.headers)
        mysql_tools.close(self.db)
        end = int(time.time())
        print("cost time(s) : %d" % (end - begin))

    def fetch_stock_news(self, url):
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
            self.fetch_category_news_list(driver, news_url)
        driver.quit()
        service.stop()

    def fetch_category_news_list(self, driver, url):
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
            news_content = self.fetch_news_content(driver, news_url)
            print("news_title: %s, news_url: %s" % (news_title, news_url))
            self.save_stock_news(news_title, news_url, news_content)
        driver.quit()
        service.stop()

    def fetch_news_content(self, driver, url):
        driver.get(url)
        news_content = ""
        paragraphs = driver.find_elements_by_xpath("//div[@id='ContentBody']/p")
        for paragraph in paragraphs:
            content = paragraph.text
            news_content += content + "\n"
        return news_content

    def create_stock_news_table(self):
        cursor = self.db.cursor()

        create_sql = """create table if not exists t_stock_news(
                            `sNewsTitle` VARCHAR(128) NULL,
                            `sNewsUrl` VARCHAR(128) NULL,
                            `sNewContent` TEXT NULL
                        )"""
        cursor.execute(create_sql)

        truncate_sql = "truncate table t_stock"
        cursor.execute(truncate_sql)

    def save_stock_news(self, title, url, content):
        cursor = self.db.cursor()
        try:
            insert_sql = "insert into t_stock_news (sNewsTitle,sNewsUrl,sNewContent) values ('%s','%s','%s')" % (
                title, url, content)
            cursor.execute(insert_sql)
            self.db.commit()
        except DatabaseError as e:
            print(e)
            self.db.rollback()

    def parse(self, response):
        self.fetch_stock_news(response.url)