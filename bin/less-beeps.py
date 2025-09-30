#!/usr/bin/env python3

r"""
usage: less-beeps.py [-h] [--yolo]

give away nine classic simple Terminal games

options:
  -h, --help  show this help message and exit
  --yolo      do what's popular now

examples:
  ./bin/less-beeps.py --yolo
"""

# code reviewed by People, Black, Flake8, Mypy-Strict, & Pylance-Standard


from __future__ import annotations  # backports new datatype syntaxes into old Pythons

import __main__
import argparse
import bdb
import collections
import dataclasses
import difflib
import math
import os
import pdb
import re
import select
import signal
import sys
import termios
import textwrap
import time
import tty
import types
import typing
import unicodedata


if not __debug__:
    raise NotImplementedError([__debug__])  # 'python3' better than 'python3 -O'

default_eq_None = None

_: object


#
# Fit to Caller
#


class flags:

    apple = sys.platform == "darwin"
    google = bool(os.environ.get("CLOUD_SHELL", default_eq_None))
    iterm2 = os.environ.get("TERM_PROGRAM", default_eq_None) == "iTerm.app"

    phone = False


#
# Run from the Shell Command Line
#


def main() -> None:
    """Run from the Shell Command Line, and launch the Py Repl vs uncaught Exceptions"""

    sys.excepthook = excepthook

    # Fit to Caller some more  # todo3: Make visible our autofit to Phone

    phone = False
    try:
        (x_width, y_height) = os.get_terminal_size()
        if x_width < 72:
            phone = True
    except Exception:
        pass

    flags.phone = phone

    # Launch some Self-Test's, or don't

    testing = False
    if testing:
        t0 = time.time()
        TerminalBytePacket(b"")._try_terminal_byte_pack_()
        t1 = time.time()
        print(t1 - t0)  # 233us

    # Launch

    mc = MainClass()
    mc.main_class_run()


main_instances: list[MainClass] = list()


@dataclasses.dataclass(order=True)  # , frozen=True)
class MainClass:
    """Run from the Shell Command Line, and launch the Py Repl vs uncaught Exceptions"""

    _touch_terminal_: TouchTerminal | None = None

    @property
    def touch_terminal(self) -> TouchTerminal:
        tt = self._touch_terminal_
        assert tt, (tt,)
        assert tt is touch_terminals[-1], (tt, touch_terminals)
        return tt

    def __init__(self) -> None:
        main_instances.append(self)

    #
    #
    #

    def main_class_run(self) -> None:
        """Run from the Shell Command Line, and launch the Py Repl vs uncaught Exceptions"""

        # Take in the Shell Command-Line Args

        ns = self.parse_less_beeps_args()
        assert ns.yolo, (ns.yolo, ns)  # todo1: Declare more Options

        # Launch

        print("⌃D to quit,  Fn F1 for more help,  or ⌥-Click far from the Cursor")

        # Run till quit, inside a Terminal

        with TerminalStudio() as ts:
            tt = self._touch_terminal_ = ts.touch_terminal  # replaces
            while True:
                (kcaps, kbytes) = tt.read_key_caps(timeout=None)
                if kcaps:
                    ts.kcaps_exec(kcaps, kbytes=kbytes)

    #
    # Take Input, edit it, and write it back out
    #

    def try_loopback(self) -> None:  # noqa: C901 complex  # todo3:
        """Take Input as Touch Tap, as Mouse Click, or as Keyboard Chord, till Quit"""

        # Run inside a Terminal, till Quit

        with TouchTerminal() as tt:  # todo2: small With bodies - move out into Classes
            self._touch_terminal_ = tt  # replaces

            stdio = tt.stdio
            fileno = stdio.fileno()

            # Ask for Height, Width, Cursor Y, Cursor X, and then also some other Input

            backtails = list()
            while True:

                if b"t" not in backtails:
                    stdio.write("\033[18t")  # ⎋[18T call for reply ⎋[8;{rows};{columns}T
                    backtails.append(b"t")

                if b"R" not in backtails:
                    stdio.write("\033[6n")  # ⎋[6N calls for reply ⎋[{y};{x}⇧R
                    backtails.append(b"R")

                assert b"" not in backtails, (backtails,)
                backtails.append(b"")  # waits for whatever other reply

                # Take Inputs in whatever order  # todo: Log if Input ever comes out of order

                (kcaps, kbytes) = ("", b"")
                while backtails:

                    # Hang invisibly while Multibyte Sequences arrive slowly  # todo3: Do better

                    (kpair_kcaps, kpair_kbytes) = tt.read_key_caps(timeout=None)
                    if not kpair_kcaps:
                        continue

                    # Take Csi Inputs

                    if kpair_kcaps.startswith("⎋["):
                        kpacket = TerminalBytePacket(kpair_kbytes)

                        if kpair_kbytes == b"\033[M":  # todo3: Packet Constructor option?
                            ok = kpacket.close_if_csi_shift_m()
                            assert ok, (ok, kpacket, kpair_kbytes)

                        backtail = bytes(kpacket.back + kpacket.tail)
                        if backtail and (backtail in backtails):
                            ints = kpacket.to_csi_ints_if(backtail, start=b"", default=-1)
                            if ints:

                                backtails.remove(backtail)

                                continue

                    # Take Input other than the first Height, Width, Cursor Y, Cursor X

                    if b"" in backtails:
                        backtails.remove(b"")

                        (kcaps, kbytes) = (kpair_kcaps, kpair_kbytes)

                        break

                # Convert Single-Byte Control Inputs

                if kbytes == b"\r":
                    if tt.paste_y != -1:
                        tt.write_paste_crlf()
                        continue

                # Convert Csi Inputs

                if kcaps.startswith("⎋["):
                    kpacket = TerminalBytePacket(kbytes)  # todo3: redundant work

                    # Convert Mouse ⌥-Click Release to Csi, or Mouse Click Release to Csi

                    m_ints = kpacket.to_csi_ints_if(b"m", start=b"<", default=-1)
                    if len(m_ints) == 3:
                        (f, x, y) = m_ints  # f x y, not f y x

                        f0 = 0  # none of ⌃ ⌥ ⇧
                        f8 = int("0b01000", base=0)  # f = ⌥ of 0b⌃⌥⇧00
                        if f in (f0, f8):  # Click or ⌥-Click
                            stdio.write(f"\033[{y};{x}H")  # no bounds caps on Mouse Click or ⌥-Click
                            continue

                # Loop Input Bytes back, no matter if well known

                stdio.flush()  # before each 'os.write'

                fd = fileno
                data = kbytes
                os.write(fd, data)

                # Quit on demand

                if kcaps in ("⌃C", "⌃D", "⌃Z", "⌃\\"):
                    sys.exit()

    #
    # Take Input as Touch Tap, as Mouse Click, or as Keyboard Chord, till Quit
    #

    def try_key_caps(self) -> None:
        """Take Input as Touch Tap, as Mouse Click, or as Keyboard Chord, till Quit"""

        # Run inside a Terminal, till Quit

        with TouchTerminal() as tt:  # todo2: small With bodies
            self._touch_terminal_ = tt  # replaces

            stdio = tt.stdio

            # As late as now, trace the Writes of TouchTerminal.__enter__

            kcaps_list = list()
            for entry_data in tt.entries:
                kcaps = kbytes_to_precise_kcaps(entry_data)
                kcaps_list.append(kcaps)

            tprint()
            tprint("Setup:", " ".join(kcaps_list))

            # Launch a wide Ruler

            tprint()
            tprint(30 * "123456789 ")

            # Launch a fetch of Terminal Width x Height

            tprint()
            tprint("⎋[18T")
            tt.stdio.write("\033[18t")  # the ⎋[18 T Call
            while True:
                (kcaps, kbytes) = tt.read_key_caps(timeout=None)
                if kcaps:
                    break
            self.kbytes_tprint_some(kcaps, kbytes=kbytes)  # the ⎋[8 T Reply

            # Launch a fetch of Terminal Cursor Y X

            tprint()
            tprint("⎋[6N")
            tt.stdio.write("\033[6n")  # the ⎋[ 6N Call
            while True:
                (kcaps, kbytes) = tt.read_key_caps(timeout=None)
                if kcaps:
                    break
            self.kbytes_tprint_some(kcaps, kbytes=kbytes)  # the ⎋[ ⇧R reply

            # Run till quit

            tprint()
            tt.row_y = min(tt.y_height, tt.row_y + 1)
            while True:

                # Prompt

                if tt.column_x == X1:
                    text = f"{tt.row_y};{tt.column_x}"
                    tprint(text, end=" ")
                    tt.column_x += len(text + " ")

                # Flush and read, but trace each Byte as it comes

                stdio.flush()
                (kcaps, kbytes) = tt.read_key_caps(timeout=None)
                assert kbytes, (kbytes, kcaps)

                kbyte = kbytes[-1:]
                self.kbyte_tprint_one(kbyte)

                if not kcaps:
                    assert kbytes == kbyte, (kbytes, kbyte, kcaps)

                    continue

                # Trace the Key Caps, as they come

                self.kbytes_tprint_some(kcaps, kbytes=kbytes)

                # Quit on demand

                if kcaps in ("⌃C", "⌃D", "⌃Z", "⌃\\"):
                    sys.exit()

    def kbyte_tprint_one(self, kbyte: bytes) -> int:
        """Print each Byte, as they come"""

        try:

            precise = kbytes_to_precise_kcaps(kbyte)
            tprint(precise, end=" ")
            dx = len(str(precise) + " ")

        except UnicodeDecodeError:

            tprint(kbyte, end=" ")
            dx = len(str(kbyte) + " ")

        return dx

    def kbytes_tprint_some(self, kcaps: str, kbytes: bytes) -> None:
        """Print each Key Caps Text, as they come"""

        tt = self.touch_terminal

        burst_kbytes = tt._arrow_burst_kbytes_as_if_
        if (not burst_kbytes) or (kbytes == burst_kbytes):
            tprint(">", kcaps, kbytes)
        else:
            tprint(">", kcaps, kbytes, burst_kbytes)
            tt._arrow_burst_kbytes_as_if_ = b""

        if -1 not in (tt.y_height, tt.row_y, tt.column_x):
            tt.row_y = min(tt.y_height, tt.row_y + 1)
            tt.column_x = X1

    #
    # Say what we got for Input, if Keyboard Chord, if Arrow Burst, and how long we waited
    #

    def try_byte_times(self) -> None:
        """Say what we got for Input, if Keyboard Chord, if Arrow Burst, and how long we waited"""

        # Take in the Shell Command-Line Args

        ns = self.parse_less_beeps_args()
        assert ns.yolo, (ns.yolo, ns)

        # Run till quit

        with TouchTerminal() as tt:  # todo2: small With bodies - move out into Classes

            # As late as now, trace the Writes of TouchTerminal.__enter__

            kcaps_list = list()
            for entry_data in tt.entries:
                kcaps = kbytes_to_precise_kcaps(entry_data)
                kcaps_list.append(kcaps)

            tprint()
            tprint("Setup:", " ".join(kcaps_list))

            # Launch a wide Ruler

            tprint()
            tprint(30 * "123456789 ")

            # Launch a fetch of Terminal Width x Height

            tprint()
            tprint("⎋[18T")
            tt.stdio.write("\033[18t")  # ⎋[18T call for reply ⎋[8;{rows};{columns}T
            tp = tt.read_terminal_poke(timeout=None)
            rep = tp.to_sketch_text()  # the ⎋[8 T reply
            tprint(rep)

            # Launch a fetch of Terminal Cursor Y X

            tprint()
            tprint("⎋[6N")
            tt.stdio.write("\033[6n")  # ⎋[6N calls for reply ⎋[{y};{x}⇧R
            tp = tt.read_terminal_poke(timeout=None)
            rep = tp.to_sketch_text()  # the ⎋[ ⇧R reply
            tprint(rep)

            # Run till Quit

            while True:

                tt.stdio.flush()
                tp = tt.read_terminal_poke(timeout=None)
                reads_plus = (tp.reads + (tp.extra,)) if tp.extra else tp.reads

                breaking = False
                for read in reads_plus:
                    precise = kbytes_to_precise_kcaps(read)
                    if precise in ("⌃C", "⌃D", "⌃Z", "⌃\\"):
                        breaking = True

                rep = tp.to_sketch_text()
                tprint(rep)  # could be repr(tp) or str(tp)

                if breaking:
                    break

                # quits at Cat ⌃C ⌃D ⌃Z ⌃\
                # todo1: Quit at Emacs ⌃X ⌃C, ⌃X ⌃S
                # todo1: Quit at Vim ⇧Z ⇧Q, ⇧Z ⇧Z

            # todo3: Decipher ⌥-Click encoding at Google Cloud Shell

    #
    #
    #

    def parse_less_beeps_args(self) -> argparse.Namespace:
        """Take in the Shell Command-Line Args"""

        parser = self.compile_less_beeps_doc()

        argv = sys.argv[1:]
        if not argv:
            if os.path.basename(sys.argv[0]) in ("+", "@"):
                argv = ["--yolo"]

        ns = parser.parse_args_if(argv)

        return ns

    def compile_less_beeps_doc(self) -> ArgDocParser:
        """Declare the Options & Positional Arguments"""

        doc = __main__.__doc__
        assert doc, (doc,)

        parser = ArgDocParser(doc, add_help=True)

        yolo_help = "do what's popular now"
        parser.add_argument("--yolo", action="count", help=yolo_help)

        return parser


#
#
#


# todo3: rewrite screen
# todo3: Route .tprint's through last TouchTerminal if it exists
# todo3: Primarily mirror, but also update the Hardware if it overlaps, like track Y X in projection
# todo3: Left Arrow wraps inside of a Line wrapped across Multiple Rows (Right Arrow doesn't)


class TerminalStudio:
    """Run inside a Terminal, till Quit"""

    def __init__(self) -> None:

        self.touch_terminal = TouchTerminal()

    def __enter__(self) -> typing.Self:
        tt = self.touch_terminal
        tt.__enter__()
        return self

    def __exit__(self, *exc_info: object) -> None:
        tt = self.touch_terminal
        tt.__exit__(*exc_info)

    def kcaps_exec(self, kcaps: str, kbytes: bytes) -> None:

        mc = main_instances[-1]

        if kcaps == "F1":
            tprint()
            tprint("⌃D to quit")
            tprint("F1 - Show this menu")
            tprint("⎋F1 - Show a menu of tests to run")
            return

        if kcaps == "⎋F1":
            tprint()
            tprint("⌃D to quit")
            tprint("⎋F1 - Show this menu")
            tprint("⎋F2 - Trace the Timing of Bytes of Input")
            tprint("⎋F3 - Trace the Key Caps of Input")
            tprint("⎋F4 - Loopback the Bytes of Input")
            return

        if kcaps == "⎋F2":
            mc.try_byte_times()
            sys.exit()  # todo1: stop exiting after ⎋F2

        if kcaps == "⎋F3":
            mc.try_key_caps()
            sys.exit()  # todo1: stop exiting after ⎋F3

        if kcaps == "⎋F4":
            tprint("⎋F4")
            mc.try_loopback()
            sys.exit()  # todo1: stop exiting after ⎋F4

        if kcaps in ("⌃C", "⌃D", "⌃Z", "⌃\\"):
            sys.exit()

        # tprint(kbytes.decode(), end="")
        tprint(kcaps, end=" ")


#
# Amp up Import ArgParse
#


_ARGPARSE_3_10_ = (3, 10)  # Ubuntu 2022 Oct/2021 Python 3.10


class ArgDocParser:
    """Scrape out Prog & Description & Epilog from Doc to form an Argument Parser"""

    doc: str  # a copy of parser.format_help()
    add_help: bool  # truthy to define '-h, --help', else not

    parser: argparse.ArgumentParser  # the inner standard ArgumentParser
    text: str  # something like the __main__.__doc__, but dedented and stripped
    closing: str  # the last Graf of the Epilog, minus its Top Line

    add_argument: typing.Callable[..., object]

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
        # Fetch from a Black Terminal of 89 columns, not from the current Terminal width
        # Fetch from later Python of "options:", not earlier Python of "optional arguments:"

        if "COLUMNS" not in os.environ:

            os.environ["COLUMNS"] = str(89)  # adds
            try:
                b_text = parser.format_help()
            finally:
                del os.environ["COLUMNS"]  # removes

        else:

            with_columns = os.environ["COLUMNS"]  # backs up
            os.environ["COLUMNS"] = str(89)  # replaces
            try:
                b_text = parser.format_help()
            finally:
                os.environ["COLUMNS"] = with_columns  # restores

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


def sketch(f: float, near: float) -> str:
    """Format F as '0', else as 2 or 3 digits with a metric exponent, but not the exponent of near"""

    if f == 0:
        return "0"  # 0

    neg = "-" if (f < 0) else ""  # omits '+' at left
    abs_ = abs(f)

    sci = math.floor(math.log10(abs_))
    eng = (sci // 3) * 3
    precise = abs_ / (10**eng)
    assert 1 <= precise <= 1000, (precise, abs_, eng, f)  # todo: Log if '== 1000' ever happens

    dotted = round(precise, 1)  # 1.0  # 9.9  # 10.0
    assert 1.0 <= dotted <= 1000.0, (dotted, abs_, eng, f)

    concise = dotted
    if concise >= 10:
        concise = round(precise)  # 10  # 1000
        assert 10 <= concise <= 1000, (concise, abs_, eng, f)

    log10_near = int(math.log10(near))
    if eng == log10_near:
        rep = f"{neg}{concise}"
    else:
        rep = f"{neg}{concise}e{eng}"  # sends 'e+' as 'e', sends 'e0' as 'e0'

    return rep


#
# Amp up Import Termios
#


# Name some Magic Numbers

Immediately = 0.000_001

Y1 = 1  # indexes Y Rows as Southbound across 1 .. Height
X1 = 1  # indexes X Columns as Eastbound across 1 .. Width

PN1 = 1  # min Pn of Csi is 1
PN_MAX_32100 = 32100  # a Numeric [Int] beyond the Counts of Rows & Columns at any Real Terminal

PS0 = 0  # min Ps of Csi is 0


touch_terminals = list()


class TouchTerminal:
    """Write/ Read Bytes at Screen/ Keyboard/ Click/ Tap of the Terminal"""

    stdio: typing.TextIO  # for writes to Screen by 'print(file='
    fileno: int  # for reads from Keyboard by 'os.read'

    before: int  # for writing at Entry
    tcgetattr: list[int | list[bytes | int]]  # replaced by Entry
    entries: list[bytes]  # for writes at Entry
    exits: list[bytes]  # for writes at Exit
    after: int  # for writing at Exit  # todo1: Prefer .TCSAFLUSH vs large mess of Paste

    kbytearray: bytearray  # cleared then formed by .read_key_caps_plus and .getch
    _kpacket_: TerminalBytePacket  # cleared then formed by .read_key_caps_plus

    y_height: int  # Terminal Screen Pane Rows, else -1
    x__width: int  # Terminal Screen Pane Columns, else -1
    row_y: int  # Terminal Cursor Y Row, else -1
    column_x: int  # Terminal Cursor X Column, else -1
    paste_y: int  # Bracketed Paste Cursor Y Row, else -1
    paste_x: int  # Bracketed Paste Cursor X Column, else -1

    _arrow_burst_kbytes_as_if_: bytes  # from .to_mouse_key_caps_if_start

    #
    # Init, enter, exit, and poll
    #

    def __init__(self) -> None:

        touch_terminals.append(self)

        assert sys.__stderr__ is not None
        stdio = sys.__stderr__

        self.stdio = stdio
        self.fileno = stdio.fileno()

        self.before = termios.TCSADRAIN
        self.tcgetattr = list()
        self.entries = list()
        self.exits = list()
        self.after = termios.TCSADRAIN

        self.kbytearray = bytearray()
        self._kpacket_ = TerminalBytePacket(b"")

        self.y_height = -1
        self.x_width = -1
        self.row_y = -1
        self.column_x = -1
        self.paste_y = -1
        self.paste_x = -1

        self._arrow_burst_kbytes_as_if_ = b""

    def __enter__(self) -> typing.Self:
        r"""Stop line-buffering Input, stop replacing \n Output with \r\n, etc"""

        stdio = self.stdio
        fileno = self.fileno
        before = self.before
        entries = self.entries
        tcgetattr = self.tcgetattr
        exits = self.exits

        if tcgetattr:
            return self

        tcgetattr = termios.tcgetattr(fileno)  # replaces
        assert tcgetattr, (tcgetattr,)

        self.tcgetattr = tcgetattr  # replaces

        assert before in (termios.TCSADRAIN, termios.TCSAFLUSH), (before,)
        tty.setraw(fileno, when=before)  # Tty SetRaw defaults to TcsaFlush
        # tty.setcbreak(fileno, when=termios.TCSAFLUSH)  # for ⌃C prints Py Traceback

        entries.append(b"\033[?2004h")
        exits.append(b"\033[?2004l")

        if flags.phone:
            entries.append(b"\033[?1000;1006h")
            exits.append(b"\033[?1000;1006l")

        #

        stdio.flush()  # before each 'os.write'

        for entry_data in entries:
            fd = fileno
            data = entry_data

            os.write(fd, data)

        #

        return self

    def __exit__(self, *exc_info: object) -> None:
        r"""Start line-buffering Input, start replacing \n Output with \r\n, etc"""

        stdio = self.stdio
        fileno = self.fileno
        tcgetattr = self.tcgetattr
        exits = self.exits
        after = self.after

        if not tcgetattr:
            return

        #

        stdio.flush()  # before each 'os.write'

        for exit_data in exits:
            fd = fileno
            data = exit_data

            os.write(fd, data)

        #

        self.tcgetattr = list()  # replaces

        stdio.flush()  # for '__exit__' of BytesTerminal

        assert after in (termios.TCSADRAIN, termios.TCSAFLUSH), (after,)

        fd = fileno
        when = after
        attributes = tcgetattr
        termios.tcsetattr(fd, when, attributes)

        return None

    def write_paste_crlf(self) -> None:
        """Break Paste Line at Cursor"""

        stdio = self.stdio
        y_height = self.y_height
        paste_y = self.paste_y
        paste_x = self.paste_x

        if paste_y < y_height:
            paste_y = paste_y + 1
        else:
            stdio.write("\n")

        stdio.write(f"\033[{paste_y};{paste_x}H")  # todo: stop writing y == y

        self.paste_y = paste_y

    def kbhit(self, timeout: float | None) -> bool:  # a la msvcrt.kbhit
        """Block till next Input Byte, else till Timeout, else till forever"""

        kbytearray = self.kbytearray
        if kbytearray:
            return True

        hit = self._kbhit_(timeout=timeout)

        return hit

    def _kbhit_(self, timeout: float | None) -> bool:  # a la msvcrt.kbhit
        """Block till next Input Byte, else till Timeout, else till forever"""

        fileno = self.fileno
        stdio = self.stdio
        tcgetattr = self.tcgetattr

        assert tcgetattr, (tcgetattr,)

        stdio.flush()  # for .kbhit of BytesTerminal

        (r, w, x) = select.select([fileno], [], [], timeout)
        fileno_hit = fileno in r

        return fileno_hit

        # 'timeout' is None for Never, 0 for Now, else a Float of Seconds

    #
    # Read from Keyboard, Mouse, and Touch
    #

    def read_key_caps(self, timeout: float | None) -> tuple[str, bytes]:  # noqa  # todo3: C901
        """Read one whole Input as Str, else just peek at the next Input Byte"""

        kbytearray = self.kbytearray
        _kpacket_ = self._kpacket_

        y_height = self.y_height
        x_width = self.x_width
        row_y = self.row_y
        column_x = self.column_x

        # Fetch more Bytes, when needed

        tp = TerminalPoke(hit=0, delays=tuple(), reads=tuple(), extra=b"")
        if not kbytearray:
            tp = self._fill_kbytearray_(timeout=timeout)
            if not kbytearray:
                return ("", b"")

            # Collapse each Arrow Burst down into a Mouse Release, if

            hwyx = (y_height, x_width, row_y, column_x)
            # hwyx = (-1, -1, -1, -1)
            if -1 not in hwyx:

                (mouse_ktext, mouse_kbytes) = tp.to_mouse_key_caps_if_start(hwyx)
                assert bool(mouse_ktext) == bool(mouse_kbytes), (mouse_ktext, mouse_kbytes, tp)

                if mouse_ktext and mouse_kbytes:
                    self._arrow_burst_kbytes_as_if_ = arrow_burst_kbytes_pn_compress(mouse_kbytes)

                    if len(mouse_kbytes) >= (4 * 3):  # if not a single Arrow
                        del kbytearray[: len(mouse_kbytes)]
                        kbytearray[0:0] = mouse_ktext.encode()

        poke_kbytes = bytes(kbytearray)
        poke_kbyte = bytes(kbytearray[:1])  # does peek, doesn't pop

        # Pass back the ⌥`` encoded as rapid ``

        if poke_kbytes == b"``":
            kbytearray.clear()

            concise = kbytes_to_concise_kcaps_if(poke_kbytes)
            assert concise == "⌥``", (concise, poke_kbytes)

            return (concise, poke_kbytes)

        # Pass back each of the early Bytes, one at a time
        # todo1: Think more about accepting more than ⎋ as a prefix for whatever

        headbook = (b"\033", b"\033\033", b"\033\033O", b"\033\033[", b"\033O", b"\033[")
        assert TerminalBytePacket.Headbook == headbook

        packet_kbytes = _kpacket_.to_bytes()  # maybe not .closed

        try:
            poke_decode_if = poke_kbytes.decode()
        except UnicodeDecodeError:
            poke_decode_if = ""

        closing_head = False
        if (not poke_decode_if) or (not poke_decode_if[:1].isprintable()):
            if packet_kbytes in headbook:
                if packet_kbytes != b"\033":  # ⎋
                    closing_head = True  # ⎋⎋ ⎋⎋O ⎋⎋[ ⎋O ⎋[

        if not closing_head:

            extra = _kpacket_.take_one_if(poke_kbyte)  # truthy at ⎋ [ ⇧! 9, etc
            packet_kbytes = _kpacket_.to_bytes()  # replaces  # maybe not .closed

            closing_tail = bool(_kpacket_.text or _kpacket_.closed or extra)

            if (packet_kbytes == b"\033[M") and (len(poke_kbytes) <= 1):  # ⎋[M
                ok = _kpacket_.close_if_csi_shift_m()
                assert ok, (ok, _kpacket_, packet_kbytes)
                closing_tail = True

            # if (packet_kbytes == b"\033\033") and (len(poke_kbytes) <= 1):  # ⎋⎋
            #     closing_tail = True

            if not closing_tail:
                kbytearray.pop(0)
                return ("", poke_kbyte)

            if not extra:  # pops if taken, else keeps inside .kbytearray when not taken
                kbytearray.pop(0)

        # Read, snoop, and clear one whole Packet

        self.snoop_packet()
        _kpacket_.clear_packet()

        # Pick out concise or precise Key Caps, and return them

        concise = kbytes_to_concise_kcaps_if(packet_kbytes)
        if concise:
            return (concise, packet_kbytes)

        precise = kbytes_to_precise_kcaps(packet_kbytes)
        return (precise, packet_kbytes)

    def snoop_packet(self) -> None:
        """Mirror updates to Height, Width, Y, and X, as they fly by"""

        _kpacket_ = self._kpacket_

        # Snoop ⎋[ ⇧R Cursor-Position-Report (CSR)

        yx_ints = _kpacket_.to_csi_ints_if(b"R", start=b"", default=PN1)  # ⎋[ ⇧R
        if len(yx_ints) == 2:
            self.row_y = yx_ints[0]
            self.column_x = yx_ints[-1]

        # Snoop ⎋[8 T Terminal Window Pane Height x Width Report

        nhw_ints = _kpacket_.to_csi_ints_if(b"t", start=b"", default=PN1)  # ⎋[8 T
        if len(nhw_ints) == 3:
            assert nhw_ints[0] == 8, (
                nhw_ints[0],
                nhw_ints,
            )
            self.y_height = nhw_ints[1]
            self.x_width = nhw_ints[2]

        # Snoop ⎋[200 ⎋[201 ⇧~ Start/ End of Bracketed Paste

        se_ints = _kpacket_.to_csi_ints_if(b"~", start=b"", default=PS0)  # ⎋[ ⇧~
        if len(se_ints) == 1:
            ps = se_ints[-1]

            assert -1 not in (self.row_y, self.column_x), (self.row_y, self.column_x)

            if ps == 200:
                self.paste_y = self.row_y
                self.paste_x = self.column_x

            if ps == 201:
                self.paste_y = -1
                self.paste_x = -1

    def getch(self, timeout: float | None) -> bytes:  # a la msvcrt.getch
        """Read next Byte of Keyboard Chord, Mouse Arrow Burst, Mouse Click, or Touch Tap"""

        kbytearray = self.kbytearray

        # Fetch more Bytes, when needed

        if not kbytearray:
            self._fill_kbytearray_(timeout=timeout)
            if not kbytearray:
                return b""

        # Pass back the first Byte

        kord = kbytearray.pop(0)
        kbytes = bytes([kord])

        return kbytes

    def _fill_kbytearray_(self, timeout: float | None) -> TerminalPoke:
        """Fetch Bytes into Self, and return their Timing and simple ⎋[0 N Closing separately"""

        kbytearray = self.kbytearray

        assert not kbytearray, (kbytearray,)

        tp = self.read_terminal_poke(timeout=timeout)
        kbytes = tp.to_kbytes()

        assert kbytes != b"\033[0n", (kbytes, tp)  # todo: Log if ⎋[0 N ever comes (as Paste?)

        if tp.reads and tp.reads[-1].endswith(b"\033[0n"):
            tp_reads_n1 = tp.reads[-1].removesuffix(b"\033[0n")
            tp_reads = tp.reads[:-1] + (tp_reads_n1,)

            tp = dataclasses.replace(tp, reads=tp_reads)
            kbytes = tp.to_kbytes()

        kbytearray.extend(kbytes)

        return tp

    def read_terminal_poke(self, timeout: float | None) -> TerminalPoke:
        """Read one Keyboard Chord, Mouse Arrow Burst, Mouse Click, or Touch Tap"""

        fileno = self.fileno
        stdio = self.stdio

        assert Immediately == 0.000_001

        # Flush Output, and wait for Input

        stdio.flush()

        t0 = time.time()
        kbhit = self._kbhit_(timeout=timeout)
        t1 = time.time()

        hit = t1 - t0
        if not kbhit:
            tp = TerminalPoke(hit=hit, delays=tuple(), reads=tuple(), extra=b"")
            return tp

        # Read Bursts of Bytes

        delay_list: list[float] = list()
        read_list: list[bytes] = list()
        extra: bytes = b""

        t = t1
        m = None
        while not m:

            fd = fileno
            length = 1

            read = os.read(fd, length)
            read_plus = read

            while self._kbhit_(timeout=0.000_001):
                read = os.read(fd, length)
                read_plus += read

            t2 = time.time()

            # Exactly once, write the ⎋[5 N Call for the ⎋[0 N Reply to close Input
            # Take quick and slow Inputs till the closing ⎋[0 N Reply does arrive

            read = read_plus
            if not read_list:
                stdio.write("\033[5n")  # todo: Try calling for different Replies to close Input
                stdio.flush()  # todo: Don't call for Reply to close Text, except to close the ` of ⌥``
            else:
                m = re.search(rb"\033\[0n", string=read_plus)
                if m:
                    extra = read_plus[m.end() :]
                    read = read_plus[: m.end()]

                    # todo: Stop finding ⎋[0 N Closing Reply out of context

            delay_list.append(t2 - t)
            read_list.append(read)
            t = t2

        #

        kbytes = b"".join(read_list)
        if kbytes == b"``" b"\033[0n":
            assert len(read_list) >= 2, (read_list,)
            read_list[::] = (b"``", b"\033[0n")
            delay_list[::] = (sum(delay_list[:1]), delay_list[-1])

        # Succeed

        reads = tuple(read_list)
        delays = tuple(delay_list)

        tp = TerminalPoke(hit=hit, delays=delays, reads=reads, extra=extra)

        return tp


class TerminalBytePacket:
    """Hold 1 Control Char, else 1 or more Text Chars, else some Bytes"""

    text: str  # 0 or more Chars of Printable Text

    head: bytearray  # 1 Control Byte, else ⎋[, or ⎋O, or 3..6 Bytes starting with ⎋[M
    neck: bytearray  # CSI Parameter Bytes, in 0x30..0x3F (16 Codes)  # ...... 0123456789:;<=>?
    back: bytearray  # CSI Intermediate Bytes, in 0x20..0x2F (16 Codes)  # .... !"#$%&'()*+,-./

    stash: bytearray  # 1..3 Bytes taken for now, in hope of decoding 2..4 Later
    tail: bytearray  # CSI Final Byte, in 0x40..0x7E (63 Codes)

    closed: bool = False  # closed because completed, or because continuation undefined

    Headbook = (b"\033", b"\033\033", b"\033\033O", b"\033\033[", b"\033O", b"\033[")

    #
    # Init, Bool, Repr, Str, and .require_simple to check invariants
    #

    def __init__(self, data: bytes) -> None:
        self._refill_packet_(data)

    def clear_packet(self) -> None:
        """Clear Self, but leave it open to taking in Bytes"""

        self._refill_packet_(b"")

    def _refill_packet_(self, data: bytes) -> None:
        """Clear Self, and then take in the Bytes, but require that they all fit"""

        self.text = ""

        self.head = bytearray()
        self.neck = bytearray()
        self.back = bytearray()

        self.stash = bytearray()
        self.tail = bytearray()

        self.closed = False

        self._require_simple_()  # does let the initial .data be empty

        # Take in the Bytes, but require that they all fit

        extras = self.take_some_if(data)
        if extras:
            raise ValueError(extras, data)  # for example, raises the b'\x80' of b'\xc0\x80'

        self._require_simple_()

        # doesn't take bytes([0x80 | 0x0B]) as meaning b"\033\x5b" CSI ⎋[
        # doesn't take bytes([0x80 | 0x0F]) as meaning b"\033\x4f" SS3 ⎋O

    def __bool__(self) -> bool:
        truthy = bool(
            self.text or (self.head or self.neck or self.back) or (self.stash or self.tail)
        )
        return truthy  # no matter if .closed

    def __repr__(self) -> str:

        cname = self.__class__.__name__

        text = self.text

        head_ = bytes(self.head)  # reps bytearray(b'') loosely, as b''
        neck_ = bytes(self.neck)
        back_ = bytes(self.back)

        stash_ = bytes(self.stash)
        tail_ = bytes(self.tail)

        closed = self.closed

        s = f"text={text!r}, "
        s += f"head={head_!r}, neck={neck_!r}, back={back_!r}, stash={stash_!r}, tail={tail_!r}"
        s = f"{cname}({s}, {closed=})"

        return s

        # 'TerminalBytePacket(head=b'', back=b'', neck=b'', stash=b'', tail=b'', closed=False)'

    def __str__(self) -> str:

        text = self.text

        head_ = bytes(self.head)  # reps bytearray(b'') loosely, as b''
        neck_ = bytes(self.neck)
        back_ = bytes(self.back)

        stash_ = bytes(self.stash)
        tail_ = bytes(self.tail)

        if text:
            if stash_:
                return repr(text) + " " + str(stash_)
            return repr(text)

            # "'abc' b'\xc0'"

        if not head_:
            if stash_:
                return str(stash_)

                # "b'\xc0'"

        s = str(head_)
        if neck_:  # 'Parameter' Bytes
            s += " " + str(neck_)
        if back_ or stash_ or tail_:  # 'Intermediate' Bytes or Final Byte
            assert (not stash_) or (not tail_), (stash_, tail_)
            s += " " + str(back_ + stash_ + tail_)

        return s  # no matter if .closed

        # "b'\033[' b'6' b' q'"

    def to_bytes(self) -> bytes:
        """List the Bytes taken, as yet"""

        text = self.text
        head_ = bytes(self.head)
        neck_ = bytes(self.neck)
        back_ = bytes(self.back)
        stash_ = bytes(self.stash)
        tail_ = bytes(self.tail)

        b = text.encode()
        b += head_ + neck_ + back_ + stash_ + tail_

        return b  # no matter if .closed

    def to_csi_ints_if(self, backtail: bytes, start: bytes, default: int) -> list[int]:
        """Pick out the Nonnegative Int Literals of a CSI Escape Sequence"""

        head = self.head
        neck = self.neck
        back = self.back
        stash = self.stash
        tail = self.tail
        closed = self.closed

        if head.startswith(b"\033["):
            if neck.startswith(start):
                neckpart = neck.removeprefix(start)
                if re.fullmatch(b"[0-9;]*", string=neckpart):
                    if backtail == (back + tail):
                        if closed:
                            assert not stash, (stash, backtail, self)

                            ints = list((int(_) if _ else default) for _ in neckpart.split(b";"))

                            return ints

        return list()

    def _require_simple_(self) -> None:
        """Raise Exception if a mutation gone wrong has damaged Self"""

        text = self.text

        head = self.head
        neck = self.neck
        back = self.back

        stash = self.stash
        tail = self.tail

        closed = self.closed  # only via 'def close' if text or stash or not head

        if (not text) and (not head):
            assert (not tail) and (not closed), (tail, closed, stash, self)

        if text:
            assert not head, (head, text, self)
            assert (not neck) and (not back) and (not tail), (neck, back, tail, text, self)

        if head:
            assert not text, (text, head, self)
        if neck or back or tail:
            assert head, (head, neck, back, tail, self)
        if stash:
            assert not tail, (tail, closed, stash, self)
            assert not closed, (closed, stash, self)
        if tail:
            assert closed, (closed, tail, self)

    #
    # Tests, to run slowly and thoroughly across like 211ms
    #

    def _try_terminal_byte_pack_(self) -> None:  # todo: Call this slow Self-Test more often
        """Try some Packets open to, or closed against, taking more Bytes"""

        # Try some Packets left open to taking more Bytes

        pack = TerminalBytePacket(b"Superb")
        assert str(pack) == "'Superb'" and not pack.closed, (pack,)
        extras = pack.take_one_if(b"\xc2")
        assert not extras and not pack.closed, (extras, pack.closed, pack)
        assert str(pack) == r"'Superb' b'\xc2'", (repr(str(pack)), pack)

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
        """Require the Eval of the Str of the Packet equals its Bytes"""

        pack = self._try_bytes_(*args)
        assert not pack.closed, (pack,)

    def _try_closed_(self, *args: bytes) -> None:
        """Require the Eval of the Str of the Packet equals its Bytes"""

        pack = self._try_bytes_(*args)
        assert pack.closed, (pack,)

    def _try_bytes_(self, *args: bytes) -> "TerminalBytePacket":
        """Require the Eval of the Str of the Packet equals its Bytes"""

        data = b"".join(args)
        join = " ".join(str(_) for _ in args)

        pack = TerminalBytePacket(data)
        pack_bytes = pack.to_bytes()
        pack_str = str(pack)

        assert pack_bytes == data, (pack_bytes, data)
        assert pack_str == join, (data, pack_bytes, join)

        return pack

    #
    # Close
    #

    def close(self) -> None:
        """Close, if not closed already"""

        head = self.head
        stash = self.stash
        closed = self.closed

        if closed:
            return

        self.closed = True

        head_plus = head + stash  # if closing a 6-Byte Mouse-Report that decodes to < 6 Chars
        if head_plus.startswith(b"\033[M"):
            try:
                decode = head_plus.decode()
                if len(decode) < 6:
                    if len(head_plus) == 6:

                        head.extend(stash)
                        stash.clear()

            except UnicodeDecodeError:
                pass

        self._require_simple_()

    #
    # Take in the Bytes and return 0 Bytes, else return the trailing Bytes that don't fit
    #

    def take_some_if(self, data: bytes) -> bytes:
        """Take in the Bytes and return 0 Bytes, else return the trailing Bytes that don't fit"""

        for index in range(len(data)):
            byte = data[index:][:1]
            after_bytes = data[index:][1:]

            extras = self.take_one_if(byte)
            if extras:
                return extras + after_bytes

        return b""  # maybe .closed, maybe not

    def take_one_if(self, byte: bytes) -> bytes:
        """Take in next 1 Byte and return 0 Bytes, else return 1..4 Bytes that don't fit"""

        extras = self._take_one_if_(byte)
        self._require_simple_()

        return extras

    def _take_one_if_(self, byte: bytes) -> bytes:
        """Take in next 1 Byte and return 0 Bytes, else return 1..4 Bytes that don't fit"""

        text = self.text
        head = self.head
        closed = self.closed

        # Decline Bytes after Closed

        if closed:
            return byte  # declines Byte after Closed

        # Take 1 Byte into Stash, if next Bytes could make it Decodable

        (stash_plus_decodes, stash_extras) = self._take_one_stashable_if(byte)
        assert len(stash_plus_decodes) <= 1, (stash_plus_decodes, stash_extras, byte)
        if not stash_extras:
            return b""  # holds 1..3 possibly Decodable Bytes in Stash

        # Take 1 Byte into Mouse Report, if next Bytes could close as Mouse Report

        mouse_extras = self._take_some_mouse_if_(stash_extras)
        if not mouse_extras:
            return b""  # holds 1..5 Undecodable Bytes, or 1..11 Bytes as 1..5 Chars as Mouse Report

        assert mouse_extras == stash_extras, (mouse_extras, stash_extras)

        # Take 1 Char into Text

        if stash_plus_decodes:
            printable = stash_plus_decodes.isprintable()
            if printable and not head:
                self.text += stash_plus_decodes
                return b""  # takes 1 Printable Char into Text, or as starts Text

        if text:
            return mouse_extras  # declines 1..4 Unprintable Bytes after Text

        # Take 1 Char into 1 Control Sequence

        control_extras = self._take_some_control_if_(stash_plus_decodes, data=mouse_extras)
        return control_extras

    def _take_one_stashable_if(self, byte: bytes) -> tuple[str, bytes]:
        """Take 1 Byte into Stash, if next Bytes could make it Decodable"""

        stash = self.stash
        stash_plus = bytes(stash + byte)

        try:
            decode = stash_plus.decode()
        except UnicodeDecodeError:
            decodes = self.any_decodes_startswith(stash_plus)
            if decodes:
                stash.extend(byte)
                return ("", b"")  # holds 1..3 possibly Decodable Bytes in Stash

            stash.clear()
            return ("", stash_plus)  # declines 1..4 Undecodable Bytes

        stash.clear()
        assert len(decode) == 1, (decode, stash, byte)

        return (decode, stash_plus)  # forwards 1..4 Decodable Bytes

    def any_decodes_startswith(self, data: bytes) -> str:
        """Return Say if these Bytes start 1 or more UTF-8 Encodings of Chars"""

        closers = (b"\x80", b"\xbf", b"\x80\x80", b"\xbf\xbf", b"\x80\x80\x80", b"\xbf\xbf\xbf")

        for closer in closers:
            encode = data + closer
            try:
                decode = encode.decode()
                assert len(decode) >= 1, (decode,)
                return decode
            except UnicodeDecodeError:
                continue

        return ""

        # b"\xc2\x80", b"\xe0\xa0\x80", b"\xf0\x90\x80\x80" .. b"\xf4\x8f\xbf\xbf"
        # todo: Invent UTF-8'ish Encoding beyond 1..4 Bytes for Unicode Codes < 0x110000 ?

    def _take_some_mouse_if_(self, data: bytes) -> bytes:
        """Take 1 Byte into Mouse Report, if next Bytes could close as Mouse Report"""

        assert data, (data,)

        head = self.head
        neck = self.neck
        back = self.back

        # Do take the 3rd Byte of this kind of CSI here, and don't take the first 2 Bytes here

        if (head == b"\033[") and (not neck) and (not back):
            if data == b"M":
                head.extend(data)
                return b""  # takes 3rd Byte of CSI Mouse Report here

        if not head.startswith(b"\033[M"):  # ⎋[M Mouse Report
            return data  # doesn't take the first 2 Bytes of Mouse Report here

        # Take 3..15 Bytes into a 3..6 Char Mouse Report

        head_plus = head + data
        try:
            head_plus_decode_if = head_plus.decode()
        except UnicodeDecodeError:
            head_plus_decode_if = ""

        if head_plus_decode_if:
            assert len(head_plus_decode_if) <= 6, (head_plus_decode_if, data)
            head.extend(data)
            if len(head_plus_decode_if) == 6:
                self.closed = True
            return b""  # takes 3..15 Bytes into a 6 Char Mouse Report

        # Take 4..15 Bytes into a 6 Byte Mouse Report

        if len(head_plus) > 6:  # 6..15 Bytes
            return data  # declines 2..4 Bytes into 5 of 6 Chars or into 5 of 6 Bytes

        head.extend(data)
        if len(head_plus) == 6:
            self.closed = True

        return b""  # takes 4..14 Bytes into a 6 Byte Mouse Report

    def _take_some_control_if_(self, decodes: str, data: bytes) -> bytes:
        """Take 1 Char into Control Sequence, else return 1..4 Bytes that don't fit"""

        assert data, (data,)

        head = self.head
        tail = self.tail
        closed = self.closed

        assert not tail, (tail,)
        assert not closed, (closed,)

        assert ESC == "\033"  # ⎋
        assert CSI == "\033["  # ⎋[
        assert SS3 == "\033O"  # ⎋⇧O

        # Look only outside of Mouse Reports

        assert not head.startswith(b"\033[M"), (head,)  # Mouse Report

        # Judge as printable or not

        printable = False
        if decodes:
            assert len(decodes) == 1, (decodes, data)
            printable = decodes.isprintable()

            # Require the Caller to route Printable Chars elsewhere till Head chosen

            assert head or not printable, (decodes, data, head, printable)

        # Take first 1 or 2 or 3 Bytes into Esc Sequences
        #
        #   ⎋ Esc  # ⎋⎋ Esc Esc
        #   ⎋O SS3  # ⎋⎋O Esc SS3
        #   ⎋[ CSI  # ⎋⎋[ Esc CSI
        #

        headbook = (b"\033", b"\033\033", b"\033\033O", b"\033\033[", b"\033O", b"\033[")
        assert TerminalBytePacket.Headbook == headbook

        head_plus = bytes(head + data)
        if head_plus in headbook:
            head.extend(data)
            return b""  # takes first 1 or 2 Bytes into Esc Sequences

        # Take & close 1 Unprintable Char as Head

        if not head:
            if not printable:
                head.extend(data)
                self.closed = True
                return b""  # takes & closes Unprintable Chars or 1..4 Undecodable Bytes

            # takes \b \t \n \r \x7f etc

        # Take & close 1 Escaped Printable Decoded Char,
        # as Tail after Head of  ⎋ Esc  ⎋⎋ Esc Esc  ⎋O SS3  ⎋⎋O Esc SS3

        if bytes(head) in (b"\033", b"\033\033", b"\033\033O", b"\033O"):
            if printable:
                tail.extend(data)
                self.closed = True
                return b""  # takes & closes 1 Escaped Printable Decoded Char

            # Take & close Unprintable Chars or 1..4 Undecodable Bytes, as Escaped Tail

            tail.extend(data)  # todo: More test of Unprintable/ Undecodable Tails after ⎋O or ⎋⎋O
            self.closed = True
            return b""  # takes & closes Unprintable Chars or 1..4 Undecodable Bytes

            # does take ⎋\x10 ⎋\b ⎋\t ⎋\n ⎋\r ⎋\x7f etc

            # doesn't take bytes([0x80 | 0x0B]) as meaning b"\033\x5b" CSI ⎋[
            # doesn't take bytes([0x80 | 0x0F]) as meaning b"\033\x4f" SS3 ⎋O

        # Decline 1..4 Undecodable Bytes, when escaped by CSI or Esc CSI

        if not decodes:
            return data  # declines 1..4 Undecodable Bytes

        decode = decodes
        assert len(decodes) == 1, (decodes, data)
        assert data == decode.encode(), (data, decodes)

        # Take or don't take 1 Decodable Char into CSI or Esc CSI Sequence

        esc_csi_extras = self._take_one_esc_csi_if_(decode)
        return esc_csi_extras  # maybe empty

    def _take_one_esc_csi_if_(self, decode: str) -> bytes:
        """Take 1 Char into CSI or Esc CSI Sequence, else return 1..4 Bytes that don't fit"""

        assert len(decode) == 1, decode
        ord_ = ord(decode)
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

        byte = chr(ord_).encode()
        assert byte == encode, (byte, encode)

        # Decline 1..4 Bytes of Unprintable or Multi-Byte Char

        if ord_ > 0x7F:
            return byte  # declines 2..4 Bytes of 1 Unprintable or Multi-Byte Char

            # todo: More test of Unprintable/ Undecodable Tails after ⎋[ or ⎋⎋[

        # Accept 1 Byte into Back, into Neck, or as Tail

        assert CSI_P_CHARS == "0123456789:;<=>?"
        assert CSI_I_CHARS == """ !'#$%&'()*+,-./"""
        assert CSI_F_CHARS == "@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~"

        if not back:
            if 0x30 <= ord_ < 0x40:  # 16 Codes  # 0123456789:;<=>?
                neck.extend(byte)
                return b""  # takes 1 of 16 Parameter Byte Codes

        if 0x20 <= ord_ < 0x30:  # 16 Codes  # Spacebar !"#$%&\'()*+,-./
            back.extend(byte)
            return b""  # takes 1 of 16 Intermediate Byte Codes

        if 0x40 <= ord_ < 0x7F:  # 63 Codes  # @A Z[\\]^_`a z{|}~
            assert not tail, (tail,)
            tail.extend(byte)
            self.closed = True
            return b""  # takes 1 of 63 Final Byte Codes

        # Decline 1 Byte of Unprintable Char

        return byte  # declines 1 Byte <= b"\x7f" of Unprintable Char

        # splits '⎋[200~' and '⎋[201~' away from enclosed Bracketed Paste

        # todo: Limit the length of a CSI Escape Sequence

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

    # todo: Limit rate of input so livelocks go less wild, like in Keyboard/ Screen loopback


ESC = "\033"
SS3 = "\033O"
CSI = "\033["

CSI_P_CHARS = """0123456789:;<=>?"""  # Csi Parameter Bytes
CSI_I_CHARS = """ !'#$%&'()*+,-./"""  # Csi Intermediate [Penultimate] Bytes
CSI_F_CHARS = "@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~"  # Csi Final Bytes


@dataclasses.dataclass(order=True, frozen=True)
class TerminalPoke:
    """Say what we got for Input, and how long we waited"""

    hit: float  # time spent waiting for Input to start arriving
    delays: tuple[float, ...]  # time till each Burst of Bytes ended
    reads: tuple[bytes, ...]  # each Burst of Bytes
    extra: bytes  # Bytes arriving with the last Read, but past Close of Input

    def __post_init__(self) -> None:
        """Run after dataclass constructor completes"""

        reads = self.reads
        delays = self.delays

        assert len(reads) == len(delays), (len(reads), len(delays))

    def __str__(self) -> str:

        hit = self.hit
        delays = self.delays
        reads = self.reads
        extra = self.extra

        h = sketch(hit, near=1e-3)
        d = ", ".join(sketch(_, near=1e-3) for _ in delays)
        r = ", ".join(repr(kbytes_to_precise_kcaps(_)) for _ in reads)
        e = repr(extra)

        if len(delays) == 1:
            d += ","
        if len(reads) == 1:
            r += ","

        rep = f"TerminalPoke(hit={h}, delays=({d}), reads=({r}), extra={e})"

        return rep

    def to_kbytes(self) -> bytes:
        """Form the Bytes of the Terminal Poke"""

        reads = self.reads
        extra = self.extra
        kbytes = b"".join(reads) + extra

        return kbytes

    def to_mouse_key_caps_if_start(self, hwyx: tuple[int, int, int, int]) -> tuple[str, bytes]:
        """Form the Key Caps and Bytes of a Mouse Release, if from an Arrow Burst"""

        (y_height, x_width, row_y, column_x) = hwyx

        assert Y1 <= row_y <= y_height, (row_y, y_height)
        assert X1 <= column_x <= x_width, (column_x, x_width)

        reads = self.reads
        extra = self.extra

        dy_dx_by_arrow_kbytes = DY_DX_BY_ARROW_KBYTES

        # Visit each Arrow

        y = row_y
        x = column_x

        from_bytearray = bytearray(b"".join(reads) + extra)
        to_bytearray = bytearray()

        while True:
            arrow = bytes(from_bytearray[:3])
            if arrow not in dy_dx_by_arrow_kbytes.keys():
                break

            to_bytearray.extend(arrow)
            del from_bytearray[:3]

            # Look up which way this Arrow points

            (dy, dx) = dy_dx_by_arrow_kbytes[arrow]

            assert bool(dy) != bool(dx), (dy, dx)
            assert dy in (-1, 0, +1), (dy,)
            assert dx in (-1, 0, +1), (dx,)

            # Move our more virtual Arrow Cursor (not the more real Terminal Cursor outside)

            if x > x_width:
                x = X1
                y = min(y + 1, y_height)

            assert Y1 <= y <= y_height, (y, y_height)
            assert X1 <= x <= x_width, (x, x_width)

            y += dy
            x += dx

            y = max(Y1, min(y, y_height))

            if x < X1:
                x = x_width
                y = max(Y1, y - 1)

        if x > x_width:
            x = x_width  # caps differently at end of Arrow Burst

        assert Y1 <= y <= y_height, (y, y_height)
        assert X1 <= x <= x_width, (x, x_width)

        # Give up here, if no Arrow Burst found

        if not to_bytearray:
            return ("", b"")

        # Encode the Arrow Burst as an ⌥-Click Release of the Mouse

        kbytes = bytes(to_bytearray)

        f8 = int("0b01000", base=0)  # f = ⌥ of 0b⌃⌥⇧00
        kcaps = f"\033[<{f8};{x};{y}m"  # f x y, not f y x  # 'm' for Release  # not 'M' for Press

        # Succeed (but trust the Caller to distinguish Single Arrows from Longer Bursts as needed)

        return (kcaps, kbytes)

        # ('\033[<8;25;80m', b'\033[C',)  # Down Arrow into the Southeast Corner

    def to_sketch_text(self) -> str:
        """Say what we got for Input, if Keyboard Chord, if Arrow Burst, and how long we waited"""

        # reads = self.reads

        (reads_text, concisely) = self._format_reads_()
        hit_delays_text = self._format_hit_delays_(concisely=concisely)
        extra_text = self._format_extra_()

        # rep = f"{reads_text} {hit_delays_text} {extra_text} {reads}"
        rep = f"{reads_text} {hit_delays_text} {extra_text}"

        return rep

    def _format_hit_delays_(self, concisely: bool) -> str:
        """Say how long we waited"""

        hit = self.hit
        delays = self.delays

        h = sketch(hit, near=1e-3)

        d = "(" + ", ".join(sketch(_, near=1e-3) for _ in delays) + ")"
        if concisely:
            d = sketch(sum(delays), near=1e-3)

        rep = f"{h} {d}"

        return rep

    def _format_reads_(self) -> tuple[str, bool]:
        """Say what we got for Input, if Keyboard Chord, and if Arrow Burst"""

        reads = self.reads

        kbytes = self.to_kbytes()

        if not reads:
            rep = repr(b"")
            return (rep, False)

        chord_plus = self._format_reads_as_chord_plus_if_()
        if chord_plus:
            if kbytes == b"``" b"\033[0n":
                return (chord_plus, False)
            return (chord_plus, True)

        arrow_burst = self._format_reads_as_arrow_burst_if_()
        if arrow_burst:
            return (arrow_burst, True)

        closed_simply = self._format_reads_as_closed_simply_if_()
        if closed_simply:
            return (closed_simply, True)

        precise = " ".join(kbytes_to_precise_kcaps(_) for _ in reads)
        rep = f"{precise} {ascii(kbytes)}"  # K W⎋[0N b'kw\x1b[0n'

        return (rep, False)

    def _format_reads_as_chord_plus_if_(self) -> str:
        """Say what we got for Input, if indeed it is a Keyboard Chord"""

        reads = self.reads

        # Require a simple Close (and then don't speak of it)

        if reads[-1] != b"\033[0n":
            return ""

        # Require a simple single Read and then a separate ⎋[0 N Reply to Close

        if len(reads) != 2:
            return ""

        # Speak concisely of Key Caps, and then also precisely of Key Caps, if possible

        kbytes = reads[0]
        assert kbytes == b"".join(reads[:-1]), (kbytes, reads[:-1])

        concise = kbytes_to_concise_kcaps_if(kbytes)
        precise = kbytes_to_precise_kcaps(kbytes)

        if concise:
            if concise == precise:
                rep = f"{concise} {ascii(kbytes)}"  # Tab b'\t'
            else:
                rep = f"{concise} {precise}"  # '⇧Tab ⎋[⇧Z'
            return rep

        # Fall back to speak only precisely of Key Caps

        if len(precise.lstrip("⇧⌃⌥")) == 1:  # ⌃ ⌥ ⇧ sorted by Ord
            rep = f"{precise} {ascii(kbytes)}"  # "⌃P b'\x10'"  # ⌥Q b'\xc5\x93'
            return rep

        # Give up on speaking of Key Caps, like fall back to speak of Bytes

        return ""

    def _format_reads_as_arrow_burst_if_(self) -> str:
        """Say what we got for Input, if indeed it is an Arrow Burst"""

        reads = self.reads
        dy_dx_by_arrow_kbytes = DY_DX_BY_ARROW_KBYTES

        # Take nothing but ⎋[A ⎋[B ⎋[C ⎋[D plain Arrow Keystroke Chords, up to a ⎋[0 N Reply

        arrow_burst_kbytearray = bytearray()
        end = b""

        kbytes = b"".join(reads)
        for index in range(0, len(kbytes), 3):
            arrow = kbytes[index:][:3]

            if arrow not in dy_dx_by_arrow_kbytes.keys():
                end = kbytes[index:]
                break

            arrow_burst_kbytearray.extend(arrow)

        if len(arrow_burst_kbytearray) < (4 * 3):
            return ""

        if b"\033[0n" not in end:
            return ""

        # Say briefly how many Arrows came in what order, and if the End was strange

        arrow_burst_kbytes = bytes(arrow_burst_kbytearray)
        kbytes_as_if = arrow_burst_kbytes_pn_compress(arrow_burst_kbytes)
        rep = str(kbytes_as_if)

        if end != b"\033[0n":
            rep += f" {end!r}"

        # Succeed

        return rep

    def _format_reads_as_closed_simply_if_(self) -> str:
        """Say what we got for Input, if indeed it is a simple Close"""

        reads = self.reads
        kbytes = b"".join(reads)

        if len(reads) < 2:
            return ""
        if reads[-1] != b"\033[0n":
            return ""

        removesuffix = kbytes.removesuffix(b"\033[0n")

        precise = " ".join(kbytes_to_precise_kcaps(_) for _ in reads[:-1])
        rep = f"{precise} {ascii(removesuffix)}"  # PQ R b'pqr'

        return rep

    def _format_extra_(self) -> str:
        """Say if we got more Input after the closing ⎋[0 N Reply"""

        extra = self.extra
        rep = repr(extra) if extra else ""

        return rep

    # todo2: Fill Bold over 8 Dim keyboards | unmarked, ⌃, ⌥, ⇧ | ⌥⇧, ⌃⇧, ⌃⌥ | ⌃⌥⇧


# Name the Shifting Keys

Meta = unicodedata.lookup("Broken Circle With Northwest Arrow")  # ⎋
Control = unicodedata.lookup("Up Arrowhead")  # ⌃
Option = unicodedata.lookup("Option Key")  # ⌥
Shift = unicodedata.lookup("Upwards White Arrow")  # ⇧
Command = unicodedata.lookup("Place of Interest Sign")  # ⌘  # Super  # Windows
Fn = "Fn"

# note: Meta hides inside Apple > Settings > Keyboard > Use Option as Meta Key
# note: Meta hides inside Google > Settings > Keyboard > Alt is Meta


# Point the Arrows

DY_DX_BY_ARROW_KBYTES = {
    b"\033[A": (-1, 0),  # ⎋[⇧A  # ↑
    b"\033[B": (+1, 0),  # ⎋[⇧B  # ↓
    b"\033[C": (0, +1),  # ⎋[⇧C  # →
    b"\033[D": (0, -1),  # ⎋[⇧D  # ←
}


# Decode each distinct Key Chord Byte Encoding as a distinct Str without a " " Space in it

KCAP_SEP = " "  # separates '⇧Tab' from '⇧T a b', '⎋⇧FnX' from '⎋⇧Fn X', etc

# headbook = (b"\033", b"\033\033", b"\033\033O", b"\033\033[", b"\033O", b"\033[")
# assert TerminalBytePacket.Headbook == headbook

KCAP_BY_KTEXT = {  # r"←|↑|→|↓" and so on  # ⌃ ⌥ ⇧ ⌃⌥ ⌃⇧ ⌥⇧ ⌃⌥⇧ and so on
    "\x00": "⌃Spacebar",  # ⌃@  # ⌃⇧2
    # "\x03": "Interrupt",  # ⌃C also found at FnReturn in iTerm2 Apple
    # "\x08": "Backspace",  # ⌃H also found at ⌃⇧Delete and ⌃⌥⇧Delete in iTerm2 Apple
    "\x09": "Tab",  # '\t' ⇥
    "\x0d": "Return",  # '\r' ⏎
    "\033": "⎋",  # Esc  # Meta  # includes ⎋Spacebar ⎋Tab ⎋Return ⎋Delete without ⌥
    "\033" "\x01": "⌥⇧Fn←",  # ⎋⇧Fn←   # coded with ⌃A
    "\033" "\x03": "⎋FnReturn",  # coded with ⌃C  # not ⌥FnReturn
    "\033" "\x04": "⌥⇧Fn→",  # ⎋⇧Fn→   # coded with ⌃D
    "\033" "\x08": "⎋⌃Delete",  # ⎋⌃Delete  # coded with ⌃H  # aka \b
    "\033" "\x0b": "⌥⇧Fn↑",  # ⎋⇧Fn↑   # coded with ⌃K
    "\033" "\x0c": "⌥⇧Fn↓",  # ⎋⇧Fn↓  # coded with ⌃L  # aka \f
    "\033" "\x10": "⎋⇧Fn",  # ⎋ Meta ⇧ Shift of FnF1..FnF12  # not ⌥⇧Fn  # coded with ⌃P
    "\033" "\033": "⎋⎋",  # Meta Esc  # not ⌥⎋
    "\033" "\033O" "A": "⌃⌥↑",  # ESC SS3 ⇧A  # Google
    "\033" "\033O" "B": "⌃⌥↓",  # ESC SS3 ⇧B  # Google
    "\033" "\033O" "C": "⌃⌥→",  # ESC SS3 ⇧C  # Google
    "\033" "\033O" "D": "⌃⌥←",  # ESC SS3 ⇧D  # Google
    "\033" "\033[" "3;5~": "⌥⌃FnDelete",  # ⎋⌃FnDelete  # Apple
    "\033" "\033[" "A": "⌥↑",  # CSI 04/01 Cursor Up (CUU)  # Option-as-Meta  # Google
    "\033" "\033[" "B": "⌥↓",  # CSI 04/02 Cursor Down (CUD)  # Option-as-Meta  # Google
    "\033" "\033[" "C": "⌥→",  # CSI 04/03 Cursor [Forward] Right (CUF_X)  # Google
    "\033" "\033[" "D": "⌥←",  # CSI 04/04 Cursor [Back] Left (CUB_X)  # Google
    "\033" "\033[" "Z": "⎋⇧Tab",  # ⇤  # CSI 05/10 CBT  # not ⌥⇧Tab
    "\033" "\x28": "⎋FnDelete",  # not ⌥FnDelete
    #
    "\033O" "P": "F1",  # SS3 ⇧P  # but Apple takes ⇧F1 ⇧F2 ⇧F3 ⇧F4 from Terminal
    "\033O" "Q": "F2",  # SS3 ⇧Q
    "\033O" "R": "F3",  # SS3 ⇧R
    "\033O" "S": "F4",  # SS3 ⇧S
    #
    "\033[" "15;2~": "⇧F5",  # iTerm2 Apple
    "\033[" "15;3~": "⌥F5",  # iTerm2 Apple
    "\033[" "15;4~": "⌥⇧F5",  # ⌥⇧F6  # iTerm2 Apple
    "\033[" "15;5~": "⌃F5",  # iTerm2 Apple
    "\033[" "15;6~": "⌃⇧F5",  # iTerm2 Apple
    "\033[" "15;7~": "⌃⌥F5",  # iTerm2 Apple
    "\033[" "15;8~": "⌃⌥⇧F5",  # iTerm2 Apple
    "\033[" "15~": "F5",  # Esc 07/14 is LS1R, but CSI 07/14 is unnamed
    "\033[" "17;2~": "⇧F6",  # iTerm2 Apple
    "\033[" "17;3~": "⌥F6",  # iTerm2 Apple
    "\033[" "17;4~": "⌥⇧F7",  # iTerm2 Apple
    "\033[" "17;5~": "⌃F6",  # iTerm2 Apple
    "\033[" "17;6~": "⌃⇧F6",  # iTerm2 Apple
    "\033[" "17;7~": "⌃⌥F6",  # iTerm2 Apple
    "\033[" "17;8~": "⌃⌥⇧F6",  # iTerm2 Apple
    "\033[" "17~": "F6",  # ⌥F1  # ⎋F1
    "\033[" "18;2~": "⇧F7",  # iTerm2 Apple
    "\033[" "18;3~": "⌥F7",  # iTerm2 Apple
    "\033[" "18;4~": "⌥⇧F8",  # iTerm2 Apple
    "\033[" "18;5~": "⌃F7",  # iTerm2 Apple
    "\033[" "18;6~": "⌃⇧F7",  # iTerm2 Apple
    "\033[" "18;7~": "⌃⌥F7",  # iTerm2 Apple
    "\033[" "18;8~": "⌃⌥⇧F7",  # iTerm2 Apple
    "\033[" "18~": "F7",  # ⌥F2  # ⎋F2
    "\033[" "19;2~": "⇧F8",  # iTerm2 Apple
    "\033[" "19;3~": "⌥F8",  # iTerm2 Apple
    "\033[" "19;4~": "⌥⇧F9",  # iTerm2 Apple
    "\033[" "19;5~": "⌃F8",  # iTerm2 Apple  # Apple takes ⌃F8
    "\033[" "19;6~": "⌃⇧F8",  # iTerm2 Apple
    "\033[" "19;7~": "⌃⌥F8",  # iTerm2 Apple
    "\033[" "19;8~": "⌃⌥⇧F8",  # iTerm2 Apple
    "\033[" "19~": "F8",  # ⌥F3  # ⎋F3
    #
    "\033[" "1;2A": "⇧↑",  # iTerm2 Apple
    "\033[" "1;2B": "⇧↓",  # iTerm2 Apple
    "\033[" "1;2C": "⇧→",  # CSI 04/03 Cursor [Forward] Right (CUF_YX) Y=1 X=2  # Apple
    "\033[" "1;2D": "⇧←",  # CSI 04/04 Cursor [Back] Left (CUB_YX) Y=1 X=2  # Apple
    "\033[" "1;2F": "⇧Fn→",  # iTerm2 Apple
    "\033[" "1;2H": "⇧Fn←",  # iTerm2 Apple
    "\033[" "1;2P": "⇧F1",  # iTerm2 Apple
    "\033[" "1;2Q": "⇧F2",  # iTerm2 Apple
    "\033[" "1;2R": "⇧F3",  # iTerm2 Apple
    "\033[" "1;2S": "⇧F4",  # iTerm2 Apple
    #
    "\033[" "1;3A": "⌥↑",  # iTerm2 Apple
    "\033[" "1;3B": "⌥↓",  # iTerm2 Apple
    "\033[" "1;3C": "⌥→",  # iTerm2 Apple
    "\033[" "1;3D": "⌥←",  # iTerm2 Apple
    "\033[" "1;3F": "⌥Fn→",  # iTerm2 Apple
    "\033[" "1;3H": "⌥Fn←",  # iTerm2 Apple
    "\033[" "1;3P": "⌥F1",  # iTerm2 Apple
    "\033[" "1;3Q": "⌥F2",  # iTerm2 Apple
    "\033[" "1;3R": "⌥F3",  # iTerm2 Apple
    "\033[" "1;3S": "⌥F4",  # iTerm2 Apple
    #
    "\033[" "1;4A": "⌥⇧↑",  # iTerm2 Apple
    "\033[" "1;4B": "⌥⇧↓",  # iTerm2 Apple
    "\033[" "1;4C": "⌥⇧→",  # iTerm2 Apple
    "\033[" "1;4D": "⌥⇧←",  # iTerm2 Apple
    "\033[" "1;4F": "⌥⇧Fn→",  # iTerm2 Apple
    "\033[" "1;4H": "⌥⇧Fn←",  # iTerm2 Apple
    "\033[" "1;4P": "⌥⇧F1",  # iTerm2 Apple
    "\033[" "1;4Q": "⌥⇧F2",  # iTerm2 Apple
    "\033[" "1;4R": "⌥⇧F3",  # iTerm2 Apple
    "\033[" "1;4S": "⌥⇧F4",  # iTerm2 Apple
    #
    "\033[" "1;5P": "⌃F1",  # iTerm2 Apple  # Apple takes ⌃F1
    "\033[" "1;5Q": "⌃F2",  # iTerm2 Apple
    "\033[" "1;5R": "⌃F3",  # iTerm2 Apple  # Apple takes ⌃F3
    "\033[" "1;5S": "⌃F4",  # iTerm2 Apple
    #
    "\033[" "1;6A": "⌃⇧↑",  # iTerm2 Apple
    "\033[" "1;6B": "⌃⇧↓",  # iTerm2 Apple
    "\033[" "1;6C": "⌃⇧→",  # iTerm2 Apple
    "\033[" "1;6D": "⌃⇧←",  # iTerm2 Apple
    "\033[" "1;6P": "⌃⇧F1",  # iTerm2 Apple
    "\033[" "1;6Q": "⌃⇧F2",  # iTerm2 Apple
    "\033[" "1;6R": "⌃⇧F3",  # iTerm2 Apple
    "\033[" "1;6S": "⌃⇧F4",  # iTerm2 Apple
    #
    "\033[" "1;7A": "⌃⌥↑",  # iTerm2 Apple
    "\033[" "1;7B": "⌃⌥↓",  # iTerm2 Apple
    "\033[" "1;7C": "⌃⌥→",  # iTerm2 Apple
    "\033[" "1;7D": "⌃⌥←",  # iTerm2 Apple
    "\033[" "1;7F": "⌃⌥Fn←",  # iTerm2 Apple
    "\033[" "1;7H": "⌃⌥Fn→",  # iTerm2 Apple
    "\033[" "1;7P": "⌃⌥F1",  # iTerm2 Apple
    "\033[" "1;7Q": "⌃⌥F2",  # iTerm2 Apple
    "\033[" "1;7R": "⌃⌥F3",  # iTerm2 Apple
    "\033[" "1;7S": "⌃⌥F4",  # iTerm2 Apple
    #
    "\033[" "1;8A": "⌃⌥⇧↑",  # iTerm2 Apple
    "\033[" "1;8B": "⌃⌥⇧↓",  # iTerm2 Apple
    "\033[" "1;8C": "⌃⌥⇧→",  # iTerm2 Apple
    "\033[" "1;8D": "⌃⌥⇧←",  # iTerm2 Apple
    "\033[" "1;8P": "⌃⌥⇧F1",  # iTerm2 Apple
    "\033[" "1;8Q": "⌃⌥⇧F2",  # iTerm2 Apple
    "\033[" "1;8R": "⌃⌥⇧F3",  # iTerm2 Apple
    "\033[" "1;8S": "⌃⌥⇧F4",  # iTerm2 Apple
    #
    "\033[" "20;2~": "⇧F9",  # iTerm2 Apple
    "\033[" "20;3~": "⌥F9",  # iTerm2 Apple
    "\033[" "20;4~": "⌥⇧F10",  # iTerm2 Apple
    "\033[" "20;5~": "⌃F9",  # iTerm2 Apple
    "\033[" "20;6~": "⌃⇧F9",  # iTerm2 Apple
    "\033[" "20;7~": "⌃⌥F9",  # iTerm2 Apple
    "\033[" "20;8~": "⌃⌥⇧F9",  # iTerm2 Apple
    "\033[" "20~": "F9",  # ⌥F4  # ⎋F4
    "\033[" "21;2~": "⇧F10",  # iTerm2 Apple
    "\033[" "21;3~": "⌥F10",  # iTerm2 Apple
    "\033[" "21;4~": "⌥⇧F11",  # iTerm2 Apple
    "\033[" "21;5~": "⌃F10",  # iTerm2 Apple
    "\033[" "21;6~": "⌃⇧F10",  # iTerm2 Apple
    "\033[" "21;7~": "⌃⌥F10",  # iTerm2 Apple
    "\033[" "21;8~": "⌃⌥⇧F10",  # iTerm2 Apple
    "\033[" "21~": "F10",  # ⌥F5  # ⎋F5
    "\033[" "22;4~": "⌥⇧F12",  # iTerm2 Apple
    "\033[" "23;2~": "⇧F11",  # iTerm2 Apple
    "\033[" "23;3~": "⌥F11",  # iTerm2 Apple
    "\033[" "23;5~": "⌃F11",  # iTerm2 Apple
    "\033[" "23;6~": "⌃⇧F11",  # iTerm2 Apple
    "\033[" "23;7~": "⌃⌥F11",  # iTerm2 Apple
    "\033[" "23;8~": "⌃⌥⇧F11",  # iTerm2 Apple
    "\033[" "23~": "F11",  # ⌥F6  # ⎋F6  # Apple takes F11
    "\033[" "24;2~": "⇧F12",  # iTerm2 Apple
    "\033[" "24;3~": "⌥F12",  # iTerm2 Apple
    "\033[" "24;5~": "⌃F12",  # iTerm2 Apple
    "\033[" "24;6~": "⌃⇧F12",  # iTerm2 Apple
    "\033[" "24;7~": "⌃⌥F12",  # iTerm2 Apple
    "\033[" "24;8~": "⌃⌥⇧F12",  # iTerm2 Apple
    "\033[" "24~": "F12",  # ⌥F7  # ⎋F7
    "\033[" "25~": "⇧F5",  # ⌥F8  # ⎋F8
    "\033[" "26~": "⇧F6",  # ⌥F9  # ⎋F9
    "\033[" "28~": "⇧F7",  # ⌥F10  # ⎋F10
    "\033[" "29~": "⇧F8",  # ⌥F11  # ⎋F11
    #
    "\033[" "31~": "⇧F9",  # ⌥F12  # ⎋F12
    "\033[" "32~": "⇧F10",
    "\033[" "33~": "⇧F11",
    "\033[" "34~": "⇧F12",
    "\033[" "3;2~": "⇧FnDelete",
    "\033[" "3;3~": "⌥FnDelete",  # iTerm2 Apple
    "\033[" "3;4~": "⌥⇧FnDelete",  # iTerm2 Apple
    "\033[" "3;5~": "⌃FnDelete",  # Apple
    "\033[" "3;6~": "⌃⇧FnDelete",  # iTerm2 Apple
    "\033[" "3;7~": "⌃⌥Delete",  # iTerm2 Apple
    "\033[" "3;8~": "⌃⌥⇧FnDelete",  # iTerm2 Apple
    "\033[" "3~": "FnDelete",
    #
    "\033[" "5;3~": "⌥Fn↑",  # iTerm2 Apple
    "\033[" "5;4~": "⌥⇧Fn↑",  # iTerm2 Apple
    "\033[" "5;7~": "⌃⌥Fn↑",  # iTerm2 Apple
    "\033[" "5~": "⇧Fn↑",  # Apple
    #
    "\033[" "6;3~": "⌥Fn↓",  # iTerm2 Apple
    "\033[" "6;4~": "⌥⇧Fn↓",  # iTerm2 Apple
    "\033[" "6;7~": "⌃⌥Fn↓",  # iTerm2 Apple
    "\033[" "6~": "⇧Fn↓",  # Apple
    #
    "\033[" "A": "↑",  # CSI 04/01 Cursor Up (CUU)  # also ⌥↑ Apple
    "\033[" "B": "↓",  # CSI 04/02 Cursor Down (CUD)  # also ⌥↓ Apple
    "\033[" "C": "→",  # CSI 04/03 Cursor Right [Forward] (CUF)  # also ⌥→ Apple
    "\033[" "D": "←",  # CSI 04/04 Cursor [Back] Left (CUB)  # also ⌥← Apple
    "\033[" "F": "⇧Fn→",  # Apple  # CSI 04/06 Cursor Preceding Line (CPL)
    "\033[" "H": "⇧Fn←",  # Apple  # CSI 04/08 Cursor Position (CUP)
    "\033[" "Z": "⇧Tab",  # ⇤  # CSI 05/10 Cursor Backward Tabulation (CBT)
    "\033" "b": "⌥←",  # ⎋B  # ⎋←  # Emacs M-b Backword-Word  # Apple
    "\033" "f": "⌥→",  # ⎋F  # ⎋→  # Emacs M-f Forward-Word  # Apple
    "\x20": "Spacebar",  # ' '  # ␠  # ␣  # ␢
    "``": "⌥``",  # sometimes arrives as "`" "`" split across hundreds of milliseconds
    "\x7f": "Delete",  # ␡  # ⌫  # ⌦
    "\xa0": "⌥Spacebar",  # '\N{No-Break Space}'
}

assert list(KCAP_BY_KTEXT.keys()) == sorted(KCAP_BY_KTEXT.keys())

assert KCAP_SEP == " "
for _KCAP in KCAP_BY_KTEXT.values():
    assert " " not in _KCAP, (_KCAP,)


SHIFT_KEYCAPS = '!"#$%&()*+' ":<>?" "@" "^_" "{|}~"  # !"#$%&()*+ :<>? @ ^_ {|}~


OPTION_KTEXT_BY_KT = {
    "á": "⌥EA",  # E
    "é": "⌥EE",
    "í": "⌥EI",
    # without the "j́" of ⌥EJ here (because its Combining Accent comes after as a 2nd Character)
    "ó": "⌥EO",
    "ú": "⌥EU",
    "´": "⌥⇧E",
    "é": "⌥EE",
    "â": "⌥IA",  # I
    "ê": "⌥IE",
    "î": "⌥II",
    "ô": "⌥IO",
    "û": "⌥IU",
    "ˆ": "⌥⇧I",
    "ã": "⌥NA",  # N
    "ñ": "⌥NN",
    "õ": "⌥NO",
    "˜": "⌥⇧N",
    "ä": "⌥UA",  # U
    "ë": "⌥UE",
    "ï": "⌥UI",
    "ö": "⌥UO",
    "ü": "⌥UU",
    "ÿ": "⌥UY",
    "¨": "⌥⇧U",
    "à": "⌥`A",  # `
    "è": "⌥`E",
    "ì": "⌥`I",
    "ò": "⌥`O",
    "ù": "⌥`U",
    # without the "`" of ⌥⇧` here (because it comes in as a U+0060 Grave Accent ` of a US Keyboard)
}

# hand-sorted by ⌥E ⌥I ⌥N ⌥U ⌥` order


def kbytes_to_concise_kcaps_if(kbytes: bytes) -> str:
    """Choose Keycaps to speak of the Bytes of 1 Keyboard Chord"""

    ktext = kbytes.decode()  # todo: .kbytes_to_concise_kcaps_if may raise UnicodeDecodeError
    kcap_by_ktext = KCAP_BY_KTEXT  # '\e\e[A' for ⎋↑ etc

    headbook = (b"\033", b"\033\033", b"\033\033O", b"\033\033[", b"\033O", b"\033[")
    assert TerminalBytePacket.Headbook == headbook

    assert KCAP_SEP == " "

    concise_if = ""
    if ktext in kcap_by_ktext.keys():

        concise_if = kcap_by_ktext[ktext]
        assert concise_if, (concise_if, kbytes)

    else:

        esc_ktext = ktext.removeprefix("\033")
        if esc_ktext.startswith("\033"):
            if esc_ktext in kcap_by_ktext.keys():

                esc_concise_if = kcap_by_ktext[esc_ktext]
                assert esc_concise_if, (esc_concise_if, kbytes)

                concise_if = "⎋" + esc_concise_if

    assert " " not in concise_if, (concise_if, kbytes)  # accepts empty, but not split by Spaces

    return concise_if

    # ⌥Y often comes through as \ U+005C Reverse-Solidus aka Backslash  # not ¥ Yen-Sign

    # 'A'
    # '⌃L'
    # '⇧Z'
    # '⎋9' from ⌥9 while Apple Keyboard > Option as Meta Key


def kbytes_to_precise_kcaps(kbytes: bytes) -> str:
    """Choose 1 Keycaps per Character tos peak of the Bytes of 1 Keyboard Chord"""

    assert kbytes, (kbytes,)

    assert KCAP_SEP == " "

    ktext = kbytes.decode()  # todo: .kbytes_to_precise_kcaps may raise UnicodeDecodeError
    assert ktext, (ktext,)

    precise = ""
    for kt in ktext:  # often 'len(ktext) == 1'
        kc = _kt_to_kcap_(kt)
        precise += kc

    assert precise, (precise, kbytes)
    assert " " not in precise, (precise, kbytes)

    return precise

    # '⎋[25;80R' Cursor-Position-Report (CPR)
    # '⎋[25;80t' Rows x Column Terminal Size Report

    # '⎋[200~' and '⎋[201~' before/ after Paste to bracket it


def _kt_to_kcap_(kt: str) -> str:
    """Form 1 Key Cap to speak of 1 Keyboard Chord"""

    ko = ord(kt)

    option_kt_str = OPTION_KT_STR  # '∂' for ⌥D
    option_ktext_by_kt = OPTION_KTEXT_BY_KT  # 'é' for ⌥EE
    kcap_by_ktext = KCAP_BY_KTEXT  # '\x7F' for 'Delete'

    assert SHIFT_KEYCAPS == '!"#$%&()*+' ":<>?" "@" "^_" "{|}~"

    # Show more Key Caps than US-Ascii mentions

    if kt in '!"#$%&()*+' ":<>?" "@" "^_" "{|}~":
        kc = "⇧" + kt

    elif kt in kcap_by_ktext.keys():  # Mac US Key Caps for Spacebar, F12, etc
        kc = kcap_by_ktext[kt]  # '⌃Spacebar', 'Return', 'Delete', etc

    elif (kt != "`") and (kt in option_ktext_by_kt.keys()):  # Mac US Option Accents
        kc = option_ktext_by_kt[kt]

    elif kt in option_kt_str:  # Mac US Option Key Caps
        kc = _option_kt_to_kcap_(kt)

    # Show the Key Caps of US-Ascii, plus the ⌃ ⇧ Control/ Shift Key Caps

    elif (ko < 0x20) or (ko == 0x7F):  # C0 Control Bytes, or \x7F Delete (DEL)
        if ko == 0x1F:  # Apple ⌃- doesn't come through as  (0x2D ^ 0x40)
            kc = "⌃-"  # Apple ⌃-  and ⌃⇧_ do come through as (0x5F ^ 0x40)
        else:
            kc = "⌃" + chr(ko ^ 0x40)  # '^ 0x40' mixes ⌃ into one of @ A..Z [\]^_ ?, such as ⌃^

        # '^ 0x40' speaks of ⌃@ but not ⌃⇧@ and not ⌃⇧2 and not ⌃Spacebar at b"\x00"
        # '^ 0x40' speaks of ⌃M but not Return at b"\x0D"
        # '^ 0x40' speaks of ⌃[ ⌃\ ⌃] ⌃_ but not ⎋ and not ⌃⇧_ and not ⌃⇧{ ⌃⇧| ⌃⇧} ⌃-
        # '^ 0x40' speaks of ⌃? but not Delete at b"\x7F"

        # ⌃` ⌃2 ⌃6 ⌃⇧~ don't work

    elif "A" <= kt <= "Z":  # printable Upper Case English
        kc = "⇧" + chr(ko)  # shifted Key Cap '⇧A' from b'A'

    elif "a" <= kt <= "z":  # printable Lower Case English
        kc = chr(ko ^ 0x20)  # plain Key Cap 'A' from b'a'

    # Test that no Keyboard sends the C1 Control Bytes, nor the Quasi-C1 Bytes

    elif ko in range(0x80, 0xA0):  # C1 Control Bytes
        kc = repr(bytes([ko]))  # b'\x80'
    elif ko == 0xA0:  # 'No-Break Space'
        kc = "⌥Spacebar"
        assert False, (ko, kt)  # unreached because 'kcap_by_ktext'
    elif ko == 0xAD:  # 'Soft Hyphen'  # near to a C1 Control Byte
        kc = repr(bytes([ko]))  # b'\xad'

    # Show the US-Ascii or Unicode Char as if its own Key Cap

    else:
        assert ko < 0x11_0000, (ko, kt)
        kc = chr(ko)  # '!', '¡', etc

        # todo: Got Key Caps Str "\u00A1" .. "\u00FF" for Bytes b"\xA1" .. b"\xFF" - Want better?

    # Succeed, but insist that Blank Space is never a Key Cap

    assert kc, (kc, ko, kt)
    assert kc.isprintable(), (kc, ko, kt)  # has no \x00..\x1f, \x7f, \xa0, \xad, etc
    assert " " not in kc, (kc, ko, kt)

    return kc

    # '⌃L'  # '⇧Z'


# Decode one ⌥ KeyCap per US-Ascii Printable Byte, at an Apple MacBook

# .  !"#$%&'()*+,-./0123456789:;<=>?
# . @ABCD FGHIJK     LMNOPQRSTUVWXYZ[\]^_
# .  abcd fgh jklm opqrst vwxyz{|}~

_DENTED_OPTION_KT_STR_ = """

     ⁄Æ‹›ﬁ‡æ·‚°±≤–≥÷º¡™£¢∞§¶•ªÚ…¯≠˘¿
    €ÅıÇÎ Ï˝Ó Ô\uf8ffÒÂ Ø∏Œ‰Íˇ ◊„˛Á¸“«‘ﬂ—
     å∫ç∂ ƒ©˙ ∆˚¬µ øπœ®ß† √∑≈¥Ω”»’

"""

# ⌥⇧K is Apple Logo Icon  is \uF8FF is in the U+E000..U+F8FF Private Use Area (PUA)
# ⌥Y often comes through as \ U+005C Reverse-Solidus aka Backslash  # not ¥ Yen-Sign

OPTION_KT_STR = " " + textwrap.dedent(_DENTED_OPTION_KT_STR_).strip() + " "
OPTION_KT_STR = OPTION_KT_STR.replace("\n", "")

assert len(OPTION_KT_STR) == (0x7E - 0x20) + 1  # counts Defs per ⌥ KeyCap of a US-Ascii Printable

_SPACELESS_OPTION_KT_STR_ = OPTION_KT_STR.replace(" ", "")
assert len(_SPACELESS_OPTION_KT_STR_) == len(set(_SPACELESS_OPTION_KT_STR_))


def _option_kt_to_kcap_(kt: str) -> str:
    """Convert to Mac US Option Key Caps from any of OPTION_KT_STR"""

    option_kt_str = OPTION_KT_STR  # '∂' for ⌥D, etc
    assert len(OPTION_KT_STR) == (0x7E - 0x20) + 1

    assert SHIFT_KEYCAPS == '!"#$%&()*+' ":<>?" "@" "^_" "{|}~"

    index = option_kt_str.index(kt)

    alt_cap = chr(0x20 + index)
    if "A" <= alt_cap <= "Z":
        end = "⇧" + alt_cap  # '⇧A'
    elif "a" <= alt_cap <= "z":
        end = chr(ord(alt_cap) ^ 0x20)  # 'Z'
    elif alt_cap in '!"#$%&()*+' ":<>?" "@" "^_" "{|}~":
        end = "⇧" + alt_cap  # '⇧@'
    else:
        end = alt_cap

    kc = "⌥" + end  # '⌥⇧P'

    return kc


# Define each KText once, never more than once

_KTEXT_LISTS_ = [
    list(KCAP_BY_KTEXT.keys()),
    list(OPTION_KTEXT_BY_KT.keys()),
    list(_SPACELESS_OPTION_KT_STR_),
]

_KTEXT_UNROLL_ = list(_KTEXT_ for _KTEXT_LIST_ in _KTEXT_LISTS_ for _KTEXT_ in _KTEXT_LIST_)
for _KTEXT_, _COUNT_ in collections.Counter(_KTEXT_UNROLL_).items():
    assert _COUNT_ == 1, (_COUNT_, _KTEXT_)


def arrow_burst_kbytes_pn_compress(kbytes: bytes) -> bytes:
    """Compress each run of Arrows into a Pn > 1"""

    pairs: list[tuple[int, bytes]] = list()

    kbytearray = bytearray(kbytes)
    while kbytearray:
        arrow = bytes(kbytearray[:3])
        del kbytearray[:3]

        tail = arrow[-1:]
        if pairs and pairs[-1][-1] == tail:
            pairs[-1] = (pairs[-1][0] + 1, tail)
        else:
            pair = (1, tail)
            pairs.append(pair)

    kbytes = b"".join(
        (b"\033[" + (str(pn).encode() if (pn >= 2) else b"") + tail) for (pn, tail) in pairs
    )

    return kbytes


def tprint(*args: object, end: str = "\r\n") -> None:
    """Print to Terminal"""

    text = " ".join(str(_) for _ in args)

    tt = touch_terminals[-1]
    stdio = tt.stdio
    tcgetattr = tt.tcgetattr

    assert tcgetattr, (tcgetattr,)

    print(text, end=end, file=stdio)


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

    print(file=with_stderr)
    print(file=with_stderr)
    print("ExceptHook", file=with_stderr)

    with_excepthook(exc_type, exc_value, exc_traceback)

    # Launch the Post-Mortem Debugger

    print(">>> pdb.pm()", file=with_stderr)
    pdb.pm()


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


#
# Run from the Shell Command Line, if not imported
#


if __name__ == "__main__":
    main()


# 3456789 123456789 123456789 123456789 123456789 123456789 123456789 123456789 123456789 123456789

# posted into:  https://github.com/pelavarre/less-beeps/blob/main/bin/less-beeps.py
# copied from:  git clone git@github.com:pelavarre/less-beeps.git
