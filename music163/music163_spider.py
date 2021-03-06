# -*- coding: utf-8 -*-
"""
    @Author  : shenxuexin
    @Time    : 2021/1/5 13:07
    @File    : music163_spider.py
    @software:PyCharm
"""
import requests
import os
import time
import sys
import re

from datetime import datetime
from threading import Thread
from queue import Queue
from lxml import etree
from loguru import logger
from config import *


class MusicSpider(object):
    def __init__(self, mode):
        self.mode = mode
        self.type = MODE_TYPE_REFLECT.get(self.mode)
        self.session = requests.Session()
        self.category_queue = Queue()
        self.singer_batch_link_Queue = Queue()
        self.singer_queue = Queue()
        self.song_queue = Queue()
        self.file_save_path = os.path.join(FILE_SAVE_PATH, self.type)
        self.count = {'category': 0, 'singer': 0, 'song': 0}

        self.session.headers.update({'User-Agent': USER_AGENT})

        if self.mode not in MODE_LIST:
            logger.error(f'Mode not be supported. | mode: {self.mode}')
            sys.exit(0)

        if not os.path.exists(self.file_save_path):
            os.makedirs(self.file_save_path)

    @staticmethod
    def regular_file_str(str):
        # 文件名不能包含 \/:*?"<>字符
        return re.sub(r'[\\/:*?"<>|]', '_', str)

    def safe_get(self, url, params=None):
        time.sleep(SLEEP_PER_REQUEST)
        try:
            resp = self.session.get(url, params=params)
            if resp.status_code == 404:
                logger.error(f'404 not found.')
                return
            elif resp.status_code == 403:
                logger.warning(f'Frequent requests. sleep for {SLEEP_PER_ANTI_SCRAPER}s.')
                time.sleep(SLEEP_PER_ANTI_SCRAPER)
                return
        except Exception as e:
            logger.error(f'Request failed. | Exception: {e}')
            return

        return resp

    def get_category(self):
        artist_discover_url = ARTIST_DISCOVER_URL
        resp = self.safe_get(artist_discover_url)

        html = etree.HTML(resp.text)
        cate_elem_list = html.xpath(f'//h2[text()="{self.type}"]/following-sibling::ul/li')

        category_list = []
        for cate_elem in cate_elem_list:
            cate_name = cate_elem.xpath('./a/text()')[0] if cate_elem.xpath('./a/text()') else None
            url = BASIC_SERVER_URL + cate_elem.xpath('./a/@href')[0] if cate_elem.xpath('./a/@href') else None

            if cate_name:
                cate_name = self.regular_file_str(cate_name)
                category_list.append(cate_name)
                self.count['category'] += 1
                self.category_queue.put((cate_name, url))

        logger.info(f'Get category successful. | category_list: {category_list}')

    def get_singer_batch_link(self):
        while True:
            if not self.category_queue.empty():
                cate, url = self.category_queue.get()
            else:
                time.sleep(3)
                continue
            logger.info(f'Start collecting singers. | category: {cate}')

            resp = self.safe_get(url)
            if not resp:
                continue
            html = etree.HTML(resp.text)
            link_elem_list = html.xpath('//ul[@id="initial-selector"]/li[position()>1]/a')
            for link_elem in link_elem_list:
                url = BASIC_SERVER_URL + link_elem.xpath('./@href')[0] if link_elem.xpath('./@href') else None
                if url:
                    self.singer_batch_link_Queue.put((cate, url))

            logger.info(f'Get singer batch link done.')
            self.category_queue.task_done()

    def get_singer_list(self):
        while True:
            if not self.singer_batch_link_Queue.empty():
                cate, singer_batch_url = self.singer_batch_link_Queue.get()
            else:
                time.sleep(3)
                continue

            resp = self.safe_get(singer_batch_url)
            if not resp:
                continue

            html = etree.HTML(resp.text)
            singer_elem_list = html.xpath('//ul[@id="m-artist-box"]/li//a[@class="f-tdn"]/preceding-sibling::a')
            for singer_elem in singer_elem_list:
                singer_name = singer_elem.xpath('./text()')[0].strip() if singer_elem.xpath('./text()') else None
                url = BASIC_SERVER_URL + singer_elem.xpath('./@href')[0].strip() if singer_elem.xpath('./@href') else None
                if all([singer_name, url]):
                    singer_name = self.regular_file_str(singer_name)
                    self.count['singer'] += 1
                    self.singer_queue.put((cate, singer_name, url))

            logger.info(f'Get singer list done. | url: {singer_batch_url}')
            self.singer_batch_link_Queue.task_done()

    def get_song_list(self):
        while True:
            if not self.singer_queue.empty():
                cate, singer_name, singer_url = self.singer_queue.get()
            else:
                time.sleep(3)
                continue

            resp = self.safe_get(singer_url)
            if not resp:
                continue

            html = etree.HTML(resp.text)
            song_elem_list = html.xpath('//ul[@class="f-hide"]/li/a')

            for song_elem in song_elem_list:
                url = song_elem.xpath('./@href')[0] if song_elem.xpath('./@href') else None
                title = song_elem.xpath('./text()')[0] if song_elem.xpath('./text()') else None

                if all([url, title]):
                    title = self.regular_file_str(title)
                    song_id = url.split('?')[-1].split('=')[-1]
                    self.count['song'] += 1
                    self.song_queue.put((cate, singer_name, title, song_id))
                else:
                    logger.warning(f'url: {url}, title: {title}')

            logger.info(f'Get song list done. | url: {singer_url}')
            self.singer_queue.task_done()

    def song_download(self):
        while True:
            if not self.song_queue.empty():
                cate, singer_name, title, song_id = self.song_queue.get(timeout=1)
            else:
                time.sleep(3)
                continue

            logger.info(f'Start downloading. | singer: {singer_name} | title: {title}')
            download_url = SONG_DOWNLOAD_URL.format(song_id)
            resp = self.safe_get(download_url)

            if not resp:
                self.song_queue.task_done()
                continue

            singer_folder = os.path.join(self.file_save_path, cate, singer_name)
            if not os.path.exists(singer_folder):
                os.makedirs(singer_folder)

            save_path = os.path.join(singer_folder, f'{title}.mp3')
            if os.path.exists(save_path):
                logger.info(f'file already exists. | singer: {singer_name} | title: {title}')
                self.song_queue.task_done()
                continue

            try:
                with open(save_path, 'wb') as f:
                    f.write(resp.content)
            except Exception as e:
                logger.error(f'Save file failed. | Exception: {e}')
            else:
                logger.info(f'Download successful. | singer: {singer_name} | title: {title}')
            finally:
                self.song_queue.task_done()

    def main(self):
        time_bgn = datetime.now().replace(microsecond=0)
        logger.info(f'Start scraping. | time: {time_bgn}')
        self.get_category()
        t_get_singer_batch_link = Thread(target=self.get_singer_batch_link)
        t_get_singer_list = Thread(target=self.get_singer_list)
        t_get_song_list = Thread(target=self.get_song_list)
        t_song_download = Thread(target=self.song_download)

        for t in [t_get_singer_batch_link, t_get_singer_list, t_get_song_list, t_song_download]:
            t.setDaemon(True)
            t.start()

        for q in [self.category_queue, self.singer_batch_link_Queue, self.singer_queue, self.song_queue]:
            q.join()

        logger.info(f'Scrape done. | count: {self.count} | time_span: {(datetime.now()-time_bgn).seconds}s')


if __name__ == '__main__':
    music_spider = MusicSpider(mode='Chinese')
    music_spider.main()