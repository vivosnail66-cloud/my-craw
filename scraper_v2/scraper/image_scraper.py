#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Author :  @fangwangme
Time   :  2023-05-24
Desc   :  
"""


import datetime
import os
import shutil
import sys
import pathlib

from concurrent.futures import ThreadPoolExecutor

import requests

# sys path append parent folder
sys.path.append(f"{pathlib.Path(__file__).parent}/../")
from common.logger import logger
from common import db_sqlite, settings, tools


def get_all_media_tasks():
    # get all media tasks
    sql = f"SELECT * FROM images WHERE status != {settings.STATUS_SUCCESS}"
    return db_sqlite.query_by_sql(sql)


# scrape media task
def scrape_media_task(task):
    # get task info
    _, original_media_url, file_name, media_type, _ = task

    if media_type == "image":
        folder_path = settings.IMAGE_PATH.format(pathlib.Path(__file__).parent)
    elif media_type == "video":
        folder_path = settings.VIDEO_PATH.format(pathlib.Path(__file__).parent)
    else:
        logger.error(f"Unknown media type {media_type}")
        return

    # create fold if not exist
    pathlib.Path(folder_path).mkdir(parents=True, exist_ok=True)
    full_file_path = os.path.join(folder_path, file_name)

    try:
        media_url = original_media_url
        # modify the media url
        if not media_url.startswith("http"):
            media_url = f"https:{media_url}"

        if "////" in media_url:
            media_url = media_url.replace("////", "//")

        r = requests.get(media_url, stream=True)
        if r.status_code == 200:
            with open(full_file_path, "wb") as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)

            p = pathlib.Path(full_file_path)
            if p.exists():
                logger.info(f"Download {media_type} {file_name} success.")
                update_ret = db_sqlite.update_image_status(
                    original_media_url, settings.STATUS_SUCCESS
                )
                logger.info(
                    f"Update {media_type} {file_name} status to success with ret {update_ret}"
                )
    except Exception as e:
        logger.error(f"Download {media_type} {file_name} failed due to {str(e)}")


def scrape_all_media_tasks():
    update_image_task_status()

    stat_dict = dict()

    while True:
        # get all media tasks
        tasks = get_all_media_tasks()

        if not tasks:
            logger.info("No more tasks, exit.")
            break

        task_length = len(tasks)
        if task_length not in stat_dict:
            stat_dict[task_length] = 0
        stat_dict[task_length] += 1

        retry_times = tools.get_retry_times()
        if stat_dict.get(task_length, 0) > retry_times:
            logger.info(
                f"There are {task_length} tasks for {stat_dict.get(task_length, 0)} times, and the retry times is {retry_times}, exit."
            )
            break
        else:
            logger.info(
                f"There are {task_length} tasks for {stat_dict.get(task_length, 0)} times, and the retry times is {retry_times}, continue."
            )

        workers = tools.get_workers()
        if workers > 1:
            with ThreadPoolExecutor(max_workers=workers) as executor:
                executor.map(scrape_media_task, tasks)

        else:
            try:
                for task in tasks:
                    scrape_media_task(task)
            except Exception as e:
                logger.error(f"Failed to scrape media tasks due to {str(e)}")

    # fix all image url
    fix_all_image_urls()


def load_success_image_urls():
    # get all media tasks
    # get all files in image folder
    succeed_image_urls = list()
    folder_path = settings.IMAGE_PATH.format(pathlib.Path(__file__).parent)
    pathlib.Path(folder_path).mkdir(parents=True, exist_ok=True)

    for file_name in os.listdir(folder_path):
        succeed_image_urls.append(file_name)
    return succeed_image_urls


# update image task status
def update_image_task_status():
    # get all media tasks
    succeed_media_urls = load_success_image_urls()
    logger.info(f"Load {len(succeed_media_urls)} success image urls.")

    # get all video files
    folder_path = settings.VIDEO_PATH.format(pathlib.Path(__file__).parent)
    pathlib.Path(folder_path).mkdir(parents=True, exist_ok=True)

    for file_name in os.listdir(folder_path):
        succeed_media_urls.append(file_name)

    for media_url in succeed_media_urls:
        sql = f"UPDATE images SET status = {settings.STATUS_SUCCESS} WHERE file_name = '{media_url}';"
        update_ret = db_sqlite.execute_sql(sql)
        logger.info(f"Update image {media_url} status to success with ret {update_ret}")


# fix all image url
def fix_all_image_urls():
    succeed_image_urls = load_success_image_urls()
    logger.info(f"Load {len(succeed_image_urls)} success image urls.")

    # get image urls from proudct table
    sql = f"SELECT images, url FROM products where images != '';"
    results = db_sqlite.query_by_sql(sql)

    for result in results:
        images, url = result
        if not images:
            continue

        # check if image url is valid
        image_urls = images.split(",")
        new_image_urls = list()
        for image_url in image_urls:
            image_file_name = image_url.split("/")[-1]
            if image_file_name in succeed_image_urls:
                new_image_urls.append(image_url)
        new_image_url = ",".join(new_image_urls)
        sql = f"UPDATE products SET images = '{new_image_url}' WHERE url = '{url}';"
        ret = db_sqlite.execute_sql(sql)
        logger.info(f"Update product {url} images to {new_image_url} with ret {ret}")

    # fix review image url
    sql = f"SELECT review_id, picture_urls FROM reviews where picture_urls != '';"
    results = db_sqlite.query_by_sql(sql)

    for result in results:
        review_id, picture_urls = result
        if not picture_urls:
            continue

        # check if image url is valid
        image_urls = picture_urls.split(",")
        new_image_urls = list()
        for image_url in image_urls:
            image_file_name = image_url.split("/")[-1]
            if image_file_name in succeed_image_urls:
                new_image_urls.append(image_url)
        new_image_url = ",".join(new_image_urls)
        sql = f"UPDATE reviews SET picture_urls = '{new_image_url}' WHERE review_id = '{review_id}';"
        ret = db_sqlite.execute_sql(sql)
        logger.info(
            f"Update review {review_id} images to {new_image_url} with ret {ret}"
        )

    # fix_description_image_urls()


# fix description image url
def fix_description_image_urls():
    # get all failed images
    sql = f"select * from images where status != {settings.STATUS_SUCCESS};"
    results = db_sqlite.query_by_sql(sql)
    logger.info(f"Load {len(results)} failed images.")

    current_year = datetime.datetime.now().year
    # get current month, need 05 instead of 5
    current_month = datetime.datetime.now().strftime("%m")

    failed_list = list()
    for each in results:
        _, image_url, file_name, _, _ = each
        if "goods_desc" in image_url:
            real_image_url = f"https://smanny.com/wp-content/uploads/{current_year}/{current_month}/{file_name}"  # type: ignore
            failed_list.append(real_image_url)

    logger.info(f"Load {len(failed_list)} failed images.")

    # get sku and description from product table
    sql = f"select sku, description, url from products;"
    results = db_sqlite.query_by_sql(sql)

    for result in results:
        sku, description, url = result
        if not description:
            continue

        # check whether description contains failed image url
        for failed_image_url in failed_list:
            if failed_image_url in description:
                logger.info(
                    f"Found failed image url {failed_image_url} in product {url} description."
                )
                # update image url
                # repalce failed image url with "https://img.bestvibe.com/cdn-cgi/image/format=auto//mobile/asset/css/f/blank.png"
                description = description.replace(
                    failed_image_url,
                    "https://img.bestvibe.com/cdn-cgi/image/format=auto//mobile/asset/css/f/blank.png",
                )
                sql = f"UPDATE products SET description = ? WHERE sku = ? and url = ?;"
                ret = db_sqlite.execute_sql(sql, (description, sku, url))
                logger.info(
                    f"Update product {url} description to {description} with ret {ret}"
                )


# test one single task
def test_one_task():
    tasks = get_all_media_tasks()
    if tasks:
        scrape_media_task(tasks[0])


if __name__ == "__main__":
    # test_one_task()
    # fix_all_image_urls()
    # print(load_success_image_urls())
    # update_image_task_status()

    fix_description_image_urls()
    pass
