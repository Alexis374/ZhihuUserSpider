# ZhihuUserSpider
crawl all users that care about some topics
---
### 功能：爬取知乎某个话题之下所有关注者的 url、用户名、地点、学校、关注数、被关注数、提问、回答、点赞、感谢等数据，并存入sqlite文件中

###依赖:
1. Scrapy
2. BeautifulSoup
3. json

### 运行：在start_urls里填入想要爬取的话题关注者列表的url，填入自己的知乎账户名，密码，`scrapy crawl zhihuspider`。