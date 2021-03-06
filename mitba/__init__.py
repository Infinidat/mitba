# Adapted from
# http://wiki.python.org/moin/PythonDecoratorLibrary#Cached_Properties
import threading
import itertools
import flux
from functools import wraps
from types import MethodType, FunctionType
from contextlib import contextmanager
from inspect import getmembers
import logbook

_logger = logbook.Logger(__name__)


class _Local(threading.local):
    enabled = True

_local_caching = _Local()


@contextmanager
def ignoring_cache():
    prev_enabled = _local_caching.enabled
    _local_caching.enabled = False
    try:
        yield
    finally:
        _local_caching.enabled = prev_enabled


class cached_property(object):
    """Decorator for read-only properties evaluated only once.

    It can be used to created a cached property like this::

        import random

        # the class containing the property must be a new-style class
        class MyClass(object):
            # create property whose value is cached for ten minutes
            @cached_method
            def randint(self):
                # will only be evaluated every 10 min. at maximum.
                return random.randint(0, 100)

    The value is cached  in the '__mitba_cache__' attribute of the object inst that
    has the property getter method wrapped by this decorator. The '__mitba_cache__'
    attribute value is a dictionary which has a key for every property of the
    object which is wrapped by this decorator. Each entry in the cache is
    created only when the property is accessed for the first time and is a
    two-element tuple with the last computed property value and the last time
    it was updated in seconds since the epoch.

    To expire a cached property value manually just do::

        del inst.__mitba_cache__[<property name>]
    """

    def __init__(self, fget, doc=None):
        super(cached_property, self).__init__()
        self.fget = fget
        self.__doc__ = doc or fget.__doc__
        self.__name__ = fget.__name__
        self.__module__ = fget.__module__

    def __get__(self, inst, owner):
        try:
            if not _local_caching.enabled:
                raise KeyError()
            value = inst.__mitba_cache__[self.__name__]
        except (KeyError, AttributeError):
            value = self.fget(inst)
            try:
                cache = inst.__mitba_cache__
            except AttributeError:
                cache = inst.__mitba_cache__ = {}
            cache[self.__name__] = value
        return value

_cached_method_id_allocator = itertools.count()


def _get_instancemethod_cache_entry(method_id, *args, **kwargs):
    if len(args) + len(kwargs) == 0:
        return method_id
    try:
        kwargs_keys = list(kwargs.keys())
        kwargs_keys.sort()
        key = (method_id,) + args + tuple([kwargs[key] for key in kwargs_keys])
        _ = {key: None}
        return key
    except TypeError:
        return None


def cached_method(func):
    """Decorator that caches a method's return value each time it is called.
    If called later with the same arguments, the cached value is returned, and
    not re-evaluated.
    """
    method_id = next(_cached_method_id_allocator)

    @wraps(func)
    def callee(inst, *args, **kwargs):
        key = _get_instancemethod_cache_entry(method_id, *args, **kwargs)
        if key is None:
            _logger.debug(
                "Passed arguments to {.__name__} are mutable, so the returned value will not be cached", func.__name__)
            return func(inst, *args, **kwargs)
        try:
            if not _local_caching.enabled:
                raise KeyError()
            value = inst.__mitba_cache__[key]
        except (KeyError, AttributeError):
            value = func(inst, *args, **kwargs)
            try:
                inst.__mitba_cache__[key] = value
            except AttributeError:
                inst.__mitba_cache__ = {}
                inst.__mitba_cache__[key] = value
        return value

    callee.__cached_method__ = True
    callee.__method_id__ = method_id
    return callee


class cached_method_with_custom_cache(object):

    def __init__(self, cache_class=None):
        if cache_class is None:
            cache_class = dict
        self.cache_class = cache_class

    def __call__(self, func):
        """Decorator that caches a method's return value each time it is called.
        If called later with the same arguments, the cached value is returned, and
        not re-evaluated.
        decorated class must implement inst.init_cache() which creates inst.__mitba_cache__ dictionary.
        """
        method_id = next(_cached_method_id_allocator)

        @wraps(func)
        def callee(inst, *args, **kwargs):
            key = _get_instancemethod_cache_entry(method_id, *args, **kwargs)
            func_name = func.__name__
            if key is None:
                _logger.debug(
                    "Passed arguments to {} are mutable, so the returned value will not be cached", func_name)
                return func(inst, *args, **kwargs)
            try:
                if not _local_caching.enabled:
                    raise KeyError()
                return inst.__mitba_cache__[func_name][key]
            except (KeyError, AttributeError):
                value = func(inst, *args, **kwargs)
                if not hasattr(inst, "__mitba_cache__"):
                    inst.__mitba_cache__ = CacheData()
                if inst.__mitba_cache__.get(func_name, None) is None:
                    # cache class creator returns a dict
                    inst.__mitba_cache__[func_name] = self.cache_class()
                inst.__mitba_cache__[func_name][key] = value
            return value

        callee.__cached_method__ = True
        callee.__method_id__ = method_id
        return callee


def _get_function_cache_entry(args, kwargs):
    return (tuple(args), frozenset(kwargs.items()))


def cached_function(func):
    """Decorator that caches a function's return value each time it is called.
    If called later with the same arguments, the cached value is returned, and
    not re-evaluated.
    """
    @wraps(func)
    def callee(*args, **kwargs):
        key = _get_function_cache_entry(args, kwargs)
        try:
            if not _local_caching.enabled:
                raise KeyError()
            value = func.__mitba_cache__[key]
        except (KeyError, AttributeError):
            value = func(*args, **kwargs)
            if not hasattr(func, '__mitba_cache__'):
                setattr(func, '__mitba_cache__', {})
            func.__mitba_cache__[key] = value
        return value

    callee.__mitba_cache__ = func.__mitba_cache__ = dict()
    callee.__cached_method__ = True
    return callee


def clear_cache(self):
    if hasattr(self, '__mitba_cache__'):
        getattr(self, '__mitba_cache__').clear()


def clear_cached_entry(self, *args, **kwargs):
    if isinstance(self, MethodType) and getattr(self, '__cached_method__', False):
        method = self
        self = getattr(method, 'im_self', getattr(method, '__self__', None))
        if self is None:
            return
        key = _get_instancemethod_cache_entry(
            method.__method_id__, *args, **kwargs)
    elif isinstance(self, FunctionType) and getattr(self, '__cached_method__', False):
        key = _get_function_cache_entry(args, kwargs)
    else:
        return
    _ = getattr(self, '__mitba_cache__', {}).pop(key, None)


def populate_cache(self, attributes_to_skip=()):
    """this method attempts to get all the lazy cached properties and methods
    There are two special cases:

    - Some attributes may not be available and raises exceptions.
      If you wish to skip these, pass them in the attributes_to_skip list
    - The calling of cached methods is done without any arguments, and catches TypeError exceptions
      for the case a cached method requires arguments. The exception is logged."""
    for key, value in getmembers(self):
        if key in attributes_to_skip:
            continue
        if hasattr(value, "__cached_method__"):
            _logger.debug("getting attribute {} from {}", repr(key), repr(self))
            try:
                _ = value()
            except TypeError as e:
                _logger.exception(e)


class LazyImmutableDict(object):
    """ Use this object when you have a list of keys but fetching the values is expensive,
    and you want to do it in a lazy fasion"""

    def __init__(self, dict):  # pylint: disable=redefined-builtin
        self._dict = dict  # pylint: disable=redefined-builtin

    def __getitem__(self, key):
        value = self._dict[key]
        if value is None:
            value = self._dict[key] = self._create_value(key)
        return value

    def keys(self):
        return self._dict.keys()

    def __contains__(self, key):
        return self._dict.__contains__(key)

    def has_key(self, key):
        return self._dict.has_key(key)

    def __len__(self):
        return len(self._dict)

    def _create_value(self, key):
        raise NotImplementedError()


class CacheData(dict):

    def __init__(self):
        super(CacheData, self).__init__()
        self._is_valid = set()

    def __getitem__(self, key):
        if key not in self._is_valid:
            _logger.debug(
                "cache found invalidate., updating cache for {}", key)
            raise KeyError(key)
        return dict.__getitem__(self, key)

    def __setitem__(self, key, value):
        ret_val = dict.__setitem__(self, key, value)
        self._is_valid.add(key)
        return ret_val

    def invalidate(self):
        _logger.debug("Invalidate cache")
        self._is_valid = set()


class TimerCacheData(CacheData):

    def __init__(self, poll_time):
        super(TimerCacheData, self).__init__()
        self.poll_time = poll_time

    def __getitem__(self, key):
        next_poll_time, value = CacheData.__getitem__(self, key)
        if flux.current_timeline.time() > next_poll_time:
            raise KeyError(key)
        return value

    def __setitem__(self, key, value):
        next_poll_time = flux.current_timeline.time() + self.poll_time
        ret_val = CacheData.__setitem__(self, key, (next_poll_time, value))
        return ret_val
