#!/usr/bin/env python3

r"""
usage: less-beeps.py [-h] [--yolo] [-yxhw Y,X,H,W] [CHORD ...]

give away nine classic simple terminal games for you to fork

positional arguments:
  CHORD          taken as if pressed, such as 'F2' or 'Esc' or '^'

options:
  -h, --help     show this help message and exit
  --yolo         do what's popular now
  -yxhw Y,X,H,W  limit writes to just part of the terminal screen

notes:
  distributed as a single .py file, now that a million words isn't many

examples:
  ./bin/less-beeps.py --yolo
  bin/@ Fn F1
"""

# code reviewed by People, Black, Flake8, Mypy-Strict, & Pylance-Standard


from __future__ import annotations  # backports new datatype syntaxes into old Pythons

import __main__  # for to parse the __main__.__doc__
import argparse
import bdb  # for to catch bdb.BdbQuit
import collections
import collections.abc  # .abc is not .collections.abc
import dataclasses
import difflib
import math
import os
import pdb
import select  # for select.select
import signal
import sys
import termios  # for termios.TCSADRAIN
import textwrap
import time
import tty  # for tty.setraw and tty.setcbreak
import types
import typing


_: object  # blocks Mypy from aggressively narrowing the Datatype of '_ =' at first mention

default_eq_None = None  # shoves back on .dict.get rudely refusing to take a ', default=' Kwarg

if not __debug__:
    raise NotImplementedError([__debug__])  # insists 'python3' better than 'python3 -O'


#
# Fit to the Calling Terminal Shell
#


@dataclasses.dataclass(order=True)  # , frozen=True)
class flags:

    apple = sys.platform == "darwin"  # flags.apple
    google = bool(os.environ.get("CLOUD_SHELL", default_eq_None))  # flags.google
    terminal = os.environ.get("TERM_PROGRAM", default_eq_None) == "Apple_Terminal"  # flags.terminal

    landscape: bool | None = None  # flags.landscape, for when lots more wide than high
    barefoot: bool | None = None  # flags.barefoot, for when no rows beneath a Southern Keyboard


#
# Run from the Shell Command Line, but tell the uncaught Exceptions to launch the Py Repl
#


def main() -> None:
    """Run from the Shell Command Line, but tell the uncaught Exceptions to launch the Py Repl"""

    sys.excepthook = excepthook

    sys_argv_parse()
    with TerminalStudio() as ts:
        ts.launch_ts_quickly()
        ts.run_ts_awhile()


def sys_argv_parse() -> None:
    """Take in the Shell Command-Line Args"""

    argv = sys.argv
    parser = main_doc_to_parser()
    parser.parse_args_if(argv[1:])


def main_doc_to_parser() -> ArgDocParser:
    """Declare the Options & Positional Arguments"""

    assert argparse.ZERO_OR_MORE == "*"

    doc = __main__.__doc__
    assert doc, (doc,)

    parser = ArgDocParser(doc, add_help=True)

    chord_help = "taken as if pressed, such as 'F2' or 'Esc' or '^'"
    yolo_help = "do what's popular now"
    yxhw_help = "limit writes to just part of the terminal screen"

    parser.add_argument("chords", metavar="CHORD", nargs="*", help=chord_help)
    parser.add_argument("--yolo", action="count", help=yolo_help)
    parser.add_argument("-yxhw", metavar="Y,X,H,W", help=yxhw_help)

    return parser


#
# Run inside 1 Terminal Window Pane, till Quit
#


terminal_studios = list()


@dataclasses.dataclass(order=True)  # , frozen=True)
class TerminalStudio:
    """Run from the Shell Command Line, and launch the Py Repl vs uncaught Exceptions"""

    stdio: typing.TextIO
    fileno: int
    tcgetattr: list[int | list[bytes | int]]  # replaced by .__enter__

    mock_screen: MockScreen
    mock_keyboard: MockKeyboard

    #
    # Init, Enter, Exit
    #

    def __init__(self) -> None:

        terminal_studios.append(self)

        assert sys.__stderr__ is not None  # refuses to run headless
        stdio = sys.__stderr__
        fileno = stdio.fileno()

        ms = MockScreen(self)

        mk = MockKeyboard(self, mock_screen=ms)

        self.stdio = stdio
        self.fileno = fileno
        self.tcgetattr = list()  # replaced by .__enter__
        self.mock_screen = ms
        self.mock_keyboard = mk

    def __enter__(self) -> TerminalStudio:

        stdio = self.stdio
        fileno = self.fileno
        tcgetattr = self.tcgetattr

        # Enter once

        if tcgetattr:
            return self

        stdio.flush()  # before each 'tty.setraw' of TerminalStudio.__enter__

        with_tcgetattr = termios.tcgetattr(fileno)
        assert with_tcgetattr, (with_tcgetattr,)

        self.tcgetattr = with_tcgetattr  # replaces

        # Stop line-buffering Input, stop replacing \n Output with \r\n, etc

        tty.setraw(fileno, when=termios.TCSADRAIN)  # todo: .when defaults to .TCSAFLUSH

        # Succeed

        return self

        # todo: try termios.TCSAFLUSH to discard Input at entry
        # todo: try tty.setcbreak, especially when debugging hangs

    def __exit__(self, *args: object) -> None:

        stdio = self.stdio
        fileno = self.fileno
        tcgetattr = self.tcgetattr

        # Exit once

        if not tcgetattr:
            return

        stdio.flush()  # before each 'termios.tcsetattr' of TerminalStudio.__exit__

        fd = fileno
        when = termios.TCSADRAIN
        attributes = tcgetattr
        termios.tcsetattr(fd, when, attributes)

        self.tcgetattr = list()  # replaces

        return None

        # todo: try termios.TCSAFLUSH to discard Input at exit

    #
    # Launch, run, quit
    #

    def launch_ts_quickly(self) -> None:
        """Launch quickly"""

        self.sprint("⌃D to quit,  Fn F1 for more help,  or ⌥-Click far from the Cursor")

    def run_ts_awhile(self) -> None:
        """Run till quit, inside the Terminal"""

        while True:
            kk = self.take_ts_input()
            self.give_ts_reply(kk)
            sys.exit()

    #
    # Read & eval & print
    #

    def take_ts_input(self) -> KeyboardKhord:
        """Read one Keyboard Chord"""

        mk = self.mock_keyboard

        while True:
            kk = mk.read_kk_khord(timeout=None)
            kpack = kk.kpack
            self.sprint(kpack)
            if kpack.text or kpack.closed:
                break

        return kk

    def give_ts_reply(self, kk: KeyboardKhord) -> None:
        """Reply to one Keyboard Chord"""

        self.sprint("ok")

    #
    # Fetch from Keyboard
    #

    def read_one_kbyte_if(self, timeout: float | None) -> bytes:
        """Fetch one Byte from the Keyboard, else zero Bytes at Timeout"""

        fileno = self.fileno

        assert self.tcgetattr, (self.tcgetattr,)

        kbhit = self.kbhit(timeout=timeout)  # includes .flush
        if not kbhit:
            return b""

        fd = fileno
        length = 1

        kbyte = os.read(fd, length)
        assert kbyte, (kbyte,)  # because .tcgetattr
        assert len(kbyte) == 1, (kbyte,)  # because .length == 1

        return kbyte

    def kbhit(self, timeout: float | None) -> bool:
        """Block till next Input Byte, else till Timeout, else till forever"""

        stdio = self.stdio
        fileno = self.fileno

        assert self.tcgetattr, (self.tcgetattr,)

        stdio.flush()

        (r, w, x) = select.select([fileno], [], [], timeout)
        hit = fileno in r

        return hit

    #
    # Write to Screen
    #

    def sprint(self, *args: object, end: str = "\r\n") -> None:
        """Write to the Terminal Screen"""

        stdio = self.stdio
        print(*args, end=end, file=stdio)


@dataclasses.dataclass(order=True)  # , frozen=True)
class MockScreen:
    """Mirror the Writes to a Terminal Screen"""

    terminal_studio: TerminalStudio
    mock_keyboard: MockKeyboard

    def __init__(self, terminal_studio: TerminalStudio) -> None:
        self.terminal_studio = terminal_studio


@dataclasses.dataclass(order=True)  # , frozen=True)
class MockKeyboard:
    """Mirror the Reads from a Terminal Keyboard"""

    terminal_studio: TerminalStudio
    mock_screen: MockScreen

    kbytesahead: bytearray
    kbindex: int

    kpack: KeyboardPack

    def __init__(self, terminal_studio: TerminalStudio, mock_screen: MockScreen) -> None:

        self.terminal_studio = terminal_studio
        self.mock_screen = mock_screen

        self.kbytesahead = bytearray()
        self.kbindex = 0
        self.kpack = KeyboardPack(b"")

    def read_kk_khord(self, timeout: float | None) -> KeyboardKhord:
        """Read one Keyboard Chord"""

        kbytesahead = self.kbytesahead
        kbindex = self.kbindex
        kpack = self.kpack

        # Read nothing after timeout

        empty_kk = KeyboardKhord(b"")
        if kbindex >= len(kbytesahead):
            self._fill_kbytesahead_(timeout)
            if kbindex >= len(kbytesahead):
                return empty_kk

            # Read the ⌥``` Keyboard Khord Sequence as a single Keyboard Khord

            option_backtick_backtick = KeyboardKhord(b"``")
            if kbytesahead[kbindex:] == b"``":
                kbindex += len(b"``")
                return option_backtick_backtick

        # Peek at one Byte, and close the Pack early if it doesn't fit, else read it in

        kpack = KeyboardPack(kpack.to_kbytes())
        self.kpack = kpack  # insists better copied than aliased

        kbyte = bytes(kbytesahead[kbindex:][:1])
        kbyte_beyond = kpack.take_one_kbyte_if(kbyte)

        if not kbyte_beyond:
            self.kbindex += 1

        # Succeed

        kbytes = kpack.to_kbytes()
        kk = KeyboardKhord(kbytes)

        return kk

    def _fill_kbytesahead_(self, timeout: float | None) -> None:
        """Fetch Bytes into Self"""

        ts = self.terminal_studio

        kbyte = ts.read_one_kbyte_if(timeout=timeout)  # fetches one or zero K-Byte's
        self.kbytesahead.extend(kbyte)


#
# Amp up Import ArgParse
#


_ARGPARSE_3_10_ = (3, 10)  # Ubuntu 2022 Oct/2021 Python 3.10


@dataclasses.dataclass(order=True)  # , frozen=True)
class ArgDocParser:
    """Scrape out Prog & Description & Epilog from Doc to form an Argument Parser"""

    doc: str  # a copy of parser.format_help()
    add_help: bool  # truthy to define '-h, --help', else not

    parser: argparse.ArgumentParser  # the inner standard ArgumentParser
    text: str  # something like the __main__.__doc__, but dedented and stripped
    closing: str  # the last Graf of the Epilog, minus its Top Line

    add_argument: collections.abc.Callable[..., object]

    def __init__(self, doc: str, add_help: bool) -> None:

        self.doc = doc
        self.add_help = add_help

        text = textwrap.dedent(doc).strip()

        prog = self._scrape_prog_(text)
        description = self._scrape_description_(text)
        epilog = self._scrape_epilog_(text, description=description)
        closing = self._scrape_closing_(epilog)

        parser = argparse.ArgumentParser(  # doesn't distinguish Closing from Epilog
            prog=prog,
            description=description,
            add_help=add_help,
            formatter_class=argparse.RawTextHelpFormatter,  # lets Lines be wide
            epilog=epilog,
        )

        self.parser = parser
        self.text = text
        self.closing = closing

        self.add_argument = parser.add_argument

        # callers who need Options & Positional Arguments have to add them

        # 'add_help=False' for needs like 'cal -h', 'df -h', 'du -h', 'ls -h', etc

    #
    # Take in the Shell Args, else print Help and exit zero or nonzero
    #

    def parse_args_if(self, args: list[str]) -> argparse.Namespace:
        """Take in the Shell Args, else print Help and exit zero or nonzero"""

        parser = self.parser
        closing = self.closing

        # Drop the "--" Shell Args Separator, if present,
        # because 'ArgumentParser.parse_args()' without Pos Args wrongly rejects it

        shargs = args
        if args == ["--"]:  # ArgParse chokes if Sep present without Pos Args
            shargs = list()

        # Print Diffs & exit nonzero, when Arg Doc wrong

        diffs = self._diff_doc_vs_format_help_()
        if diffs:
            if sys.version_info >= _ARGPARSE_3_10_:
                print("\n".join(diffs))

                sys.exit(2)  # exits 2 for wrong Args in Help Doc

            # takes 'usage: ... [HINT ...]', rejects 'usage: ... HINT [HINT ...]'
            # takes 'options:', rejects 'optional arguments:'
            # takes '-F, --isep ISEP', rejects '-F ISEP, --isep ISEP'

        # Print Closing & exit zero, if no Shell Args

        if not args:
            print()
            print(closing)
            print()

            sys.exit(0)  # exits 0 after printing Closing

        # Print help lines & exit zero, else return Parsed Args

        ns = parser.parse_args(shargs)

        return ns

        # often prints help & exits zero

    #
    # Scrape out Parser, Prog, Description, Epilog, & Closing from Doc Text
    #

    def _scrape_prog_(self, text: str) -> str:
        """Pick the Prog out of the Usage Graf that starts the Doc"""

        lines = text.splitlines()
        prog = lines[0].split()[1]  # second Word of first Line  # 'prog' from 'usage: prog'

        return prog

    def _scrape_description_(self, text: str) -> str:
        """Take the first Line of the Graf after the Usage Graf as the Description"""

        lines = text.splitlines()

        firstlines = list(_ for _ in lines if _ and (_ == _.lstrip()))
        docline = firstlines[1]  # first Line of second Graf

        description = docline
        if self._docline_is_skippable_(docline):
            description = "just do it"

        return description

    def _scrape_epilog_(self, text: str, description: str) -> str:
        """Take up the Lines past Usage, Positional Arguments, & Options, as the Epilog"""

        lines = text.splitlines()

        epilog = ""
        for index, line in enumerate(lines):
            if self._docline_is_skippable_(line) or (line == description):
                continue

            epilog = "\n".join(lines[index:])
            break

        return epilog  # maybe empty

    def _docline_is_skippable_(self, docline: str) -> bool:
        """Guess when a Doc Line can't be the first Line of the Epilog"""

        strip = docline.rstrip()

        skippable = not strip
        skippable = skippable or strip.startswith(" ")  # includes .startswith("  ")
        skippable = skippable or strip.startswith("usage")
        skippable = skippable or strip.startswith("positional arguments")
        skippable = skippable or strip.startswith("options")  # ignores "optional arguments"

        return skippable

    def _scrape_closing_(self, epilog: str) -> str:
        """Pick out the last Graf of the Epilog, minus its Top Line"""

        lines = epilog.splitlines()

        indices = list(_ for _ in range(len(lines)) if lines[_])  # drops empty Lines
        indices = list(_ for _ in indices if not lines[_].startswith(" "))  # finds top Lines

        closing = ""
        if indices:
            index = indices[-1] + 1

            join = "\n".join(lines[index:])  # last Graf, minus its Top Line
            dedent = textwrap.dedent(join)
            closing = dedent.strip()

        return closing  # maybe empty

    #
    # Form Diffs from Help Doc to Parser Format_Help
    #

    def _diff_doc_vs_format_help_(self) -> list[str]:
        """Form Diffs from Help Doc to Parser Format_Help"""

        text = self.text
        parser = self.parser

        # Say where the Help Doc came from

        a = text.splitlines()

        basename = os.path.split(__file__)[-1]
        fromfile = "{} --help".format(basename)

        # Fetch the Parser Doc from a fitting virtual Terminal
        # Fetch from a Black Terminal of 89 columns, not from the current Terminal Width
        # Fetch from later Python of "options:", not earlier Python of "optional arguments:"

        with_columns_else = os.environ.get("COLUMNS", default_eq_None)  # checkpoints
        with_no_color_else = os.environ.get("NO_COLOR", default_eq_None)  # checkpoints

        os.environ["COLUMNS"] = str(89)  # adds or replaces
        os.environ["NO_COLOR"] = "True"  # adds or replaces

        try:

            b_text = parser.format_help()

        finally:

            if with_no_color_else is None:
                del os.environ["NO_COLOR"]  # removes
            else:
                os.environ["NO_COLOR"] = with_no_color_else  # reverts

            if with_columns_else is None:
                del os.environ["COLUMNS"]  # removes
            else:
                os.environ["COLUMNS"] = with_columns_else  # reverts

        b = b_text.splitlines()

        tofile = "ArgumentParser(...)"

        # Form >= 0 Diffs from Help Doc to Parser Format_Help,
        # but ask for lineterm="", for else the '---' '+++' '@@' Diff Control Lines end with '\n'

        diffs = list(difflib.unified_diff(a=a, b=b, fromfile=fromfile, tofile=tofile, lineterm=""))

        # Succeed

        return diffs


#
# Amp up Import Math
#


def sketch(f: float, near: float, unit: str) -> str:
    """Format F as '0', else as 2 or 3 digits with a metric exponent, but not the exponent of near"""

    if f == 0:
        return "0"  # 0

    neg = "-" if (f < 0) else ""  # omits '+' at left
    abs_f = abs(f)

    sci = math.floor(math.log10(abs_f))
    eng = (sci // 3) * 3
    precise = abs_f / (10**eng)
    assert 1 <= precise <= 1000, (precise, abs_f, eng, f)  # todo: Log if '== 1000' ever happens

    dotted = round(precise, 1)  # 1.0  # 9.9  # 10.0
    assert 1.0 <= dotted <= 1000.0, (dotted, abs_f, eng, f)

    concise = dotted
    if concise >= 10:
        concise = round(precise)  # 10  # 1000
        assert 10 <= concise <= 1000, (concise, abs_f, eng, f)

    log10_near = int(math.log10(near))
    if eng == log10_near:
        join = f"{neg}{concise}"
    elif eng <= 0:
        join = f"{neg}{concise}e{eng}{unit}"
    else:
        join = f"{neg}{concise}e+{eng}{unit}"

    return join


#
# Amp up Import Traceback
#
# Especially when installed via:  sys.excepthook = excepthook
#


with_excepthook = sys.excepthook  # aliases old hook, and fails fast to chain hooks
assert with_excepthook.__module__ == "sys", (with_excepthook.__module__,)
assert with_excepthook.__name__ == "excepthook", (with_excepthook.__name__,)

assert sys.__stderr__ is not None  # refuses to run headless
with_stderr = sys.stderr


assert int(0x80 + signal.SIGINT) == 130  # discloses the Nonzero Exit Code for after ⌃C SigInt


def excepthook(  # ) -> ...:
    exc_type: type[BaseException],
    exc_value: BaseException,
    exc_traceback: types.TracebackType | None,
) -> None:
    """Run at Process Exit"""

    if exc_type is SystemExit:  # todo: doc how raise SystemExit calls .excepthook in python3 -i
        with_excepthook(exc_type, exc_value, exc_traceback)
        return

    # Quit now for visible cause, if KeyboardInterrupt

    if exc_type is KeyboardInterrupt:
        with_stderr.write("KeyboardInterrupt\n")
        sys.exit(130)  # 0x80 + signal.SIGINT

    if exc_type is bdb.BdbQuit:
        with_stderr.write("BdbQuit\n")
        sys.exit(130)  # 0x80 + signal.SIGINT  # same as for KeyboardInterrupt

    # Print the Traceback, etc

    print(file=with_stderr)  # once
    print(file=with_stderr)  # twice
    print("ExceptHook", file=with_stderr)

    with_excepthook(exc_type, exc_value, exc_traceback)

    # Launch the Post-Mortem Debugger

    print(">>> pdb.pm()", file=with_stderr)
    pdb.pm()


#
# Amp up Import Tty
#


@dataclasses.dataclass(order=True)  # , frozen=True)
class KeyboardKhord:
    """Bundle one Tap or Click or Keyboard Input"""

    kface: str  # 'Return'
    kcaps: str  # '⌃M'
    kpack: KeyboardPack  # .head .neck .back .stash .tail
    kintsmark: bytes  # neck-start + back + tail
    kints: list[int]  # via Csi Neck after Csi Next Start

    def __init__(self, kbytes: bytes) -> None:

        kface = ""
        kcaps = ""
        kpack = KeyboardPack(kbytes)
        kintsmark = b""
        kints: list[int] = list()

        self.kface = kface
        self.kcaps = kcaps
        self.kpack = kpack
        self.kintsmark = kintsmark
        self.kints = kints

    def __str__(self) -> str:

        kface = self.kface
        # kcaps = self.kcaps
        kpack = self.kpack
        kintsmark = self.kintsmark
        kints = self.kints

        parts = list()

        if kface:
            parts.append(kface)

        # todo: parts.append(kcaps)
        parts.append(str(kpack))

        if not kintsmark:
            assert not kints, (kints,)
        else:
            parts.append(str(kints))  # lets the .kpack show the .kintsmark

        join = " ".join(parts)

        return join


@dataclasses.dataclass(order=True)  # , frozen=True)
class KeyboardPack:
    """Bundle one whole Byte Sequence from a Terminal Keyboard, or no Bytes"""

    Headbook = (b"\033", b"\033\033", b"\033\033O", b"\033\033[", b"\033O", b"\033[", b"\033]")

    text: str  # 0 or more Chars of Printable Text, mutates as the Pack grows

    head: bytearray  # 1 Leading Bytes, starts with Control Byte, from the .Headbook or not
    neck: bytearray  # CSI Parameter Bytes, in 0x30..0x3F (16 Codes)  # ...... 0123456789:;<=>?
    back: bytearray  # CSI Intermediate Bytes, in 0x20..0x2F (16 Codes)  # .... !"#$%&'()*+,-./
    stash: bytearray  # 1..3 Bytes taken for now, in hope of decoding 2..4 Later
    tail: bytearray  # CSI Final Byte, in 0x40..0x7E (63 Codes)

    closed: bool = False  # closed because completed, or because continuation undefined

    #
    # Init, Bool, Repr, Str, and .require_simple
    #

    def __init__(self, kbytes: bytes) -> None:

        self.text = ""

        self.head = bytearray()
        self.neck = bytearray()
        self.back = bytearray()
        self.stash = bytearray()
        self.tail = bytearray()

        self.closed = False

        # Add in the .kbytes

        for index in range(len(kbytes)):
            kbyte = kbytes[index:][:1]
            kbytes_beyond = kbytes[index:]

            kbyte_beyond = self.take_one_kbyte_if(kbyte)
            if kbyte_beyond:

                raise ValueError(kbytes_beyond, kbytes)  # raises the b'\x80' of b'\xc0\x80'

        # Succeed

        self._require_simple_kpack_()

        # maybe .closed, maybe not

    def __bool__(self) -> bool:

        kbytes = self.to_kbytes()
        truthy = bool(kbytes or self.closed)
        return truthy

    def __repr__(self) -> str:

        cname = self.__class__.__name__  # 'KeyboardPack'

        text = self.text

        head_ = bytes(self.head)  # reps bytearray(b'') loosely, as b''
        neck_ = bytes(self.neck)
        back_ = bytes(self.back)

        stash_ = bytes(self.stash)
        tail_ = bytes(self.tail)

        closed = self.closed

        join = f"text={text!r}, "
        join += f"head={head_!r}, neck={neck_!r}, back={back_!r}, stash={stash_!r}, tail={tail_!r}"
        join = f"{cname}({join}, {closed=})"

        return join

        # 'TerminalBytePack(head=b'', back=b'', neck=b'', stash=b'', tail=b'', closed=False)'

    def __str__(self) -> str:

        text = self.text

        head_ = bytes(self.head)  # reps bytearray(b'') loosely, as b''
        neck_ = bytes(self.neck)
        back_ = bytes(self.back)

        stash_ = bytes(self.stash)
        tail_ = bytes(self.tail)

        # Solve Text without Stash, and Text with Stash

        if text:
            if stash_:
                return repr(text) + " " + str(stash_)  # "'abc' b'\xc0'"
            return repr(text)  # "'abc'"

        # Solve Headless without Stash, and Headless with Stash

        if not head_:
            if stash_:
                return str(stash_)  # "b'\xc0'"
            return repr(head_)  # "b''"

        # Solve Headed, with or without Neck/ Back/ Stash/ Tail

        join = str(head_)
        if neck_:  # 'Parameter' Bytes
            join += " " + str(neck_)
        if back_ or stash_ or tail_:  # 'Intermediate' Bytes or Final Byte
            assert (not stash_) or (not tail_), (stash_, tail_)
            join += " " + str(back_ + stash_ + tail_)

        return join  # consciously doesn't show if .closed

        # "b'\033[' b'6' b' q'"

    def to_kbytes(self) -> bytes:
        """List the Bytes taken, as yet"""

        text = self.text
        head_ = bytes(self.head)
        neck_ = bytes(self.neck)
        back_ = bytes(self.back)
        stash_ = bytes(self.stash)
        tail_ = bytes(self.tail)

        join = text.encode()
        join += head_ + neck_ + back_ + stash_ + tail_

        return join  # consciously doesn't show if .closed

    def _require_simple_kpack_(self) -> None:
        """Raise Exception when Self can't be real"""

        text = self.text

        head = self.head
        neck = self.neck
        back = self.back

        stash = self.stash
        tail = self.tail

        closed = self.closed  # only via 'def close' if text or stash or not head

        if (not text) and (not head):
            assert (not neck) and (not back), (neck, back, self)
            assert (not tail) and (not closed), (tail, closed, stash, self)

        if text:
            assert not head, (head, text, self)
            assert (not neck) and (not back) and (not tail), (neck, back, tail, text, self)

        if head:
            assert not text, (text, head, self)

        if neck or back or tail:
            assert head, (head, neck, back, tail, self)
            if tail:
                assert closed, (closed, tail, self)

        if stash:
            assert not tail, (tail, closed, stash, self)

    #
    # Run Self-Test's
    #

    def _try_keyboard_pack_(self) -> None:
        """Try some Packets open to, or closed against, taking more Bytes"""

        # Try some Text and Stash

        kpack = KeyboardPack(b"Superb")
        assert str(kpack) == "'Superb'" and not kpack.closed, (kpack,)
        kbytes_beyond = kpack._take_one_kbyte_if_(b"\xc2")
        assert not kbytes_beyond and not kpack.closed, (kbytes_beyond, kpack.closed, kpack)
        assert str(kpack) == r"'Superb' b'\xc2'", (repr(str(kpack)), kpack)

        # Try some Packets left open to taking more Bytes

        self._try_open_(b"")  # empty
        self._try_open_(b"\033")  # first Byte of Esc Sequence
        self._try_open_(b"\033\033")  # first Two Bytes of Esc-Esc Sequence
        self._try_open_(b"\033O")  # first Two Bytes of Three-Byte SS3 Sequence
        self._try_open_(b"\033[", b"6", b" ")  # CSI Head with Neck and Back but no Tail
        self._try_open_(b"\xed\x80")  # Head of >= 3 Byte UTF-8 Encoding
        self._try_open_(b"\xf4\x80\x80")  # Head of >= 4 Byte UTF-8 Encoding
        self._try_open_(b"\033[M#\xff")  # Undecodable Head, incomplete CSI Mouse Report
        self._try_open_(b"\033[M \xc4\x8a")  # Head only, 6 Byte incomplete CSI Mouse Report

        # Try some Packets closed against taking more Bytes

        self._try_closed_(b"\n")  # Head only, of 7-bit Control Byte
        self._try_closed_(b"\033\033[", b"3;5", b"~")  # CSI Head with Neck and Tail, no Back
        self._try_closed_(b"\xc0")  # Head only, of 8-bit Control Byte
        self._try_closed_(b"\xff")  # Head only, of 8-bit Control Byte
        self._try_closed_(b"\xc2\xad")  # Head only, of 2 Byte UTF-8 of U+00AD Soft-Hyphen Control
        self._try_closed_(b"\033", b"A")  # Head & Text Tail of a Two-Byte Esc Sequence
        self._try_closed_(b"\033", b"\t")  # Head & Control Tail of a Two-Byte Esc Sequence
        self._try_closed_(b"\033O", b"P")  # Head & Text Tail of a Three-Byte SS3 Sequence
        self._try_closed_(b"\033[", b"3;5", b"H")  # CSI Head with Next and Tail
        self._try_closed_(b"\033[", b"6", b" q")  # CSI Head with Neck and Back & Tail

        # todo: Test each Control Flow Return? Test each Control Flow Branch?

    def _try_open_(self, *args: bytes) -> None:
        """Require the Eval of the Str of the Pack equals its Bytes"""

        kpack = self._try_bytes_(*args)
        assert not kpack.closed, (kpack,)

    def _try_closed_(self, *args: bytes) -> None:
        """Require the Eval of the Str of the Pack equals its Bytes"""

        kpack = self._try_bytes_(*args)
        assert kpack.closed, (kpack,)

    def _try_bytes_(self, *args: bytes) -> KeyboardPack:
        """Require the Eval of the Str of the Pack equals its Bytes"""

        kbytes = b"".join(args)
        join = " ".join(str(_) for _ in args)

        kpack = KeyboardPack(kbytes)
        kpack_kbytes = kpack.to_kbytes()
        kpack_str = str(kpack)

        assert kpack_kbytes == kbytes, (kpack_kbytes, kbytes)
        assert kpack_str == join, (kbytes, kpack_kbytes, join)

        return kpack

    #
    # Take in one K-Byte and return 0 Bytes, else return the K-Byte that doesn't fit
    #

    def take_one_kbyte_if(self, kbyte: bytes) -> bytes:
        """Take in next 1 Byte and return 0 Bytes, else return 1..4 Bytes that don't fit"""

        kbyte_beyond = self._take_one_kbyte_if_(kbyte)
        self._require_simple_kpack_()

        return kbyte_beyond

    def _take_one_kbyte_if_(self, kbyte: bytes) -> bytes:
        """Take in next 1 Byte and return 0 Bytes, else return 1..4 Bytes that don't fit"""

        text = self.text
        head = self.head
        closed = self.closed

        # Decline Bytes after Closed

        if closed:
            return kbyte  # declines Byte after Closed

        # Take 1 Byte into Stash, if next Bytes could make it Decodable

        (stash_plus_decodes, stash_beyond) = self._take_one_stashable_if(kbyte)
        assert len(stash_plus_decodes) <= 1, (stash_plus_decodes, stash_beyond, kbyte)
        if not stash_beyond:
            return b""  # holds 1..3 possibly Decodable Bytes in Stash

        if stash_plus_decodes:
            assert stash_plus_decodes == stash_beyond.decode(), (stash_plus_decodes, stash_beyond)

        # Take 1 Byte into 6-Char Mouse Report, if next Bytes could close as Mouse Report

        sixem_beyond = self._take_some_sixem_if_(stash_beyond)
        if not sixem_beyond:
            return b""  # holds 1..5 Undecodable Bytes, or 1..11 Bytes as 1..5 Chars as Mouse Report

        assert sixem_beyond == stash_beyond, (sixem_beyond, stash_beyond)

        # Take 1 Char into Text

        if stash_plus_decodes:
            printable = stash_plus_decodes.isprintable()
            if printable and not head:
                self.text += stash_plus_decodes
                return b""  # takes the first Printable Char into Text, or a later

        if text:
            return sixem_beyond  # declines 1..4 Unprintable Bytes after Text

        # Take 1 Char into 1 Control Sequence

        control_beyond = self._take_some_control_if_(stash_plus_decodes, kbytes=sixem_beyond)
        return control_beyond

    def _take_one_stashable_if(self, kbyte: bytes) -> tuple[str, bytes]:
        """Take 1 Byte into Stash, if next Bytes could make it Decodable"""

        stash = self.stash
        stash_plus = bytes(stash + kbyte)

        try:
            decode = stash_plus.decode()
        except UnicodeDecodeError:
            decodes = self.any_decodes_startswith(stash_plus)
            if decodes:
                stash.extend(kbyte)
                return ("", b"")  # holds 1..3 possibly Decodable Bytes in Stash

            stash.clear()
            return ("", stash_plus)  # declines 1..4 Undecodable Bytes

        stash.clear()
        assert len(decode) == 1, (decode, stash, kbyte)

        return (decode, stash_plus)  # forwards 1..4 Decodable Bytes

    def any_decodes_startswith(self, kbytes: bytes) -> str:
        """Say if these Bytes start 1 or more UTF-8 Encodings of Chars"""

        closers = (b"\x80", b"\xbf", b"\x80\x80", b"\xbf\xbf", b"\x80\x80\x80", b"\xbf\xbf\xbf")

        for closer in closers:
            encode = kbytes + closer
            try:
                decode = encode.decode()
                assert len(decode) >= 1, (decode,)
                return decode
            except UnicodeDecodeError:
                continue

        return ""

        # b"\xc2\x80", b"\xe0\xa0\x80", b"\xf0\x90\x80\x80" .. b"\xf4\x8f\xbf\xbf"
        # todo: Invent UTF-8'ish Encoding beyond 1..4 Bytes for Unicode Codes < 0x110000 ?

    def _take_some_sixem_if_(self, kbytes: bytes) -> bytes:
        """Take 1 Byte into Mouse Report, if next Bytes could close as Mouse Report"""

        assert kbytes, (kbytes,)

        head = self.head
        neck = self.neck
        back = self.back

        # Do take the 3rd Byte of this kind of CSI here, and don't take the first 2 Bytes here

        if (head == b"\033[") and (not neck) and (not back):
            if kbytes == b"M":
                head.extend(kbytes)
                return b""  # takes 3rd Byte of CSI Mouse Report here

        if not head.startswith(b"\033[M"):  # ⎋[M Mouse Report
            return kbytes  # doesn't take the first 2 Bytes of Mouse Report here

        # Take 3..15 Bytes into a 3..6 Char Mouse Report

        head_plus = head + kbytes
        try:
            head_plus_decode_if = head_plus.decode()
        except UnicodeDecodeError:
            head_plus_decode_if = ""

        if head_plus_decode_if:
            assert len(head_plus_decode_if) <= 6, (head_plus_decode_if, kbytes)
            head.extend(kbytes)
            if len(head_plus_decode_if) == 6:
                self.closed = True
            return b""  # takes 3..15 Bytes into a 6 Char Mouse Report

        # Take 4..15 Bytes into a 6 Byte Mouse Report

        if len(head_plus) > 6:  # 6..15 Bytes
            return kbytes  # declines 2..4 Bytes into 5 of 6 Chars or into 5 of 6 Bytes

        head.extend(kbytes)
        if len(head_plus) == 6:
            self.closed = True

        return b""  # takes 4..14 Bytes into a 6 Byte Mouse Report

    #
    # Deal with not .isprintable = U+0000 .. U+0020, U+007F, U+00A0, U+00AD, etc
    #

    def _take_some_control_if_(self, decodes: str, kbytes: bytes) -> bytes:
        """Take 1 Char into Control Sequence, else return 1..4 Bytes that don't fit"""

        assert kbytes, (kbytes,)

        head = self.head
        tail = self.tail
        closed = self.closed

        assert not tail, (tail,)
        assert not closed, (closed,)

        # Require Caller to route 6-Char Mouse Reports elsewhere

        assert not head.startswith(b"\033[M"), (head,)  # 6-Char Mouse Report

        # Judge as printable or not

        printable = False
        if decodes:
            assert len(decodes) == 1, (decodes, kbytes)
            printable = decodes.isprintable()

            # Require Caller to route Printable Chars elsewhere till Head chosen

            assert head or not printable, (decodes, kbytes, head, printable)

        # Take first 1 or 2 or 3 Bytes into Esc Sequences, without closing

        headbook = (b"\033", b"\033\033", b"\033\033O", b"\033\033[", b"\033O", b"\033[", b"\033]")
        assert KeyboardPack.Headbook == headbook

        head_plus = bytes(head + kbytes)
        if head_plus in headbook:
            head.extend(kbytes)
            return b""  # takes first 1 or 2 or 3 Bytes into Esc Sequences, without closing

        # Take & close 1 Unprintable Char or 1..4 Undecodable Bytes as Head

        if not head:
            if not printable:
                head.extend(kbytes)
                self.closed = True
                return b""  # takes & closes Unprintable Chars or 1..4 Undecodable Bytes

            # takes \b \t \n \r \x7f etc

        # Take & close 1 Escaped Printable Decoded Char,
        # as Tail after Head of  ⎋ Esc  ⎋⎋ Esc Esc  ⎋O SS3  ⎋⎋O Esc SS3

        if bytes(head) in (b"\033", b"\033\033", b"\033\033O", b"\033O"):
            if printable:
                tail.extend(kbytes)
                self.closed = True
                return b""  # takes & closes 1 Escaped Printable Decoded Char

            # Take & close Unprintable Chars or 1..4 Undecodable Bytes, as Escaped Tail

            tail.extend(kbytes)  # todo: More test of Unprintable/ Undecodable Tails after ⎋O or ⎋⎋O
            self.closed = True
            return b""  # takes & closes Unprintable Chars or 1..4 Undecodable Bytes

            # does take ⎋\x10 ⎋\b ⎋\t ⎋\n ⎋\r ⎋\x7f etc

            # doesn't take bytes([0x80 | 0x0B]) as meaning b"\033\x5b" CSI ⎋[
            # doesn't take bytes([0x80 | 0x0F]) as meaning b"\033\x4f" SS3 ⎋O

        # Decline 1..4 Undecodable Bytes, when escaped by CSI or Esc CSI

        if not decodes:
            return kbytes  # declines 1..4 Undecodable Bytes

        decode = decodes
        assert len(decodes) == 1, (decodes, kbytes)
        assert kbytes == decode.encode(), (kbytes, decodes)

        # Take or don't take 1 Decodable Char into OSC Sequence

        if bytes(head) == b"\033]":
            osc_beyond = self._take_one_osc_if_(decode)
            return osc_beyond  # maybe empty

            # todo: Esc Osc Sequences

        # Take or don't take 1 Decodable Char into CSI or Esc CSI Sequence

        esc_csi_beyond = self._take_one_esc_csi_if_(decode)
        return esc_csi_beyond  # maybe empty

    def _take_one_esc_csi_if_(self, decode: str) -> bytes:
        """Take 1 Char into CSI or Esc CSI Sequence, else return 1..4 Bytes that don't fit"""

        assert len(decode) == 1, decode
        code = ord(decode)
        encode = decode.encode()

        head = self.head
        neck = self.neck
        back = self.back
        tail = self.tail
        closed = self.closed

        # Look only at unclosed CSI or Esc CSI Sequence

        assert CSI == "\033[", (CSI,)  # ⎋[
        if not head.startswith(b"\033\033["):  # ⎋⎋[ Esc CSI
            assert head.startswith(b"\033["), (head,)  # ⎋[ CSI

        assert not tail, (tail,)
        assert not closed, (closed,)

        byte = chr(code).encode()
        assert byte == encode, (byte, encode)

        # Decline 1..4 Bytes of Unprintable or Multi-Byte Char

        if not (0x20 <= code <= 0x7F):
            return byte  # declines 2..4 Bytes of 1 Unprintable or Multi-Byte Char

            # todo: More test of Unprintable/ Undecodable Tails after ⎋[ or ⎋⎋[

        # Accept 1 Byte into Back, into Neck, or as Tail

        assert CSI_P_CHARS == "0123456789:;<=>?"
        assert CSI_I_CHARS == """ !'#$%&'()*+,-./"""
        assert CSI_F_CHARS == "@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~"

        if not back:
            if 0x30 <= code < 0x40:  # 16 Codes  # 0123456789:;<=>?
                neck.extend(byte)
                return b""  # takes 1 of 16 Parameter Byte Codes

        if 0x20 <= code < 0x30:  # 16 Codes  # Spacebar !"#$%&\'()*+,-./
            back.extend(byte)
            return b""  # takes 1 of 16 Intermediate Byte Codes

        if 0x40 <= code < 0x7F:  # 63 Codes  # @A Z[\\]^_`a z{|}~
            assert not tail, (tail,)
            tail.extend(byte)
            self.closed = True
            return b""  # takes 1 of 63 Final Byte Codes

        # Decline 1 Byte of Unprintable Char

        return byte  # declines 1 Byte <= b"\x7f" of Unprintable Char

        # splits '⎋[200~' and '⎋[201~' away from enclosed Bracketed Paste

        # todo: Limit the length of a CSI Escape Sequence

    def _take_one_osc_if_(self, decode: str) -> bytes:
        """Take 1 Char into OSC Sequence, else return 1..4 Bytes that don't fit"""

        assert len(decode) == 1, decode
        code = ord(decode)
        encode = decode.encode()

        head = self.head
        neck = self.neck
        back = self.back
        tail = self.tail
        closed = self.closed

        # Look only at unclosed OSC Sequence

        assert OSC == "\033]", (OSC,)  # ⎋]
        assert bytes(head) == b"\033]", (head,)  # ⎋]

        assert not tail, (tail,)
        assert not closed, (closed,)

        byte = chr(code).encode()
        assert byte == encode, (byte, encode)

        # Accept Printable Bytes into this Osc Sequence

        if not back:
            if 0x20 <= code <= 0x7F:
                neck.extend(byte)
                return b""

        # Accept \033 \134 Esc \ String Terminator (ST) into Back and Tail

        if not back:
            if encode == b"\033":
                back.extend(byte)
                return b""

        if back == b"\033":
            if code == 0o134 == 0x5C == ord("\\"):
                tail.extend(byte)
                self.closed = True
                return b""

        # Accept \007 BEL, much as if String Terminator (ST)

        if code == 0o007:  # BEL
            tail.extend(byte)
            self.closed = True
            return b""

        # Decline 1 Bytes of Unprintable or Multi-Byte Char

        return byte  # declines 1 Byte of 1 Unprintable or Multi-Byte Char

        # todo: Limit rate of input so livelocks go less wild, like in Keyboard/ Screen loopback

    #
    # Close
    #

    def close_if_csi_shift_m(self) -> bool:
        """Convert to Csi ⎋[⇧M cut short, if now standing open as 3 of 6 Char Mouse Report"""

        head = self.head
        back = self.back
        neck = self.neck
        tail = self.tail
        closed = self.closed

        if (head == b"\033[M") and (not back) and (not neck) and (not tail):
            if not closed:

                self.head.clear()
                self.head.extend(b"\033[")
                self.tail.extend(b"M")

                self.closed = True

                return True

        return False

    def close(self) -> None:
        """Close, if not closed already"""

        head = self.head
        stash = self.stash
        closed = self.closed

        if closed:
            return

        self.closed = True

        head_plus = head + stash  # if closing a 6-Char Mouse-Report
        if head_plus.startswith(b"\033[M"):
            try:
                decode = head_plus.decode()
                if len(decode) < 6:
                    if len(head_plus) == 6:

                        head.extend(stash)
                        stash.clear()

            except UnicodeDecodeError:
                pass

        self._require_simple_kpack_()


@dataclasses.dataclass(order=True)  # , frozen=True)
class KeyboardByte:
    """Mirror one Os Read of one Byte, or zero Bytes, from a Terminal Keyboard"""

    t0: int  # time of Call
    kbytes: bytes  # empty at timeout, else 1 Byte
    t1: int  # time of Return


BEL = "\a"  # U+0007 Bell (BEL)
CR = "\r"  # U+000D Carriage Return (CR)
ESC = "\033"  # U+001B Escape (ESC)

SS3 = "\033O"  # 01/11 04/15 Single Shift Three (SS3)
CSI = "\033["  # 01/11 05/11 Control Sequence Introducer
OSC = "\033]"  # 01/11 05/13 Operating System Command
ST = "\033\134"  # 05/11 05/12 String Terminator

CUP_Y_X = "\033[" "{};{}H"  # CSI 04/08 [Choose] Cursor Position

DCH_X = "\033[" "{}" "P"  # CSI 05/00 Delete Character


DSR_5 = "\033[" "5n"  # CSI 06/14 [Request] Device Status Report  # Ps 5 Request DSR_0
DSR_0 = "\033[" "0n"  # CSI 06/14 [Response] Device Status Report  # Ps 0 Response Ready

DSR_6 = "\033[" "6n"  # CSI 06/14 [Request] Device Status Report  # Ps 6 Request CPR
CPR_Y_X = "\033[" "{};{}R"  # CSI 05/02 [Response] Active [Cursor] Pos Rep

XTWINOPS_18 = "\033[" "18t"  # CSI 07/04 [Request] XTWINOPS_18
XTWINOPS_8_H_W = "\033[" "8;{};{}t"  # CSI 07/04 [Response] XTWINOPS_8


CSI_P_CHARS = """0123456789:;<=>?"""  # Csi Parameter Bytes
CSI_I_CHARS = """ !'#$%&'()*+,-./"""  # Csi Intermediate [Penultimate] Bytes
CSI_F_CHARS = "@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~"  # Csi Final Bytes


_SM_SGR_MOUSE_ = "\033[" "?1000;1006h"  # codes Press/ Release as ⎋[{f};{x};{y} ⇧M and M
_RM_SGR_MOUSE_ = "\033[" "?1000;1006l"

_SM_BRACKETED_PASTE_ = "\033[" "?2004h"  # codes Start/ End as ⎋[200~ and ⎋[201~
_RM_BRACKETED_PASTE_ = "\033[" "?2004l"
_START_PASTE_ = "\033[" "200~"  # ⎋[200⇧~
_END_PASTE_ = "\033[" "201~"  # ⎋[201⇧~

SM_DECTCEM = "\033[" "?25h"  # 06/08 Set Mode (SMS) 25 VT220 Show Cursor
RM_DECTCEM = "\033[" "?25l"  # 06/12 Reset Mode (RM) 25 VT220 Hide Cursor


#
# Run self-tests  # todo1: more often
#


def main_self_test() -> None:
    """Call Self-Test's and print how slowly they run"""

    t0 = time.time()
    print(t0)

    kpack = KeyboardPack(b"")
    kpack._try_keyboard_pack_()  # < 2ms

    t1 = time.time()
    print(t1 - t0)


#
# Cite some Terminal Escape & Control Sequence Docs
#


_ = """  # our top choices

    https://unicode.org/charts/PDF/U0000.pdf
    https://unicode.org/charts/PDF/U0080.pdf

    https://en.wikipedia.org/wiki/ANSI_escape_code
    https://jvns.ca/blog/2025/03/07/escape-code-standards

    https://invisible-island.net/xterm/ctlseqs/ctlseqs.html

    https://www.ecma-international.org/publications-and-standards/standards/ecma-48
        /wp-content/uploads/ECMA-48_5th_edition_june_1991.pdf

"""

_ = """  # more breadth found via https://jvns.ca/blog/2025/03/07/escape-code-standards

    https://github.com/tmux/tmux/blob/master/tools/ansicode.txt  <= close to h/t jvns.ca
    https://man7.org/linux/man-pages/man4/console_codes.4.html
    https://sw.kovidgoyal.net/kitty/keyboard-protocol
    https://vt100.net/docs/vt100-ug/chapter3.html

    https://iterm2.com/feature-reporting
    https://gist.github.com/egmontkob/eb114294efbcd5adb1944c9f3cb5feda
    https://github.com/Alhadis/OSC8-Adoption?tab=readme-ov-file

"""

_ = """  # more famous Python Imports to run in place of Code here

    curses — Terminal handling for character-cell displays
    https://docs.python.org/3/library/curses.html for 'import curses'

    tkinter — Python interface to Tcl/Tk
    https://docs.python.org/3/library/tkinter.html

    turtle — Turtle graphics
    https://docs.python.org/3/library/turtle.html for 'import turtle'

"""


#
# Run from the Shell Command Line, if not imported
#


if __name__ == "__main__":
    main()


# todo: foster todo's


# 3456789 123456789 123456789 123456789 123456789 123456789 123456789 123456789 123456789 123456789

# posted into:  https://github.com/pelavarre/less-beeps/blob/main/bin/less-beeps.py
# copied from:  git clone git@github.com:pelavarre/less-beeps.git
