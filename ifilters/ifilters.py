from math import inf
from itertools import chain
import bisect
import typing

import pyparsing as pp

__all__ = [
    'grammar',
    'IntSeqPredicate',
]

IntOrISeq = typing.Union[int, typing.Sequence[int]]

_DNFAtom = typing.Optional[typing.Tuple[typing.Optional[int],
                                        typing.Optional[int]]]
"""
    - None             empty set
    - (-inf, inf)      universe set
    - (-inf, b)        { x | x < b }
    - (a, inf)         { x | x >= a }
    - (a, b)           { x | a <= a < b }
"""

_DNF = typing.List[_DNFAtom]


def grammar() -> pp.ParserElement:
    """
    Returns the grammar object used to parsing the provided pattern
    """
    nums = pp.Combine(pp.Optional('-') + pp.Word(pp.nums))

    single = nums('s')
    prefix = (pp.Suppress(':') + nums)('pf')
    suffix = (nums + pp.Suppress(':'))('sf')
    irange_ = (nums + pp.Suppress('-') + nums)('ir')
    xrange_ = (nums + pp.Suppress(':') + nums)('xr')
    all_ = pp.Literal(':')('a')
    atom = irange_ | xrange_ | prefix | suffix | single | all_
    enum = pp.delimitedList(atom)
    qenums = pp.delimitedList(pp.nestedExpr('[', ']', content=enum))
    nil = pp.Empty()
    compose = pp.StringStart() + (qenums | enum | nil) + pp.StringEnd()

    return compose


class IntSeqPredicate:
    """
    Make predicate on integer or a sequence of integers according to the given
    pattern.

    Example use:

    >>> isp = IntSeqPredicate('4,5,7')
    >>> isp(7), isp(8)
    (True, False)
    >>> isp = IntSeqPredicate('[:],[3]')
    >>> isp((4, 3))
    True
    """

    def __init__(self, pattern: str) -> None:
        parser = grammar()
        matches: pp.ParseResults = parser.parseString(pattern)
        if not matches.asList():
            predicates = [[]]
        elif matches.asDict():
            predicates = [[self.__populate_adnf(*x)
                           for x in matches.asDict().items()]]
        else:
            predicates = []
            for i, m in enumerate(matches):
                if not m.asDict():
                    raise ValueError('Too many quotes at integer pattern-{}'
                                     .format(i))
                predicates.append([self.__populate_adnf(*x)
                                   for x in m.asDict().items()])

        # now, the ith element of ``predicates`` is a DNF assertion for the
        # ith element of the incoming integer sequence

        # pre-processing -- removing empty and universe ADNF
        for i in range(len(predicates)):
            predicates[i] = list(filter(None, predicates[i]))
            if (-inf, inf) in predicates[i]:
                predicates[i] = [(-inf, inf)]
            # now predicates[i] must be one of the three cases:
            # 1. []
            # 2. [(-inf, inf)]
            # 3. [..., adnf, ...]

        # simplifying the third case for each DNF
        for i in range(len(predicates)):
            if not predicates[i] or predicates[i] == [(-inf, inf)]:
                continue
            _p = sorted(predicates[i])
            predicates[i] = [_p.pop(0)]  # this must hold
            while _p:
                adnf = predicates[i].pop()
                next_adnf = _p.pop(0)
                # assert adnf[0] <= next_adnf[0], due to ``sorted``
                if next_adnf[0] <= adnf[1]:
                    adnf = (adnf[0], max(adnf[1], next_adnf[1]))
                    predicates[i].append(adnf)
                else:
                    predicates[i].extend((adnf, next_adnf))
            # now predicates[i] must be one of the two cases:
            # 1. []
            # 2. [..., adnf_i, ..., adnf_j, ...], such that adnf_i and adnf_j
            #    are disjoint

        # flatten DNFs
        self.fpredicates = [list(chain(*x)) for x in predicates]

    @staticmethod
    def __populate_adnf(ty: str, args: typing.List[str]) -> _DNFAtom:
        return {
            's': lambda _a: (int(_a[0]), int(_a[0]) + 1),
            'pf': lambda _a: (-inf, int(_a[0])),
            'sf': lambda _a: (int(_a[0]), inf),
            'ir': lambda _a: (int(_a[0]), int(_a[1]) + 1),
            'xr': lambda _a: (int(_a[0]), int(_a[1])),
            'a': lambda _a: (-inf, inf),
        }[ty](args)

    @staticmethod
    def __to_iseq(value: IntOrISeq) -> typing.Sequence[int]:
        try:
            _ = iter(value)
        except TypeError:
            value = [value]
        return value

    def __call__(self, value: IntOrISeq) -> bool:
        value = self.__to_iseq(value)
        xn = len(self.fpredicates)
        if xn != len(value):
            if xn == 1:
                err = 'Expecting integer or length-1 int sequence'
            else:
                err = 'Expecting length-{} int sequence'.format(xn)
            raise ValueError('{}, but got {}'.format(err, value))
        for fpr, val in zip(self.fpredicates, value):
            if bisect.bisect(fpr, val) % 2 == 0:
                return False
        return True
