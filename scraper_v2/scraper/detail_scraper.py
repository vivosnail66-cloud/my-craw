#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Author :  @fangwangme
Time   :  2023-05-24
Desc   :  
"""

import copy
import json
import random
import re
import datetime
import sys
import pathlib
import time

from concurrent.futures import ThreadPoolExecutor

import cloudscraper
from bs4 import BeautifulSoup

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
        "Host": "www.bestvibe.com",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/114.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
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
    scraper = cloudscraper.create_scraper()  # type: ignore
    # update headers

    use_proxy_flag = tools.get_use_proxy()
    if use_proxy_flag:
        proxy_data = proxy_utils.get_proxy()
    else:
        proxy_data = {}

    try:
        # get detail page
        r = scraper.get(task_url, timeout=settings.REQ_TIMEOUT, proxies=proxy_data)
        logger.info(f"Finished request {task_url} with status code {r.status_code}")

        if r.status_code == 200:
            products, media_tasks, review_tasks = parse_detail_page(
                r.text, task_url, task_category
            )

            if products:
                # update product
                insert_ret = db_sqlite.insert_products(products)
                if insert_ret:
                    task_status = settings.STATUS_SUCCESS

                    # update listing product status
                    task_ret = db_sqlite.update_listing_product_status(
                        url=task_url, status=task_status
                    )
                    logger.info(
                        f"Finished update listing product status with status {task_ret}"
                    )

                # insert media tasks
                if media_tasks:
                    media_ret = db_sqlite.insert_images(media_tasks)
                    logger.info(
                        f"Finished insert {len(media_tasks)} media tasks with status {media_ret}"
                    )

                # insert review tasks
                if review_tasks:
                    review_ret = db_sqlite.insert_review_tasks(review_tasks)
                    logger.info(
                        f"Finished insert {len(review_tasks)} review tasks with status {review_ret}"
                    )
        else:
            logger.error(
                f"Failed to request {task_url} with status code {r.status_code}"
            )
            task_status = settings.STATUS_REQ_ERROR
    except Exception as e:
        logger.error(f"Failed to request {task_url} due to {str(e)}", exc_info=True)
        task_status = settings.STATUS_REQ_ERROR

    time_cost = time.time() - start_time
    logger.info(
        f"Finished detail of {task_url} with status {task_status} in {time_cost} seconds"
    )

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

    # parse data from <script id='bm_product_variants' type='application/json'>
    script_ele = soup.select_one("script#bm_product_variants")
    variant_data_list = list()

    if script_ele:
        # convert to json
        variant_data_list = json.loads(script_ele.text.strip())

        product.sku = variant_data_list[0].get("sku", "").split("-")[0]
        product.sale_price = variant_data_list[0].get("price", "") / 100
        tmp_compare_price = variant_data_list[0].get("compare_at_price", "")
        if tmp_compare_price:
            product.regular_price = tmp_compare_price / 100

    # parse title from <h1 class='product-single__title'>
    title_ele = soup.select_one("h1.t4s-product__title")
    if title_ele:
        product.name = title_ele.text.strip()

    # parse images with given xpath //div[@class='t4s_ratio t4s-product__media']
    image_elements = soup.select("div.t4s_ratio.t4s-product__media > img")
    logger.info(f"Found {len(image_elements)} images")
    real_image_urls = list()
    for each in image_elements:
        # print attr of each
        tmp_image_url = each.attrs.get("data-src", "")
        if not tmp_image_url:
            continue

        image_url = "https:" + tmp_image_url.split("?")[0]

        # parse file name from url
        image_file_name = image_url.split("/")[-1]
        image_file_name = f"{product.sku}_{image_file_name}"
        real_image_url = f"https://smanny.com/wp-content/uploads/{current_year}/{current_month}/{image_file_name}"  # type: ignore

        media_list.append((image_url, image_file_name, "image", settings.STATUS_INIT))
        real_image_urls.append(real_image_url)

    product.images = ",".join(real_image_urls)

    # parse short description with given xpath //ul[@class='sellingpoint']/li
    try:
        short_desc_elements = soup.select("ul.sellingpoint > li")
        short_desc = ""

        for each in short_desc_elements:
            short_desc += each.text.strip() + "\n"

        product.short_description = short_desc.strip()
    except Exception as e:
        logger.error(f"Failed to parse short description due to {str(e)}")

    # parse description
    try:
        video_html = ""
        desc_html = ""

        # parse images from description
        image_soup = BeautifulSoup(desc_html, "html.parser")
        image_elements = image_soup.select("img")
        for each in image_elements:
            image_url = each.get("src")
            if image_url:
                tmp_file_name = image_url.split("/")[-1]  # type: ignore
                if product.sku:
                    file_name = f"{product.sku}_{tmp_file_name}"
                else:
                    file_name = tmp_file_name

                real_image_url = f"https://smanny.com/wp-content/uploads/{current_year}/{current_month}/{file_name}"  # type: ignore
                media_list.append((image_url, file_name, "image", settings.STATUS_INIT))
                desc_html = desc_html.replace(image_url, real_image_url)  # type: ignore

        # get video html with xpath div[@id='video'], then get full html
        video_html = ""
        video_element = soup.select_one("div#PVideo")
        if video_element:
            video_html = str(video_element)
            # replace video url and image url in the video html
            video_soup = BeautifulSoup(video_html, "html.parser")
            # get video element with xpath //source[@type='video/mp4']
            video_ele = video_soup.select_one("source[type='video/mp4']")
            if video_ele:
                video_url = video_ele.get("src")
                if video_url:
                    video_file_name = video_url.split("/")[-1]  # type: ignore
                    video_file_name = f"{product.sku}_{video_file_name}"
                    real_video_url = f"https://smanny.com/wp-content/uploads/{current_year}/{current_month}/{video_file_name}"  # type: ignore
                    media_list.append(
                        (video_url, video_file_name, "video", settings.STATUS_INIT)
                    )
                    video_html = video_html.replace(video_url, real_video_url)  # type: ignore

            # get video image element with xpath //img
            video_image_eles = video_soup.select("img")
            for each in video_image_eles:
                original_image_url = each.get("src")
                if original_image_url:
                    image_url = original_image_url.split("?")[0]
                    tmp_file_name = image_url.split("/")[-1]  # type: ignore
                    video_img_file_name = f"{product.sku}_{tmp_file_name}"
                    real_video_img_url = f"https://smanny.com/wp-content/uploads/{current_year}/{current_month}/{video_img_file_name}"  # type: ignore
                    media_list.append(
                        (
                            image_url,
                            video_img_file_name,
                            "image",
                            settings.STATUS_INIT,
                        )
                    )
                    video_html = video_html.replace(
                        original_image_url, real_video_img_url
                    )

        # get description html with xpath //div[@class='dcontent-list'],
        # need to get element with class equal to dcontent-list exactly
        tmp_desc_eles = soup.find_all("div", class_="dcontent-list")
        desc_element = None
        for each in tmp_desc_eles:
            # check if the element is the one we want with class equal to dcontent-list exactly
            if each.attrs.get("class") == ["dcontent-list"]:
                desc_element = each
                break

        if desc_element:
            desc_html = str(desc_element)

            # replace image url in the description html
            desc_soup = BeautifulSoup(desc_html, "html.parser")
            # get image elements with xpath //img
            desc_image_eles = desc_soup.select("img")
            for each in desc_image_eles:
                original_image_url = each.get("src")
                if original_image_url:
                    image_url = original_image_url.split("?")[0]
                    image_url = image_url.replace(
                        ".__CR0,0,970,600_PT0_SX970_V1___", ""
                    )
                    tmp_file_name = image_url.split("/")[-1]
                    desc_img_file_name = f"{product.sku}_{tmp_file_name}"
                    real_desc_img_url = f"https://smanny.com/wp-content/uploads/{current_year}/{current_month}/{desc_img_file_name}"  # type: ignore
                    media_list.append(
                        (
                            image_url,
                            desc_img_file_name,
                            "image",
                            settings.STATUS_INIT,
                        )
                    )
                    desc_html = desc_html.replace(original_image_url, real_desc_img_url)

        full_desc_html = f"""<div id="fulldesc">
    {video_html}
    {desc_html}
</div>
"""

        product.description = full_desc_html

    except Exception as e:
        logger.error(f"Failed to parse description due to {str(e)}")

    # set other fields
    product.visibility_in_catalog = "visible"

    # parse reviews
    review_count = 0
    try:
        # parse review count with xpath //div[@class='loox-rating']
        rating_ele = soup.select_one("div.loox-rating")
        if rating_ele:
            # get review count from attribute data-raters
            review_count_str = rating_ele.attrs["data-raters"]
            if review_count_str:
                review_count = int(review_count_str)

        review_url = ""
        loox_hash_id = ""
        product_id = ""
        idx_code = ""

        loox_hash_pat = re.compile(r"var loox_global_hash = '(\d+)';")
        loox_hash_match = loox_hash_pat.search(page_content)
        if loox_hash_match:
            loox_hash_id = loox_hash_match.group(1)

        # get product id
        product_id_ele = soup.select_one("div#looxReviews")
        if product_id_ele:
            product_id = product_id_ele.attrs["data-product-id"]

        # get idx code
        # '''<script async src="https://loox.io/widget/VkgIBbP9eh/loox.1646359077854.js'''
        idx_code_pat = re.compile(
            r"<script async src=\"https://loox.io/widget/(\w+)/loox\.\d+\.js"
        )
        idx_code_match = idx_code_pat.search(page_content)
        if idx_code_match:
            idx_code = idx_code_match.group(1)

        if review_count > 0 and loox_hash_id and product_id and idx_code:
            # https://loox.io/widget/VkgIBbP9eh/reviews/6721355022359?h=1686907594718
            review_url = f"https://loox.io/widget/{idx_code}/reviews/{product_id}?h={loox_hash_id}"
            review_tasks.append(
                (product.sku, review_url, review_count, 0, settings.STATUS_INIT)
            )
    except Exception as e:
        logger.error(f"Failed to parse reviews due to {str(e)}")

    # set fixed values
    product.tax_status = "taxable"
    product.published = 1  # type: ignore
    product.is_featured = 0  # type: ignore
    product.backorders_allowed = 0  # type: ignore
    product.sold_individually = 0  # type: ignore
    product.in_stock = 1  # type: ignore
    product.position = 0  # type: ignore

    if review_count > 0:
        product.allow_customer_reviews = 1  # type: ignore
    else:
        product.allow_customer_reviews = 0  # type: ignore

    # if length of colors is 1, then only color name is Default, then set product.type to simple
    if (
        len(variant_data_list) == 1
        and variant_data_list[0].get("option1") == "Default Title"
    ):
        product.type = "simple"
        products.append(product.to_detail_tuple())
    else:
        color_names = list()
        pos_index = 1
        for variant_data in variant_data_list:
            color_name = variant_data.get("option1")

            # if color name is Default Title, then skip
            if color_name == "Default Title":
                continue

            color_names.append(color_name)

            new_product = copy.deepcopy(product)
            new_product.name = f"{product.name} - {color_name}"
            new_product.sku = variant_data.get("sku", "")
            if new_product.sku == product.sku:
                new_product.sku = f"{product.sku}-{color_name}"
            new_product.sale_price = variant_data.get("price", 0) / 100
            tmp_compare_price = variant_data.get("compare_at_price", 0)
            if tmp_compare_price:
                new_product.regular_price = tmp_compare_price / 100
            new_product.parent = product.sku
            new_product.type = "variation"
            new_product.attribute1_name = "Color"
            new_product.attribute1_value = color_name
            new_product.attribute1_global = 1  # type: ignore
            new_product.tax_class = "parent"
            new_product.position = pos_index  # type: ignore
            new_product.allow_customer_reviews = 0  # type: ignore
            new_product.short_description = ""
            new_product.description = ""
            new_product.categories = ""
            new_product.tags = ""

            products.append(new_product.to_detail_tuple())
            pos_index += 1

        product.type = "variable"
        product.attribute1_name = "Color"
        product.attribute1_value = ",".join(color_names)
        product.attribute1_global = 1  # type: ignore
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
            logger.info(
                f"There are {task_length} detail tasks to be scraped at {stat_dict.get(task_length, 0)} times, the scraper will exit."
            )
            break
        else:
            logger.info(
                f"There are {task_length} detail tasks to be scraped at {stat_dict.get(task_length, 0)} times."
            )

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
def test_single_task(task_id):
    db_sqlite.create_images_table()
    db_sqlite.create_review_tasks_table()
    db_sqlite.create_products_table()

    # reshuflle tasks
    sql = f"SELECT scraped_category, url FROM listing_products WHERE id = {task_id};"
    tasks = db_sqlite.query_by_sql(sql)

    if not tasks:
        logger.info("There is no detail task, the scraper will exit.")
        return
    else:
        logger.info(f"There are {len(tasks)} detail tasks to be scraped.")
        task = tasks[0]
        scrape_detail_task(task)


if __name__ == "__main__":
    test_single_task(17)

    # # test parse product
    # with open("test2.html", "r") as f:
    #     page_content = f.read()
    #     print(
    #         parse_detail_page(
    #             page_content,
    #             "https://www.sohimi.com/products/sohimi-rose-toy",
    #             "Rose Vibrators",
    #         )
    #     )

    pass
