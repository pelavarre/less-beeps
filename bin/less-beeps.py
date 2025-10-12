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
import re
import select  # for select.select
import signal
import sys
import termios  # for termios.TCSADRAIN
import textwrap
import time
import tty  # for tty.setraw and tty.setcbreak
import types
import typing
import unicodedata


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
        ts.launch_quickly()
        ts.run_awhile()


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

    mock_screen: MockScreen
    mock_keyboard: MockKeyboard

    def __init__(self) -> None:
        terminal_studios.append(self)

        ms = MockScreen(self)
        mk = MockKeyboard(self, mock_screen=ms)

        self.mock_screen = ms
        self.mock_keyboard = mk

    def __enter__(self) -> "TerminalStudio":
        return self

    def __exit__(self, *args: object) -> None:
        pass

    def launch_quickly(self) -> None:
        """Launch quickly"""

        print("⌃D to quit,  Fn F1 for more help,  or ⌥-Click far from the Cursor")

    def run_awhile(self) -> None:
        """Run till quit, inside the Terminal"""

        while True:
            kk = self.take_input()
            self.give_reply(kk)
            sys.exit()

    def take_input(self) -> KeyboardKhord:
        """Read one Keyboard Chord"""

        mk = self.mock_keyboard
        kk = mk.read_keyboard_khord(timeout=None)

        return kk

    def give_reply(self, kk: KeyboardKhord) -> None:
        """Reply to one Keyboard Chord"""

        print(kk)


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

    def __init__(self, terminal_studio: TerminalStudio, mock_screen: MockScreen) -> None:
        self.terminal_studio = terminal_studio
        self.mock_screen = mock_screen
        self.mock_keyboard = self

    def read_keyboard_khord(self, timeout: float | None) -> KeyboardKhord:
        """Read one Keyboard Chord"""

        kk = KeyboardKhord(
            kface="Return", kcaps="⌃M", kpack=KeyboardPack(b"\r"), kintsmark=b"", kints=list()
        )

        return kk


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
        rep = f"{neg}{concise}"
    elif eng <= 0:
        rep = f"{neg}{concise}e{eng}{unit}"
    else:
        rep = f"{neg}{concise}e+{eng}{unit}"

    return rep


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
    """Run at Process Exit, when not bypassed by raising SystemExit"""

    assert exc_type is not SystemExit, (exc_type,)

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
    """Mirror one Tap or Click or Keyboard Input"""

    kface: str  # 'Return'
    kcaps: str  # '⌃M'
    kpack: KeyboardPack  # .head .neck .back .stash .tail
    kintsmark: bytes  # neck-start + back + tail
    kints: list[int]  # via Csi Neck after Csi Next Start


@dataclasses.dataclass(order=True)  # , frozen=True)
class KeyboardPack:
    """Mirror one whole Os Read from a Terminal Keyboard"""

    Headbook = (b"\033", b"\033\033", b"\033\033O", b"\033\033[", b"\033O", b"\033[", b"\033]")

    text: str  # 0 or more Chars of Printable Text, mutates as the Pack grows

    head: bytearray  # 1 Leading Bytes, starts with Control Byte, from the .Headbook or not
    neck: bytearray  # CSI Parameter Bytes, in 0x30..0x3F (16 Codes)  # ...... 0123456789:;<=>?
    back: bytearray  # CSI Intermediate Bytes, in 0x20..0x2F (16 Codes)  # .... !"#$%&'()*+,-./
    stash: bytearray  # 1..3 Bytes taken for now, in hope of decoding 2..4 Later
    tail: bytearray  # CSI Final Byte, in 0x40..0x7E (63 Codes)

    closed: bool = False  # closed because completed, or because continuation undefined

    # except the .text .head .back .back .stash .tail start empty, and may be left empty

    def __init__(self, kbytes: bytes) -> None:

        # Form an empty Self

        self.text = ""

        self.head = bytearray()
        self.neck = bytearray()
        self.back = bytearray()
        self.stash = bytearray()
        self.tail = bytearray()

        self.closed = False

        # Add in the .kbytes

        assert kbytes == b"\r", (kbytes,)
        self.head.extend(kbytes)


@dataclasses.dataclass(order=True)  # , frozen=True)
class KeyboardByte:
    """Mirror one Os Read of one Byte, or zero Bytes, from a Terminal Keyboard"""

    t0: int  # time of Call
    kbytes: bytes  # empty at timeout, else 1 Byte
    t1: int  # time of Return


#
# Amp up Import ArgParse
#


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
