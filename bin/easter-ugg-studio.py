#!/usr/bin/env python3

r"""
usage: easter-egg-studio.py [-h] [--yolo]

give away nine classic simple Terminal games

options:
  -h, --help  show this help message and exit
  --yolo      do what's popular now

examples:
  ./bin/easter-egg-studio.py --yolo
"""

# code reviewed by People, Black, Flake8, Mypy-Strict, & Pylance-Standard


from __future__ import annotations  # backports new datatype syntaxes into old Pythons

import __main__
import argparse
import bdb
import collections
import dataclasses
import difflib
import itertools
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
# Run from the Shell Command Line
#


def main() -> None:
    """Run from the Shell Command Line, and launch the Py Repl vs uncaught Exceptions"""

    sys.excepthook = excepthook

    mc = MainClass()
    mc.main_class_run()


@dataclasses.dataclass(order=True)  # , frozen=True)
class MainClass:

    def __init__(self) -> None:  # todo1: needed after we add Instance Fields
        pass

    def main_class_run(self) -> None:
        """Run from the Shell Command Line, and launch the Py Repl vs uncaught Exceptions"""

        # Take in the Shell Command-Line Args

        ns = self.parse_ugg_args()
        assert ns.yolo, (ns.yolo, ns)  # todo1: needed after other Options declared

        # Launch

        print(30 * "123456789 ")
        print()

        print("⌃D to quit,  Fn F1 for more help,  or ⌥-Click far from the Cursor<br>")

        # Run till quit

        with TouchTerminal() as tt:

            tt.stdio.write("\033[6n")  # ⎋[6N calls for reply ⎋[{y};{x}⇧R
            tp = tt.read_terminal_poke(timeout=None)

            print(end="\r\n")

            rep = str(tp).replace("\n", "\r\n")  # prints the ⎋[ ⇧R reply
            print(tp, end="\r\n")

            while True:

                tt.stdio.flush()
                tp = tt.read_terminal_poke(timeout=None)
                reads_plus = (tp.reads + (tp.extra,)) if tp.extra else tp.reads

                breaking = False
                for read in reads_plus:
                    precise = kbytes_to_precise_kcaps(read)
                    if precise in ("⌃C", "⌃D", "⌃Z", "⌃\\"):
                        breaking = True

                rep = str(tp).replace("\n", "\r\n")
                print(rep, end="\r\n")

                if breaking:
                    break

                # quits at Cat ⌃C ⌃D ⌃Z ⌃\
                # todo1: quits at Emacs ⌃X ⌃C, ⌃X ⌃S
                # todo1: quits at Vim ⇧Z ⇧Q, ⇧Z ⇧Z

            # todo2: split Control Input Bytes into TerminalBytePacket's
            # todo2: gather Text Input Bytes into TerminalBytePacket's
            # todo2: ⎋F1 to lists Tests apart from Games
            # todo0: show the ← mouse explosion over wrapped Lines at iTerm2 & Google Cloud Shell

        # todo2: Mouse Strokes at iPhone

    def parse_ugg_args(self) -> argparse.Namespace:
        """Take in the Shell Command-Line Args"""

        parser = self.compile_ugg_doc()

        argv = sys.argv[1:]
        if not argv:
            if os.path.basename(sys.argv[0]) in ("+", "@"):
                argv = ["--yolo"]

        ns = parser.parse_args_if(argv)

        return ns

    def compile_ugg_doc(self) -> ArgDocParser:
        """Declare the Options & Positional Arguments"""

        doc = __main__.__doc__
        assert doc, (doc,)

        parser = ArgDocParser(doc, add_help=True)

        yolo_help = "do what's popular now"
        parser.add_argument("--yolo", action="count", help=yolo_help)

        return parser


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


def blur(f: float) -> str:
    """Format 0e0 as '0', but other Floats as 2 or 3 Digits, with a Metric Exponent"""

    if f == 0:
        return "0"  # 0

    neg = "-" if (f < 0) else ""  # omits '+' at left
    abs_ = abs(f)

    sci = math.floor(math.log10(abs_))
    eng = (sci // 3) * 3
    precise = abs_ / (10**eng)
    assert 1 <= precise <= 1000, (precise, abs_, eng, f)  # todo: log if ever == 1000

    dotted = round(precise, 1)  # 1.0  # 9.9  # 10.0
    assert 1.0 <= dotted <= 1000.0, (dotted, abs_, eng, f)

    concise = dotted
    if concise >= 10:
        concise = round(precise)  # 10  # 1000
        assert 10 <= concise <= 1000, (concise, abs_, eng, f)

    rep = f"{neg}{concise}e{eng}"  # omits '+' in the exponent

    return rep

    # lets the caller choose drop the "e0"s, or the "e-3"s, or neither, or whatever


#
# Amp up Import Termios
#


# Name some Magic Numbers

Y1 = 1  # indexes Y Rows as Southbound across 1 .. Height
X1 = 1  # indexes X Columns as Eastbound across 1 .. Width

PN_MAX_32100 = 32100  # a Numeric [Int] beyond the Counts of Rows & Columns at any Real Terminal


touch_terminals = list()


class TouchTerminal:
    """Write/ Read Bytes at Screen/ Keyboard/ Click/ Tap of the Terminal"""

    stdio: typing.TextIO
    fileno: int

    before: int  # for writing at Enter
    tcgetattr: list[int | list[bytes | int]]  # replaced by Enter
    after: int  # for writing at Exit  # todo1: .TCSAFLUSH vs large Paste

    #
    # Init, enter, exit, and poll
    #

    def __init__(self) -> None:

        touch_terminals.append(self)

        assert sys.__stderr__ is not None
        stdio = sys.__stderr__

        self.stdio = stdio
        self.fileno = stdio.fileno()

        self.before = termios.TCSADRAIN  # for writing at Enter
        self.tcgetattr = list()  # replaced by Enter
        self.after = termios.TCSADRAIN  # for writing at Exit

    def __enter__(self) -> typing.Self:
        r"""Stop line-buffering Input, stop replacing \n Output with \r\n, etc"""

        fileno = self.fileno
        before = self.before
        tcgetattr = self.tcgetattr

        if tcgetattr:
            return self

        tcgetattr = termios.tcgetattr(fileno)  # replaces
        assert tcgetattr, (tcgetattr,)

        self.tcgetattr = tcgetattr  # replaces

        assert before in (termios.TCSADRAIN, termios.TCSAFLUSH), (before,)
        tty.setraw(fileno, when=before)  # Tty SetRaw defaults to TcsaFlush
        # tty.setcbreak(fileno, when=termios.TCSAFLUSH)  # for ⌃C prints Py Traceback

        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        r"""Start line-buffering Input, start replacing \n Output with \r\n, etc"""

        stdio = self.stdio
        fileno = self.fileno
        tcgetattr = self.tcgetattr
        after = self.after

        if not tcgetattr:
            return

        self.tcgetattr = list()  # replaces

        stdio.flush()  # for '__exit__' of BytesTerminal

        assert after in (termios.TCSADRAIN, termios.TCSAFLUSH), (after,)

        fd = fileno
        when = after
        attributes = tcgetattr
        termios.tcsetattr(fd, when, attributes)

        return None

    def kbhit(self, timeout: float | None) -> bool:
        """Block till next Input Byte, else till Timeout, else till forever"""

        fileno = self.fileno
        stdio = self.stdio
        assert self.tcgetattr, self.tcgetattr

        stdio.flush()  # for .kbhit of BytesTerminal

        (r, w, x) = select.select([fileno], [], [], timeout)
        fileno_hit = fileno in r

        return fileno_hit

        # 'timeout' is None for Never, 0.000 for Now, else a count of Seconds
        # but our timeout=Immediately fearfully ducks away as far as 0.000_001 from the 0.000 of Now

    #
    # Read one Keyboard Chord, Mouse Arrow Burst, Mouse Click, or Mouse Tap
    #

    def read_terminal_poke(self, timeout: float | None) -> TerminalPoke:
        """Read one Keyboard Chord, Mouse Arrow Burst, Mouse Click, or Mouse Tap"""

        fileno = self.fileno
        stdio = self.stdio

        # Flush Output, and wait for Input

        stdio.flush()

        t0 = time.time()
        kbhit = self.kbhit(timeout=timeout)
        t1 = time.time()

        hit = t1 - t0
        if not kbhit:
            tp = TerminalPoke(hit=hit, reads=tuple(), delays=tuple(), extra=b"")
            return tp

        # Read Bursts of Bytes

        delay_list = list()
        read_list = list()

        fd = fileno
        length = 1

        t = t1
        while True:

            read = os.read(fd, length)
            while self.kbhit(timeout=0.000_001):
                read += os.read(fd, length)
            t2 = time.time()

            delay_list.append(t2 - t)
            read_list.append(read)
            t = t2

            # Exactly once, write the ⎋[5 N Call for the ⎋[0 N Reply to close Input

            if len(read_list) == 1:
                stdio.write("\033[5n")
                stdio.flush()

            late_bytes = b"".join(read_list[1:])

            # Take quick and slow Inputs till the closing ⎋[0 N Reply does arrive

            m = re.search(rb"\033\[0n", string=late_bytes)
            if m:
                break

        # Succeed

        reads = tuple(read_list)
        delays = tuple(delay_list)
        extra = late_bytes[m.end() :]

        tp = TerminalPoke(hit=hit, reads=reads, delays=delays, extra=extra)

        return tp


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
        extra = self.extra

        assert reads, (reads,)
        assert len(reads) == len(delays), (len(reads), len(delays))
        assert not extra  # todo1: wait to solve Str of .extra till after we learn to repro it

        close = reads[-1]
        assert close.endswith(b"\033[0n"), (close,)

    def __str__(self) -> str:

        hit = self.hit
        reads = self.reads
        delays = self.delays

        if not reads:
            delay = blur(hit + sum(delays)).replace("e-3", "")
            rep = delay
            return rep

        chord = self._chord_str_if_()
        if chord:
            return chord

        arrows = self._arrow_burst_str_if_()
        if arrows:
            return arrows

        kbytes = b"".join(reads[:-1])
        precise = kbytes_to_precise_kcaps(kbytes)

        delay = blur(hit + sum(delays)).replace("e-3", "")
        rep = f"{precise} {delay}"

        return rep

    def _chord_str_if_(self) -> str:
        """Say what we got for Input, and how long we waited, when it's a Keyboard Chord"""

        hit = self.hit
        delays = self.delays
        reads = self.reads

        if len(reads) != 2:
            return ""

        read = reads[0]
        assert read == b"".join(reads[:-1]), (read, reads[:-1])

        concise = kbytes_to_concise_kcaps_if(read)
        precise = kbytes_to_precise_kcaps(read)

        if concise:
            delay = blur(hit + sum(delays)).replace("e-3", "")
            if concise == precise:
                rep = f"{concise} {read.decode()!r} {delay}"
            else:
                rep = f"{concise} {precise} {delay}"
            return rep

        if len(precise.lstrip("⌃⌥⇧")) == 1:  # ⇧ ⌃ ⌥ would be sorted by Ord
            delay = blur(hit + sum(delays)).replace("e-3", "")
            rep = f"{precise} {delay}"
            return rep

        return ""

    def _arrow_burst_str_if_(self) -> str:
        """Say what we got for Input, and how long we waited, when it's an Arrow Burst"""

        hit = self.hit
        delays = self.delays
        reads = self.reads

        kbytes = b"".join(reads[:-1])

        dy_dx_by_arrow_kbytes = DY_DX_BY_ARROW_KBYTES

        # Require >= 4 triple-byte sequences

        if len(kbytes) % 3:
            return ""  # requires a burst of triple-bytes

        if len(kbytes) < (4 * 3):
            return ""

        # Require nothing but ⎋[A ⎋[B ⎋[C ⎋[D plain Arrow Keystroke Chords

        count_by_arrow: dict[bytes, int]
        count_by_arrow = collections.defaultdict(int)

        arrows = list()
        for index in range(0, len(kbytes), 3):
            triple = kbytes[index:][:3]
            if triple not in dy_dx_by_arrow_kbytes.keys():
                return ""

            arrow = triple
            arrows.append(arrow)
            count_by_arrow[arrow] += 1

            # often tested with only 1 or 2 kinds of arrows per burst

        # Say briefly how many Arrows came in what order

        parts = list()
        for k, vv in itertools.groupby(arrows):
            n = len(list(vv))
            concise = kbytes_to_concise_kcaps_if(k)

            s = concise
            s = s.replace("←", "*Lt")
            s = s.replace("↑", "*Up")
            s = s.replace("→", "*Rt")
            s = s.replace("↓", "*Dn")

            part = f"{n}{s}"
            parts.append(part)

        join = "+".join(parts)
        # join += str(kbytes)

        # Say how long we waited

        delay = blur(hit + sum(delays)).replace("e-3", "")
        join += " " + delay

        # Succeed

        return join

    # todo1: stop calling for the close to delay text

    # todo1: testing app to go from dim to bold when key found
    # todo1: 8 keyboards | unmarked, ⌃, ⌥, ⇧ | ⌥⇧, ⌃⇧, ⌃⌥ | ⌃⌥⇧


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

KCAP_BY_KTEXT = {  # r"←|↑|→|↓" and so on  # ⌃ ⌥ ⇧ ⌃⌥ ⌃⇧ ⌥⇧ ⌃⌥⇧ and so on
    "\x00": "⌃Spacebar",  # ⌃@  # ⌃⇧2
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
    "\033" "\033[" "3;5~": "⎋⌃FnDelete",  # ⌥⌃FnDelete
    "\033" "\033[" "A": "⌥↑",  # CSI 04/01 Cursor Up (CUU)  # Option-as-Meta  # Google
    "\033" "\033[" "B": "⌥↓",  # CSI 04/02 Cursor Down (CUD)  # Option-as-Meta  # Google
    "\033" "\033[" "C": "⌥→",  # CSI 04/03 Cursor [Forward] Right (CUF_X)  # Google
    "\033" "\033[" "D": "⌥←",  # CSI 04/04 Cursor [Back] Left (CUB_X)  # Google
    "\033" "\033[" "Z": "⎋⇧Tab",  # ⇤  # CSI 05/10 CBT  # not ⌥⇧Tab
    "\033" "\x28": "⎋FnDelete",  # not ⌥FnDelete
    "\033O" "P": "F1",  # SS3 ⇧P
    "\033O" "Q": "F2",  # SS3 ⇧Q
    "\033O" "R": "F3",  # SS3 ⇧R
    "\033O" "S": "F4",  # SS3 ⇧S
    "\033[" "15~": "F5",  # Esc 07/14 is LS1R, but CSI 07/14 is unnamed
    "\033[" "17~": "F6",  # ⌥F1  # ⎋F1
    "\033[" "18~": "F7",  # ⌥F2  # ⎋F2
    "\033[" "19~": "F8",  # ⌥F3  # ⎋F3
    "\033[" "1;2A": "⇧↑",  # iTerm2 Apple
    "\033[" "1;2B": "⇧↓",  # iTerm2 Apple
    "\033[" "1;2C": "⇧→",  # CSI 04/03 Cursor [Forward] Right (CUF_YX) Y=1 X=2  # Apple
    "\033[" "1;2D": "⇧←",  # CSI 04/04 Cursor [Back] Left (CUB_YX) Y=1 X=2  # Apple
    "\033[" "1;2F": "⇧Fn→",  # iTerm2 Apple
    "\033[" "1;2H": "⇧Fn←",  # iTerm2 Apple
    "\033[" "1;3A": "⌥↑",  # iTerm2 Apple
    "\033[" "1;3B": "⌥↓",  # iTerm2 Apple
    "\033[" "1;3C": "⌥→",  # iTerm2 Apple
    "\033[" "1;3D": "⌥←",  # iTerm2 Apple
    "\033[" "1;3F": "⌥Fn→",  # iTerm2 Apple
    "\033[" "1;3H": "⌥Fn←",  # iTerm2 Apple
    "\033[" "1;4A": "⌥⇧↑",  # iTerm2 Apple
    "\033[" "1;4B": "⌥⇧↓",  # iTerm2 Apple
    "\033[" "1;4C": "⌥⇧→",  # iTerm2 Apple
    "\033[" "1;4D": "⌥⇧←",  # iTerm2 Apple
    "\033[" "1;4F": "⌥⇧Fn→",  # iTerm2 Apple
    "\033[" "1;4H": "⌥⇧Fn←",  # iTerm2 Apple
    "\033[" "1;6A": "⌃⇧↑",  # iTerm2 Apple
    "\033[" "1;6B": "⌃⇧↓",  # iTerm2 Apple
    "\033[" "1;6C": "⌃⇧→",  # iTerm2 Apple
    "\033[" "1;6D": "⌃⇧←",  # iTerm2 Apple
    "\033[" "1;7A": "⌃⌥↑",  # iTerm2 Apple
    "\033[" "1;7B": "⌃⌥↓",  # iTerm2 Apple
    "\033[" "1;7C": "⌃⌥→",  # iTerm2 Apple
    "\033[" "1;7D": "⌃⌥←",  # iTerm2 Apple
    "\033[" "1;7F": "⌃⌥Fn←",  # iTerm2 Apple
    "\033[" "1;7H": "⌃⌥Fn→",  # iTerm2 Apple
    "\033[" "1;8A": "⌃⌥⇧↑",  # iTerm2 Apple
    "\033[" "1;8B": "⌃⌥⇧↓",  # iTerm2 Apple
    "\033[" "1;8C": "⌃⌥⇧→",  # iTerm2 Apple
    "\033[" "1;8D": "⌃⌥⇧←",  # iTerm2 Apple
    "\033[" "20~": "F9",  # ⌥F4  # ⎋F4
    "\033[" "21~": "F10",  # ⌥F5  # ⎋F5
    "\033[" "23~": "F11",  # ⌥F6  # ⎋F6  # Apple takes F11
    "\033[" "24~": "F12",  # ⌥F7  # ⎋F7
    "\033[" "25~": "⇧F5",  # ⌥F8  # ⎋F8
    "\033[" "26~": "⇧F6",  # ⌥F9  # ⎋F9
    "\033[" "28~": "⇧F7",  # ⌥F10  # ⎋F10
    "\033[" "29~": "⇧F8",  # ⌥F11  # ⎋F11
    "\033[" "31~": "⇧F9",  # ⌥F12  # ⎋F12
    "\033[" "32~": "⇧F10",
    "\033[" "33~": "⇧F11",
    "\033[" "34~": "⇧F12",
    "\033[" "3;2~": "⇧FnDelete",
    "\033[" "3;5~": "⌃FnDelete",
    "\033[" "3~": "FnDelete",
    "\033[" "5;3~": "⌥Fn↑",  # iTerm2 Apple
    "\033[" "5;4~": "⌥⇧Fn↑",  # iTerm2 Apple
    "\033[" "5;7~": "⌃⌥Fn↑",  # iTerm2 Apple
    "\033[" "5~": "⇧Fn↑",  # Apple
    "\033[" "6;3~": "⌥Fn↓",  # iTerm2 Apple
    "\033[" "6;4~": "⌥⇧Fn↓",  # iTerm2 Apple
    "\033[" "6;7~": "⌃⌥Fn↓",  # iTerm2 Apple
    "\033[" "6~": "⇧Fn↓",  # Apple
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
    "\x7f": "Delete",  # ␡  # ⌫  # ⌦
    "\xa0": "⌥Spacebar",  # '\N{No-Break Space}'
}

assert list(KCAP_BY_KTEXT.keys()) == sorted(KCAP_BY_KTEXT.keys())

assert KCAP_SEP == " "
for _KCAP in KCAP_BY_KTEXT.values():
    assert " " not in _KCAP, (_KCAP,)


OPTION_KSTR_BY_KT = {
    "á": "⌥EA",  # E
    "é": "⌥EE",
    "í": "⌥EI",
    # without the "j́" of ⌥EJ here (because its Combining Accent comes after as a 2nd K Char)
    "ó": "⌥EO",
    "ú": "⌥EU",
    "´": "⌥ESpacebar",
    "é": "⌥EE",
    "â": "⌥IA",  # I
    "ê": "⌥IE",
    "î": "⌥II",
    "ô": "⌥IO",
    "û": "⌥IU",
    "ˆ": "⌥ISpacebar",
    "ã": "⌥NA",  # N
    "ñ": "⌥NN",
    "õ": "⌥NO",
    "˜": "⌥NSpacebar",
    "ä": "⌥UA",  # U
    "ë": "⌥UE",
    "ï": "⌥UI",
    "ö": "⌥UO",
    "ü": "⌥UU",
    "ÿ": "⌥UY",
    "¨": "⌥USpacebar",
    "à": "⌥`A",  # `
    "è": "⌥`E",
    "ì": "⌥`I",
    "ò": "⌥`O",
    "ù": "⌥`U",
    "`": "⌥`Spacebar",  # ⌥` Spacebar comes out equal to U+0060 Grave Accent ` of a US Keyboard
}

# hand-sorted by ⌥E ⌥I ⌥N ⌥U ⌥` order


def kbytes_to_concise_kcaps_if(kbytes: bytes) -> str:
    """Choose Keycaps to speak of the Bytes of 1 Keyboard Chord"""

    kstr = kbytes.decode()  # may raise UnicodeDecodeError
    kcap_by_ktext = KCAP_BY_KTEXT  # '\e\e[A' for ⎋↑ etc
    assert KCAP_SEP == " "

    concise = ""
    if kstr in kcap_by_ktext.keys():
        concise = kcap_by_ktext[kstr]

    assert " " not in concise, (concise,)

    return concise

    # ⌥Y often comes through as \ U+005C Reverse-Solidus aka Backslash  # not ¥ Yen-Sign

    # 'A'
    # '⌃L'
    # '⇧Z'
    # '⎋9' from ⌥9 while Apple Keyboard > Option as Meta Key


def kbytes_to_precise_kcaps(kbytes: bytes) -> str:
    """Choose 1 Keycaps per Character tos peak of the Bytes of 1 Keyboard Chord"""

    assert kbytes, (kbytes,)

    kstr = kbytes.decode()  # may raise UnicodeDecodeError
    assert KCAP_SEP == " "

    precise = ""
    for kt in kstr:  # often 'len(kstr) == 1'
        kc = _kt_to_kcap_(kt)
        precise += kc

    assert " " not in precise, (precise,)

    return precise

    # '⎋[25;80R' Cursor-Position-Report (CPR)
    # '⎋[25;80t' Rows x Column Terminal Size Report

    # '⎋[200~' and '⎋[201~' before/ after Paste to bracket it


def _kt_to_kcap_(kt: str) -> str:
    """Form 1 Key Cap to speak of 1 Keyboard Chord"""

    ko = ord(kt)

    option_kt_str = OPTION_KT_STR  # '∂' for ⌥D
    option_kstr_by_kt = OPTION_KSTR_BY_KT  # 'é' for ⌥EE
    kcap_by_ktext = KCAP_BY_KTEXT  # '\x7F' for 'Delete'

    # Show more Key Caps than US-Ascii mentions

    if kt in '!"#$%&()*+' ":<>?" "@" "^_" "{|}~":
        kc = "⇧" + kt

    elif kt in kcap_by_ktext.keys():  # Mac US Key Caps for Spacebar, F12, etc
        kc = kcap_by_ktext[kt]  # '⌃Spacebar', 'Return', 'Delete', etc

    elif (kt != "`") and (kt in option_kstr_by_kt.keys()):  # Mac US Option Accents
        kc = option_kstr_by_kt[kt]

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

        # todo0: have we fuzzed b"\xA1" .. FF vs "\u00A1" .. 00FF like we want?

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

# todo1: more test of combining accents - like ⌥⇧I should come through as itself not as ⌥ISpacebar ?


def _option_kt_to_kcap_(kt: str) -> str:
    """Convert to Mac US Option Key Caps from any of OPTION_KT_STR"""

    option_kt_str = OPTION_KT_STR  # '∂' for ⌥D, etc
    assert len(OPTION_KT_STR) == (0x7E - 0x20) + 1

    index = option_kt_str.index(kt)

    end = chr(0x20 + index)
    if "A" <= end <= "Z":
        end = "⇧" + end  # '⇧A'
    if "a" <= end <= "z":
        end = chr(ord(end) ^ 0x20)  # 'Z'

    kc = "⌥" + end  # '⌥⇧P'

    return kc


# Define each KText once, never more than once

_KTEXT_LISTS_ = [
    list(KCAP_BY_KTEXT.keys()),
    list(OPTION_KSTR_BY_KT.keys()),
    list(_SPACELESS_OPTION_KT_STR_),
]

_KTEXT_UNROLL_ = list(_KTEXT_ for _KTEXT_LIST_ in _KTEXT_LISTS_ for _KTEXT_ in _KTEXT_LIST_)
for _KTEXT_, _COUNT_ in collections.Counter(_KTEXT_UNROLL_).items():
    assert _COUNT_ == 1, (_COUNT_, _KTEXT_)


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
# Run from the Shell Command Line, if not imported
#


if __name__ == "__main__":
    main()


# 3456789 123456789 123456789 123456789 123456789 123456789 123456789 123456789 123456789 123456789

# posted into:  https://github.com/pelavarre/easter-ugg-studio/blob/main/bin/easter-ugg-studio.py
# copied from:  git clone git@github.com:pelavarre/easter-ugg-studio.git
