from web_spider.nlp import *
from web_spider.spiders.tool import *


def fetch_news():
    db = mysql_tools.connect()
    try:
        cursor = db.cursor()
        select_sql = "select * from t_stock_news limit 1"
        cursor.execute(select_sql)
        datas = cursor.fetchall()
        return datas[0][2]
    finally:
        mysql_tools.close(db)


def jieba_analyzer(news: str):
    seg_list = jieba.cut(news, cut_all=True)  # 全模式
    result = pseg.cut(news)  # 词性标注，标注句子分词后每个词的词性
    result2 = jieba.cut(news)  # 默认是精准模式
    result3 = jieba.analyse.extract_tags(news, 2)
    # 关键词提取，参数setence对应str1为待提取的文本,topK对应2为返回几个TF/IDF权重最大的关键词，默认值为20
    result4 = jieba.cut_for_search(news)  # 搜索引擎模式

    # print(" /".join(seg_list))
    #
    # for w in result:
    #     print(w.word, "/", w.flag, ", ", )
    #
    # for t in result2:
    #     print(t),
    #
    # for s in result3:
    #     print(s)

    print(" ,".join(result2))


def nlpir_analyzer(news: str):
    pynlpir.open()
    print(pynlpir.segment(news))
    pynlpir.close()


if __name__ == '__main__':
    news = fetch_news()
    print("jieba_analyzer result:")
    jieba_analyzer(news)
    print("nlpir_analyzer result:")
    nlpir_analyzer(news)