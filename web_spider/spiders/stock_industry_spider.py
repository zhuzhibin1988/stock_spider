from web_spider.spiders.tool import *
from web_spider.spiders import *
from scrapy.http import TextResponse

headers = {'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate', 'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
           'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36'}


class StockIndustrySpider(scrapy.Spider):
    name = "stock_industry"

    def __init__(self, name=None, **kwargs):
        super(StockIndustrySpider, self).__init__(name, **kwargs)
        self.db = None

    def start_requests(self):
        industry_url = "http://data.eastmoney.com/bkzj/hy.html"
        yield scrapy.Request(url=industry_url, callback=self.parse, headers=headers)

    def fetch_all_stock_industry_info(self, response: TextResponse):
        """解析所有股票名称"""
        self.db = mysql_tools.connect()
        self.create_stock_industry_table()
        self.fetch_all_industry(response.url)
        for industry in self.select_all_industry():
            stock_industry_code = industry[0]
            stock_industry_url = industry[2]
            print("start to update industry %s stocks." % stock_industry_code)
            count = self.fetch_stock_industry_detail(stock_industry_code, stock_industry_url)
            print("update industry %s total %d stocks done." % (stock_industry_code, count))
        mysql_tools.close(self.db)

    def fetch_all_industry(self, industry_url):
        service = selenium_tools.new_service()
        service.start()
        driver = selenium_tools.get_driver(options=selenium_tools.get_browser_options())
        driver.get(industry_url)
        xpath = "//table[@id='dt_1']/tbody/tr/td/a[starts-with(@href,'http://quote.eastmoney.com/center/')]"
        try:
            while True:
                industrys = driver.find_elements_by_xpath(xpath)
                for industry in industrys:
                    stock_industry_url = industry.get_attribute("href")
                    stock_industry = industry.text
                    stock_industry_code = self.parse_stock_industry_code(stock_industry_url)
                    print("code: %s, name: %s, url: %s" % (stock_industry_code, stock_industry, stock_industry_url))
                    self.save_stock_industry(stock_industry_code, stock_industry, stock_industry_url)
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
        finally:
            driver.quit()
            service.stop()


    def fetch_stock_industry_detail(self, stock_industry_code, stock_industry_url):
        service = selenium_tools.new_service()
        service.start()
        driver = selenium_tools.get_driver(options=selenium_tools.get_browser_options())
        driver.get(stock_industry_url)
        count = 0
        try:
            while True:
                stock_codes = driver.find_elements_by_xpath("//table[@id='main-table']/tbody/tr/td[2]/a")
                for stock_code in stock_codes:
                    self.update_stock_industry(stock_code.text, stock_industry_code)
                    count += 1
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
                    time.sleep(2)
        finally:
            driver.quit()
            service.stop()
        return count

    def parse_stock_industry_code(self, url: str):
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

    def create_stock_industry_table(self):
        cursor = self.db.cursor()

        create_sql = """create table if not exists t_stock_industry (
                              `sIndustryCode` VARCHAR(16) NULL,
                              `sIndustry` VARCHAR(64) NULL,
                              `sUrl` VARCHAR(128) NULL,
                              UNIQUE INDEX `sIndustryCode_UNIQUE` (`sIndustryCode` ASC)
                            )"""
        cursor.execute(create_sql)

        truncate_sql = "truncate table t_stock_industry"
        cursor.execute(truncate_sql)

    def select_all_industry(self):
        cursor: Cursor = self.db.cursor()
        select_sql = "select * from t_stock_industry"
        cursor.execute(select_sql)
        datas = cursor.fetchall()
        industrys = []
        for data in datas:
            industry_code = data[0]
            industry = data[1]
            url = data[2]
            industrys.append((industry_code, industry, url))
        return industrys

    def save_stock_industry(self, industry_code, industry, url):
        cursor = self.db.cursor()
        try:
            insert_sql = "insert into t_stock_industry (sIndustryCode,sIndustry,sUrl) values ('%s','%s','%s')" % (
                industry_code, industry, url)
            cursor.execute(insert_sql)
            self.db.commit()
        except DatabaseError as e:
            print(e)
            self.db.rollback()

    def update_stock_industry(self, stock_code, industry_code):
        cursor = self.db.cursor()
        try:
            update_sql = "update t_stock set sIndustryCode = %s where sStockCode = %s" % (industry_code, stock_code)
            cursor.execute(update_sql)
            self.db.commit()
        except DatabaseError as e:
            print(e)
            self.db.rollback()

    def parse(self, response: TextResponse):
        self.fetch_all_stock_industry_info(response)