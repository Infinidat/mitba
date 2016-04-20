# put py.test fixtures here
from collections import defaultdict
import pytest

from mitba import cached_property, cached_method


class Subject(object):

    def __init__(self):
        super(Subject, self).__init__()
        self._counter = 0
        self._counters = defaultdict(lambda: defaultdict(int))

    @cached_property
    def prop(self):
        self._counter += 1
        return self._counter

    def orig_method(self, value):
        """some docstring"""
        self._counters['orig_method'][value] += 1
        return self._counters['orig_method'][value]

    @cached_method
    def cached_method_3(self, value):  # pylint: disable=unused-argument
        self._counter += 1
        return self._counter

    @cached_method
    def cached_method_4(self):
        self._counter = 1
        return self._counter

    cached_method_1 = cached_method(orig_method)
    cached_method_2 = cached_method(orig_method)


class Counter(object):

    def __init__(self):
        super(Counter, self).__init__()
        self._count = 0

    @cached_method
    def count(self):
        self._count += 1
        return self._count

    @cached_method
    def sum(self, num):
        return num + self._count


@pytest.fixture
def subject():
    return Subject()


@pytest.fixture
def counter():
    return Counter()
