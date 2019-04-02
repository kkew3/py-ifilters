from math import inf
import re
import itertools
import bisect
import typing

__all__ = [
    'IntSeqPredicate',
    'IntSeqIter',
    'UnboundedPredicateError',
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


def build_global_regexes() -> typing.Dict[str, typing.Pattern]:
    """
    Returns a list where each element is a tuple of
    ``(label, possible_regexes)``.
    """
    nums = r'-?\d+'
    ip_atom = r'(({0})|({0}:)|(:{0})|({0}:{0})|({0}-{0})|(:))?'.format(nums)
    ip = r'^{0}(,{0})*$'.format(ip_atom)
    ip_qform = r'^\[{0}(,{0})*\]$'.format(ip_atom)
    sp = r'^{0}(,{0})*$'.format(ip_qform[1:-1])
    return {
        'ip': re.compile(ip),  # unquoted form only, quoted form is-a sp
        'sp': re.compile(sp),
    }


def match_isp(gp: typing.Dict[str, typing.Pattern], string: str) -> str:
    """
    Match int/int-seq string against the regexes.

    :param gp: global regexes
    :param string: the string to match
    :return: canonical int/int-seq pattern (i.e. matching sp)
    """
    if gp['ip'].match(string):
        string = ''.join(('[', string, ']'))
    elif gp['sp'].match(string):
        pass
    else:
        raise ValueError('Invalid int/int-seq pattern')
    return string


def parse_sp(can_string: str) -> typing.List[_DNF]:
    """
    Parse DNF for each dimension from canonical int/int-seq pattern.

    :param can_string: the canonical pattern
    :return: list of DNFs for each dimension
    """
    dnfs = []
    _nums = r'(-?\d+)'
    a = re.compile(r'^:$')
    n = re.compile(r'^$')
    s = re.compile(r'^{0}$'.format(_nums))
    ir = re.compile(r'^{0}-{0}$'.format(_nums))
    xr = re.compile(r'^{0}:{0}$'.format(_nums))
    pf = re.compile(r'^:{0}$'.format(_nums))
    sf = re.compile(r'^{0}:$'.format(_nums))
    for _s in re.split(r',(?=\[)', can_string):
        _dnf = []
        for s_adnf in _s[1:-1].split(','):
            if a.match(s_adnf):
                _dnf.append((-inf, inf))
                break
            if n.match(s_adnf):
                continue
            if s.match(s_adnf):
                _m1 = int(s.match(s_adnf).group(1))
                _dnf.append((_m1, _m1 + 1))
            elif ir.match(s_adnf):
                _m1, _m2 = tuple(map(int, ir.match(s_adnf).groups()))
                if _m1 <= _m2:
                    _dnf.append((_m1, _m2 + 1))
            elif xr.match(s_adnf):
                _m1, _m2 = tuple(map(int, xr.match(s_adnf).groups()))
                if _m1 < _m2:
                    _dnf.append((_m1, _m2))
            elif pf.match(s_adnf):
                _m1 = int(pf.match(s_adnf).group(1))
                _dnf.append((-inf, _m1))
            elif sf.match(s_adnf):
                _m1 = int(sf.match(s_adnf).group(1))
                _dnf.append((_m1, inf))
        dnfs.append(_dnf)

    if not all(dnfs):
        dnfs = [[] for _ in dnfs]
    return dnfs


class IntSeqPredicate:
    """
    Make predicate on integer or a sequence of integers according to the given
    pattern.

    Example use:

    >>> IntSeqPredicate('4,5,7,9,2-5,-3-0')  # DNF in __repr__
    IntSeqPredicate({[-3,1) U [2,6) U [7,8) U [9,10)}_0)
    >>> isp = IntSeqPredicate('4,5,7')  # predicate integers
    >>> isp(7), isp(8)
    (True, False)
    >>> isp = IntSeqPredicate('[:],[3]')  # predicate int-sequences
    >>> isp((4, 3)), isp([4, 3])
    (True, True)
    >>> bool(IntSeqPredicate('0'))  # matching something (only zero here)
    True
    >>> bool(IntSeqPredicate(''))  # not matching any integers
    False
    >>> IntSeqPredicate('7:2') == IntSeqPredicate('')  # {x|7<=x<2} is empty
    True
    >>> IntSeqPredicate('4') == IntSeqPredicate('4:5,7-1')
    True
    """

    def __init__(self, pattern: typing.Optional[str]) -> None:
        """
        :param pattern: the int/int-seq pattern to build the predicator
        """
        if pattern is None:
            pattern = ''
        gp = build_global_regexes()
        can = match_isp(gp, pattern)
        predicates = parse_sp(can)

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

        # flatten DNFs
        self.__fpredicates = [list(itertools.chain(*x)) for x in predicates]

    @staticmethod
    def __to_iseq(value: IntOrISeq) -> typing.Sequence[int]:
        try:
            _ = iter(value)
        except TypeError:
            value = [value]
        return value

    @property
    def infimums(self) -> typing.Optional[typing.List]:
        """
        Infimum for each dimension. If ``self`` matches empty set, the
        infimum is undefined, thus returns None.
        """
        try:
            return [x[0] for x in self.__fpredicates]
        except IndexError:
            return None

    @property
    def supremums(self):
        """
        Supremem for each dimension. If ``self`` matches empty set, the
        supremum is undefined, thus returns None.
        """
        try:
            return [x[-1] for x in self.__fpredicates]
        except IndexError:
            return None

    def __call__(self, value: IntOrISeq) -> bool:
        value = self.__to_iseq(value)
        xn = len(self.__fpredicates)
        if xn != len(value):
            if xn == 1:
                err = 'Expecting integer or length-1 int sequence'
            else:
                err = 'Expecting length-{} int sequence'.format(xn)
            raise ValueError('{}, but got {}'.format(err, value))
        for fpr, val in zip(self.__fpredicates, value):
            if bisect.bisect(fpr, val) % 2 == 0:
                return False
        return True

    def __repr__(self):
        sbuf = []
        for i, fp in enumerate(self.__fpredicates):
            sbuf.append(''.join((
                '{',
                ' U '.join(
                    ['[{0[0]},{0[1]})'.format(fp[i:i + 2])
                     for i in range(0, len(fp), 2)]),
                '}}_{}'.format(i),
            )))
        sbuf = ' && '.join(sbuf)
        sbuf = ''.join((type(self).__name__, '(', sbuf, ')'))
        return sbuf

    def __eq__(self, other):
        """
        Returns ``True`` if ``self`` and ``other`` accepts the same set of
        integers.
        """
        if not isinstance(other, IntSeqPredicate):
            return NotImplemented
        return self.__fpredicates == other.__fpredicates

    def __hash__(self):
        return hash(self.__fpredicates)

    def __bool__(self):
        """
        Returns ``True`` if ``self`` matches at least one valid input
        """
        return all(self.__fpredicates)


class UnboundedPredicateError(ValueError):
    pass

class IntSeqIter:
    """
    Make int/int-seq iterator from predicate implying a upper- and
    lower-bounded finite set of integers or integer sequences.

    >>> list(IntSeqIter('3-4,7-10', use_int_if_possible=True))
    [3, 4, 7, 8, 9, 10]
    >>> list(IntSeqIter('3-4,6'))
    [(3,), (4,), (6,)]
    >>> list(IntSeqIter(''))
    []
    """
    def __init__(self, predicate: typing.Union[str, IntSeqPredicate],
                 use_int_if_possible: bool = False):
        """
        :param predicate: the predicate object or predication expression
        :param use_int_if_possible: if ``predicate`` implies a one dimension
               int-sequence pattern, let ``__iter__`` returns an iterator
               of ``int`` rather than an iterator of singleton ``int tuple``s.
        :raise UnboundedPredicateError: if ``predicate`` implies unbounded
               language
        """
        if not isinstance(predicate, IntSeqPredicate):
            predicate = IntSeqPredicate(predicate)

        ifs = predicate.infimums
        sps = predicate.supremums
        if not ifs or not sps:
            self.__ds = None
        elif -inf in ifs or inf in sps:
            raise ValueError('Iterator undefined for infinite set')
        else:
            self.__ds = [range(a, b) for a, b in zip(ifs, sps)]
        self.as_int_if_possible = use_int_if_possible
        self.predicate = predicate

    def __iter__(self):
        if self.__ds is None:
            it = iter(())
        elif len(self.__ds) == 1 and self.as_int_if_possible:
            it = filter(self.predicate, self.__ds[0])
        else:
            it = filter(self.predicate, itertools.product(*self.__ds))
        return it
