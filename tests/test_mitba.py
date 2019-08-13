import flux
import functools
from mitba import (CacheData, TimerCacheData, cached_function,
                   cached_method_with_custom_cache, clear_cache,
                   clear_cached_entry, ignoring_cache, populate_cache)

POLL_TIME = 0.05


def test_subject_cached_property(subject):
    assert subject.prop == 1

def test_subject_clear_cache(subject):
    assert subject.prop == 1
    clear_cache(subject)
    assert subject.prop == 2

def test_subject_populate_cache(subject):
    # pylint: disable=protected-access
    assert subject._counter == 0
    populate_cache(subject)
    assert subject._counter == 1


def test_subject_populate_cache_with_ignored_keys(subject):
    # pylint: disable=protected-access
    assert subject._counter == 0
    populate_cache(subject, ['cached_method_4'])
    assert subject._counter == 1


def test_cached_method_doc(subject):
    assert subject.cached_method_1.__doc__ == subject.cached_method_2.__doc__ == subject.orig_method.__doc__

def test_cached_method_name(subject):
    assert subject.cached_method_2.__name__ == subject.cached_method_2.__name__ == subject.orig_method.__name__

def test_cached_method_cached_method(subject):
    assert subject.cached_method_1(1) == 1
    assert subject.cached_method_1(1) == 1
    assert subject.cached_method_2(1) == 2

def test_cached_method_clear_cache(subject):
    assert subject.cached_method_1(1) == 1
    assert subject.cached_method_1(1) == 1
    clear_cache(subject)
    assert subject.cached_method_1(1) == 2

def test_cached_method_args(subject):
    clear_cache(subject)
    assert subject.cached_method_3(1) == 1
    assert subject.cached_method_3(1) == 1
    assert subject.cached_method_3(2) == 2
    assert subject.cached_method_3(2) == 2
    with ignoring_cache():
        assert subject.cached_method_3(1) == 3
        assert subject.cached_method_3(2) == 4
    assert subject.cached_method_3(1) == 3
    assert subject.cached_method_3(2) == 4

def test_cached_method_mutable_args(subject):
    clear_cache(subject)
    assert subject.cached_method_3([1]) == 1
    assert subject.cached_method_3([1]) == 2

def test_cached_method_kwargs(subject):
    clear_cache(subject)
    assert subject.cached_method_3(value=1) == 1
    assert subject.cached_method_3(value=1) == 1
    assert subject.cached_method_3(value=2) == 2
    assert subject.cached_method_3(value=2) == 2
    with ignoring_cache():
        assert subject.cached_method_3(value=1) == 3
        assert subject.cached_method_3(value=2) == 4
    assert subject.cached_method_3(value=1) == 3
    assert subject.cached_method_3(value=2) == 4

def test_cached_method_mutable_kwargs(subject):
    clear_cache(subject)
    assert subject.cached_method_3(value=[1]) == 1
    assert subject.cached_method_3(value=[1]) == 2

def test_cached_method_no_args_and_kwargs(subject):
    clear_cache(subject)
    assert subject.cached_method_4() == 1
    assert subject.prop == 2
    assert subject.cached_method_4() == 1
    clear_cache(subject)


def test_cached_method_caching_method_on_class_instance():
    class Foo(object):

        def __init__(self):
            self.counter = 0

        def __inicached_methodt__(self):
            self.counter = 0

        def invalidate_cache(self):
            self.__mitba_cache__["tested_method"].invalidate()  # pylint: disable=no-member

        @cached_method_with_custom_cache(CacheData)
        def tested_method(self):
            self.counter += 1
            return self.counter

    foo = Foo()  # pylint: disable=blacklisted-name
    for i in range(1, 5):
        for _ in range(5):
            assert foo.tested_method() == i
        foo.invalidate_cache()


def test_caching_method_on_external_call():
    class Bar(object):

        def __init__(self):
            self.counter = 0

        @cached_method_with_custom_cache(functools.partial(TimerCacheData, POLL_TIME))
        def tested_method(self):
            self.counter += 1
            return self.counter

    bar = Bar()  # pylint: disable=blacklisted-name
    for _ in range(3):
        assert bar.tested_method() == 1

    flux.current_timeline.sleep(POLL_TIME + 0.01)
    for _ in range(3):
        assert bar.tested_method() == 2


def test_cached_method_single_class_with_two_caches():
    class FooBar(object):

        def __init__(self):
            self.timer = 0
            self.data_counter = 0

        @cached_method_with_custom_cache(functools.partial(TimerCacheData, POLL_TIME))
        def timer_cache(self):
            self.timer += 1
            return self.timer

        @cached_method_with_custom_cache(CacheData)
        def data_cache(self):
            self.data_counter += 1
            return self.data_counter

        def invalidate_cache(self):
            self.__mitba_cache__["data_cache"].invalidate()  # pylint: disable=no-member

    foobar = FooBar()
    for i in range(1, 10):
        for _ in range(10):
            assert foobar.data_cache() == i
            flux.current_timeline.sleep(0.01)
        foobar.invalidate_cache()

    for _ in range(3):
        assert foobar.timer_cache() == 1
        foobar.invalidate_cache()

    flux.current_timeline.sleep(POLL_TIME + 0.1)
    for _ in range(3):
        assert foobar.timer_cache() == 2
        foobar.invalidate_cache()


@cached_function
def func():
    return flux.current_timeline.time()


def test_cache_function_works():
    before = func()
    after = func()
    assert before == after
    with ignoring_cache():
        value = func()
    assert func() == value
    assert value != before
    assert value != after

def test_cache_function_clear_cache_works():
    before = func()
    clear_cache(func)
    after = func()
    assert before != after

def test_cache_function_works_after_cleanup():
    first = func()
    clear_cache(func)
    second = func()
    third = func()
    assert first != second
    assert second == third

def test_clear_cached_entry_on_instance_method__no_args(counter):
    method = counter.count
    assert method() == 1
    assert method() == 1
    clear_cached_entry(method)
    assert method() == 2

def test_clear_cached_entry_on_instance_method__with_args(counter):
    method = counter.sum
    assert method(1) == 1
    counter.count()
    assert method(1) == 1
    clear_cached_entry(method, 1)
    assert method(1) == 2

def test_clear_cached_entry_on_function__with_args():
    count = 0

    @cached_function
    def sum(num):  # pylint: disable=redefined-builtin
        return num + count
    assert sum(1) == 1
    assert sum(1) == 1
    count = 2
    assert sum(1) == 1
    clear_cached_entry(sum, 1)
    assert sum(1) == 3

def test_clear_cached_entry_with_mismatching_args_does_nothing(counter):
    method = counter.sum
    assert method(1) == 1
    counter.count()
    assert method(1) == 1
    clear_cached_entry(method, 3)
    assert method(1) == 1
