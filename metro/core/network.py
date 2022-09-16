"""
Map Machine.

Utility for network connections.

Author: Sergey Vartanov (me@enzet.ru)
"""

import json
import logging
import os
import urllib
from pathlib import Path
from typing import Optional

import urllib3
import time

from datetime import datetime, timedelta


def get(address: str, parameters: dict[str, str], cache_file: Path) -> Optional[bytes]:

    if cache_file.exists():
        with cache_file.open("rb") as input_file:
            return input_file.read()

    pool: urllib3.PoolManager = urllib3.PoolManager()

    try:
        result = pool.request("GET", address, parameters)
    except urllib3.exceptions.MaxRetryError:
        return None

    time.sleep(1)

    pool.clear()
    if result.data:
        with cache_file.open("wb+") as output_file:
            output_file.write(result.data)
        return result.data

    return None


def get_data(address: str, parameters: dict[str, str], is_secure: bool = False, name: str = None) -> bytes:
    """
    Construct Internet page URL and get its descriptor.

    :param address: first part of URL without "http://"
    :param parameters: URL parameters
    :param is_secure: https or http
    :param name: name to display in logs
    :return: connection descriptor
    """
    url = "http" + ("s" if is_secure else "") + "://" + address
    if len(parameters) > 0:
        url += "?" + urllib.parse.urlencode(parameters)
    if not name:
        name = url
    logging.info("getting " + name)
    pool_manager = urllib3.PoolManager()
    url = url.replace(" ", "_")
    urllib3.disable_warnings()
    result = pool_manager.request("GET", url)
    pool_manager.clear()
    time.sleep(2)
    return result.data


def get_content(address, parameters, cache_file_name, kind, is_secure, name=None, exceptions=None, update_cache=False):
    """
    Read content from URL or from cached file.

    :param address: first part of URL without "http://"
    :param parameters: URL parameters
    :param cache_file_name: name of cache file
    :param kind: type of content: "html" or "json"
    :return: content if exist
    """
    if exceptions and address in exceptions:
        return None
    if (
        os.path.isfile(cache_file_name)
        and datetime(1, 1, 1).fromtimestamp(os.stat(cache_file_name).st_mtime) > datetime.now() - timedelta(days=90)
        and not update_cache
    ):
        with open(cache_file_name) as cache_file:
            if kind == "json":
                try:
                    return json.load(cache_file)
                except ValueError:
                    return None
            if kind == "html":
                return cache_file.read()
    else:
        try:
            data = get_data(address, parameters, is_secure=is_secure, name=name)
            if kind == "json":
                try:
                    obj = json.loads(data.decode("utf-8"))
                    with open(cache_file_name, "w+") as cached:
                        cached.write(json.dumps(obj, indent=4))
                    return obj
                except ValueError:
                    logging.error("cannot get " + address + " " + str(parameters))
                    return None
            if kind == "html":
                with open(cache_file_name, "w+") as cached:
                    cached.write(data)
                return data
        except Exception as e:
            logging.error("during getting JSON from " + address + " with parameters " + str(parameters))
            print(e)
            if exceptions:
                exceptions.append(address)
            return None
