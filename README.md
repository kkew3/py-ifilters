Int/Int-seq Filter
==================

Filter integers or integer sequences as per numpy-like advanced indexing.

`ifilters` provides predicate class that produces predicator according to
the provided numpy-like advanced indexing pattern. For example,

- `1-2`: \{1, 2\}
- `-1--2`: \{\}
- `-2--1`: \{-2, -1\}
- `1,3`: \{1, 3\}
- `1:5`: \{1, 2, 3, 4\}
- `1,3,7:`: \{1, 3\} \cup \{x \mid x \ge 7\}
- `[2],[3-5]`: \{(2,x) \mid 3 \le x \le 5\}

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

- single: `^-?[0-9]+$`
- prefix: `^:-?[0-9]+`
- suffix: `^-?[0-9]+:`
- inclusive range: `^-?[0-9]+--?[0-9]+$`
- exclusive range: `^-?[0-9]+:-?[0-9]+$`
- all: `:`

An atomic single matches the exact integer. An atomic prefix matches all
integers smaller than the referential integer. An atomic suffix matches all
integers greater than or equal to the referential integer. An atomic inclusive
range matches all integers within range :math:`[a, b]`. An atomic exclusive
range matches all integers within range :math:`[a, b)`. An atomic all matches
all integers.

Example Usage
-------------

```python
>>> from ifilters import IntSeqPredicate as isp
>>> list(filter(isp('4-10'), range(8)))
[4, 5, 6, 7]
>>> list(filter(isp('[-3],[:]'), [(x, 4) for x in range(-5, 1)]))
[(-3, 1)]
```

Installation
------------

This package requires `Python 3.5` or above.


```bash
pip install ifilters
```


ifilter (attached executable)
=============================

Installation
------------

There are many ways to install and use in Python-free environment.
For example,

```bash
git clone https://github.com/kkew3/py-ifilters
cd py-ifilters
python3 -m virtualenv rt
. rt/bin/activate
pip install -r requirements.txt
pip install pyinstaller
pyinstaller ifilters/ifilter
deactivate

# assuming that "$PREFIX" is the directory to place the utility and is in PATH
(
	ifilter_path="$(pwd)/dist/ifilter/ifilter";
	cd "$PREFIX";
	ln -s "$ifilter_path" ifilter;
)
```

Detailed help
-------------

> Copied from `ifilter --help`

```plain
usage: range2nums [-h] [-v] [-d DELIMITER] [-L] pattern

Delete integers passed from stdin that don't match against the provided
pattern. For example, use with `seq' in coreutils to output a list of integers
satisfying the provided pattern. Return code: 0) success; 1) pattern parsing
error; 2) error parsing input from stdin; 4) integer sequence length not
matching the pattern.

positional arguments:
  pattern               the integer pattern

optional arguments:
  -h, --help            show this help message and exit
  -v, --invert-match    delete integers matching the pattern instead
  -d DELIMITER, --delimiter DELIMITER
                        the field delimiter to separate fields in an integer
                        tuple; should not contain `\r' or `\n'; default to
                        whitespace characters
  -L, --suppress-length-mismatch
                        do not raise error on length mismatch, e.g. expecting
                        two integers as per pattern `[2],[4]' but got only one
                        integer per line, and instead treat it as a normal
                        match failure
```

Example usage
-------------

Assuming that `ifilter` is in PATH. Denote the prompt as `prompt> `.

```bash
prompt> seq 1 10 | ifilter -v 3,4,7
1
2
5
6
8
9
10
prompt> printf '%s\n' {1..3},{2..4} | ifilter -d, '[3],[3:]'
3,3
3,4
```
