# -*- coding: utf-8 -*-

from __future__ import with_statement  # Make 2.5-compatible
from StringIO import StringIO
from curses import tigetstr, tparm
import sys

from nose.tools import eq_

# This tests that __all__ is correct, since we use below everything that should
# be imported:
from blessings import *
from blessings import Capability


def bytes_eq(bytes1, bytes2):
    """Make sure ``bytes1`` equals ``bytes2``, the latter of which gets cast to something bytes-like, depending on Python version."""
    eq_(bytes1, Capability(bytes2))


def test_capability():
    """Check that a capability lookup works.

    Also test that Terminal grabs a reasonable default stream. This test
    assumes it will be run from a tty.

    """
    t = Terminal()
    sc = tigetstr('sc')
    eq_(t.save, sc)
    eq_(t.save, sc)  # Make sure caching doesn't screw it up.


def test_capability_without_tty():
    """Assert capability templates are '' when stream is not a tty."""
    t = Terminal(stream=StringIO())
    eq_(t.save, Capability(''))
    eq_(t.red, Capability(''))


def test_capability_with_forced_tty():
    """If we force styling, capabilities had better not (generally) be empty."""
    t = Terminal(stream=StringIO(), force_styling=True)
    assert len(t.save) > 0


def test_parametrization():
    """Test parametrizing a capability."""
    eq_(Terminal().cup(3, 4), tparm(tigetstr('cup'), 3, 4))


def height_and_width():
    """Assert that ``height_and_width()`` returns ints."""
    t = Terminal()
    assert isinstance(int, t.height)
    assert isinstance(int, t.width)


def test_stream_attr():
    """Make sure Terminal exposes a ``stream`` attribute that defaults to something sane."""
    eq_(Terminal().stream, sys.__stdout__)


def test_location():
    """Make sure ``location()`` does what it claims."""
    t = Terminal(stream=StringIO(), force_styling=True)

    with t.location(3, 4):
        t.stream.write('hi')

    eq_(t.stream.getvalue(), tigetstr('sc') +
                             tparm(tigetstr('cup'), 4, 3) +
                             'hi' +  # TODO: Encode with Terminal's encoding.
                             tigetstr('rc'))

def test_horizontal_location():
    """Make sure we can move the cursor horizontally without changing rows."""
    t = Terminal(stream=StringIO(), force_styling=True)
    with t.location(x=5):
        pass
    eq_(t.stream.getvalue(), t.save + tparm(tigetstr('hpa'), 5) + t.restore)


def test_null_fileno():
    """Make sure ``Terminal`` works when ``fileno`` is ``None``.

    This simulates piping output to another program.

    """
    out = stream=StringIO()
    out.fileno = None
    t = Terminal(stream=out)
    bytes_eq(t.save, '')


def test_mnemonic_colors():
    """Make sure color shortcuts work."""
    # Avoid testing red, blue, yellow, and cyan, since they might someday
    # chance depending on terminal type.
    t = Terminal()
    bytes_eq(t.white, '\x1b[37m')
    bytes_eq(t.green, '\x1b[32m')  # Make sure it's different than white.
    bytes_eq(t.on_black, '\x1b[40m')
    bytes_eq(t.on_green, '\x1b[42m')
    bytes_eq(t.bright_black, '\x1b[90m')
    bytes_eq(t.bright_green, '\x1b[92m')
    bytes_eq(t.on_bright_black, '\x1b[100m')
    bytes_eq(t.on_bright_green, '\x1b[102m')


def test_formatting_functions():
    """Test crazy-ass formatting wrappers, both simple and compound."""
    t = Terminal(encoding='utf-8')
    eq_(t.bold('hi'), t.bold + 'hi' + t.normal)
    eq_(t.green('hi'), t.green + 'hi' + t.normal)
    # Test encoding of unicodes:
    eq_(t.bold_green(u'boö'), t.bold + t.green + u'boö'.encode('utf-8') + t.normal)
    eq_(t.bold_underline_green_on_red('boo'),
        t.bold + t.underline + t.green + t.on_red + 'boo' + t.normal)
    # Don't spell things like this:
    eq_(t.on_bright_red_bold_bright_green_underline('meh'),
        t.on_bright_red + t.bold + t.bright_green + t.underline + 'meh' + t.normal)


def test_formatting_functions_without_tty():
    """Test crazy-ass formatting wrappers when there's no tty."""
    t = Terminal(stream=StringIO())
    eq_(t.bold('hi'), 'hi')
    eq_(t.green('hi'), 'hi')
    # Test encoding of unicodes:
    eq_(t.bold_green(u'boö'), u'boö'.encode('utf-8'))  # unicode
    eq_(t.bold_underline_green_on_red('boo'), 'boo')
    eq_(t.on_bright_red_bold_bright_green_underline('meh'), 'meh')


def test_nice_formatting_errors():
    """Make sure you get nice hints if you misspell a formatting wrapper."""
    t = Terminal()
    try:
        t.bold_misspelled('hey')
    except TypeError, e:
        assert 'probably misspelled' in e.args[0]

    try:
        t.bold_misspelled(None)  # an arbitrary non-string
    except TypeError, e:
        assert 'probably misspelled' not in e.args[0]

    try:
        t.bold_misspelled('a', 'b')  # >1 string arg
    except TypeError, e:
        assert 'probably misspelled' not in e.args[0]
