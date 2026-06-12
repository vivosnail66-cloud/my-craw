#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Author :  @fangwangme
Time   :  2023-05-04
Desc   :  
"""

import os
import sys
import pathlib
import pandas as pd
from datetime import datetime

sys.path.append("{}/../".format(pathlib.Path(__file__).parent))
from common import db_sqlite, settings
from common.logger import logger

import pandas as pd


def export_products_to_csv():
    # connect to your database
    conn = db_sqlite.get_db()

    # query to fetch data from products table
    query = "SELECT * FROM products;"

    # use pandas to run the query and store the result in a DataFrame
    df = pd.read_sql_query(query, conn)

    df.columns = ['ID', 'Type', 'SKU', 'Name', 'Published', 'Is featured?', 'Visibility in catalog', 'Short description', 'Description', 'Date sale price starts', 'Date sale price ends', 'Tax status', 'Tax class', 'In stock?', 'Stock', 'Low stock amount', 'Backorders allowed?', 'Sold individually?', 'Weight (kg)', 'Length (cm)', 'Width (cm)', 'Height (cm)', 'Allow customer reviews?', 'Purchase note', 'Sale price', 'Regular price', 'Categories', 'Tags', 'Shipping class', 'Images', 'Download limit', 'Download expiry days', 'Parent', 'Grouped products', 'Upsells', 'Cross-sells', 'External URL', 'Button text', 'Position', 'Attribute 1 name', 'Attribute 1 value(s)', 'Attribute 1 visible', 'Attribute 1 global', 'Attribute 1 default', 'Attribute 2 name', 'Attribute 2 value(s)', 'Attribute 2 visible', 'Attribute 2 global', 'Attribute 2 default', "Video Url", "Scraped Cateogry", "Url", "status"]
    # drop the 'status' and 'keyword' columns
    df = df.drop(columns=["status"])

    # add a new column 'product_handler' to store the product handler
    df["Product Handler"] = df["Url"].apply(lambda x: x.split("/")[-1].replace(".html", ""))

    # create folder if not exists
    folder_path = settings.OUTPUT_PATH.format(pathlib.Path(__file__).parent)
    pathlib.Path(folder_path).mkdir(parents=True, exist_ok=True)

    # create a filename by replacing spaces with nothing
    filename = "bestvibe.csv"
    real_file_name = os.path.join(folder_path, filename)

    # export the filtered DataFrame to an Excel file
    df.to_csv(real_file_name, index=False)
    logger.info(f"Exported {df.shape[0]} products to {real_file_name}.")

    # drop Video Url column and URL column and Scraped Cateogry column
    df = df.drop(columns=["Video Url", "Scraped Cateogry", "Url", "Product Handler"])
    clean_file_name = os.path.join(folder_path, "cleaned_" + filename)
    df.to_csv(clean_file_name, index=False)
    logger.info(f"Exported {df.shape[0]} products to {clean_file_name}.")
    
    # close the connection to the database
    conn.close()


# build review_mapping with url and sku
def build_review_mapping():
    sql = "select sku, url from products where `type` in ('simple', 'variable')"
    results = db_sqlite.query_by_sql(sql)
    logger.info(f"Got {len(results)} products")

    mapping = {}
    for result in results:
        sku = result[0]
        url = result[1]
        mapping[url] = sku
    
    return mapping


# export reviews
def export_reviews_to_csv():
    # connect to your database
    conn = db_sqlite.get_db()

    # query to fetch data from products table
    query = "SELECT * FROM reviews;"

    # use pandas to run the query and store the result in a DataFrame
    df = pd.read_sql_query(query, conn)

    # # sort the columns with title,body,rating,review_date,reviewer_name,reviewer_email,product_id,product_handle,reply,picture_urls
    # df = df[["title", "body", "rating", "review_date", "reviewer_name", "reviewer_email", "product_id", "product_handle", "reply", "picture_urls"]]

    # add a new column proudct_sku with mapping
    mapping = build_review_mapping()
    df["product_sku"] = df["product_url"].apply(lambda x: mapping[x])

    # drop all rows with product_sku is null
    print(f"Before dropna, df.shape: {df.shape}")
    df = df.dropna(subset=["product_sku"])
    print(f"After dropna, df.shape: {df.shape}")

    # handle review_date, make sure it great than 2022-01-01, if not, set it to the date (current_date - original_date) / 
    # handle review_date, make sure it's greater than 2022-01-01 and not greater than today's date
    min_date = datetime.strptime("2022-01-01", "%Y-%m-%d")
    today = datetime.now()

    def adjust_date(date_str):
        if not date_str:
            return today.strftime("%Y-%m-%d %H:%M:%S")
        
        date_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S UTC")
        if date_obj < min_date:
            # calculate the difference between the minimum date and the original date
            diff = (today - min_date) -  (min_date - date_obj)
            # add the difference to the current date to get the adjusted date
            adjusted_date = min_date + diff
            # check if the adjusted date is greater than today's date
            if adjusted_date > today:
                return today.strftime("%Y-%m-%d 00:00:00")
            elif adjusted_date < min_date:
                return min_date.strftime("%Y-%m-%d 00:00:00")
            else:
                return adjusted_date.strftime("%Y-%m-%d %H:%M:%S")
        else:
            return date_obj.strftime("%Y-%m-%d %H:%M:%S")

    df["review_date"] = df["review_date"].apply(adjust_date)

    # print max and min review_date
    print(f"max review_date: {df['review_date'].max()}")
    print(f"min review_date: {df['review_date'].min()}")

    # final columns "comment_ID","comment_post_ID","product_SKU","comment_author","comment_author_url","comment_author_email","comment_date","comment_date_gmt","comment_content","comment_approved","comment_parent","user_id","comment_alter_id","rating"
    # set "comment_ID","comment_post_ID" to ""
    # set "comment_approved" to 1
    # set "comment_parent" to 0
    # set "user_id" and "comment_alter_id" to ""
    # set "comment_author_url","comment_author_email" to ""
    # set "comment_date_gmt" and "comment_date" to "review_date"
    df["comment_ID"] = ""
    df["comment_post_ID"] = ""
    df["comment_approved"] = 1
    df["comment_parent"] = 0
    df["user_id"] = ""
    df["comment_alter_id"] = ""
    df["comment_author_url"] = ""
    df["comment_author_email"] = ""
    df["comment_date_gmt"] = df["review_date"]
    df["comment_date"] = df["review_date"]

    # set comment_author to reviewer_name
    df["comment_author"] = df["reviewer_name"]

    # set comment_content to body
    df["comment_content"] = df["body"]
    # set product_sku to product_SKU
    df["product_SKU"] = df["product_sku"]
    # set rating to rating
    df["rating"] = df["rating"]

    # only keep "comment_ID","comment_post_ID","product_SKU","comment_author","comment_author_url","comment_author_email","comment_date","comment_date_gmt","comment_content","comment_approved","comment_parent","user_id","comment_alter_id","rating"
    df = df[["comment_ID","comment_post_ID","product_SKU","comment_author","comment_author_url","comment_author_email","comment_date","comment_date_gmt","comment_content","comment_approved","comment_parent","user_id","comment_alter_id","rating"]]
    # print(df.head(5))
    
    # create folder if not exists
    folder_path = settings.OUTPUT_PATH.format(pathlib.Path(__file__).parent)
    pathlib.Path(folder_path).mkdir(parents=True, exist_ok=True)

    # create a filename by replacing spaces with nothing
    filename = "reviews.csv"
    real_file_name = os.path.join(folder_path, filename)

    # export the filtered DataFrame to an Excel file
    df.to_csv(real_file_name, index=False)
    logger.info(f"Exported {df.shape[0]} reviews to {real_file_name}.")

    # close the connection to the database
    conn.close()


def export_all_data():
    export_products_to_csv()

    export_reviews_to_csv()


if __name__ == "__main__":
    # export_products_to_csv()
    
    export_reviews_to_csv()


