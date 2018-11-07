from web_spider.spiders.tool import *
from web_spider.spiders import *
from scrapy.http import TextResponse
from parsel import SelectorList


class StocksSpider(scrapy.Spider):
    name = "stock_list"

    def __init__(self, name=None, **kwargs):
        super(StocksSpider, self).__init__(name, **kwargs)
        self.db = None

    def start_requests(self):
        stock_list_url = "http://quote.eastmoney.com/stocklist.html"
        yield scrapy.Request(url=stock_list_url, callback=self.parse)

    def fetch_all_stock_info(self, response: TextResponse):
        """解析所有股票名称"""
        self.db = mysql_tools.connect()
        self.create_stock_table()
        xpath = "//div[@id='quotesearch']/ul/li"
        stock_selectors: SelectorList = response.xpath(xpath)
        for stock_selector in stock_selectors:
            stock = stock_selector.xpath("./a/text()").extract_first()
            stock_info = self.parse_stock_info(stock)
            if stock_info is not None:
                stock_name = stock_info[0]
                stock_code = stock_info[1]
                stock_url = stock_selector.xpath("./a/@href").extract_first()
                stock_type = self.paser_stock_type(stock_code, stock_url)
                self.save_stock_info(stock_type, stock_name, stock_code)
        mysql_tools.close(self.db)

    def paser_stock_type(self, stock_code: str, stock_url: str):
        """解析URL获取股票是深圳还是上海股"""
        last_sprit_idx = stock_url.rindex("/")
        stock_code_idx = stock_url.rindex(stock_code)
        stock_type = stock_url[last_sprit_idx + 1:stock_code_idx]
        return stock_type

    def parse_stock_info(self, stock: str):
        """格式：基金金泰(500001)"""
        try:
            left_parentheses_idx = stock.index("(")
            right_parentheses_idx = stock.index(")")
        except ValueError as e:
            return None
        else:
            name = stock[0:left_parentheses_idx]
            code = stock[left_parentheses_idx + 1:right_parentheses_idx]
            return name, code

    def create_stock_table(self):
        cursor = self.db.cursor()

        create_sql = """create table if not exists t_stock(
                            `sStockCode` VARCHAR(8) NOT NULL,
                            `sStock` VARCHAR(64) NULL,
                            `sStockType` VARCHAR(2) NULL,
                            `sIndustryCode` VARCHAR(16) NULL,
                            UNIQUE INDEX `sStockCode_UNIQUE` (`sStockCode` ASC)
                        )"""
        cursor.execute(create_sql)

        truncate_sql = "truncate table t_stock"
        cursor.execute(truncate_sql)

    def save_stock_info(self, stock_type, stock_name, stock_code):
        cursor = self.db.cursor()
        try:
            insert_sql = "insert into t_stock (sStockCode,sStock,sStockType) values ('%s','%s','%s')" % (
                stock_code, stock_name, stock_type)
            cursor.execute(insert_sql)
            self.db.commit()
        except DatabaseError as e:
            print(e)
            self.db.rollback()

    def parse(self, response: TextResponse):
        self.fetch_all_stock_info(response)