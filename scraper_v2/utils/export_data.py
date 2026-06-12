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
    # Connect to your database

    conn = db_sqlite.get_db()

    # Query to fetch data from products table
    query = "SELECT * FROM products;"

    # Use pandas to run the query and store the result in a DataFrame
    df = pd.read_sql_query(query, conn)

    # Define the column names
    column_names = [
        "ID",
        "Type",
        "SKU",
        "Name",
        "Published",
        "Is featured?",
        "Visibility in catalog",
        "Short description",
        "Description",
        "Date sale price starts",
        "Date sale price ends",
        "Tax status",
        "Tax class",
        "In stock?",
        "Stock",
        "Low stock amount",
        "Backorders allowed?",
        "Sold individually?",
        "Weight (kg)",
        "Length (cm)",
        "Width (cm)",
        "Height (cm)",
        "Allow customer reviews?",
        "Purchase note",
        "Sale price",
        "Regular price",
        "Categories",
        "Tags",
        "Shipping class",
        "Images",
        "Download limit",
        "Download expiry days",
        "Parent",
        "Grouped products",
        "Upsells",
        "Cross-sells",
        "External URL",
        "Button text",
        "Position",
        "Attribute 1 name",
        "Attribute 1 value(s)",
        "Attribute 1 visible",
        "Attribute 1 global",
        "Attribute 1 default",
        "Attribute 2 name",
        "Attribute 2 value(s)",
        "Attribute 2 visible",
        "Attribute 2 global",
        "Attribute 2 default",
        "Scraped Category",
        "Url",
        "Status",
    ]

    # Rename the columns
    df.columns = column_names

    # Create a folder if it does not exist
    folder_path = settings.PRODUCT_PATH.format(pathlib.Path(__file__).parent)
    pathlib.Path(folder_path).mkdir(parents=True, exist_ok=True)

    # Group the data by the "Scraped Category" column
    grouped_data = df.groupby("Scraped Category")

    # Export the data to separate CSV files based on the "Scraped Category"
    for category, group in grouped_data:
        # Sort the data by "Url" column
        group = group.sort_values(by="Url")

        # Remove unnecessary columns
        group.drop(columns=["Status", "Url"], inplace=True)

        # Create a filename based on the scraping category
        filename = f"{category.replace(' ', '')}.csv"
        file_path = os.path.join(folder_path, filename)

        # Export the group data to the CSV file without the "Scraped Category" column
        group.drop(columns=["Scraped Category"], inplace=True)
        group.to_csv(file_path, index=False)
        logger.info(f"Exported {group.shape[0]} products to {file_path}.")

    # Close the connection to the database
    conn.close()


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
    df["product_SKU"] = df["sku"]
    # set rating to rating
    df["rating"] = df["rating"]

    # only keep "comment_ID","comment_post_ID","product_SKU","comment_author","comment_author_url","comment_author_email","comment_date","comment_date_gmt","comment_content","comment_approved","comment_parent","user_id","comment_alter_id","rating"
    df = df[
        [
            "comment_ID",
            "comment_post_ID",
            "product_SKU",
            "comment_author",
            "comment_author_url",
            "comment_author_email",
            "comment_date",
            "comment_date_gmt",
            "comment_content",
            "comment_approved",
            "comment_parent",
            "user_id",
            "comment_alter_id",
            "rating",
        ]
    ]
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
