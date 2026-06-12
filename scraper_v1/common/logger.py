#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Author :  @fangwangme
Time   :  2023-04-19
Desc   :  
"""

import logging.config

# set format for log
FORMAT = (
    "%(asctime)-15s %(threadName)s %(filename)s:%(lineno)d %(levelname)s %(message)s"
)
logging.basicConfig(level=logging.INFO, format=FORMAT)

selenium_logger = logging.getLogger("seleniumwire").setLevel(logging.WARNING)

logger = logging.getLogger("crawlLog")
logger.setLevel(logging.INFO)
