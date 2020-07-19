# !/usr/bin/python
# -*- coding: utf-8 -*-

import argparse


class RequestParser:
    def __init__(self):
        pass

    def get_args(self):
        args = argparse.ArgumentParser(description="Parsing argument.")
        args.add_argument("-M", "--cat_main", type=int, default=None, required=False)
        args.add_argument("-T", "--cat_type", type=int, default=None, required=False)
        args.add_argument("-L", "--loc_id", type=int, default=None, required=False)
        args.add_argument("-R", "--loc_region", type=int, default=None, required=False)
        args.add_argument("-S", "--cat_sub", type=int, default=None, required=False)
        args.add_argument("-D", "--debug", action="store_true", required=False)
        args.add_argument("-W", "--workers", type=int, default=5, required=False)
        args.add_argument("-F", "--filters", action="store_true", required=False)
        print(args.parse_args())
        return args.parse_args()
