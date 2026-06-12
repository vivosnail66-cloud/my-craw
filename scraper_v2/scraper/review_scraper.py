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
import random
import re
import datetime
import sys
import pathlib
import time
import urllib.parse

from concurrent.futures import ThreadPoolExecutor

import cloudscraper
from bs4 import BeautifulSoup


# sys path append parent folder
sys.path.append(f"{pathlib.Path(__file__).parent}/../")
from common.logger import logger
from common import db_sqlite, settings, class_common, tools, proxy_utils


REVIEW_PAT = re.compile(r'"reviewCount": "(\d+)"', re.S)
MPN_PAT = re.compile(r'"mpn":"(\d+)"', re.S)
PAGE_SIZE = 20


# build headers
def build_headers():
    headers = {
        "Host": "loox.io",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/115.0",
        "Accept": "*/*",
        "Accept-Language": "en-US",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
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
    task_id, product_sku, review_url, total_count, crawled_count, task_status = task

    s = cloudscraper.create_scraper()

    # get proxy
    use_proxy_flag = tools.get_use_proxy()
    if use_proxy_flag:
        proxy_data = proxy_utils.get_proxy()
    else:
        proxy_data = {}

    try:
        total_pages = math.ceil(total_count / PAGE_SIZE)
        logger.info(f"Total pages {total_pages}")
        current_page = 1

        while current_page <= total_pages:
            # get review page
            # h=1686907594718&total=257&variant=visible&page=2
            req_url = f"{review_url}&total={total_count}&variant=visible&page={current_page}&limit={PAGE_SIZE}"

            logger.info(
                f"Start to scrape reviews at page {current_page} with url {req_url}"
            )
            # driver.get(req_url)
            r = s.get(req_url, proxies=proxy_data, timeout=settings.REQ_TIMEOUT)
            logger.info(f"Get review page with url {req_url} success")

            is_success, reviews, media_tasks = parse_reviews(r.text, product_sku)

            if is_success:
                # save reviews
                ret = db_sqlite.insert_reviews(reviews)
                logger.info(f"Save {len(reviews)} reviews with ret {ret}")

                current_page += 1
                crawled_count += len(reviews)
                logger.info(
                    f"Scrape reviews at page {current_page} with url {review_url} successfully"
                )

                # save media tasks
                task_ret = db_sqlite.insert_images(media_tasks)
                logger.info(f"Save {len(media_tasks)} media tasks with ret {task_ret}")
            else:
                logger.error(
                    f"Parse reviews at page {current_page} with url {review_url} failed"
                )
                raise Exception(
                    f"Parse reviews at page {current_page} with url {review_url} failed"
                )
    except Exception as e:
        logger.error(f"Failed to scrape review task {task} due to {str(e)}")

    # get count of reviews
    sql = f"SELECT COUNT(*) FROM reviews WHERE sku = '{product_sku}';"
    real_crawled_count = db_sqlite.query_by_sql(sql)[0][0]

    if real_crawled_count >= total_count:
        task_status = settings.STATUS_SUCCESS
    else:
        task_status = settings.STATUS_PART_SUCCESS

    # update review task
    update_ret = db_sqlite.update_review_task(
        url=product_sku,
        total=total_count,
        crawled=real_crawled_count,
        status=task_status,
    )
    logger.info(
        f"Updated crawled {real_crawled_count}, status {task_status} for review task {product_sku} with ret {update_ret}"
    )

    time_cost = time.time() - start_time
    logger.info(f"Scrape review task {product_sku} with time cost {time_cost}")


# parse reviews
def parse_reviews(page_context, product_sku):
    is_success = False
    reviews = list()
    media_tasks = list()

    current_year = datetime.datetime.now().year
    # get current month, need 05 instead of 5
    current_month = datetime.datetime.now().strftime("%m")

    # testing
    with open("test.html", "w") as f:
        f.write(page_context)

    try:
        soup = BeautifulSoup(page_context, "html.parser")
        # get review elements with xpath //div[@class='grid-item clearfix']
        review_eles = soup.select("div.grid-item.clearfix")
        logger.info(f"Found {len(review_eles)} review elements")

        for review_ele in review_eles:
            review = class_common.Review()

            # parse review id
            review_id = review_ele.attrs.get("data-id", "")
            if not review_id:
                logger.error(f"Failed to parse review id")
                continue

            review.review_id = review_id
            review.sku = product_sku

            # parse user name with xpath //div[@class='block title']/text()
            user_name_ele = review_ele.find("div", class_="block title")
            if user_name_ele:
                review.reviewer_name = user_name_ele.text.strip()

            # parse rating
            rating = "0"
            try:
                rating_ele = review_ele.find("div", class_="block stars")
                if rating_ele:
                    rating_str = rating_ele["aria-label"]
                    rating = rating_str.strip().split(" ")[0]
            except Exception as e:
                logger.error(f"Failed to parse rating due to {str(e)}")
            review.rating = int(rating)

            # parse review content with xpath //div[@class='pre-wrap main-text action']
            review_content_ele = review_ele.find(
                "div", class_="pre-wrap main-text action"
            )
            if review_content_ele:
                review_content = review_content_ele.text.strip()
                review.body = review_content

            # parse review images
            try:
                image_list = list()

                image_eles = review_ele.select("img")
                for image_ele in image_eles:
                    image_url = image_ele["src"]
                    image_url = urllib.parse.urljoin("https://", image_url)

                    file_name = image_url.split("/")[-1]
                    real_file_name = f"REVIEW_{product_sku}_{file_name}"
                    real_image_url = f"https://smanny.com/wp-content/uploads/{current_year}/{current_month}/{real_file_name}"  # type: ignore
                    image_list.append(real_image_url)

                    # add media task
                    media_tasks.append(
                        (image_url, real_file_name, "image", settings.STATUS_INIT)
                    )

                review.picture_urls = ",".join(image_list)
            except Exception as e:
                logger.error(f"Failed to parse review images due to {str(e)}")

            # set a random date from 2023-01-01 to now
            start_date = datetime.datetime(2023, 1, 1)
            end_date = datetime.datetime.now()
            delta = end_date - start_date
            random_days = random.randint(0, delta.days)
            review_date = start_date + datetime.timedelta(days=random_days)
            # convert to "%Y-%m-%d %H:%M:%S" format
            review_date_str = review_date.strftime("%Y-%m-%d %H:%M:%S")
            review.review_date = review_date_str

            reviews.append(review.to_tuple())
    except Exception as e:
        logger.error(f"Failed to parse reviews due to {str(e)}")

    if reviews:
        is_success = True
        logger.info(f"Found {len(reviews)} reviews for product {product_sku}")

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
            logger.info(
                f"Task length {task_length} with retry times {retry_times} > {total_retry_times}. break"
            )
            break
        else:
            logger.info(
                f"Task length {task_length} with retry times {retry_times} <= {total_retry_times}. continue"
            )

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
                logger.error(
                    f"Failed to scrape review tasks due to {str(e)}", exc_info=True
                )


# test one tasks
def test_one_task(id):
    # create reviews table
    db_sqlite.create_reviews_table()

    sql = f"select * from review_tasks where id={id};"
    tasks = db_sqlite.query_by_sql(sql)

    if not tasks:
        logger.info("No review tasks found. break")
        return
    else:
        task = tasks[0]
        # with CustomChromeDriver() as driver:
        #     scrape_review_task(task, driver)
        scrape_review_task(task)


if __name__ == "__main__":
    test_one_task(id=2)
    # scrape_all_review_tasks()

    # # test parse reviews
    # with open("test.html", "r") as f:
    #     page_context = f.read()
    #     parse_reviews(page_context, 2117, "https://www.bestvibe.com/bestvibe-7-thrusting--rotating-heating-wearable-masturbation-cup.html")

    pass
