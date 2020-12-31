USER_AGENT = 'Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_1 like Mac OS X) ' \
             'AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.0 Mobile/14E304 Safari/602.1'

BASIC_SERVER_URL = 'https://m.douban.com'
BOOK_URL = 'https://m.douban.com/book/'
BOOK_INFO_URL = 'https://m.douban.com/rexxar/api/v2/subject_collection/{}/items'

SLEEP_PER_CATEGORY = 10
SLEEP_PER_BOOK_PAGE = 5
SLEEP_PER_REQUEST = 3

IMG_DOWNLOAD_PATH = '.\\book_img'
FILE_SAVE_PATH = '.\\book_info'

BATCH_PER_GEVENT = 10