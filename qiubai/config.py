USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'

BASIC_SERVER_URL = 'https://www.qiushibaike.com'
MODE_LIST = ['video', 'image', 'text']
MODE_URL_DICT = {'video': '/video/page/{}',
                 'image': '/imgrank/page/{}',
                 'text': '/text/page/{}'}

FILE_SAVE_PATH = '.\\qiubai'

SLEEP_PER_REQUEST = 1
SLEEP_PER_ANTI_SCRAPER = 60

PER_BATCH_FOR_GEVENT = 20

