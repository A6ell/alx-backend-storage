#!/usr/bin/env python3
"""
Redis module
"""
import sys
from functools import wraps
from typing import Union, Optional, Callable
from uuid import uuid4

import redis

UnionOfTypes = Union[str, bytes, int, float]


def count_calls(method: Callable) -> Callable:
    """
    a system to count how many
    times methods of the Cache class are called.
    :param method:
    :return:
    """
    key = method.__qualname__

    @wraps(method)
    def wrapper(self, *args, **kwargs):
        """
        Wrap
        :param self:
        :param args:
        :param kwargs:
        :return:
        """
        self._redis.incr(key)
        return method(self, *args, **kwargs)

    return wrapper


def call_history(method: Callable) -> Callable:
    """
    add its input parameters to one list
    in redis, and store its output into another list.
    :param method:
    :return:
    """
    key = method.__qualname__
    i = "".join([key, ":inputs"])
    o = "".join([key, ":outputs"])

    @wraps(method)
    def wrapper(self, *args, **kwargs):
        """ Wrapp """
        self._redis.rpush(i, str(args))
        res = method(self, *args, **kwargs)
        self._redis.rpush(o, str(res))
        return res

    return wrapper


class Cache:
    """
    Cache redis class
    """

    def __init__(self):
        """
        constructor of the redis model
        """
        self._redis = redis.Redis()
        self._redis.flushdb()

    @count_calls
    @call_history
    def replay(self, method: Callable) -> None:
        """
        Display the history of calls for a particular function.
        :param method: The method to replay.
        """
        key = method.__qualname__
        i = "".join([key, ":inputs"])
        o = "".join([key, ":outputs"])

        inputs = self._redis.lrange(i, 0, -1)
        outputs = self._redis.lrange(o, 0, -1)

        print(f"{key} was called {len(inputs)} times:")

        for input_params, output_key in zip(inputs, outputs):
            output_data = self._redis.get(output_key.decode("utf-8"))
            print(f"{key}(*{eval(input_params)}) -> "
                  f"{output_key.decode('utf-8')}")

    def store(self, data: UnionOfTypes) -> str:
        """
        generate a random key (e.g. using uuid),
         store the input data in Redis using the
          random key and return the key.
        :param data:
        :return:
        """
        key = str(uuid4())
        self._redis.mset({key: data})
        return key

    def get(self, key: str, fn: Optional[Callable] = None) \
            -> UnionOfTypes:
        """
        convert the data back
        to the desired format
        :param key:
        :param fn:
        :return:
        """
        if fn:
            return fn(self._redis.get(key))
        data = self._redis.get(key)
        return data

    def get_int(self: bytes) -> int:
        """get a number"""
        return int.from_bytes(self, sys.byteorder)

    def get_str(self: bytes) -> str:
        """get a string"""
        return self.decode("utf-8")
