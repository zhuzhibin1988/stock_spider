from scrapy import cmdline

if __name__ == '__main__':
    # cmdline.execute("scrapy crawl stock_list".split())
    # cmdline.execute("scrapy crawl stock".split())
    # cmdline.execute("scrapy crawl stock_industry".split())
    cmdline.execute("scrapy crawl stock_news".split())