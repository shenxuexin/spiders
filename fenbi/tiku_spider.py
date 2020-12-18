# -*-coding:utf-8-*-
import os
import time
import requests
import execjs

from loguru import logger
from config import *

import urllib3
urllib3.disable_warnings()


class TikuSpider(object):
    def __init__(self, phone, password, mode='xingce', exclude_area_list=None):
        self.phone = phone
        self.password = password
        self.exclude_area_list = exclude_area_list
        self.mode = mode
        self.paper_download_count = 0

        self.session = requests.Session()
        self.session.headers.update({'User-Agent': USER_AGENT})
        self.session.verify = False

        # 设置存储路径
        self.mode_save_path = os.path.join(FILE_SAVE_PATH, self.mode)
        if not os.path.exists(self.mode_save_path):
            os.makedirs(self.mode_save_path)

        self.anti_scrape = False

    def encode_paw(self, code):
        with open('password_encrypt.js') as f:
            js_encrypt = f.read()
        ctx_encrypt = execjs.compile(js_encrypt)
        password = ctx_encrypt.call('get_pwd', code)
        return password

    def login(self):
        password = self.encode_paw(self.password)
        data = {'phone': self.phone, 'password': password}
        login_url = BASIC_SERVER_URL + LOGIN_URL
        resp = self.session.post(login_url, data=data)

        try:
            user_info = resp.json()
        except Exception as e:
            logger.info(f'Login failed. | Exception: {e}')
            return False

        login_code = user_info.get('code')
        if login_code != 1:
            return False

        logger.info(f'Login successful. | phone: {self.phone}')
        return True

    def get_sublabel_info(self):
        '''获取区域id'''
        sublabel_url = BASIC_SERVER_URL + SUBLABEL_URL.format(self.mode)
        sublabel_resp = self.session.get(sublabel_url)

        try:
            sublabel_info_list = sublabel_resp.json()
        except Exception as e:
            logger.error(f'Get sublabel info failed. | Exception: {e}')
            return

        logger.info(f'Get sublabel info successful. | area_count: {len(sublabel_info_list)}')
        return sublabel_info_list

    def get_paper_list(self, sublabel_info):
        '''获取试卷列表'''
        try:
            sublabel_id = sublabel_info['labelMeta']['id']
            area_name = sublabel_info['name']
        except Exception as e:
            logger.error(f'Get sublabel id failed. | Exception: {e}')
            return

        logger.info(f'Start getting paper list. | area: {area_name} | labelId: {sublabel_id}')

        paper_list_url = BASIC_SERVER_URL + PAPER_LIST_URL.format(self.mode)
        paper_list = []
        has_next_page = True
        cur_page = 0
        while has_next_page:
            try:
                args = {'toPage': cur_page, 'pageSize': PAPER_SIZE, 'labelId': sublabel_id}
                paper_info_resp = self.session.get(paper_list_url, params=args).json()
            except Exception as e:
                logger.error(f'Get paper list failed. | Exception: {e}')
                return

            # 添加到试卷列表
            cur_page_paper_list = paper_info_resp.get('list')
            paper_list.extend(cur_page_paper_list)

            page_info = paper_info_resp.get('pageInfo')
            total_page = page_info.get('totalPage')
            cur_page += 1

            has_next_page = total_page > cur_page
            time.sleep(SLEEP_PER_REQUEST)

        logger.info(f'Get paper list successful. | area: {area_name} | paper_count: {len(paper_list)}')
        return paper_list

    def get_exercise_id(self, paper_info):
        '''获取试卷id'''
        if (not paper_info) or (not isinstance(paper_info, dict)):
            logger.error(f'Get exercise id failed. | Exception: paper info require dict type.')
            return

        if paper_info.get('exercise'):
            exercise_id = paper_info['exercise']['id']
        else:
            try:
                data = {'type': TYPE, 'paperId': paper_info.get('id'), 'exerciseTimeMode': EXERCISE_TIME_MODE}
                exercise_info_url = BASIC_SERVER_URL + EXERCISE_INFO_URL.format(self.mode)
                exercise_info = self.session.post(exercise_info_url, data=data)
                exercise_id = exercise_info.json().get('id')
            except Exception as e:
                logger.error(f'Get exercise id failed. | Exception: {e}')
                return
            finally:
                time.sleep(SLEEP_PER_REQUEST)

        # logger.info(f'Get exercise id successful. | exercise id: {exercise_id}')
        return exercise_id

    def papers_download(self, folder_path, paper_list):
        if not paper_list or not isinstance(paper_list, list):
            logger.error(f'Paper download failed. | Exception: paper_list should be a list and not null.')
            return

        cur_paper_num = 0
        total_paper_count = len(paper_list)
        for paper_info in paper_list:
            exercise_id = self.get_exercise_id(paper_info)
            paper_title = paper_info.get('name')

            # 替换特殊字符
            paper_title = paper_title.replace('/', '_')

            cur_paper_num += 1
            logger.info(f'Start downloading. | title: {paper_title} | id: {exercise_id} | process: {cur_paper_num}/{total_paper_count}')

            paper_download_url = BASIC_SERVER_URL + PAPER_DOWNLOAD_URL.format(self.mode, exercise_id)
            paper_file_path = os.path.join(folder_path, f'{paper_title}.pdf')

            if os.path.exists(paper_file_path):
                logger.info(f'Paper already exists. | title: {paper_title}')
                continue

            try:
                paper_resp = self.session.get(paper_download_url)
            except Exception as e:
                logger.error(f'Download paper failed. | title: {paper_title} | Exception: {e}')
                continue

            with open(paper_file_path, 'wb') as f:
                f.write(paper_resp.content)

            self.paper_download_count += 1
            logger.info(f'Download paper successful. | title: {paper_title} | process: {cur_paper_num}/{total_paper_count} | path: {paper_file_path}')

            time.sleep(SLEEP_PER_PAPER)

    def main(self):
        # 登录
        if not self.login():
            return

        # 获取区域列表
        sublabel_info_list = self.get_sublabel_info()

        if not sublabel_info_list:
            logger.info(f'No sublabel_info_list, exit.')
            return

        cur_area_num = 0
        total_area_count = len(sublabel_info_list)
        for sublabel_info in sublabel_info_list:
            children_label_list = sublabel_info.get('childrenLabels')
            area_name = sublabel_info.get('name')

            cur_area_num += 1
            logger.info(f'Start scraping for area. | area: {area_name} | process: {cur_area_num}/{total_area_count}')

            area_path = os.path.join(self.mode_save_path, area_name)
            if not os.path.exists(area_path):
                os.mkdir(area_path)

            if self.exclude_area_list and area_name in self.exclude_area_list:
                continue

            if not children_label_list:
                paper_list = self.get_paper_list(sublabel_info)
                time.sleep(SLEEP_PER_AREA)
                self.papers_download(area_path, paper_list)
            else:
                for children_label_info in children_label_list:
                    sub_area_name = children_label_info.get('name')

                    sub_area_path = os.path.join(area_path, sub_area_name)
                    if not os.path.exists(sub_area_path):
                        os.mkdir(sub_area_path)

                    paper_list = self.get_paper_list(children_label_info)
                    time.sleep(SLEEP_PER_AREA)

                    self.papers_download(sub_area_path, paper_list)

            logger.info(f'Area scraped done. | area: {area_name} | process: {cur_area_num}/{total_area_count}')

        logger.info(f'All paper scrape done. | paper_download_count: {self.paper_download_count}')


if __name__ == '__main__':
    tiku_spider = TikuSpider(phone='', password='', mode='shenlun')
    tiku_spider.main()
