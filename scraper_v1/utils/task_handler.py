#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Author :  @fangwangme
Time   :  2023-05-05
Desc   :  
"""


import sys
import pathlib

sys.path.append("{}/../".format(pathlib.Path(__file__).parent))
from common import settings, db_sqlite
from common.logger import logger


def generate_tasks(keyword_str, page_limit):
    # create search tasks table if not exist
    db_sqlite.create_search_tasks_table()

    if not keyword_str:
        logger.error("Keyword is empty")
        return

    # build search tasks
    search_tasks = []
    keyword_list = keyword_str.split(";")
    for keyword in keyword_list:
        if not keyword:
            continue
        search_tasks.append((keyword, page_limit, 0, 0, settings.STATUS_INIT))

    ret = db_sqlite.insert_search_tasks(search_tasks)
    logger.info(f"Inserted {len(search_tasks)} tasks with ret {ret}")


if __name__ == "__main__":
    start_date = "20230501"
    generate_tasks(start_date)
