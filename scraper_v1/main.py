#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Author :  @fangwangme
Time   :  2023-05-04
Desc   :  
"""

import argparse

# sys path append parent folder
from scraper import listing_scraper, detail_scraper, image_scraper, review_scraper
from utils import export_data
from common.logger import logger


# set argument
def get_args():
    parser = argparse.ArgumentParser(description="the options of executing the scraper")

    parser.add_argument(
        "--mode",
        type=str,
        default="auto",
        required=True,
        help="The mode of the scraper, task/listing/detail/image/review/export/auto",
    )

    # add page limit
    parser.add_argument(
        "--limit",
        type=int,
        default=10000,
        required=False,
        help="The page limit of the search result",
    )

    return parser.parse_args()


def main():
    args = get_args()
    mode = args.mode

    if mode == "task":
        listing_scraper.scrape_all_category()
    elif mode == "listing":
        listing_scraper.scrape_all_listing_tasks()
    elif mode == "detail":
        detail_scraper.scrape_all_detail_tasks()
    elif mode == "review":
        review_scraper.scrape_all_review_tasks()
    elif mode == "image":
        image_scraper.scrape_all_media_tasks()
    elif mode == "export":
        export_data.export_all_data()
    elif mode == "auto":
        listing_scraper.scrape_all_category()
        listing_scraper.scrape_all_listing_tasks()
        detail_scraper.scrape_all_detail_tasks()
        review_scraper.scrape_all_review_tasks()
        image_scraper.scrape_all_media_tasks()
        export_data.export_all_data()
    else:
        logger.error("The mode is not supported, please check again.")


if __name__ == "__main__":
    main()
