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

    quickly = False
    quickly = True  # todo1: more often try quickly=False
    KeyPack(b"")._try_key_pack_(quickly)

    sys_argv_parse()
    with TerminalStudio() as ts:
        ts.launch_ts_quickly()
        ts.run_ts_awhile()


def sys_argv_parse() -> None:
    """Take in the Shell Command-Line Args"""

    argv = sys.argv
    parser = main_doc_to_parser()
    ns = parser.parse_args_if(argv[1:])

    assert ns.yolo, (ns.yolo, ns)
    assert ns.yxhw is None, (ns.yxhw, ns)
    assert not ns.chords, (ns.chords, ns)


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

    def take_ts_input(self) -> KeyKhord:
        """Read one Key Chord"""

        mk = self.mock_keyboard

        while True:
            kk = mk.read_khord(timeout=None)
            kpack = kk.kpack
            self.sprint(kpack)
            if kpack.text or kpack.closed:
                break

        return kk

    def give_ts_reply(self, kk: KeyKhord) -> None:
        """Reply to one Key Chord"""

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

    kpack: KeyPack

    def __init__(self, terminal_studio: TerminalStudio, mock_screen: MockScreen) -> None:

        self.terminal_studio = terminal_studio
        self.mock_screen = mock_screen

        self.kbytesahead = bytearray()
        self.kbindex = 0
        self.kpack = KeyPack(b"")

    def read_khord(self, timeout: float | None) -> KeyKhord:
        """Read one Key Chord"""

        kbytesahead = self.kbytesahead
        kbindex = self.kbindex
        kpack = self.kpack

        # Read nothing after timeout

        empty_kk = KeyKhord(b"")
        if kbindex >= len(kbytesahead):
            self._fill_kbytesahead_(timeout)
            if kbindex >= len(kbytesahead):
                return empty_kk

            # Read the ⌥``` Key Khord Sequence as a single Key Khord

            option_backtick_backtick = KeyKhord(b"``")
            if kbytesahead[kbindex:] == b"``":
                kbindex += len(b"``")
                return option_backtick_backtick

        # Peek at one Byte, and close the Pack early if it doesn't fit, else read it in

        kpack = KeyPack(kpack.to_kbytes())
        self.kpack = kpack  # insists better copied than aliased

        kbyte = bytes(kbytesahead[kbindex:][:1])
        kbyte_beyond = kpack.take_one_kbyte_if(kbyte)

        if not kbyte_beyond:
            self.kbindex += 1

        # Succeed

        kbytes = kpack.to_kbytes()
        kk = KeyKhord(kbytes)

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
class KeyKhord:
    """Bundle one Tap or Click or Keyboard Input"""

    kface: str  # 'Return'
    kcaps: str  # '⌃M'
    kpack: KeyPack  # .head .neck .back .stash .tail
    kintsmark: bytes  # neck-start + back + tail
    kints: list[int]  # via Csi Neck after Csi Next Start

    def __init__(self, kbytes: bytes) -> None:

        kface = ""
        kcaps = ""
        kpack = KeyPack(kbytes)
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

        # todo1: examples of KeyKhord.__str__ results


@dataclasses.dataclass(order=True)  # , frozen=True)
class KeyPack:
    """Bundle one whole Byte Sequence from a Terminal Keyboard, or no Bytes"""

    Headbook = (b"\033", b"\033\033", b"\033\033O", b"\033\033[", b"\033O", b"\033[", b"\033]")

    text: str  # 0 or more Chars of Printable Text, mutates as the Pack grows

    head: bytearray  # 1 Leading Bytes, starts with Control Byte, from the .Headbook or not
    neck: bytearray  # Csi Parameter Bytes, in 0x30..0x3F (16 Codes)  # ...... 0123456789:;<=>?
    back: bytearray  # Csi Intermediate Bytes, in 0x20..0x2F (16 Codes)  # .... !"#$%&'()*+,-./
    stash: bytearray  # 1..3 Bytes taken for now, in hope of decoding 2..4 Later
    tail: bytearray  # Csi Final Byte, in 0x40..0x7E (63 Codes)

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

        kbytes_beyond = self.take_some_kbytes_if(kbytes)
        if kbytes_beyond:
            raise ValueError(kbytes_beyond, kbytes)  # raises the b'\x80' of b'\xc0\x80'

        self._require_simple_kpack_()

        # maybe .closed, maybe not

    def __bool__(self) -> bool:

        kbytes = self.to_kbytes()
        truthy = bool(kbytes or self.closed)
        return truthy

    def __repr__(self) -> str:

        cname = self.__class__.__name__  # 'KeyPack'

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
            assert not tail, (tail, stash, self)

        if text:
            assert not head, (head, text, self)
            assert (not neck) and (not back) and (not tail), (neck, back, tail, text, self)

        if head:
            assert not text, (text, head, self)

        if neck or back or tail:
            assert head, (head, neck, back, tail, self)
            assert head in self.Headbook, (head, self.Headbook, self)
            if tail:
                assert closed, (closed, tail, self)

        if stash:
            assert not tail, (tail, closed, stash, self)

    #
    # Run quick and slow Self-Test's
    #

    def _try_key_pack_(self, quickly: bool) -> None:
        """Run quick and slow Self-Test's"""

        t0 = time.time()

        self._try_open_(b"")  # empty

        self._try_headbook_()
        if not quickly:
            self._try_tailbook_()  # ~200ms

        self._try_one_more_kbyte_()
        self._try_some_control_()

        t1 = time.time()
        t1t0 = t1 - t0

        assert t1t0 < 1.000, (t1t0,)
        if quickly:
            assert t1t0 < 0.001, (t1t0,)

    def _try_headbook_(self) -> None:
        """Accept the Bytes of any Head of the Headbook, without closing the Pack"""

        headbook = KeyPack.Headbook

        for head in headbook:
            self._try_open_(head)

    def _try_tailbook_(self) -> None:
        """Require each Opener accepted by .any_decodes_startswith via the Tailbook"""

        openers_set = set()
        for cp in range(0x110000):
            if 0xD800 <= cp <= 0xDFFF:  # skips surrogates
                continue
            kbytes = chr(cp).encode()
            for index in range(1, len(kbytes) - 1):
                opener = kbytes[:index]
                openers_set.add(opener)

        for opener in openers_set:
            assert self.any_decodes_startswith(opener), (opener,)

    def _try_one_more_kbyte_(self) -> None:
        """Try some Packets open to, or closed against, taking more Bytes"""

        # Decline Bytes after Closed

        KeyPack(b"")._closed_()._try_drop_kbytes_(b"\x41")

        # Take Bytes into Stash, while could be decodable

        self._try_open_("Superb", b"\xc2")
        self._try_open_(b"\xed\x80")  # Head of >= 3 Byte UTF-8 Encoding
        self._try_open_(b"\xf4\x80\x80")  # Head of >= 4 Byte UTF-8 Encoding

        # Take Bytes into 6-Char Mouse Report, while could be 6 Bytes or 6 Decoded Chars

        self._try_open_(b"\033[M" b"\xff\xff")  # 5 Undecodable Bytes
        self._try_open_(b"\033[M" b".\xc2\xa3")  # 6 Decodable Bytes but < 6 Chars
        self._try_open_(b"\033[M" b"\xf4\x8f\xbf\xbf" b"\xf4\x8f\xbf\xbf", b"\xf4\x8f\xbf")

        self._try_close_(b"\033[M" b"\xc2\x80\xff")  # 6 Undecodable Bytes
        self._try_close_(b"\033[M" b"\xf4\x8f\xbf\xbf" b"\xf4\x8f\xbf\xbf" b"\xf4\x8f\xbf\xbf")

        KeyPack(b"\033[M" b"\xff\xff")._try_drop_kbytes_(b"\xc2\x80")

        # Take Bytes into Text

        self._try_open_("\u20ac", "\ufffd".encode()[:-1])

        # Decline 1..4 Unprintable Bytes after Text

        KeyPack(b"Text")._try_drop_kbytes_(b"\x7f")
        KeyPack(b"Plain")._try_drop_kbytes_("\uffff".encode())

    def _try_some_control_(self) -> None:

        # Take & close 1 Unprintable Char or 1..4 Undecodable Bytes as an Alt Head

        self._try_close_(b"\n")  # Head only, of 7-bit Control Byte
        self._try_close_(b"\xc0")  # Head only, of 8-bit Control Byte
        self._try_close_(b"\xc2\xad")  # Head only, of 2 Byte UTF-8 of U+00AD Soft-Hyphen Control
        self._try_close_(b"\xf5")
        self._try_close_(b"\xff")  # Head only, of 8-bit Control Byte
        self._try_close_(b"\xf4\x8f\xbf\xc0")

        # Take & close 1 Printable Char escaped by a Head simpler than Csi, Esc Csi, and Osc

        self._try_close_(b"\033", b"A")  # Head & Text Tail of a Two-Byte Esc Sequence
        self._try_close_(b"\033O", b"P")  # Head & Text Tail of a Three-Byte Ss3 Sequence

        # Take & close 1 Unprintable Char or 1..4 Undecodable Bytes escaped by a Simpler Head

        self._try_close_(b"\033", b"\t")  # Head & Control Tail of a Two-Byte Esc Sequence

        # Decline 1..4 Undecodable Bytes, when escaped by Csi or Esc Csi or Osc

        pass  # todo1

        # Take or don't take 1 Decodable Char escaped by Csi or Esc Csi

        self._try_open_(b"\033[", b"6", b" ")  # Csi Head with Neck and Back but no Tail

        self._try_close_(b"\033\033[", b"3;5", b"~")  # Esc Csi Head with Neck and Tail, no Back
        self._try_close_(b"\033[", b"3;5", b"H")  # Csi Head with Neck and Tail, no Back
        self._try_close_(b"\033[", b"6", b" q")  # Csi Head with Neck and Back & Tail

        # Take or don't take 1 Decodable Char escaped by Osc

        pass  # todo1

    def _closed_(self) -> KeyPack:
        """Close, if not closed already, and return Self"""

        self.close()
        return self

    def _try_drop_kbytes_(self, kbytes: bytes) -> None:
        """Require the Pack to reject these Bytes"""

        kbytes_beyond = self.take_some_kbytes_if(kbytes)
        assert kbytes_beyond == kbytes, (kbytes_beyond, kbytes)

    def _try_open_(self, *args: str | bytes) -> None:
        """Require the Eval of the Str of the Pack equals its Bytes"""

        kpack = self._try_bytes_(*args)
        assert not kpack.closed, (kpack,)

    def _try_close_(self, *args: bytes) -> None:
        """Require the Eval of the Str of the Pack equals its Bytes"""

        kpack = self._try_bytes_(*args)
        assert kpack.closed, (kpack,)

    def _try_bytes_(self, *args: str | bytes) -> KeyPack:
        """Require the Eval of the Str of the Pack equals its Bytes"""

        kbytes = b""
        for arg in args:
            if isinstance(arg, str):
                kbytes += arg.encode()
            else:
                kbytes += arg

        join = " ".join(repr(_) for _ in args)

        kpack = KeyPack(kbytes)
        kpack_kbytes = kpack.to_kbytes()
        kpack_str = str(kpack)

        assert kpack_kbytes == kbytes, (kpack_kbytes, kbytes)
        assert kpack_str == join, (kpack_str, join)

        return kpack

    #
    # Take in one K-Byte and return 0 Bytes, else return the K-Byte that doesn't fit
    #

    def take_some_kbytes_if(self, kbytes: bytes) -> bytes:
        """Take in next N Bytes and return 0 Bytes, else return 1..4 Bytes that don't fit"""

        for index in range(len(kbytes)):
            kbyte = kbytes[index:][:1]

            kbytes_beyond = self.take_one_kbyte_if(kbyte)
            if kbytes_beyond:
                kbytes_beyond_plus = kbytes_beyond + kbytes[index:][1:]
                return kbytes_beyond_plus

        return b""

    def take_one_kbyte_if(self, kbyte: bytes) -> bytes:
        """Take in next 1 Byte and return 0 Bytes, else return 1..4 Bytes that don't fit"""

        kbyte_beyond = self._take_one_kbyte_if_(kbyte)
        self._require_simple_kpack_()

        return kbyte_beyond

    def _take_one_kbyte_if_(self, kbyte: bytes) -> bytes:
        """Take in next 1 Byte and return 0 Bytes, else return 1..4 Bytes that don't fit"""

        assert len(kbyte) == 1, (kbyte,)

        text = self.text
        head = self.head
        neck = self.neck
        back = self.back
        closed = self.closed

        # Decline Bytes after Closed

        if closed:
            return kbyte  # declines Byte after Closed

        # Take ⎋[⇧M as starts a Csi Mouse Report of 6 Bytes or 6 Chars

        if (head == b"\033[") and (not neck) and (not back):
            if kbyte == b"M":
                head.extend(kbyte)
                return b""  # takes 3rd Byte of Csi Mouse Report

        # Take Bytes into Stash, while could be decodable

        (stash_plus_decodes, stash_beyond) = self._take_one_stashable_if(kbyte)
        assert len(stash_plus_decodes) <= 1, (stash_plus_decodes, stash_beyond, kbyte)
        if not stash_beyond:
            return b""  # holds 1..3 possibly Decodable Bytes in Stash

        if stash_plus_decodes:
            assert stash_plus_decodes == stash_beyond.decode(), (stash_plus_decodes, stash_beyond)

        # Take Bytes into a Csi Mouse Report of 6 Bytes or 6 Chars

        if head.startswith(b"\033[M"):
            sixem_beyond = self._take_some_sixem_if_(stash_beyond)
            return sixem_beyond

            # holds 4..5 Undecodable Bytes, or 1..11 Bytes as 1..5 Chars of Mouse Report, or
            # takes 6 Undecodable Bytes or 6..12 Bytes as 6 Chars of Mouse Report

        # Take Bytes into Text

        if stash_plus_decodes:
            printable = stash_plus_decodes.isprintable()
            if printable and not head:
                self.text += stash_plus_decodes
                return b""  # takes the first Printable Char into Text, or a later

        # Decline 1..4 Unprintable Bytes after Text

        if text:
            return stash_beyond

        # Take 1 Char into 1 Control Sequence

        control_beyond = self._take_some_control_if_(stash_plus_decodes, kbytes=stash_beyond)
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
        """Say if some Bytes start 1 or more UTF-8 Encodings of Chars"""

        closers = self.Tailbook

        for closer in closers:
            encode = kbytes + closer
            try:
                decode = encode.decode()
                assert len(decode) >= 1, (decode,)
                return decode
            except UnicodeDecodeError:
                continue

        return ""

    Tailbook = (b"\xbf", b"\x80\x80", b"\xbf\xbf", b"\x80\x80\x80", b"\xbf\xbf\xbf")

    #
    # for b"\xc2", b"\xed", b"\xe0", b"\xf4", b"\xf0", & friends
    # because =>
    #
    # "\u0000"  # b"\x00"
    # "\u007f"  # b"\x7f"
    #
    # "\u0080"  # b"\xc2\x80" accepted with b"\xc2\xbf", could be accepted as b"\xc2\x80"
    # "\u07ff"  # b"\xdf\xbf" ditto
    #
    # "\u0800"  # b"\xe0\xa0\x80" accepted with b"\xe0\xbf\xbf"
    # "\ud7ff"  # b"\xed\x9f\xbf" accepted with b"\xed\x80\x80"
    # "\ud800".."\udfff"  # rejected as b"\xed\xa0\x80" .. b"\xed\xbf\xbf" surrogates
    # "\ue000"  # b"\xee\x80\x80" accepted
    # "\uffff"  # b"\xef\xbf\xbf" accepted
    #
    # "\U00010000"  # b"\xf0\x90\x80\x80" accepted with "\xf0\xbf\xbf\xbf"
    # "\U0010ffff"  # b"\xf4\x8f\xbf\xbf" accepted with "\xf4\x80\x80\x80"
    #

    # todo: Invent UTF-8'ish Encoding beyond 1..4 Bytes for Unicode Codes > 0x10_FFFF ?

    def _take_some_sixem_if_(self, kbytes: bytes) -> bytes:
        """Take Bytes into a Csi Mouse Report of 6 Bytes or 6 Chars"""

        assert kbytes, (kbytes,)

        head = self.head
        assert head.startswith(b"\033[M"), (head,)  # ⎋[M Mouse Report

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
            return kbytes  # declines 1 Byte into 5 of 6 Chars or into 5 of 6 Bytes

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

        # Require Caller to route elsewhere the Csi Mouse Reports of 6 Bytes or 6 Chars

        assert not head.startswith(b"\033[M"), (head,)  # 6-Char Mouse Report

        # Mark as Printable Char or not

        printable = False
        if decodes:
            assert len(decodes) == 1, (decodes, kbytes)
            printable = decodes.isprintable()  # U+0020..U+007E, U+00A1..U+00AC, U+00AE..U+00FF, etc

            # Require Caller to route elsewhere the Printable Chars till Head chosen

            assert head or not printable, (decodes, kbytes, head, printable)

        # Accept the Bytes of any Head of the Headbook, without closing the Pack

        headbook = (b"\033", b"\033\033", b"\033\033O", b"\033\033[", b"\033O", b"\033[", b"\033]")
        assert KeyPack.Headbook == headbook

        head_plus = bytes(head + kbytes)
        if head_plus in headbook:
            head.extend(kbytes)
            return b""  # takes first 1 or 2 or 3 Bytes into Esc Sequences, without closing

        # Take & close 1 Unprintable Char or 1..4 Undecodable Bytes as an Alt Head

        if not head:
            if not printable:
                head.extend(kbytes)
                self.closed = True
                return b""  # takes & closes Unprintable Chars or 1..4 Undecodable Bytes

            # takes \b \t \n \r \x7f etc

        # Take & close 1 Printable Char escaped by a Head simpler than Csi, Esc Csi, and Osc

        bytes_head = bytes(head)
        if bytes_head in (b"\033", b"\033\033", b"\033\033O", b"\033O"):
            if printable:
                tail.extend(kbytes)
                self.closed = True
                return b""  # takes & closes 1 Escaped Printable Char

            # Take & close 1 Unprintable Char or 1..4 Undecodable Bytes escaped by a Simpler Head

            tail.extend(kbytes)  # todo: More test of Unprintable/ Undecodable Tails after ⎋O or ⎋⎋O
            self.closed = True
            return b""  # takes & closes Unprintable Chars or 1..4 Undecodable Bytes

            # does take ⎋\x10 ⎋\b ⎋\t ⎋\n ⎋\r ⎋\x7f etc

            # doesn't take bytes([0x80 | 0x0B]) as meaning b"\033\x5b" Csi ⎋[
            # doesn't take bytes([0x80 | 0x0F]) as meaning b"\033\x4f" Ss3 ⎋O

        # Decline 1..4 Undecodable Bytes, when escaped by Csi or Esc Csi or Osc

        if not decodes:
            return kbytes  # declines 1..4 Undecodable Bytes

        decode = decodes
        assert len(decodes) == 1, (decodes, kbytes)
        assert kbytes == decode.encode(), (kbytes, decodes)

        # Take or don't take 1 Decodable Char escaped by Csi or Esc Csi

        if bytes_head in (b"\033[", b"\033\033["):
            esc_csi_beyond = self._take_one_esc_csi_if_(decode)
            return esc_csi_beyond  # maybe empty

        # Take or don't take 1 Decodable Char escaped by Osc

        assert bytes_head == b"\033]", (bytes_head,)

        osc_beyond = self._take_one_osc_if_(decode)
        return osc_beyond  # maybe empty

    def _take_one_esc_csi_if_(self, decode: str) -> bytes:
        """Take 1 Char into Csi or Esc Csi Sequence, else return 1..4 Bytes that don't fit"""

        assert len(decode) == 1, decode
        code = ord(decode)
        encode = decode.encode()

        head = self.head
        neck = self.neck
        back = self.back
        tail = self.tail
        closed = self.closed

        # Look only at unclosed Csi or Esc Csi Sequence

        assert CSI == "\033[", (CSI,)  # ⎋[
        assert bytes(head) in (b"\033[", b"\033\033["), (bytes(head),)

        assert not tail, (tail,)
        assert not closed, (closed,)

        # Decline 1..4 Bytes of Unprintable or Multi-Byte Char

        if not (0x20 <= code <= 0x7F):
            return encode  # declines 2..4 Bytes of 1 Unprintable or Multi-Byte Char

            # todo: More test of Unprintable/ Undecodable Tails after ⎋[ or ⎋⎋[

        # Accept 1 Byte into Back, into Neck, or as Tail

        assert CSI_P_CHARS == "0123456789:;<=>?"
        assert CSI_I_CHARS == """ !'#$%&'()*+,-./"""
        assert CSI_F_CHARS == "@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~"

        if not back:
            if 0x30 <= code < 0x40:  # 16 Codes  # 0123456789:;<=>?
                neck.extend(encode)
                return b""  # takes 1 of 16 Parameter Byte Codes

        if 0x20 <= code < 0x30:  # 16 Codes  # Spacebar !"#$%&\'()*+,-./
            back.extend(encode)
            return b""  # takes 1 of 16 Intermediate Byte Codes

        if 0x40 <= code < 0x7F:  # 63 Codes  # @A Z[\\]^_`a z{|}~
            assert not tail, (tail,)
            tail.extend(encode)
            self.closed = True
            return b""  # takes 1 of 63 Final Byte Codes

        # Decline 1 Byte of Unprintable Char

        return encode  # declines 1 Byte <= b"\x7f" of Unprintable Char

        # splits '⎋[200~' and '⎋[201~' away from enclosed Bracketed Paste

        # todo: Limit the length of a Csi Escape Sequence

    def _take_one_osc_if_(self, decode: str) -> bytes:
        """Take 1 Char into Osc Sequence, else return 1..4 Bytes that don't fit"""

        assert len(decode) == 1, decode
        code = ord(decode)
        encode = decode.encode()

        head = self.head
        neck = self.neck
        back = self.back
        tail = self.tail
        closed = self.closed

        # Look only at unclosed Osc Sequence

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
class KeyByte:
    """Mirror one Os Read of one Byte, or zero Bytes, from a Terminal Keyboard"""

    t0: int  # time of Call
    kbytes: bytes  # empty at timeout, else 1 Byte
    t1: int  # time of Return


BEL = "\a"  # U+0007 Bell
CR = "\r"  # U+000D Carriage Return
ESC = "\033"  # U+001B Escape

SS3 = "\033O"  # 01/11 04/15 Single Shift Three
CSI = "\033["  # 01/11 05/11 Control Sequence Introducer
OSC = "\033]"  # 01/11 05/13 Operating System Command
ST = "\033\134"  # 05/11 05/12 String Terminator

CUP_Y_X = "\033[" "{};{}H"  # Csi 04/08 [Choose] Cursor Position

DCH_X = "\033[" "{}" "P"  # Csi 05/00 Delete Character


DSR_5 = "\033[" "5n"  # Csi 06/14 [Request] Device Status Report  # Ps 5 Request DSR_0
DSR_0 = "\033[" "0n"  # Csi 06/14 [Response] Device Status Report  # Ps 0 Response Ready

DSR_6 = "\033[" "6n"  # Csi 06/14 [Request] Device Status Report  # Ps 6 Request CPR
CPR_Y_X = "\033[" "{};{}R"  # Csi 05/02 [Response] Active [Cursor] Pos Rep

XTWINOPS_18 = "\033[" "18t"  # Csi 07/04 [Request] XTWINOPS_18
XTWINOPS_8_H_W = "\033[" "8;{};{}t"  # Csi 07/04 [Response] XTWINOPS_8


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
