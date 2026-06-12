#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Author :  @fangwangme
Time   :  2023-04-02
Desc   :  
"""

import random
import sys
import pathlib

sys.path.append(f"{pathlib.Path(__file__).parent}/../")
from common.tools import get_config_by_key


def parse_proxy_config():
    proxy_type = get_config_by_key("RUNNING", "PROXY_TYPE")

    proxy_user = get_config_by_key(proxy_type, "USER")
    proxy_password = get_config_by_key(proxy_type, "PASSWORD")

    if proxy_type == "PROXY_IP":
        proxy_list = get_config_by_key(proxy_type, "IPS").split(";")
        proxy_addr = random.choice(proxy_list)
    else:
        proxy_addr = get_config_by_key(proxy_type, "ADDRESS")

    return proxy_addr, proxy_user, proxy_password


# get one-time proxy
def get_proxy():
    proxy_str, proxy_user, proxy_password = parse_proxy_config()

    proxies = {
        "http": "http://{}:{}@{}".format(proxy_user, proxy_password, proxy_str),
        "https": "http://{}:{}@{}".format(proxy_user, proxy_password, proxy_str),
    }

    return proxies



def test_proxy():
    import requests

    proxy = get_proxy()

    url = "https://httpbin.org/ip"
    s = requests.Session()
    s.proxies = proxy
    r = s.get(url)
    print(r.status_code, r.text)


if __name__ == "__main__":
    print(get_proxy())
