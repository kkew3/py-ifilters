"""
Filter integers or integer sequences as per numpy-like advanced indexing.

``ifilters`` provides predicate class that produces predicator according to
the provided numpy-like advanced indexing pattern. For example,

    - ``1-2``: :math:`\\{1, 2\\}`
    - ``-1--2``: \\{\\}
    - ``-2--1``: \\{-2, -1\\}
    - ``1,3``: :math:`\\{1, 3\\}`
    - ``1:5``: :math:`\\{1, 2, 3, 4\\}`
    - ``1,3,7:``: :math:`\\{1, 3\\} \\cup \\{x \\mid x \\ge 7\\}`
    - ``[2],[3-5]``: :math:`\\{(2,x) \\mid 3 \\le x \\le 5\\}`

Pattern specification
---------------------

Two types of patterns are acceptable: 1) *integer pattern* and 2) *integer
sequence pattern*. Integer pattern consists of a comma-separated list of
zero or more *atomic patterns*. If it contains no atomic pattern, it's called
an *nil pattern*. Nil pattern matches nothing. An integer pattern may or may
not be enclosed in square bracket. An integer pattern expects either an integer
or a singleton sequence of integers -- sequence that contains only one integer.
An integer sequence pattern consists of a comma-separated list of square
bracket enclosed integer patterns.

There are six different atomic patterns: a) single, b) prefix, c) suffix,
d) inclusive range, e) exclusive range and f) all. The regex each atomic
pattern should match against is shown below:

    - single: ``^(-)?[0-9]+$``
    - prefix: ``^:(-)?[0-9]+``
    - suffix: ``^(-)?[0-9]+:``
    - inclusive range: ``^-?[0-9]+--?[0-9]+$``
    - exclusive range: ``^-?[0-9]+:-?[0-9]+$``
    - all: ``:``

An atomic single matches the exact integer. An atomic prefix matches all
integers smaller than the referential integer. An atomic suffix matches all
integers greater than or equal to the referential integer. An atomic inclusive
range matches all integers within range :math:`[a, b]`. An atomic exclusive
range matches all integers within range :math:`[a, b)`. An atomic all matches
all integers.

Example Usage
-------------

    .. code-block::

        >>> from ifilters import IntSeqPredicate as isp
        >>> list(filter(isp('4-10'), range(8)))
        [4, 5, 6, 7]
        >>> list(filter(isp('[-3],[:]'), [(x, 4) for x in range(-5, 1)]))
        [(-3, 1)]
"""

from ifilters.ifilters import IntSeqPredicate
