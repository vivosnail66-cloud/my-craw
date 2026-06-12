#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Author :  @fangwangme
Time   :  2023-05-13
Desc   :  
"""

import pandas as pd


def check_fields():
    file_name = "./../data/fields.csv"
    df = pd.read_csv(file_name)

    # print columns name as list
    print(df.columns.tolist())


if __name__ == "__main__":
    check_fields()
