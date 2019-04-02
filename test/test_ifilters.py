from ifilters import IntSeqPredicate

testset = frozenset(range(100))


def test_nil():
    predicate = IntSeqPredicate('')
    assert not any(predicate(x) for x in testset)
    assert not any(predicate([x]) for x in testset)


def test_single():
    predicate = IntSeqPredicate('1')
    assert not any(predicate(x) for x in testset if x != 1)
    assert not any(predicate([x]) for x in testset if x != 1)
    assert predicate(1)
    assert predicate([1])


def test_prefix():
    predicate = IntSeqPredicate(':4')
    assert all(predicate(x) for x in testset if x < 4)
    assert all(predicate([x]) for x in testset if x < 4)
    assert not any(predicate(x) for x in testset if x >= 4)
    assert not any(predicate([x]) for x in testset if x >= 4)
    predicate = IntSeqPredicate(':0')
    assert not any(predicate(x) for x in testset)
    assert not any(predicate(x) for x in testset)
    assert not any(predicate([x]) for x in testset)
    assert not any(predicate([x]) for x in testset)
    predicate = IntSeqPredicate(':101')
    assert all(predicate(x) for x in testset)
    assert all(predicate([x]) for x in testset)


def test_suffix():
    predicate = IntSeqPredicate('4:')
    assert all(predicate(x) for x in testset if x >= 4)
    assert all(predicate([x]) for x in testset if x >= 4)
    predicate = IntSeqPredicate('0:')
    assert all(predicate(x) for x in testset)
    assert all(predicate([x]) for x in testset)
    predicate = IntSeqPredicate('101:')
    assert not any(predicate(x) for x in testset)
    assert not any(predicate([x]) for x in testset)


def test_all():
    predicate = IntSeqPredicate(':')
    assert all(predicate(x) for x in testset)
    assert all(predicate([x]) for x in testset)


def test_uc1():
    predicate = IntSeqPredicate('3-4,6-8,7-19,0-4')
    assert list(filter(predicate, range(20))) == list(range(5)) + list(range(6, 20))


def test_uc2():
    predicate = IntSeqPredicate('[:],[3]')
    assert predicate((4, 3))
