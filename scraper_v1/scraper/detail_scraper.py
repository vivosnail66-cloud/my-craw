#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Author :  @fangwangme
Time   :  2023-05-24
Desc   :  
"""

import copy
import random
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


# scrape single detail task
def scrape_detail_task(task):
    start_time = time.time()

    # get info from task
    task_category, task_url = task

    logger.info(f"Start to scrape detail task {task_url}")

    task_status = settings.STATUS_INIT

    # init session
    s = requests.Session()

    # update headers
    s.headers = build_headers() # type: ignore

    use_proxy_flag = tools.get_use_proxy()
    if use_proxy_flag:
        proxy_data = proxy_utils.get_proxy()
    else:
        proxy_data = {}


    try:
        # get category page
        r = s.get(task_url, timeout=settings.REQ_TIMEOUT, proxies=proxy_data)
        logger.info(f"Finished request {HOME_PAGE} with status code {r.status_code}")

        if r.status_code == 200:
            # parse category page
            products, media_tasks, review_tasks = parse_detail_page(r.text, task_url, task_category)

            if products:
                # update product
                insert_ret = db_sqlite.insert_products(products)
                if insert_ret:
                    task_status = settings.STATUS_SUCCESS

                    # update listing product status
                    task_ret = db_sqlite.update_listing_product_status(url=task_url, status=task_status)
                    logger.info(f"Finished update listing product status with status {task_ret}")

                # insert media tasks
                if media_tasks:
                    media_ret = db_sqlite.insert_images(media_tasks)
                    logger.info(f"Finished insert {len(media_tasks)} media tasks with status {media_ret}")

                # insert review tasks
                if review_tasks:
                    review_ret = db_sqlite.insert_review_tasks(review_tasks)
                    logger.info(f"Finished insert {len(review_tasks)} review tasks with status {review_ret}")
        else:
            logger.error(f"Failed to request {task_url} with status code {r.status_code}")
            task_status = settings.STATUS_REQ_ERROR
    except Exception as e:
        logger.error(f"Failed to request {task_url} due to {str(e)}")
        task_status = settings.STATUS_REQ_ERROR

    time_cost = time.time() - start_time
    logger.info(f"Finished scrape_all_category with status {task_status} in {time_cost} seconds")

    return task_status


# parse detail page
def parse_detail_page(page_content, task_url, task_category):
    soup = BeautifulSoup(page_content, "html.parser")

    media_list = list()
    review_tasks = list()
    products = list()
    product = class_common.Product()
    product.url = task_url
    product.scraped_category = task_category

    current_year = datetime.datetime.now().year
    # get current month, need 05 instead of 5
    current_month = datetime.datetime.now().strftime("%m")

    # parse sku from <em id="sku" rel="nofollow">Q8535</em>
    try:
        sku_ele = soup.select_one("em#sku")
        if sku_ele:
            product.sku = sku_ele.text.strip()
    except Exception as e:
        logger.error(f"Failed to parse sku due to {str(e)}")

    # parse name
    try:
        title_element = soup.select_one("h1.gh1")
        product.name = title_element.text.strip() # type: ignore
    except Exception as e:
        logger.error(f"Failed to parse title due to {str(e)}")


    # parse short description
    try:
        short_desc_elements = soup.select("li.high_txt")
        short_desc = ""

        for each in short_desc_elements:
            short_desc += each.text.strip() + "\n"
        
        product.short_description = short_desc.strip()
    except Exception as e:
        logger.error(f"Failed to parse short description due to {str(e)}")

    
    # parse description
    try:
        # get highlight element with xpath div[@id='highlights'], then get full html
        highlight_element = soup.select_one("div#highlights")
        high_light_html = ""
        if highlight_element:
            high_light_html = str(highlight_element)

        # get description element with xpath div[@id='detail'], then get full html
        desc_html = ""
        desc_element = soup.select_one("div#detail")
        if desc_element:
            desc_html = str(desc_element)
        
        # need to replace @src with @src2 for all images in the description
        # like : <img height=""500"" src=""https://img.bestvibe.com/cdn-cgi/image/format=auto//mobile/asset/css/f/blank.png"" src2=""https://img.bestvibe.com/cdn-cgi/image/format=auto/images/goods/2003/goods_d      esc/20230414/20230414032830_89487.jpg"" width=""790""/>
        desc_html = desc_html.replace("src=", "src3=")
        desc_html = desc_html.replace("src2=", "src=")

        # parse images from description
        image_soup = BeautifulSoup(desc_html, "html.parser")
        image_elements = image_soup.select("img")
        for each in image_elements:
            image_url = each.get("src")
            if image_url:
                tmp_file_name = image_url.split("/")[-1]    # type: ignore
                if product.sku:
                    file_name = f"{product.sku}_{tmp_file_name}"
                else:
                    file_name = tmp_file_name

                real_image_url = f"https://smanny.com/wp-content/uploads/{current_year}/{current_month}/{file_name}"  # type: ignore
                media_list.append((image_url, file_name, "image", settings.STATUS_INIT))
                desc_html = desc_html.replace(image_url, real_image_url)    # type: ignore

        # get video html with xpath div[@id='video'], then get full html
        video_html = ""
        video_element = soup.select_one("div#video")
        if video_element:
            video_html = str(video_element)
            video_html = f'''<div class="pt10">
	<h4 class="gh2">Videos</h4>
	{video_html}
    <p></p>
    </div>'''
            
        full_desc_html = f'''<div id="fulldesc">
    {high_light_html}
    {video_html}
    {desc_html}
        '''
        product.description = full_desc_html

    except Exception as e:
        logger.error(f"Failed to parse description due to {str(e)}")

    # parse regular price
    try:
        price_element = soup.select_one("b#gprice")
        if price_element:
            product.sale_price = product.regular_price = float(price_element.text.strip().replace("$", "")) # type: ignore

        # parse regular price if exists
        regular_price_element = soup.select_one("del#loot_shops")
        if regular_price_element:
            product.regular_price = float(regular_price_element.text.strip().replace("$", "")) # type: ignore

    except Exception as e:
        logger.error(f"Failed to parse regular price due to {str(e)}")


    # parse tags
    try:
        tag_elements = soup.select("a.gs_tag")
        tags = list()
        for each in tag_elements:
            tags.append(each.text.strip())
        
        product.tags = ",".join(tags)
    except Exception as e:
        logger.error(f"Failed to parse tags due to {str(e)}")


    # parse categories
    try:
        category_elements = soup.select("a.gf_ico")
        categories = list()
        # get @title attribute
        for each in category_elements:
            categories.append(each.attrs["title"])

        product.categories = ",".join(categories)
    except Exception as e:
        logger.error(f"Failed to parse categories due to {str(e)}")

    # parse colors
    colors = list()
    try:
        color_elements = soup.select("dd#sx_html > div")

        for each in color_elements:
            color_name  = each.em.text.strip() # type: ignore
            color_sku = each.attrs["data-h"]
            color_sale_price = each.attrs["data-p"]
            color_regular_price = each.attrs["data-y"]
            color_image = each.attrs.get("data-pic", "")

            if color_image:
                image_url = color_image.replace("t/100x100/", "")
                tmp_file_name = image_url.split("/")[-1]
                if color_sku:
                    file_name = f"{color_sku}_{tmp_file_name}"
                else:
                    file_name = tmp_file_name

                real_image_url = f"https://smanny.com/wp-content/uploads/{current_year}/{current_month}/{file_name}"  # type: ignore
                media_list.append((image_url, file_name, "image", settings.STATUS_INIT))
                color_image = real_image_url

            colors.append((color_name, color_sku, color_sale_price, color_regular_price, color_image))
    except Exception as e:
        logger.error(f"Failed to parse colors due to {str(e)}", exc_info=True)

    # parse images
    try:
        image_elements = soup.select("img.jdt")
        images = list()
        for each in image_elements:
            # get lazy attribute or src attribute
            if "lazy" in each.attrs:
                images.append(each.attrs["lazy"])
            else:
                images.append(each.attrs["src"])

        # build new image url
        real_image_urls = list()

        for each in images:
            image_url = each.replace("t/500x500/", "")
            tmp_file_name = image_url.split("/")[-1]
            if product.sku:
                file_name = f"{product.sku}_{tmp_file_name}"  # type: ignore
            else:
                file_name = tmp_file_name
            real_image_url = f"https://smanny.com/wp-content/uploads/{current_year}/{current_month}/{file_name}"  # type: ignore
            media_list.append((image_url, file_name, "image", settings.STATUS_INIT))
            real_image_urls.append(real_image_url)

        product.images = ",".join(real_image_urls)
    except Exception as e:
        logger.error(f"Failed to parse images due to {str(e)}")

    # parse video
    try:
        video_element = soup.select_one("video#media")
        if video_element:
            video_url = video_element.attrs["src"]
            tmp_file_name = video_url.split("/")[-1]
            if product.sku:
                file_name = f"{product.sku}_{tmp_file_name}"
            else:
                file_name = tmp_file_name
            product.video_url = f"https://smanny.com/wp-content/uploads/{current_year}/{current_month}/{file_name}"

            media_list.append((video_url, file_name, "video", settings.STATUS_INIT))
    except Exception as e:
        logger.error(f"Failed to parse video due to {str(e)}")

    # set other fields
    product.visibility_in_catalog = "visible"

    # parse reviews
    try:
        review_count = 0
        product_id = 0

        review_result = REVIEW_PAT.search(page_content)
        if review_result:
            review_count = int(review_result.group(1))

        product_id_result = MPN_PAT.search(page_content)
        if product_id_result:
            product_id = int(product_id_result.group(1))

        if review_count > 0 and product_id > 0:
            review_tasks.append((product.url, product_id, review_count, 0, settings.STATUS_INIT))
    except Exception as e:
        logger.error(f"Failed to parse reviews due to {str(e)}")


    if product.name and product.sale_price and product.description:
        product.status = settings.STATUS_SUCCESS # type: ignore

    # if length of colors is 1, then only color name is Default, then set product.type to simple
    if len(colors) == 1 and colors[0][0] == "Default":
        product.type = "simple"
        products.append(product.to_detail_tuple())
    else:
        color_names = list()
        for color in colors:
            color_name, color_sku, color_sale_price, color_regular_price, color_image = color

            if color_name == "Default":
                continue

            color_names.append(color_name)

            new_product = copy.deepcopy(product)
            new_product.sku = color_sku
            new_product.sale_price = color_sale_price
            new_product.regular_price = color_regular_price
            new_product.parent = product.sku
            new_product.images = color_image
            new_product.type = "variation"
            new_product.attribute1_name = "Color"
            new_product.attribute1_value = color_name
            new_product.attribute1_global = 1  # type: ignore
            products.append(new_product.to_detail_tuple())

        product.type = "variable"
        product.attribute1_name = "Color"
        product.attribute1_value = ",".join(color_names)
        product.attribute1_global = 1   # type: ignore
        product.attribute1_visible = 1  # type: ignore
        products.append(product.to_detail_tuple())

    
    return products, media_list, review_tasks


# scrape all detail tasks
def scrape_all_detail_tasks():
    # create table if not exists
    db_sqlite.create_images_table()
    db_sqlite.create_review_tasks_table()
    db_sqlite.create_products_table()

    stat_dict = dict()

    while True:
        tasks = get_all_detail_tasks()

        if not tasks:
            logger.info("There is no detail task, the scraper will exit.")
            break

        task_length = len(tasks)
        if task_length not in stat_dict:
            stat_dict[task_length] = 0
        stat_dict[task_length] += 1

        total_retry_times = tools.get_retry_times()
        if stat_dict.get(task_length, 0) > total_retry_times:
            logger.info(f"There are {task_length} detail tasks to be scraped at {stat_dict.get(task_length, 0)} times, the scraper will exit.")
            break
        else:
            logger.info(f"There are {task_length} detail tasks to be scraped at {stat_dict.get(task_length, 0)} times.")

        workers = tools.get_workers()
        if workers > 1:
            # scrape all detail tasks
            with ThreadPoolExecutor(max_workers=workers) as executor:
                executor.map(scrape_detail_task, tasks)
        else:
            try:
                for each in tasks:
                    scrape_detail_task(each)

                    page_waiting_time = tools.get_page_waiting_time()
                    logger.info(f"Sleep {page_waiting_time} seconds before next page")
                    time.sleep(page_waiting_time)
            except Exception as e:
                logger.error(f"Failed to scrape detail tasks due to {str(e)}")


# get all detail tasks
def get_all_detail_tasks():
    sql = f"SELECT scraped_category, url FROM listing_products WHERE status != '{settings.STATUS_SUCCESS}'"
    results = db_sqlite.query_by_sql(sql)
    return results


# test single task
def test_single_task():
    db_sqlite.create_images_table()
    db_sqlite.create_review_tasks_table()
    db_sqlite.create_products_table()
    
    tasks = get_all_detail_tasks()
    # reshuflle tasks
    random.shuffle(tasks)
    
    if not tasks:
        logger.info("There is no detail task, the scraper will exit.")
        return
    else:
        logger.info(f"There are {len(tasks)} detail tasks to be scraped.")
        task = tasks[0]
        scrape_detail_task(task)


if __name__ == "__main__":
    test_single_task()

    # # test parse product
    # with open("test.html", "r") as f:
    #     page_content = f.read()
    #     parse_detail_page(page_content, "https://www.bestvibe.com/hardy-automatic-3-frequency-telescopic-handheld-male-masturbator.html")

    pass