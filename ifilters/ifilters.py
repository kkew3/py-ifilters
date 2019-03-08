import typing

import pyparsing as pp

__all__ = [
    'grammar',
    'IntSeqPredicate',
]


IntOrISeq = typing.Union[int, typing.Sequence[int]]
IPredicate = typing.Callable[[IntOrISeq], bool]


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


class _AtomSinglePredicate:
    def __init__(self, ref: int) -> None:
        self.ref = ref

    def __call__(self, value: int) -> bool:
        return self.ref == value

class _AtomNilPredicate:
    def __call__(self, _) -> bool:
        return False

class _AtomPrefixPredicate:
    def __init__(self, ref: int) -> None:
        self.ref = ref

    def __call__(self, value: int) -> bool:
        return value < self.ref

class _AtomSuffixPredicate:
    def __init__(self, ref: int) -> None:
        self.ref = ref

    def __call__(self, value: int) -> bool:
        return value >= self.ref

class _AtomIRangePredicate:
    def __init__(self, refs: int, reft: int) -> None:
        self.refs = refs
        self.reft = reft

    def __call__(self, value: int) -> bool:
        return self.refs <= value and value <= self.reft

class _AtomXRangePredicate:
    def __init__(self, refs: int, reft: int) -> None:
        self.refs = refs
        self.reft = reft

    def __call__(self, value: int) -> bool:
        return self.refs <= value and value < self.reft

class _AtomAllPredicate:
    def __call__(self, _) -> bool:
        return True

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
        predicates: typing.List[typing.List[IPredicate]] = []
        if not matches.asList():
            predicates.append([_AtomNilPredicate()])
        elif matches.asDict():
            predicates.append([self.__ty2pr(*x) for x in
                               matches.asDict().items()])
        else:
            for i, m in enumerate(matches):
                if not m.asDict():
                    raise ValueError('Too many quotes at integer pattern-{}'
                                     .format(i))
                predicates.append([self.__ty2pr(*x) for x in
                                   m.asDict().items()])
        self.predicates = predicates

    @staticmethod
    def __ty2pr(ty: str, args: typing.List[str]) -> IPredicate:
        return eval({
            's': '_AtomSinglePredicate(int(args[0]))',
            'pf': '_AtomPrefixPredicate(int(args[0]))',
            'sf': '_AtomSuffixPredicate(int(args[0]))',
            'ir': '_AtomIRangePredicate(int(args[0]), int(args[1]))',
            'xr': '_AtomXRangePredicate(int(args[0]), int(args[1]))',
            'a': '_AtomAllPredicate()',
        }[ty])

    def __call__(self, value: IntOrISeq) -> bool:
        try:
            _ = iter(value)
        except TypeError:
            value = [value]
        if len(self.predicates) != len(value):
            if len(self.predicates) == 1:
                err = 'Expecting integer or length-1 int sequence'
            else:
                err = ('Expecting length-{} int sequence'
                       .format(len(self.predicates)))
            raise ValueError('{}, but got {}'.format(err, value))
        return all(any(pr(val) for pr in prs)
                   for prs, val in zip(self.predicates, value))
