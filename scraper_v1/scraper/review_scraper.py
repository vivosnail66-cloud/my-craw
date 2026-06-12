#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Author :  @fangwangme
Time   :  2023-05-25
Desc   :  
"""

import hashlib
import json
import math
import re
import datetime
import sys
import pathlib
import time
from bs4 import BeautifulSoup

from concurrent.futures import ThreadPoolExecutor

import requests

# sys path append parent folder
sys.path.append(f"{pathlib.Path(__file__).parent}/../")
from common.logger import logger
from common import db_sqlite, settings, class_common, tools, proxy_utils

HOME_PAGE = "https://www.bestvibe.com/"
REVIEW_PAT = re.compile(r'"reviewCount": "(\d+)"', re.S)
MPN_PAT = re.compile(r'"mpn":"(\d+)"', re.S)
PAGE_SIZE = 10


# build headers
def build_headers():
    headers = {
        'Host': 'www.bestvibe.com',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/114.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1'
    }

    return headers


# get all review tasks
def get_all_review_tasks():
    # get all review tasks
    sql = f"SELECT * FROM review_tasks WHERE status != {settings.STATUS_SUCCESS}"
    return db_sqlite.query_by_sql(sql)


# scrape review task
def scrape_review_task(task):
    start_time = time.time()

    # get task info
    _, product_url, product_id, total_count, crawled_count, task_status = task

    s = requests.Session()
    s.headers.update(build_headers())

    use_proxy_flag = tools.get_use_proxy()
    if use_proxy_flag:
        proxy_data = proxy_utils.get_proxy()
    else:
        proxy_data = {}

    try:
        # get product page
        logger.info(f"Start to scrape product page with url {product_url}")
        r = s.get(product_url, proxies=proxy_data, timeout=settings.REQ_TIMEOUT)
        logger.info(f"Get product page with url {product_url} success with status code {r.status_code}")

        if r.status_code != 200:
            logger.error(f"Get product page {product_url} failed with status code {r.status_code}")
            raise Exception(f"Get product page {product_url} failed with status code {r.status_code}")
        
        total_pages = math.ceil(total_count / PAGE_SIZE)
        logger.info(f"Total pages {total_pages}")
        current_page = 1

        while current_page <= total_pages:
            # get review page
            review_url = f"https://www.bestvibe.com/comment.php?goods_id={product_id}&c_type=0&tag_id=0&ajax=1&p={current_page}"

            logger.info(f"Start to scrape reviews at page {current_page} with url {review_url}")
            r = s.get(review_url, proxies=proxy_data, timeout=settings.REQ_TIMEOUT)
            logger.info(f"Get review page with url {review_url} success with status code {r.status_code}")

            if r.status_code != 200:
                logger.error(f"Get review page {review_url} failed with status code {r.status_code}")
                raise Exception(f"Get review page {review_url} failed with status code {r.status_code}")
            
            is_success, reviews, media_tasks = parse_reviews(r.text, product_id, product_url)
            if is_success:
                # save reviews
                ret = db_sqlite.insert_reviews(reviews)
                logger.info(f"Save {len(reviews)} reviews with ret {ret}")

                current_page += 1
                crawled_count += len(reviews)
                logger.info(f"Scrape reviews at page {current_page} with url {review_url} successfully")

                # save media tasks
                task_ret = db_sqlite.insert_images(media_tasks)
                logger.info(f"Save {len(media_tasks)} media tasks with ret {task_ret}")
            else:
                logger.error(f"Parse reviews at page {current_page} with url {review_url} failed")
                raise Exception(f"Parse reviews at page {current_page} with url {review_url} failed")
    except Exception as e:
        logger.error(f"Failed to scrape review task {task} due to {str(e)}")

    # get count of reviews
    sql = f"SELECT COUNT(*) FROM reviews WHERE product_url = '{product_url}';"
    real_crawled_count = db_sqlite.query_by_sql(sql)[0][0]

    if real_crawled_count >= total_count:
        task_status = settings.STATUS_SUCCESS
    else:
        task_status = settings.STATUS_PART_SUCCESS

    # update review task
    update_ret = db_sqlite.update_review_task(url=product_url, total=total_count, crawled=real_crawled_count, status=task_status)
    logger.info(f"Updated crawled {real_crawled_count}, status {task_status} for review task {product_url} with ret {update_ret}")

    time_cost = time.time() - start_time
    logger.info(f"Scrape review task {product_url} with time cost {time_cost}")

    
import html
# parse reviews
def parse_reviews(page_context, product_id, product_url):
    
    is_success = False
    reviews = list()
    media_tasks = list()

    current_year = datetime.datetime.now().year
    # get current month, need 05 instead of 5
    current_month = datetime.datetime.now().strftime("%m")

    try:
        raw_json = json.loads(page_context)
        comment_context = raw_json.get("comment_list", "")
        soup = BeautifulSoup(comment_context, 'html.parser')
        review_eles = soup.find_all("li")
        logger.info(f"Found {len(review_eles)} review elements")

        
        for review_ele in review_eles:
            review = class_common.Review()

            # parse user name at first em tag
            review.reviewer_name = review_ele.find("em").text.strip()

            # parse rating
        
            rating = "0"
            try:
                rating_ele = review_ele.select_one("span.lstar > em")
                if rating_ele:
                    rating = rating_ele["class"]
                    rating = rating[-1].split("_")[-1]
            except Exception as e:
                logger.error(f"Failed to parse rating due to {str(e)}")
            review.rating = int(rating)
            
            # parse review content
            review_content = ""
            try:
                review_content_ele = review_ele.select_one("p.f14")
                if review_content_ele:
                    review_content = review_content_ele.text.strip()
            except Exception as e:
                logger.error(f"Failed to parse review content due to {str(e)}")
            review.body = review_content

            # compute review id with review body and product url
            full_review_content = f"{review_content}_{product_url}"
            review.review_id = hashlib.md5(full_review_content.encode("utf-8")).hexdigest()

            # parse review images
            try:
                image_list = list()

                image_eles = review_ele.select("div.s_d > img")
                for image_ele in image_eles:
                    image_url = image_ele["src"]
                    image_url = image_url.replace("t/80x80//", "")

                    file_name = image_url.split("/")[-1]
                    real_file_name = f"{product_id}_{file_name}"
                    real_image_url = f"https://smanny.com/wp-content/uploads/{current_year}/{current_month}/{real_file_name}"  # type: ignore
                    image_list.append(real_image_url)

                    # add media task
                    media_tasks.append((image_url, real_file_name, "image", settings.STATUS_INIT))

                review.picture_urls = ",".join(image_list)
            except Exception as e:
                logger.error(f"Failed to parse review images due to {str(e)}")

            # parse review date
            try:
                review_date_ele = review_ele.select_one("p.cmt_tm")
                if review_date_ele:
                    review_date = review_date_ele.text.strip().replace("Helpful ON", "").strip()
                    # convert date from '06 May 2023' to '2023-05-19 19:39:15 UTC'
                    review.review_date = datetime.datetime.strptime(review_date, "%d %B %Y").strftime("%Y-%m-%d %H:%M:%S UTC")
            except Exception as e:
                logger.error(f"Failed to parse review date due to {str(e)}")

            review.product_handle = product_url.split("/")[-1].split(".")[0]
            review.product_url = product_url

            reviews.append(review.to_tuple())
    except Exception as e:
        logger.error(f"Failed to parse reviews due to {str(e)}")

    if reviews:
        is_success = True
        logger.info(f"Found {len(reviews)} reviews for product {product_url}")
    
    return is_success, reviews, media_tasks



# scrape all review tasks
def scrape_all_review_tasks():
    db_sqlite.create_reviews_table()
    db_sqlite.create_images_table()

    stat_dict = dict()

    while True:
        # get all review tasks
        review_tasks = get_all_review_tasks()
        if not review_tasks:
            logger.info("No review tasks found. break")
            break
        
        task_length = len(review_tasks)
        if task_length not in stat_dict:
            stat_dict[task_length] = 0
        stat_dict[task_length] += 1

        total_retry_times = tools.get_retry_times()
        retry_times = stat_dict.get(task_length, 0)
        if retry_times > total_retry_times:
            logger.info(f"Task length {task_length} with retry times {retry_times} > {total_retry_times}. break")
            break
        else:
            logger.info(f"Task length {task_length} with retry times {retry_times} <= {total_retry_times}. continue")

        workers = tools.get_workers()

        if workers > 1:
            with ThreadPoolExecutor(max_workers=workers) as executor:
                executor.map(scrape_review_task, review_tasks)

        else:
            try:
                for task in review_tasks:
                    scrape_review_task(task)
                
                page_waiting_time = tools.get_page_waiting_time()
                logger.info(f"Sleep {page_waiting_time} seconds.")
                time.sleep(page_waiting_time)
            except Exception as e:
                logger.error(f"Failed to scrape review tasks due to {str(e)}", exc_info=True)


# test one tasks
def test_one_task():
    db_sqlite.create_reviews_table()

    tasks = get_all_review_tasks()
    if not tasks:
        logger.info("No review tasks found. break")
        return
    else:
        task = tasks[0]
        scrape_review_task(task)


if __name__ == "__main__":
    test_one_task()
    # scrape_all_review_tasks()

    # # test parse reviews
    # with open("test.html", "r") as f:
    #     page_context = f.read()
    #     parse_reviews(page_context, 2117, "https://www.bestvibe.com/bestvibe-7-thrusting--rotating-heating-wearable-masturbation-cup.html")

    pass
