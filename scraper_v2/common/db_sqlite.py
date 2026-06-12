#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Author :  @fangwangme
Time   :  2023-04-20
Desc   :  
"""


import os
import pathlib
import sqlite3
import sys

sys.path.append("{}/../".format(pathlib.Path(__file__).parent))
from common.logger import logger
from common import settings


# get the connection of database
def get_db(db_name=""):
    # create fold if not exist
    data_path = settings.DATA_FILE_PATH.format(pathlib.Path(__file__).parent)

    pathlib.Path(data_path).mkdir(parents=True, exist_ok=True)

    if not db_name:
        return sqlite3.connect(
            os.path.join(data_path, "{}.db".format(settings.DATABASE_NAME))
        )
    else:
        return sqlite3.connect(os.path.join(data_path, "{}.db".format(db_name)))


def execute_sql(sql, args=None, db_name=""):
    try:
        con = get_db(db_name)
        cur = con.cursor()
        if args:
            cur.execute(sql, args)
        else:
            cur.execute(sql)
        ret = cur.rowcount
        con.commit()
    except sqlite3.Error as e:
        logger.error("Failed to execute sql due to {}".format(str(e)), exc_info=True)
        return -1
    finally:
        cur.close()
        con.close()

    return ret


def execute_sqls(sql, args=None, db_name=""):
    try:
        con = get_db(db_name)
        cur = con.cursor()
        cur.executemany(sql, args)
        ret = cur.rowcount
        con.commit()
    except sqlite3.Error as e:
        logger.error(
            "Failed to execute sql {} due to {}".format(sql, str(e)), exc_info=True
        )
        return -1
    finally:
        cur.close()
        con.close()

    return ret


def query_by_sql(sql, db_name=""):
    result = []
    try:
        con = get_db(db_name)
        cur = con.cursor()
        rs = cur.execute(sql)
        for row in rs:
            result.append(row)
    except sqlite3.Error as e:
        logger.error("Failed to query data due to {}".format(str(e)))
        return result
    finally:
        cur.close()
        con.close()

    return result


# create search_tasks table with given format and make sure the url is unique
def create_category_tasks_table():
    sql = """
        CREATE TABLE IF NOT EXISTS category_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            url TEXT,
            total INTEGER,
            crawled INTEGER,
            status INTEGER,
            UNIQUE(url)
        )
        """
    execute_sql(sql)
    logger.info("category_tasks table created")


# insert category_tasks
def insert_category_tasks(data):
    sql = """
        INSERT INTO category_tasks (name, url, total, crawled, status)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(url) DO UPDATE SET 
            name = excluded.name,
            total = excluded.total,
            crawled = excluded.crawled,
            status = excluded.status
        """
    return execute_sqls(sql, data)


def update_category_task(category_url, total_pages, crawled_pages, status):
    sql = """
        UPDATE category_tasks SET total = ?, crawled = ?, status = ? WHERE url = ?
        """
    return execute_sql(sql, (total_pages, crawled_pages, status, category_url))


def create_products_table():
    sql = """
        CREATE TABLE IF NOT EXISTS products (
            id TEXT,
            type TEXT,
            sku TEXT,
            name TEXT,
            published TEXT,
            is_featured TEXT,
            visibility_in_catalog TEXT,
            short_description TEXT,
            description TEXT,
            date_sale_price_starts TEXT,
            date_sale_price_ends TEXT,
            tax_status TEXT,
            tax_class TEXT,
            in_stock TEXT,
            stock TEXT,
            low_stock_amount TEXT,
            backorders_allowed TEXT,
            sold_individually TEXT,
            weight TEXT,
            length TEXT,
            width TEXT,
            height TEXT,
            allow_customer_reviews TEXT,
            purchase_note TEXT,
            sale_price TEXT,
            regular_price TEXT,
            categories TEXT,
            tags TEXT,
            shipping_class TEXT,
            images TEXT,
            download_limit TEXT,
            download_expiry_days TEXT,
            parent TEXT,
            grouped_products TEXT,
            upsells TEXT,
            cross_sells TEXT,
            external_url TEXT,
            button_text TEXT,
            position TEXT,
            attribute1_name TEXT,
            attribute1_value TEXT,
            attribute1_visible TEXT,
            attribute1_global TEXT,
            attribute1_default TEXT,
            attribute2_name TEXT,
            attribute2_values TEXT,
            attribute2_visible TEXT,
            attribute2_global TEXT,
            attribute2_default TEXT,
            scraped_category TEXT,
            url TEXT,
            status TEXT,
            UNIQUE(sku, url)
        )
        """
    execute_sql(sql)
    logger.info("products table created")


def insert_products(data):
    sql = """
        INSERT INTO products (
            type,
            sku,
            name,
            published,
            is_featured,
            visibility_in_catalog,
            short_description,
            description,
            date_sale_price_starts,
            date_sale_price_ends,
            tax_status,
            tax_class,
            in_stock,
            stock,
            low_stock_amount,
            backorders_allowed,
            sold_individually,
            weight,
            length,
            width,
            height,
            allow_customer_reviews,
            purchase_note,
            sale_price,
            regular_price,
            categories,
            tags,
            shipping_class,
            images,
            download_limit,
            download_expiry_days,
            parent,
            grouped_products,
            upsells,
            cross_sells,
            external_url,
            button_text,
            position,
            attribute1_name,
            attribute1_value,
            attribute1_visible,
            attribute1_global,
            attribute1_default,
            attribute2_name,
            attribute2_values,
            attribute2_visible,
            attribute2_global,
            attribute2_default,
            scraped_category,
            url,
            status
        ) 
        VALUES 
        (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
         ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
         ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
         ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
         ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(sku, url) DO UPDATE SET
            type = excluded.type,
            name = excluded.name,
            published = excluded.published,
            is_featured = excluded.is_featured,
            visibility_in_catalog = excluded.visibility_in_catalog,
            short_description = excluded.short_description,
            description = excluded.description,
            date_sale_price_starts = excluded.date_sale_price_starts,
            date_sale_price_ends = excluded.date_sale_price_ends,
            tax_status = excluded.tax_status,
            tax_class = excluded.tax_class,
            in_stock = excluded.in_stock,
            stock = excluded.stock,
            low_stock_amount = excluded.low_stock_amount,
            backorders_allowed = excluded.backorders_allowed,
            sold_individually = excluded.sold_individually,
            weight = excluded.weight,
            length = excluded.length,
            width = excluded.width,
            height = excluded.height,
            allow_customer_reviews = excluded.allow_customer_reviews,
            purchase_note = excluded.purchase_note,
            sale_price = excluded.sale_price,
            regular_price = excluded.regular_price,
            categories = excluded.categories,
            tags = excluded.tags,
            shipping_class = excluded.shipping_class,
            images = excluded.images,
            download_limit = excluded.download_limit,
            download_expiry_days = excluded.download_expiry_days,
            parent = excluded.parent,
            grouped_products = excluded.grouped_products,
            upsells = excluded.upsells,
            cross_sells = excluded.cross_sells,
            external_url = excluded.external_url,
            button_text = excluded.button_text,
            position = excluded.position,
            attribute1_name = excluded.attribute1_name,
            attribute1_value = excluded.attribute1_value,
            attribute1_visible = excluded.attribute1_visible,
            attribute1_global = excluded.attribute1_global,
            attribute1_default = excluded.attribute1_default,
            attribute2_name = excluded.attribute2_name,
            attribute2_values = excluded.attribute2_values,
            attribute2_visible = excluded.attribute2_visible,
            attribute2_global = excluded.attribute2_global,
            attribute2_default = excluded.attribute2_default,
            scraped_category = excluded.scraped_category,
            url = excluded.url,
            status = excluded.status;
        """
    return execute_sqls(sql, data)


# create table for listing_products
def create_listing_products_table():
    sql = """
        CREATE TABLE IF NOT EXISTS listing_products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scraped_category TEXT,
            name TEXT,
            url TEXT,
            status TEXT,
            UNIQUE(url)
        )
        """
    execute_sql(sql)
    logger.info("listing_products table created")


# insert listing_products
def insert_listing_products(data):
    sql = """
        INSERT INTO listing_products (scraped_category, name, url, status)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(url) DO NOTHING;
        """
    return execute_sqls(sql, data)


# update status of listing_products
def update_listing_product_status(url, status):
    sql = """
        UPDATE listing_products SET status = ? WHERE url = ?
        """
    return execute_sql(sql, (status, url))


# create images table with given format and make sure the url is unique
def create_images_table():
    sql = """
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT,
            file_name TEXT,
            media_type TEXT,
            status INTEGER,
            UNIQUE(url)
        )
        """
    execute_sql(sql)
    logger.info("images table created")


# insert images
def insert_images(data):
    sql = """
        INSERT INTO images (url, file_name, media_type, status)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(url) DO UPDATE SET 
            file_name = excluded.file_name,
            media_type = excluded.media_type,
            status = excluded.status
        """
    return execute_sqls(sql, data)


# update image status
def update_image_status(url, status):
    sql = """
        UPDATE images SET status = ? WHERE url = ?
        """
    return execute_sql(sql, (status, url))


# create review_tasks table with given format and make sure the url is unique
def create_review_tasks_table():
    sql = """
        CREATE TABLE IF NOT EXISTS review_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT,
            good_id INTEGER,
            total INTEGER,
            crawled INTEGER,
            status INTEGER,
            UNIQUE(url)
        )
        """
    execute_sql(sql)
    logger.info("review_tasks table created")


# insert review_tasks
def insert_review_tasks(data):
    sql = """
        INSERT INTO review_tasks (url, good_id, total, crawled, status)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(url) DO UPDATE SET 
            total = excluded.total,
            crawled = excluded.crawled,
            status = excluded.status
        """
    return execute_sqls(sql, data)


# update review task
def update_review_task(url, total, crawled, status):
    sql = """
        UPDATE review_tasks SET total = ?, crawled = ?, status = ? WHERE url = ?
        """
    return execute_sql(sql, (total, crawled, status, url))


# create reviews table with given format and make sure the url is unique
def create_reviews_table():
    sql = """
        CREATE TABLE IF NOT EXISTS reviews (
            review_id TEXT,
            sku TEXT,
            product_handle TEXT,
            product_url TEXT,
            title TEXT,
            body TEXT,
            rating INTEGER,
            review_date TEXT,
            reviewer_name TEXT,
            reviewer_email TEXT,
            reply TEXT,
            picture_urls TEXT,
            ip_address TEXT,
            UNIQUE(review_id)
        )
        """
    execute_sql(sql)
    logger.info("reviews table created")


# insert reviews
def insert_reviews(data):
    sql = """
        INSERT OR IGNORE INTO reviews (
            review_id,
            sku,
            product_handle,
            product_url,
            title,
            body,
            rating,
            review_date,
            reviewer_name,
            reviewer_email,
            reply,
            picture_urls,
            ip_address
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
    return execute_sqls(sql, data)


def truncate_products_table():
    sql = "DELETE FROM products"
    execute_sql(sql)
    logger.info("products table truncated")
