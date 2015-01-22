# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import Request, FormRequest
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
import json
import bs4
import sys
import sqlite3
from sqlite3 import OperationalError
from scrapy import signals

reload(sys)
sys.setdefaultencoding('utf-8')

cx = sqlite3.connect('frontend.db')
cursor = cx.cursor()
try:
    cursor.execute("""create table zhihu
                                (id integer primary key autoincrement,
                                 url varchar(100) unique not null ,
                                 username varchar(20) not null ,
                                 location varchar(20) NULL,
                                 company varchar(20) null,
                                 school varchar (20) null,
                                 ask integer,
                                 answer integer ,
                                 like_num integer ,
                                 thanks integer ,
                                 followees integer,
                                 followers integer
                                 );
                    """
    )
except OperationalError:
    print 'table already exists'
class ZhihuspiderSpider(scrapy.Spider):
    name = "zhihuspider"
    allowed_domains = ["www.zhihu.com"]
    start_urls = (
        # 'http://www.zhihu.com/topic/19552832/followers', python
        'http://www.zhihu.com/topic/19550901/followers',#前端
    )
    download_delay = 0.1
    _xsrf = ''
    cnt = 0
    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip,deflate",
        "Accept-Language": "en-US,en;q=0.8,zh-TW;q=0.6,zh;q=0.4",
        "Connection": "keep-alive",
        "Content-Type": " application/x-www-form-urlencoded; charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 Safari/537.36",
        "Referer": "http://www.zhihu.com/"
    }

    def __init__(self, *a, **kwargs):
        super(ZhihuspiderSpider, self).__init__(*a, **kwargs)

    def findfollow(self,tag):
        try:
            return tag.name=='strong' and tag.next_sibling.name=='label'
        except:
            return False

    def start_requests(self):
        return [FormRequest(
            "http://www.zhihu.com/login",
            formdata={'email': 'yoursername',
                      'password': 'yourpassword'
            },
            callback=self.after_login,
        )]

    def after_login(self, response):
        for url in self.start_urls:
            yield Request(url, callback=self.parse_person_list)

    def parse_person_list(self, response):
        soup = bs4.BeautifulSoup(response.body)
        oringin_person_list = soup.find_all(class_='zm-list-avatar-medium')
        self._xsrf = soup.find('input', attrs={'name': '_xsrf', 'type': 'hidden'})['value']
        for person in oringin_person_list:
            yield self.make_requests_from_url('http://zhihu.com'+person['href'])
        last_person = soup.find_all(class_='zm-person-item')[-1]
        last_person_id = last_person['id'][3:]
        yield FormRequest(self.start_urls[0], formdata=
        {'_xsrf': self._xsrf, 'offset': str(0), 'start': last_person_id}, callback=self.parse_json
        )

    def parse(self, response):
        text_soup = bs4.BeautifulSoup(response.body)
        name = text_soup.find('div', class_='title-section ellipsis').findNext('span',class_='name').text.strip()
        url = response.url
        try:
            location = text_soup.find('span',class_='location item')['title']
        except TypeError:
            location = None
        try:
            company = text_soup.find('span',class_='employment item')['title']
        except TypeError:
            company = None
        try:
            school = text_soup.find('span',class_='education item')['title']
        except:
            school = None
        ask = int(text_soup.find_all('span',class_='num')[0].text)
        answer = int(text_soup.find_all('span',class_='num')[1].text)
        like = int(text_soup.find_all('strong')[0].text)
        thanks = int(text_soup.find_all('strong')[1].text)

        followees,followers = [int(i.text) for i in text_soup.find_all(self.findfollow)]

        print url,name,location,company,school,ask,answer,like,thanks,followees,followers
        cursor.execute('select url,username,location,company,school,ask,answer,like_num,thanks,followees,followers from zhihu where url=?'
                       ,(url,))
        result = cursor.fetchone()
        if result is None:
            cursor.execute("""insert into zhihu (url,username,location,company,school,ask,answer,like_num,thanks,followees,followers)
                           values (?,?,?,?,?,?,?,?,?,?,?)""",(url,name,location,company,school,ask,answer,like,thanks,followees,followers)
            )
            cx.commit()
        else:
            cursor.execute("""update zhihu set location=?,company=?,school=?,ask=?,answer=?,like_num=?,thanks=?,followees=?,followers=? where url=?""",
                (location,company,school,ask,answer,like,thanks,followees,followers,url))
            cx.commit()


    def parse_json(self, response):
        try:
            response_dict = json.loads(response.body)
            if response_dict['r'] != 0:
                return
            response_text = response_dict['msg'][1]
            soup = bs4.BeautifulSoup(response_text)
            urls = [a['href'] for a in soup.find_all('a', class_='zm-list-avatar-medium')]
            for url in urls:
                yield self.make_requests_from_url('http://zhihu.com' + url)

            last_person_id = soup.find_all('div', class_="zm-person-item")[-1]['id'][3:]
            yield FormRequest(self.start_urls[0], formdata=
            {'_xsrf': self._xsrf, 'offset': str(0), 'start': last_person_id}, callback=self.parse_json
            )
        except IndexError:
            print 'user has crawled over'
