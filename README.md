
![Build Status] (https://secure.travis-ci.org/Infinidat/mitba.png )


![Downloads] (https://pypip.in/d/mitba/badge.png )

![Version] (https://pypip.in/v/mitba/badge.png )

# Overview

`mitba` is a small library for implementing method or function-level caching for results.


## cached_property and cached_method

```python
 >>> from mitba import cached_property
 >>> class MyClass(object):
 ...     called = False
 ...     @cached_property
 ...     def value(self):
 ...         assert not self.called
 ...         self.called = True
 ...         return 1
 >>> m = MyClass()
 >>> m.value
 1
 >>> m.value
 1

```

```python
 >>> from mitba import cached_method
 >>> class MyClass(object):
 ...     called = False
 ...     @cached_method
 ...     def get_value(self):
 ...         assert not self.called
 ...         self.called = True
 ...         return 1
 >>> m = MyClass()
 >>> m.get_value()
 1
 >>> m.get_value()
 1

```

Licence
=======

BSD3

