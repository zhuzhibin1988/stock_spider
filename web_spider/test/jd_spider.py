import os
import scrapy


class JDSpider(scrapy.Spider):
    name = "jd"

    def start_requests(self):
        urls = ["https://www.jd.com/"]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        path = "./src"
        if not os.path.exists(path):
            os.mkdir(path)
        os.chdir(path)
        filename = "jd.html"
        with open(filename, "wb") as f:
            f.write(response.body)
            f.close()