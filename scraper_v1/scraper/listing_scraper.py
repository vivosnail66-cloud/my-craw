#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Author :  @fangwangme
Time   :  2023-05-23
Desc   :  
"""

import sys
import pathlib
import time
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from concurrent.futures import ThreadPoolExecutor

import requests

# sys path append parent folder
sys.path.append(f"{pathlib.Path(__file__).parent}/../")
from common.logger import logger
from common import db_sqlite, settings, class_common, tools, proxy_utils

HOME_PAGE = "https://www.bestvibe.com/"


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


# scrape all category and subcategory
def scrape_all_category():
    start_time = time.time()
    
    # create table if not exist
    db_sqlite.create_category_tasks_table()

    task_status = settings.STATUS_INIT

    # init session
    s = requests.Session()

    # update headers
    s.headers = build_headers() # type: ignore

    try:
        # get category page
        r = s.get(HOME_PAGE, timeout=settings.REQ_TIMEOUT)
        logger.info(f"Finished request {HOME_PAGE} with status code {r.status_code}")

        if r.status_code == 200:
            # parse category page
            category_tasks = parse_categories(r.content)
            if category_tasks:
                ret = db_sqlite.insert_category_tasks(category_tasks)
                logger.info(f"Finished insert {len(category_tasks)} category tasks with ret {ret}")

                if ret >= 0:
                    task_status = settings.STATUS_SUCCESS
            else:
                task_status = settings.STATUS_NO_DATA
                
        else:
            logger.error(f"Failed to request {HOME_PAGE} with status code {r.status_code}")
            task_status = settings.STATUS_REQ_ERROR
    except Exception as e:
        logger.error(f"Failed to request {HOME_PAGE} due to {str(e)}", exc_info=True)
        task_status = settings.STATUS_REQ_ERROR

    time_cost = time.time() - start_time
    logger.info(f"Finished scrape_all_category with status {task_status} in {time_cost} seconds")

    return task_status


# parse categories
def parse_categories(content):
    category_tasks = list()
    category_results = list()

    soup = BeautifulSoup(content, 'html.parser')

    # parse all category elements with xpath 'ul[@id="nav_ul"]/li'
    category_elements = soup.select('ul#nav_ul > li')
    logger.info(f"Found {len(category_elements)} category elements")

    # parse each category element
    for category_element in category_elements:
        # if @class='nav_home', skip
        if category_element.get('class') == ['nav_home']:
            continue

        # parse category name
        category_name_ele = category_element.select_one('a')
        if category_name_ele:
            category_name = category_name_ele.text

            # parse category url
            category_url = category_name_ele.get('href')

        else:
            logger.error(f"Failed to parse category name from {category_element}")
            continue


        # parse subcategory elements with xpath 'div[@class='nav_suba']/div/a
        subcategory_elements = category_element.find_all('a', class_='nav_suba')
        logger.info(f"Found {len(subcategory_elements)} subcategory elements for category {category_name}")
        
        if not subcategory_elements:
            logger.warning(f"No subcategory found for category {category_name}")
            real_category_url = urljoin(HOME_PAGE, category_url) # type: ignore
            category_results.append((category_name, real_category_url))

        else:
            for each_subcategory_element in subcategory_elements:
                # parse subcategory name
                subcategory_name = each_subcategory_element.text

                # parse subcategory url
                subcategory_url = each_subcategory_element.get('href')
                real_category_url = urljoin(HOME_PAGE, subcategory_url)
                category_results.append((subcategory_name, real_category_url))

    # build category tasks
    tmp_category_results = dict()

    for category_name, category_url in category_results:
        if category_url not in tmp_category_results:
            tmp_category_results[category_url] = []
        
        tmp_category_results[category_url].append(category_name)
    
    for categry_url, category_names in tmp_category_results.items():
        category_task = class_common.CategoryTask()
        category_task.url = categry_url
        category_task.name = ','.join(list(set(category_names)))
        category_task.status = settings.STATUS_INIT

        if category_task.name in ["Best Sellers", "Newest", "Coupons", "Sale", "Students"]:
            continue

        category_tasks.append(category_task.to_tuple())

    logger.info(f"Finished parsing {len(category_tasks)} category tasks")
    return category_tasks


# get all listing tasks
def get_all_listing_tasks():
    sql = f"SELECT * FROM category_tasks WHERE status!={settings.STATUS_SUCCESS};"
    tasks = db_sqlite.query_by_sql(sql)

    return tasks


# scrape listing task
def scrape_listing_task(task):
    start_time = time.time()

    # get info from task
    _, category_name, task_url, total_pages, crawled_pages, task_status = task 
    logger.info(f"Start to scrape listing of {category_name} with url {task_url}")

    # init session
    s = requests.Session()

    # update headers
    s.headers = build_headers() # type: ignore

    use_proxy_flag = tools.get_use_proxy()
    if use_proxy_flag:
        proxy_data = proxy_utils.get_proxy()
    else:
        proxy_data = {}

    total_pages = 1
    crawled_pages = 0

    try:

        while crawled_pages < total_pages:
            if crawled_pages > 0:
                req_url = urljoin(task_url, f"?p={crawled_pages + 1}")
            else:
                req_url = task_url
            
            # get listing page
            logger.info(f"Start to scrape listing at page {crawled_pages + 1} with url {req_url}")
            r = s.get(req_url, timeout=settings.REQ_TIMEOUT, proxies=proxy_data)
            logger.info(f"Finished request {task_url} with status code {r.status_code}")

            if r.status_code == 200:
                # parse listing page
                is_success, tmp_total_pages, listings = parse_listings(r.content, category_name)
                if is_success:
                    # update total pages and task url
                    total_pages = tmp_total_pages

                    # insert listings
                    ret = db_sqlite.insert_listing_products(listings)
                    logger.info(f"Finished insert {len(listings)} listings with ret {ret}")

                    if ret >= 0:
                        crawled_pages += 1
                else:
                    logger.error(f"Failed to parse listing page {req_url}")
                    break    
            else:
                logger.error(f"Failed to request {req_url} with status code {r.status_code}")
                break

    except Exception as e:
        logger.error(f"Failed to request {task} due to {str(e)}")

    # update task status
    if crawled_pages > 0 and crawled_pages >= total_pages:
        task_status = settings.STATUS_SUCCESS
    else:
        task_status = settings.STATUS_PART_SUCCESS

    update_ret = db_sqlite.update_category_task(category_url=task_url, total_pages=total_pages, crawled_pages=crawled_pages, status=task_status)
    logger.info(f"Finished update category task {task_url} with ret {update_ret}")
    
    time_cost = time.time() - start_time
    logger.info(f"Finished scrape_listing_task with status {task_status} in {time_cost} seconds")


# parse listing page
def parse_listings(content, category_name=""):
    is_success = False
    listings = list()
    total_pages = 0

    soup = BeautifulSoup(content, 'html.parser')

    try:
        # parse total pages with xpath //b[@id='page_totals']
        total_pages_ele = soup.select_one('b#page_totals')
        if total_pages_ele:
            total_pages = int(total_pages_ele.text)
            logger.info(f"Found total pages {total_pages}")
        else:
            total_pages = 1

        # parse listing elements with xpath //div[id='glist']/a
        listing_elements = soup.select('div#glist > a')
        logger.info(f"Found {len(listing_elements)} listing elements")
        if not listing_elements:
            listing_elements = soup.select('div#goods_box > a')

            if not listing_elements:
                is_success = True

        for each_listing_element in listing_elements:
            product = class_common.Product()

            # parse listing url
            listing_url = each_listing_element.get('href')
            product.url = urljoin(HOME_PAGE, listing_url).split("?")[0] # type: ignore

            # parse listing title from //h3
            product.name = each_listing_element.select_one('h3').text.strip() # type: ignore
            product.categories = category_name
            product.status = settings.STATUS_INIT # type: ignore

            listings.append(product.to_listing_tuple())

    except Exception as e:
        logger.error(f"Failed to parse listing page due to {str(e)}", exc_info=True)
    
    if not is_success and total_pages and listings:
        is_success = True

    return is_success, total_pages, listings
    

# scrape all listing tasks
def scrape_all_listing_tasks():
    # create table if not exist
    db_sqlite.create_products_table()

    stat_dict = dict()

    while True:
        tasks = get_all_listing_tasks()
        if not tasks:
            logger.info(f"No un-scraped listing tasks found, exit")
            break

        task_length = len(tasks)
        if task_length not in stat_dict:
            stat_dict[task_length] = 0
        stat_dict[task_length] += 1

        total_retry_times = tools.get_retry_times()
        if stat_dict.get(task_length, 0) > total_retry_times:
            logger.error(f"Retry times {total_retry_times} reached, exit")
            break
        else:
            logger.info(f"Start to scrape {task_length} listing tasks with retry times {stat_dict.get(task_length, 0)}")

        workers = tools.get_workers()
        if workers > 1:
            with ThreadPoolExecutor(max_workers=workers) as executor:
                executor.map(scrape_listing_task, tasks)
        else:
            try:
                for task in tasks:
                    scrape_listing_task(task)

                    page_waiting_time = tools.get_page_waiting_time()
                    logger.info(f"Sleep {page_waiting_time} seconds before next page")
                    time.sleep(page_waiting_time)
            except Exception as e:
                logger.error(f"Failed to scrape listing tasks due to {str(e)}", exc_info=True)
            

# test one task
def test_one_task():
    db_sqlite.create_listing_products_table()

    tasks = get_all_listing_tasks()
    if tasks:
        task = tasks[0]
        scrape_listing_task(task)


if __name__ == "__main__":

    # scrape_all_category()

    # # test parse categories/listing
    # with open('test.html', 'r') as f:
    #     content = f.read()
    #     # parse_categories(content)
    #     parse_listings(content)

    # # test single task
    test_one_task()

    pass


        
