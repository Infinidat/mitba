Welcome to mitba's documentation!
=================================

Mitba is a small library for implementing method or function-level caching for results.

Basic usage
-----------

cached_property:

.. code-block:: python

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

cached_method:

.. code-block:: python

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


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   changelog
   api


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
