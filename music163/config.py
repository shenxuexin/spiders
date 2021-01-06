USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'

BASIC_SERVER_URL = 'https://music.163.com'
ARTIST_DISCOVER_URL = BASIC_SERVER_URL + '/discover/artist'
ARTIST_CATEGORY_URL = BASIC_SERVER_URL + '/discover/artist/cat'
ARTIST_URL = BASIC_SERVER_URL + '/artist'
SONG_DOWNLOAD_URL = BASIC_SERVER_URL + '/song/media/outer/url?id={}'

MODE_LIST = ['Chinese', 'Europe_and_America', 'Japan', 'Korea', 'Other']
MODE_TYPE_REFLECT = {'Chinese': u'华语',
                     'Europe_and_America': u'欧美',
                     'Japan': u'日本',
                     'Korea': u'韩国',
                     'Other': u'其他'}

FILE_SAVE_PATH = '.\\music'

SLEEP_PER_REQUEST = 3
SLEEP_PER_ANTI_SCRAPER = 60

PER_BATCH_FOR_GEVENT = 20

