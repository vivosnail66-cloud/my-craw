#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Author :  @fangwangme
Time   :  2023-04-19
Desc   :  
"""

import pathlib
import configparser


# read config
def get_config_by_key(section_name, key_name):
    config = configparser.RawConfigParser()
    config_path = "{}/../config.ini".format(pathlib.Path(__file__).parent)
    config.read(config_path)
    return config.get(section_name, key_name)


# get page wait time
def get_page_waiting_time():
    return int(get_config_by_key("RUNNING", "PAGE_WAITING_TIME"))


# get search waiting time
def get_search_waiting_time():
    return int(get_config_by_key("RUNNING", "SEARCH_WAITING_TIME"))


# get host name
def get_host_name():
    return get_config_by_key("RUNNING", "HOST")


# get retry times
def get_retry_times():
    return int(get_config_by_key("RUNNING", "RETRY_TIMES"))


# get workers
def get_workers():
    return int(get_config_by_key("RUNNING", "THREADS"))

# get use proxy
def get_use_proxy():
    use_proxy = None

    use_proxy_flag = get_config_by_key("RUNNING", "USE_PROXY")
    if use_proxy_flag == "True":
        use_proxy = True
    elif use_proxy_flag == "False":
        use_proxy = False
    else:
        use_proxy = None

    return use_proxy
