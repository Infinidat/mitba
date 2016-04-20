import functools
import sys

_PY2 = sys.version_info < (3, 0)

if _PY2:

    def wraps(wrapped):
        """ a convenience function on top of functools.wraps:

        - adds the original function to the wrapped function as __wrapped__ attribute."""
        def new_decorator(f):
            returned = functools.wraps(wrapped)(f)
            returned.__wrapped__ = wrapped
            return returned
        return new_decorator

    def iteritems(d):
        return d.iteritems() # not dict.iteritems!!! we support ordered dicts as well


else:
    wraps = functools.wraps

    def iteritems(d):
        return d.items()
