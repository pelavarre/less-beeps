#!/usr/bin/env python3

r"""
usage: less-beeps.py [-h] [-y] [-f] [--egg EGG]

give away nine classic simple terminal games for you to fork now

options:
  -h, --help   show this help message and exit
  -y, --yolo   do what's popular now (can also be spelled as '--')
  -f, --force  ask fewer questions (launches slowly enough to complete self-test's)
  --egg EGG    toss in another easter egg, such as 'native' or 'sigint'

notes:
  travels as a single .py file, now that a million words isn't many words
  travels with an easter-eggs .md file

examples:
  bin/@
  ./bin/less-beeps.py --yolo
  ./bin/less-beeps.py --egg=native --egg=sigint  # emulations off, but ⌃C to quit
"""
# todo6: ./bin/less-beeps.py --egg=inband  # don't hide the out-of-band replies

# code reviewed by People, Black, Flake8, Mypy-Strict, & Pylance-Standard


from __future__ import annotations  # backports new datatype syntaxes into old Pythons

import __main__  # for to parse the __main__.__doc__
import argparse
import bdb  # for to catch bdb.BdbQuit
import collections
import collections.abc  # .abc is not .collections.abc
import dataclasses
import difflib
import itertools
import json
import logging
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
import urllib.parse


_: object  # blocks Mypy from narrowing the Datatype of '_ =' at first mention

_ = json, urllib.parse  # imports only needed inside of breakpoints, etc


default_eq_None = None  # shoves back on Dict Get refusing the explicit ', default=' syntax

if not __debug__:
    raise NotImplementedError([__debug__])  # because 'python3 better than python3 -O'


logger = logging.getLogger(__name__)


#
# Choose a personality
#


@dataclasses.dataclass(order=True)  # , frozen=True)
class Flags:
    """Choose a personality"""

    apple: bool = sys.platform == "darwin"  # flags.apple
    google: bool = bool(os.environ.get("CLOUD_SHELL", ""))  # flags.google
    terminal: bool = os.environ.get("TERM_PROGRAM", "") == "Apple_Terminal"  # flags.terminal

    portrait: bool = False  # flags.portrait, for when lots more high than wide
    barefoot: bool = False  # flags.barefoot, for when rows not-hidden beneath a Southern Keyboard

    native: bool | None = None  # flags.native, for don't make this Terminal feel friendlier
    # inband: bool | None = None  # flags.inband, for don't hide the out-of-band Replies
    sigint: bool | None = None  # flags.sigint, for ⌃C to work
    # sigtstp: bool | None = None  # flags.sigtstp  # todo2: or ⌃Z to work without ⌃C ⌃\ working

    breakpointing: bool = False  # flags.breakpointing

    # todo6: call to show just some extra info just for awhile?


flags = Flags()

# flags.breakpointing = True


#
# Run from the Shell, but tell uncaught Exceptions to launch the Py Repl
#


def main() -> None:
    """Run from the Shell, but tell uncaught Exceptions to launch the Py Repl"""

    sys.excepthook = excepthook

    os.makedirs("__pycache__", exist_ok=True)
    logging.basicConfig(filename="__pycache__/less-beeps.log", level=logging.INFO)

    parser = arg_doc_to_parser(__main__.__doc__ or "")
    shell_args_take_in(args=sys.argv[1:], parser=parser)

    with TerminalStudio() as ts:
        try:
            ts.speak_first()
            ts.chat_awhile()
        finally:
            ts.stop_chatting()


def arg_doc_to_parser(doc: str) -> ArgDocParser:
    """Declare the Positional Arguments & Options"""

    assert argparse.ZERO_OR_MORE == "*"

    parser = ArgDocParser(doc, add_help=True)

    yolo_help = "do what's popular now (can also be spelled as '--')"
    force_help = "ask fewer questions (launches slowly enough to complete self-test's)"
    egg_help = "toss in another easter egg, such as 'native' or 'sigint'"

    parser.add_argument("-y", "--yolo", action="count", help=yolo_help)
    parser.add_argument("-f", "--force", action="count", help=force_help)
    parser.add_argument("--egg", dest="eggs", metavar="EGG", action="append", help=egg_help)

    return parser


def shell_args_take_in(args: list[str], parser: ArgDocParser) -> None:
    """Take in the Shell Command-Line Args"""

    arg_doc_parser = parser  # marks ArgDocParser != argparse.ArgumentParser

    # Take in the Args without final judgment

    ns = arg_doc_parser.parse_args_if(args)  # often prints help & exits zero

    ns_keys = list(vars(ns).keys())
    assert ns_keys == ["yolo", "force", "eggs"], (ns_keys, ns, args)

    # Fail now, else fall through

    if ns.force:
        _try_less_beeps_()

    eggs = ns.eggs or list()
    for egg_text in eggs:
        egg_texts = egg_text.split(",")
        for egg in egg_texts:

            if egg and "native".startswith(egg):
                flags.native = True
            elif egg and "sigint".startswith(egg):
                flags.sigint = True

            # elif egg and "inband".startswith(egg):
            #     flags.inband = True
            # elif egg and "sigquit".startswith(egg):
            #     flags.sigquit = True
            # elif egg and "sigtstp".startswith(egg):
            #     flags.sigtstp = True

            else:
                arg_doc_parser.parser.print_usage()
                sys.exit(2)  # exits 2 for bad Arg

            # todo6: add --egg=info, --egg=debug, for 'import logging'

        # todo3: some new --egg to add ⌃Q and ⌃V into --egg=native ?


def _try_less_beeps_() -> None:
    """Run slow and quick Self-Test's of Less-Beeps·Py"""

    print("--force => KeyPack._try_key_pack_()", file=sys.stderr)
    KeyPack._try_key_pack_()

    print("--force => KeyMix._try_key_mix_()", file=sys.stderr)
    KeyMix._try_key_mix_()


#
# Run inside 1 Terminal Window Pane, till Quit
#


class TerminalStudio:
    """Run inside 1 Terminal Window Pane, till Quit"""

    selves: list[TerminalStudio] = list()

    stdio: typing.TextIO
    fileno: int
    tcgetattr: list[int | list[bytes | int]]  # replaced by .__enter__

    screen_writer: ScreenWriter
    inserting: bool  # truthy while inserting, else replacing

    keyboard_reader: KeyboardReader

    high_wide: tuple[int, ...]  # () and then (y_high, x_wide) from ⎋[18T
    row_column: tuple[int, ...]  # () and then (row_y, column_x) from ⎋[6N
    paste_row_paste_column: tuple[int, ...]  # () and then (row_y, column_x) from ⎋[200⇧~

    #
    # Init, Enter, Exit
    #

    def __init__(self) -> None:

        TerminalStudio.selves.append(self)

        assert sys.__stderr__ is not None  # refuses to run headless
        stdio = sys.__stderr__
        fileno = stdio.fileno()

        sw = ScreenWriter(self)

        kr = KeyboardReader(self, screen_writer=sw)

        self.stdio = stdio
        self.fileno = fileno
        self.tcgetattr = list()  # replaced by .__enter__

        self.screen_writer = sw
        self.inserting = False

        self.keyboard_reader = kr

        self.high_wide = tuple()
        self.row_column = tuple()
        self.paste_row_paste_column = tuple()

    def __enter__(self) -> TerminalStudio:  # todo3: re-enter after --egg=sigint ⌃Z sigtstp

        stdio = self.stdio
        fileno = self.fileno
        tcgetattr = self.tcgetattr

        sw = self.screen_writer

        assert _SM_BRACKETED_PASTE_ == "\033[" "?2004h"
        assert RM_IRM == "\x1b" "[" "4l"

        # Enter once

        if tcgetattr:
            return self

        # Flush Output, drain Input, and change Input Mode

        stdio.flush()  # before each 'tty.setraw' of TerminalStudio.__enter__

        with_tcgetattr = termios.tcgetattr(fileno)
        assert with_tcgetattr, (with_tcgetattr,)

        self.tcgetattr = with_tcgetattr  # replaces

        # Stop line-buffering Input, stop replacing \n Output with \r\n, etc

        if not flags.sigint:
            tty.setraw(fileno, when=termios.TCSADRAIN)  # todo: .when defaults to .TCSAFLUSH
        else:
            tty.setcbreak(fileno, when=termios.TCSADRAIN)  # todo: .when defaults to .TCSAFLUSH

        # Writes after entry

        if not flags.native:
            sw.swrite("\033[" "?2004h")  # asks for Start/ End Paste Marks, after entry
            sw.swrite("\033[" "4l")  # ask for Replacing, not Inserting, after entry

        # Succeed

        return self

        # todo: try termios.TCSAFLUSH to discard Input at entry
        # todo: try tty.setcbreak, especially when debugging hangs

    def __exit__(self, *args: object) -> None:

        stdio = self.stdio
        fileno = self.fileno
        tcgetattr = self.tcgetattr

        sw = self.screen_writer

        assert _RM_BRACKETED_PASTE_ == "\033[" "?2004l"

        # Exit once

        if not tcgetattr:
            return

        # Writes before exit

        if not flags.native:
            sw.swrite("\033[" "?2004l")  # asks for no Start/ End Paste Marks, after exit
            sw.swrite("\033[" "4l")  # ask for Replacing, not Inserting, after exit

        # Flush Output, drain Input, and change Input Mode

        stdio.flush()  # before each 'termios.tcsetattr' of TerminalStudio.__exit__

        fd = fileno
        when = termios.TCSADRAIN
        attributes = tcgetattr
        termios.tcsetattr(fd, when, attributes)

        self.tcgetattr = list()  # replaces

        # todo: try termios.TCSAFLUSH to discard Input at exit

    @staticmethod
    def breakpoint() -> None:
        """Redefine \n as \r\n for breakpoint'ing"""

        ts = TerminalStudio.selves[-1]

        ts.__exit__()  # no need to pass in:  *sys.exc_info()

        breakpoint()  # Pdb likes:  where, up, down, ts = None, continue
        pass  # Pdb likes:  where, up, down, ts = None, continue

        if ts:
            ts.__exit__()

        # todo: does each Breakpoint disturb ⌃C SigInt ?

    def recollect_y_x_h_w(self) -> tuple[int, ...]:
        """Fetch the Terminal Cursor Row & Column and its Window Pane Rows & Columns Size"""

        high_wide = self.high_wide
        row_column = self.row_column

        assert bool(high_wide) == bool(row_column), (high_wide, row_column)

        if not row_column:
            return tuple()

        (h, w) = self.high_wide
        (y, x) = self.row_column

        assert 1 <= y <= h, (y, x, h, w)
        assert 1 <= x <= w, (y, x, h, w)

        return (y, x, h, w)

        # macOS Terminal and Python .get_terminal_size speak of Columns x Rows    paste_row_paste_column: tuple[int, ...]

    #
    # Fetch from Keyboard
    #

    def read_one_kbyte_if(self, timeout: float | None) -> bytes:
        """Fetch one Byte from the Keyboard, else zero Bytes at Timeout"""

        fileno = self.fileno

        assert self.tcgetattr, (self.tcgetattr,)

        kbhit = self.kbhit(timeout=timeout)  # includes .stdio.flush before os.read
        if not kbhit:
            return b""

        fd = fileno
        length = 1

        kbyte = os.read(fd, length)  # todo3: test with ⌃D after ⌃Z fg, as if no __enter__
        assert kbyte, (kbyte,)  # because .tcgetattr
        assert len(kbyte) == 1, (kbyte,)  # because .length == 1

        logger.debug(f"i {kbyte!r}")

        return kbyte

    def kbhit(self, timeout: float | None) -> bool:
        """Block till next Input Byte, else till Timeout, else till forever"""

        stdio = self.stdio
        fileno = self.fileno

        assert self.tcgetattr, (self.tcgetattr,)

        stdio.flush()  # before select.select of .kbhit

        t0 = time.time()

        (r, w, x) = select.select([fileno], [], [], timeout)
        t1 = time.time()

        hit = fileno in r

        t1t0 = t1 - t0
        if t1t0 > 0.010:
            ms = int(t1t0 * 1000)
            logger.info("")  # TerminalStudio.kbhit
            logger.info(f"kbhit {ms}ms")

        return hit

    #
    # Launch, run, quit - read & eval & print
    #

    def speak_first(self) -> None:
        """Launch quickly"""

        kr = self.keyboard_reader
        sw = self.screen_writer

        if not flags.native:
            sw.sprint("⌃C to quit, Fn F1 for more help, or ⌥-Click far from the Cursor")
        else:
            if flags.sigint:
                sw.sprint("⌃C to quit, and expect ⌃J to imply ⌃M")
            else:
                sw.sprint("Close your Terminal Window Pane to quit")
                sw.sprint("Press Return to agree, press Spacebar to disagree")
                kmix = kr.read_one_key_mix()  # todo5: retire .read_one_key_mix
                if kmix.kface != "⏎":  # such as "␢"
                    sys.exit(1)

    def chat_awhile(self) -> None:
        r"""Loop and don't quit till one of ⌃C ⌃Z ⌃\ """

        sw = self.screen_writer

        sw.sprint()
        while True:
            self.loop_back()
            self.trace_key_mixes()

    def loop_back(self) -> None:  # noqa  # todo5: too complex (18
        """Loop-back the Keyboard to Screen, till ⌃C ⌃Q ⌃V etc"""

        kr = self.keyboard_reader
        sw = self.screen_writer

        assert DECSC == "\x1b" "7"
        assert DSR_6 == "\033[" "6n"
        assert XTWINOPS_18 == "\033[" "18t"

        # Loop-back the Keyboard to Screen, till ⌃C ⌃Q ⌃V etc

        self.high_wide = tuple()
        self.row_column = tuple()
        if not flags.native:
            sw.swrite("\033[" "6n")
            sw.swrite("\033[" "18t")

        slow_kbytearray = bytearray()
        while True:

            # Loop-back the Bytes at the ⎋ Esc and forget the ⎋ Esc, or don't

            if slow_kbytearray:
                assert not flags.native, (flags.native, flags)
                self.slow_kbytearray_clear_after_eval_if(slow_kbytearray)

            # Fetch more Key Mixes

            native_kmixes = kr.read_some_key_mixes()
            assert native_kmixes, (native_kmixes,)  # because .read_some_key_mixes runs timeout=None

            # Write straight through transparently, when given --egg=native

            if flags.native:
                slow_kbytearray.clear()  # todo: rarely needed
                for kmix in native_kmixes:
                    kdecode = kmix.kdecode  # maybe emptuy
                    sw.swrite(kdecode)  # todo: some new --egg for tracing native loopback?
                continue

                # todo: live lock in --egg=native loop back at reply is query?

            # Hide away the out-of-band Replies to out-of-band Queries

            inband_kmixes = list()
            for kmix_index, kmix in enumerate(native_kmixes):
                kmix_rindex = -len(native_kmixes) + kmix_index

                if self.kmix_take_away_if(kmix, kmix_rindex=kmix_rindex):
                    continue  # todo6: if not flags.inband

                inband_kmixes.append(kmix)

                # todo6: Stop losing the inband Replies to inband Queries
                # todo: less silence over out-of-band Replies

                # todo7: Renumber the todo's so the todo: and todo9: are the never real

            if not inband_kmixes:
                continue

            # Convert Burst of Pn Arrows to a Mouse Click Release

            kmixes = list(inband_kmixes)  # because 'copied is better than aliased'
            leap_kmix = self.kmixes_to_leap_kmix(inband_kmixes)
            if leap_kmix:
                kmixes = [leap_kmix]

            # Take up each Key Mix, in order

            kmix = KeyMix()  # else Pylance Standard wrongly fears .kmix unbound

            slow_kbytes = bytes(slow_kbytearray)
            for kmix_index, kmix in enumerate(kmixes):
                kmix_rindex = -len(kmixes) + kmix_index
                assert kmix, (kmix, kmix_index, kmix_rindex)

                # Snoop a Python Int Literal, if weakly present or strongly present

                (strong_int, weak_int) = self.slow_kbytes_to_strong_weak_ints(slow_kbytes)
                if strong_int != 1:
                    assert weak_int == strong_int, (weak_int, strong_int)

                # Take the Key Mix as a Repeated Instruction

                ok = False

                ok = ok or self.answer_pasted_kmix(kmix)  # todo3: Pastes don't repeat

                if not ok:
                    if strong_int == 1:
                        ok = ok or self.answer_printable_kmix(kmix)
                        if ok:
                            slow_kbytearray.extend(kmix.kencode)

                    # Printables don't repeat when cued weakly, or not cued

                if not ok:
                    if weak_int > 0:  # todo3: Repeat Count 0 of a bound Key Mix Sequence
                        for _ in range(weak_int):

                            ok = False

                            if strong_int != 1:
                                ok = ok or self.answer_printable_kmix(kmix)

                                # Printables do repeat when cued strongly

                            ok = ok or self.answer_controls_kmix(kmix)

                            ok = ok or self.answer_arrows_kmix(kmix)

                            if not ok:
                                break

                            # Controls and Arrows do repeat when cued weakly

                    if ok:
                        slow_kbytearray.clear()

                if not ok:
                    ok = ok or self.answer_leap_kmix(kmix, weak_int=weak_int)
                    if ok:
                        slow_kbytearray.clear()

                        # Mouse Leaps don't repeat, not even when strongly cued

                # Take the Key Mix as an Input of no immediate clear meaning

                if not ok:

                    slow_kbytearray.extend(kmix.kencode)

                    if kmix.kface == "⎋":  # such as <> ⌃U b'\x15'
                        sw.swrite("\033" "7")  # drops a pin where the ⎋ Esc came in

                if not ok:
                    if kmix.kface:
                        sw.sprint(kmix.kface, end="")
                    elif kmix.kcaps:
                        sw.sprint(kmix.kcaps, end="")
                    else:
                        sw.sprint(kmix.kencode, end="")

                # Exit at any of ⌃C ⌃Z ⌃\

                if kmix.kcaps in ("⌃C", "⌃Z", "⌃\\"):
                    sw.sprint()
                    sys.exit()

            # Stop looping back at ⌃Q or ⌃V

            if kmix.kcaps in ("⌃Q", "⌃V"):
                break

            # Refresh the calls for Terminal Height Width and Cursor Y X

            if not flags.native:
                if self.high_wide:
                    self.high_wide = tuple()  # replaces
                    sw.swrite("\033[" "18t")
                if self.row_column:
                    self.row_column = tuple()  # replaces
                    sw.swrite("\033[" "6n")

        # todo4: stop disturbing the ⎋7 Alt Cursor

        # todo1: celebrate how our ⇥ Tab and ⇧⇥ ⇧Tab do speed up and snap-to-grid the → and ←
        # todo1: livelocks less wild in Keyboard/ Screen loopback

    def slow_kbytearray_clear_after_eval_if(self, slow_kbytearray: bytearray) -> None:
        """Loop back the Key Bytes after the ⎋ Esc and forget them, else don't"""

        slow_kbytes = bytes(slow_kbytearray)
        (kpack, strong_int, weak_int) = self.slow_kbytes_to_truthy_kpack_if(slow_kbytes)
        if kpack:
            self.slow_kbytearray_clear_after_if(
                slow_kbytearray, kpack=kpack, strong_int=strong_int, weak_int=weak_int
            )

    def slow_kbytes_to_truthy_kpack_if(self, slow_kbytes: bytes) -> tuple[KeyPack, int, int]:
        """Discover a Slow Key Pack at the Esc, else return empty"""

        assert DL_Y == "\033[" "{}M"

        # Collect the Bytes of one incomplete or complete Key Pack

        kpack = KeyPack(b"")
        extra = b""

        esc_rfind = slow_kbytes.rfind(b"\033")
        if esc_rfind < 0:
            return (KeyPack(b""), -1, -1)

        end_kbytearray = slow_kbytes[esc_rfind:]
        for kord in end_kbytearray:
            kbyte = bytes([kord])

            extra = kpack.take_one_kbyte_if(kbyte)
            if extra:
                return (KeyPack(b""), -1, -1)

        # Snoop a Python Int Literal, if weakly present or strongly present, behind the ⎋ Esc

        upto_esc_kbytes = slow_kbytes[:esc_rfind]

        (strong_int, weak_int) = self.slow_kbytes_to_strong_weak_ints(upto_esc_kbytes)
        if strong_int != 1:
            assert weak_int == strong_int, (weak_int, strong_int)

        # Resolve the ambiguities of ⇧M after ⎋

        kencode = kpack.to_kbytes()
        if kencode == b"\033[M":  # DL_Y without Pn
            if weak_int > 0:
                kpack.close()
        else:
            (kintsmark, kints) = KeyMix.to_csi_shift_m6_ints_if(kbytes=kencode)
            if kintsmark:
                kpack.close()

        # Give up if still not closed

        if not kpack.closed:
            return (KeyPack(b""), -1, -1)

        # Succeed

        return (kpack, strong_int, weak_int)

    def slow_kbytearray_clear_after_if(
        self, slow_kbytearray: bytearray, kpack: KeyPack, strong_int: int, weak_int: int
    ) -> None:
        """Eval or loop back the Slow Key Pack at the Esc, else return empty"""

        kencode = kpack.to_kbytes()

        sw = self.screen_writer

        # todo: assert names for "\033[" "<{};{};{}" "M", "\033[" "<{};{};{}" "m"

        assert DECRC == "\x1b" "8"

        assert CUP_Y_X == "\033[" "{};{}H"
        assert ED_P == "\x1b" "[" "{}J"
        assert DL_Y == "\033[" "{}M"

        assert _START_PASTE_ == "\033[" "200~"
        assert _END_PASTE_ == "\033[" "201~"

        #
        # Go ahead and emulate the Key Packs that don't loop back reasonably well
        #

        # Emulate Tap or Mouse Press or Release

        leap_kencode = KeyMix.kencode_to_leap_if(kencode)
        leap_kdecode = leap_kencode.decode()
        if leap_kdecode:
            if weak_int > 0:

                leap_kmix = KeyMix(kencode)
                ok = self.answer_leap_kmix(leap_kmix, weak_int=weak_int)

                assert ok, (ok, leap_kmix)
                return

                # doesn't loop back and doesn't repeat, if Tap or Mouse Press or Release

        kdecode = kencode.decode()
        if weak_int <= 0:
            if leap_kdecode:

                (kintsmark, kints) = KeyMix.to_csi_shift_m6_ints_if(kbytes=kencode)
                if kintsmark:
                    assert kintsmark in (b"::", b":;"), (kintsmark, kencode)
                    (b, x, y) = kints
                    if kintsmark == b"::":
                        kdecode = f"⎋[⇧M:{bin(b)}:{x}:{y}"  # '⎋[⇧M:0b11:80:25'
                    else:
                        kdecode = f"⎋[⇧M:{bin(b)};{x};{y}"  # '⎋[⇧M:0b11;80;25'
                else:
                    fm = re.fullmatch(r"..<([0-9]+);([0-9]+);([0-9]+)(.)", string=leap_kdecode)
                    assert fm, (fm, leap_kdecode, kencode)

                    f = int(fm.group(1))
                    x = int(fm.group(2))
                    y = int(fm.group(3))
                    backtail = fm.group(4)

                    kdecode = f"⎋[<{f};{x};{y}{backtail}"  # '⎋[<8;80;25m'

        # Take and clear the slow-to-arrive Key Pack

        slow_kbytearray.clear()

        # Write like macOS ⎋C, but cut down to no more than ⎋[⇧H ⎋[2⇧J screen-erase
        # Write like macOS ⎋D and ⎋L, but in terms of ⎋E and ⎋[⇧H

        swrite = kdecode
        if not flags.native:
            if kdecode == "\033" "c":  # ⎋C
                swrite = "\033[" "H" "\033[" "2J"  # as if ⎋[⇧H ⎋[2⇧J screen-erase
            elif kdecode == "\033" "D":  # ⎋⇧D
                swrite = "\033" "E"  # ⎋⇧E as if ⌃M ⌃J  # todo: prefer "\r\n"?
            elif kdecode == "\033" "l":  # ⎋L
                swrite = "\033[" "H"  # as if ⎋[⇧H leap to the far Northwest

            # ⎋[⇧H ⎋[2⇧J more popular than ⎋[⇧J ⎋[⇧H etc

            # todo6: comment what works without emulation?
            # todo6: does ⎋⇧M work for our all Terminals under test? does ⎋C never clear scrollback?

        # Write at the ⎋ Esc, not beyond the Key Pack

        sw.swrite("\033" "8")

        # Write the Bytes if repeating non-negative'ly
        # Write the Py Repr of Bytes if repeating negatively

        if weak_int <= 0:  # todo3: synch the two chunks of Code defining Repeat Count
            sw.swrite(repr(swrite))
        else:
            for _ in range(weak_int):
                sw.swrite(swrite)
                self._announce_inserting_replacing_if_(swrite)

        # todo: loops back both of (b"\033[200~", b"\033[201~") into sw.write, mostly harmlessly

    #
    # todo6: shuffle Def's of Class TerminalStudio into a more meaningful arrangement
    #

    def kmix_take_away_if(self, kmix: KeyMix, kmix_rindex: int) -> bool:
        """Say if the Key Mix is not for Loop Back to answer"""

        kencode = kmix.kencode

        assert DSR_5 == "\033[" "5n"
        assert DSR_0 == "\033[" "0n"

        assert DSR_6 == "\033[" "6n"
        assert CPR_Y_X == "\033[" "{};{}R"

        assert XTWINOPS_18 == "\033[" "18t"
        assert XTWINOPS_8_H_W == "\033[" "8;{};{}t"

        # Take the DSR_0 ⎋[0N close of each DSR_5 ⎋[5N Frame

        if kmix_rindex == -1:
            if kencode == b"\033[0n":
                assert not kmix.kface, (kmix.kface, kmix.kcaps, kmix)
                return True

        # Take the ⎋[8T XTWINOPS_8_H_W reply to ⎋[18T XTWINOPS_18

        fm = re.fullmatch(rb"\033\[8;([0-9]+);([0-9]+)t", string=kencode)
        if fm:
            y_high = int(fm.group(1))
            x_wide = int(fm.group(2))
            self.high_wide = (y_high, x_wide)  # replaces
            return True

        # Take the ⎋[y;xR CPR_Y_X reply to ⎋[6n DSR_6

        fm = re.fullmatch(rb"\033\[([0-9]+);([0-9]+)R", string=kencode)
        if fm:
            y_row = int(fm.group(1))
            x_column = int(fm.group(2))
            self.row_column = (y_row, x_column)  # replaces
            return True

        # Else don't take the Key Mix

        return False

    def kmixes_to_leap_kmix(self, kmixes: list[KeyMix]) -> KeyMix:
        """Convert Burst of Pn Arrows to a Mouse Click Release"""

        assert kmixes, (kmixes,)

        assert CUU_Y == "\033[" "{}A"
        assert CUD_Y == "\033[" "{}B"
        assert CUF_X == "\033[" "{}C"
        assert CUB_X == "\033[" "{}D"

        # Take up each Key Mix, in order

        pn_arrows = list(_.kencode for _ in kmixes)

        y_x_h_w: tuple[int, ...] = tuple()
        (y, x, h, w) = (-1, -1, -1, -1)

        for kmix_index, kmix in enumerate(kmixes):
            kpack = KeyPack(kmix.kencode)  # much like kmix.kpack but maybe not .closed

            pn = -1

            backtail = bytes(kpack.back + kpack.tail)
            if kpack.head == b"\033[":
                if backtail in (b"A", b"B", b"C", b"D"):
                    fm = re.fullmatch(rb"[0-9]+", string=kpack.neck)
                    if fm:

                        pn = int(kpack.neck)

            if pn < 0:
                return KeyMix()

            # Accept a Run-Length Compression of an Arrow

            if kmix_index == 0:
                y_x_h_w = self.recollect_y_x_h_w()  # replaces
                (y, x, h, w) = y_x_h_w  # replaces

            assert 1 <= y <= h, (y, x, h, w)  # true here because true far above
            assert 1 <= x <= w, (y, x, h, w)  # ditto

            if backtail == b"A":  # ↑
                y -= pn
            elif backtail == b"B":  # ↓
                y += pn
            elif backtail == b"C":  # →
                x += pn
            elif backtail == b"D":  # ←
                x -= pn
            else:
                return KeyMix()

            assert 1 <= y <= h, (y, x, h, w, y_x_h_w, pn_arrows)  # Pn Arrows don't wrap Y

            # Wrap around the Left/ Right Screen Edges (unlike the classic ⎋[⇧C and ⎋[⇧D)

            assert 1 <= y <= h, (y, x, h, w, y_x_h_w, pn_arrows)  # y = min(max(1, y), h)

            while x < 1:
                x += w
                y -= 1

                assert 1 <= y <= h, (y, x, h, w, y_x_h_w, pn_arrows)  # y = min(max(1, y), h)

            while x > w:
                x -= w
                y += 1

                assert 1 <= y <= h, (y, x, h, w, y_x_h_w, pn_arrows)  # y = min(max(1, y), h)

            assert 1 <= y <= h, (y, x, h, w, y_x_h_w, pn_arrows)  # y = min(max(1, y), h)

        # Fabricate a Touch Tap Release or Mouse Click Release

        f = int("0b01000", base=0)  # f = 0b⌃⌥⇧00
        kencode = f"\033[<{f};{x};{y}m".encode()

        leap_kmix = KeyMix(kencode)
        assert leap_kmix, (leap_kmix,)

        # Succeed

        return leap_kmix

    def _announce_inserting_replacing_if_(self, swrite: str) -> bool:
        """Announce ⎋[ 4 H written for Inserting, or ⎋[ 4 L written for Replacing"""

        kbytes = swrite.encode()

        try:
            (kintsmark, kints) = KeyMix.to_csi_ints_if(kbytes)
        except ValueError:
            return False

        if kintsmark not in (b"h", b"l"):
            return False

        if 4 not in kints:
            return False

        if kintsmark == b"h":
            self.inserting = True
        else:
            assert kintsmark == b"l", (kintsmark,)
            self.inserting = False

        return True

    def slow_kbytes_to_strong_weak_ints(self, kbytes: bytes) -> tuple[int, int]:
        """Glance into our Key Log of Bytes and say it ends with a Python Int Literal, or not"""

        if not kbytes:
            return (1, 1)

        # Look at the End of the Key Log, inside ⌃U ... ⌃U or not

        indexed_kbytes = bytearray(kbytes)  # because 'better copied than aliased'

        past_kbytes = indexed_kbytes
        if indexed_kbytes.endswith(b"\x15"):  # ⌃U  # of Emacs Repeat Count tradition
            indexed_kbytes_minus = past_kbytes[:-1]
            rfind = indexed_kbytes_minus.rfind(b"\x15")  # ⌃U
            if rfind >= 0:
                past_kbytes = indexed_kbytes_minus[rfind:][1:]

        # Look at the End of the Key Log, inside ⌃U ... ⌃U or not

        count: int | None
        count = None

        strongly_present = False
        for index in range(len(past_kbytes)):
            reversed_rindex = -1 - index
            count_kbytearray = past_kbytes[reversed_rindex:]

            count_head = count_kbytearray[:1]
            if count_head not in b"+-" b"0123456789" b"ABCDEFOX_" b"abcdefox":  # rejects '.eE'
                break

            try:
                count = int(count_kbytearray, 0)
            except ValueError:
                continue

            if indexed_kbytes.endswith(b"\x15" + count_kbytearray + b"\x15"):  # ⌃U ... ⌃U
                assert not strongly_present, (strongly_present, count_kbytearray)
                strongly_present = True
            elif indexed_kbytes.endswith(b"\x15"):
                assert not strongly_present, (strongly_present, count_kbytearray)
                count = None
                continue

        # Strongly say 1 unless strongly told different, and weakly say 1 unless told different

        (strong_int, weak_int) = (1, 1)
        if count is not None:
            (strong_int, weak_int) = (count, count) if strongly_present else (1, count)

        if strong_int != 1:
            assert weak_int == strong_int, (weak_int, strong_int)

        return (strong_int, weak_int)

    def trace_key_mixes(self) -> None:

        sw = self.screen_writer

        kr = self.keyboard_reader
        kmixes = kr.kmixes
        entry_kmix = kmixes[-1]
        entry_kcaps = entry_kmix.kcaps

        assert DECSC == "\x1b" "7"
        assert DECRC == "\x1b" "8"
        assert DSR_0 == "\033[" "0n"
        assert CUD_Y == "\033[" "{}B"

        assert entry_kcaps in ("⌃Q", "⌃V"), (entry_kcaps,)

        # Enter the chat

        sw.swrite("\033" "7")
        sw.swrite(entry_kcaps)
        sw.swrite("\033" "8")

        # Read and print the Key Mixes of one Keyboard Chord,
        # except quit early at any of ⌃C ⌃Z ⌃\

        lock_once = False
        mark = entry_kcaps
        while True:

            kmixes = kr.read_some_key_mixes()
            assert kmixes, (kmixes,)  # because .read_some_key_mixes chooses timeout=None

            frame = ""
            framed_kmixes = kmixes
            if kmixes[1:] and kmixes[-1].kdecode == "\033[0n":
                framed_kmixes = kmixes[:-1]
                frame = " ⎋[0N"  # replied to ⎋[5N

            for index, kmix in enumerate(framed_kmixes):
                rindex = -len(framed_kmixes) + index
                str_kmix = f"{kmix}{frame}" if (rindex == -1) else str(kmix)

                sw.swrite("\033" "7")

                if len(framed_kmixes) == 1:
                    sw.sprint(mark, str_kmix, end="")
                else:
                    sw.sprint(index, mark, str_kmix, end="")

                sw.swrite("\n")  # yes the "\n" that can mean scroll up
                sw.swrite("\033" "8")
                sw.swrite("\033[" "B")  # not the "\n" that means "\r\n" while --egg=sigint

                if kmix.kcaps in ("⌃C", "⌃Z", "⌃\\"):
                    sw.sprint()
                    sys.exit()

            # Take twice entry as lock loop

            kcaps_list = list(_.kcaps for _ in kmixes)

            if kcaps_list == [entry_kcaps]:
                if not lock_once:
                    lock_once = True
                    mark = f"{entry_kcaps} {entry_kcaps}"
                    continue

            # Take once entry as break loop

            if not lock_once:
                break

            # Take thrice entry as break loop

            if kcaps_list in (["⌃Q"], ["⌃V"]):
                break

    def stop_chatting(self) -> None:
        """Drain the Buffered Input just before Quitting"""

        kr = self.keyboard_reader
        sw = self.screen_writer

        kbytearray = kr.kbytearray

        sw.sprint("bye")

        # Drain the Keyboard Buffer

        draining = False
        while self.kbhit(timeout=0.100):
            draining = True

            km = kr.read_one_key_mix()
            sw.sprint(km)

        # Drain the Keyboard Bytes fetched ahead

        kencode = bytes(kbytearray[kr.kbindex :])
        if kencode:  # todo: empty except when Exception unhandled?
            draining = True

            sw.sprint(kencode)
            sw.sprint()

        if draining:
            sw.sprint("drained")

        # todo2: revive the Apps at 'git checkout main' App's

    #
    # Choose Outputs for each Input
    #

    def answer_printable_kmix(self, kmix: KeyMix) -> bool:
        """Loop Printable Key Bytes to Screen"""

        kdecode = kmix.kdecode

        paste_row_paste_column = self.paste_row_paste_column
        sw = self.screen_writer

        if not kdecode:  # trusts b"" deployed only into ⌥`E, ⌥EE, etc
            return True

        if kdecode and kdecode.isprintable():

            if not paste_row_paste_column:
                sw.swrite(kdecode)
                return True

            (y, x, h, w) = self.recollect_y_x_h_w()

            sw.swrite(kdecode)

            x += len(kdecode)
            while x > w:
                x -= w
                y += 1
                y = min(max(1, y), h)

            self.row_column = (y, x)  # replaces

            return True

            # sw.swrite("<<" + kdecode + ">>"))  # todo: some new --egg for tracing text loopback?
            # sw.swrite(kdecode.upper())  # todo: some new --egg for tracing text loopback?

            # ⎋[201⇧~ knows 'sw.swrite(kdecode)' ran only if KR Y X changes

        return False

    def answer_pasted_kmix(self, kmix: KeyMix) -> bool:
        """Loop back Pasted Key Mixes into vertical jagged Screen Rows"""

        paste_row_paste_column = self.paste_row_paste_column
        row_column = self.row_column
        sw = self.screen_writer

        assert _START_PASTE_ == "\033[" "200~"
        assert _END_PASTE_ == "\033[" "201~"

        # Answer differently between ⎋[200⇧ and ⎋[201⇧

        if not paste_row_paste_column:
            if kmix.kdecode != "\033[200~":
                return False

            self.paste_row_paste_column = row_column  # replaces
            paste_row_paste_column = self.paste_row_paste_column  # resamples

        # Show Start of Paste

        if kmix.kdecode == "\033[200~":  # todo: but are they balanced?
            sw.sprint(kmix.kcaps, end="")
            self.swrite_pasted_crlf()
            return True

        # Show End of Paste

        if kmix.kdecode == "\033[201~":

            if row_column != paste_row_paste_column:
                self.swrite_pasted_crlf()

                row_column = self.row_column  # resamples
                paste_row_paste_column = self.paste_row_paste_column  # resamples

                assert row_column == paste_row_paste_column, (row_column, paste_row_paste_column)

            sw.sprint(kmix.kcaps, end="")
            self.swrite_pasted_crlf()
            self.swrite_pasted_crlf()  # twice

            self.paste_row_paste_column = tuple()  # replaces

            return True

        # Limit Carriage-Return of Pasted Line-Break to no more West than Paste Column

        if kmix.kdecode == "\r":
            self.swrite_pasted_crlf()
            return True

        # Else say meaning not yet found

        return False

        # todo3: turn off the wrap of key release or paste across the Eastmost column

    def swrite_pasted_crlf(self) -> None:
        """Leap to Westmost column of Paste, step South, and delete Northmost Row if need be"""

        paste_row_paste_column = self.paste_row_paste_column
        sw = self.screen_writer

        assert CUP_Y_X == "\033[" "{};{}H"

        # Find Paste on Screen

        (y, x) = paste_row_paste_column
        (_, _, h, w) = self.recollect_y_x_h_w()

        assert 1 <= y <= h, (y, x, h, w)
        assert 1 <= x <= w, (y, x, h, w)

        # Calculate next Y X and delete Northmost Row if need be and go there

        y += 1
        y = min(max(1, y), h)

        sw.swrite("\r\n")
        sw.swrite("\033[" f"{y};{x}H")

        assert 1 <= y <= h, (y, x, h, w)
        assert 1 <= x <= w, (y, x, h, w)

        # Say we've gone there, and say we'll write the next Row of Paste there

        self.row_column = (y, x)  # replaces
        self.paste_row_paste_column = (y, x)  # replaces

        # todo: why not def 'sw_swrite_crlf_as_pasted' inside 'def answer_pasted_kmix'?
        # todo: something complex about .y and/or .h "not bound"?

    def answer_controls_kmix(self, kmix: KeyMix) -> bool:
        """Loop basic Control Sequences to Screen"""

        sw = self.screen_writer

        # Loop the famous Key Faces

        swrite_by_kface = {
            "⇥": "\t",  # Tab
            "⇧⇥": "\033[Z",  # ⇧Tab
            "⏎": "\r\n",  # Return  # looped as "\r\n", not as "\r"
            "␢": " ",  # Spacebar
        }

        if self.inserting:
            swrite_by_kface["⌫"] = "\b" "\033[P"  # Delete in Inserting Mode
        else:
            swrite_by_kface["⌫"] = "\b" " " "\b"  # Delete in Replacing Mode

        kface = kmix.kface
        if kface in swrite_by_kface.keys():
            swrite = swrite_by_kface[kface]
            sw.swrite(swrite)
            return True

        # Loop the famous Key Caps

        swrite_by_kcaps = {  # ⌃H ⌃J ⌃K ⌃L not wanted here
            "⌃G": "\a",  # rings Bell
        }

        kcaps = kmix.kcaps
        if kcaps in swrite_by_kcaps.keys():
            swrite = swrite_by_kcaps[kcaps]
            sw.swrite(swrite)
            return True

        #

        return False

        # todo: less silence over Controls when they have no visible effect

    def answer_arrows_kmix(self, kmix: KeyMix) -> bool:
        """Loop Arrows and shifted Arrows to Screen"""

        kface = kmix.kface
        kcaps = kmix.kcaps

        sw = self.screen_writer

        # Take ⌃ Keys as Arrows from the First and Second Players
        # todo6: W A S D as ↑ ← ↓ → Arrows, and I J K L as ↑ ← ↓ → Arrows

        arrows_by_kcaps = {"⌃H": "←", "⌃J": "↓", "⌃K": "↑", "⌃L": "→"}
        arrows_by_kcaps |= {"⌃A": "←", "⌃S": "↓", "⌃D": "↑", "⌃F": "→"}

        alt_kface = kmix.kface
        if kcaps in arrows_by_kcaps.keys():
            alt_kface = arrows_by_kcaps[kcaps]

        # Take Arrows as Arrows, no matter if shifted by ⎋ ⌃ ⌥ ⇧ ⌘ Fn

        arrows = "".join(_ for _ in "←↑→↓" if _ in alt_kface)
        if not arrows:
            return False

        assert len(arrows) == 1, (arrows, alt_kface, kface)
        arrow = arrows[-1]

        # Move as told

        swrite_by_arrow = {
            "↑": "\033[A",
            "↓": "\033[B",
            "→": "\033[C",
            "←": "\033[D",
        }

        swrite = swrite_by_arrow[arrow]
        sw.swrite(swrite)

        return True

        # todo: less silence over Arrows when they have no visible effect

        # todo3: take ⌃S ⌃Q as --egg=xoff
        # todo2: --egg=sigtstp for ⌃Z to work without ⌃C ⌃\ working
        # todo: offer test of timeout=None timing out at ⌃D as --egg=eot

    def answer_leap_kmix(self, kmix: KeyMix, weak_int: int) -> bool:
        """Leap the Terminal Cursor to come and meet a Touch Tap or Mouse Click Release or Press"""

        sw = self.screen_writer

        kencode = kmix.kencode
        alt_kencode = KeyMix.kencode_to_leap_if(kencode)
        alt_kdecode = alt_kencode.decode()

        if not alt_kencode:
            return False

        assert alt_kdecode.startswith("\033[<"), (alt_kdecode, kencode)
        fm = re.fullmatch(r"..<([0-9]+);([0-9]+);([0-9]+)([Mm])", string=alt_kdecode)
        assert fm, (fm, alt_kdecode, kencode)

        f = int(fm.group(1))
        x = int(fm.group(2))
        y = int(fm.group(3))
        t = fm.group(4)

        # Leap the Terminal Cursor to come and meet a Touch Tap or Mouse Click Release

        if weak_int > 0:
            sw.swrite("\033[" f"{y};{x}H")
        else:
            sw.swrite(f"⎋[<{f};{x};{y}{t}")

        return True

        # todo: less silence over Taps to Leap when they have no visible effect


@dataclasses.dataclass(order=True)  # , frozen=True)
class ScreenWriter:
    """Mirror the Writes to a Terminal Screen"""

    terminal_studio: TerminalStudio

    def __init__(self, terminal_studio: TerminalStudio) -> None:
        self.terminal_studio = terminal_studio

    def sprint(self, *args: object, end: str = "\r\n") -> None:
        """Write to the Terminal Screen"""

        ts = self.terminal_studio
        stdio = ts.stdio
        print(*args, end=end, file=stdio)

    def swrite(self, text: str) -> None:
        """Write to the Terminal Screen"""

        ts = self.terminal_studio
        stdio = ts.stdio

        logger.info(f"o {text!r}")

        stdio.write(text)

        # todo2: ScreenWriter snoop ⎋[⇧?2004L and ⎋[⇧?2004H to know toggled Bracketed Paste
        # todo2: snoop ⎋[⇧?1006H and ⎋[⇧?1006L to know toggled Csi ⇧M M Sgr Mouse
        # todo2: snoop ⎋[⇧?1005H and ⎋[⇧?1005L to know toggled Csi ⇧M ⇧M Six Mouse


@dataclasses.dataclass(order=True)  # , frozen=True)
class KeyboardReader:
    """Mirror the Reads from a Terminal Keyboard"""

    terminal_studio: TerminalStudio  # where to read
    screen_writer: ScreenWriter  # where to write

    kmixes: list[KeyMix]  # Key Mixes formed from Key Packs
    kmindex: int  # count of Key Mixes returned

    kpacks: list[KeyPack]  # Key Packs formed from Key Bytes
    kpindex: int  # count of Key Packs returned

    kbytearray: bytearray  # Bytes fetched from Stdio
    kbindex: int  # count of Bytes returned

    #
    #
    #

    def __init__(self, terminal_studio: TerminalStudio, screen_writer: ScreenWriter) -> None:

        self.terminal_studio = terminal_studio
        self.screen_writer = screen_writer

        self.kmixes = list()
        self.kmindex = 0

        self.kpacks = list()
        self.kpindex = 0

        self.kbytearray = bytearray()
        self.kbindex = 0

    def read_some_key_mixes(self) -> list[KeyMix]:
        """Read all the Key Mixes that came together, minus whatever has already been read"""

        kmixes = self.kmixes
        kmindex = self.kmindex

        # Fetch some Key Mixes, else timeout and return an empty List

        if kmindex >= len(kmixes):
            self._demand_kframe_of_kmixes_(timeout=None)
            if kmindex >= len(kmixes):
                return list()

        # Read all the Key Mixes that came together, minus whatever has already been read

        some_kmixes = kmixes[kmindex:]
        self.kmindex += len(some_kmixes)
        assert self.kmindex == len(kmixes), (self.kmindex, len(kmixes))

        return some_kmixes

    def read_one_key_mix(self) -> KeyMix:
        """Read one Key Mix"""

        kmix = self.read_one_key_mix_if(timeout=None)  # todo2: more test of .timeout is not None
        assert kmix, (kmix,)  # because timeout=None

        return kmix

    def read_one_key_mix_if(self, timeout: float | None) -> KeyMix:
        """Read one truthy Key Mix, else timeout and return a falsey empty Key Mix"""

        kmixes = self.kmixes
        kmindex = self.kmindex

        # Fetch one truthy Key Mix, else timeout and return a falsey empty Key Mix

        if kmindex >= len(kmixes):
            self._demand_kframe_of_kmixes_(timeout=timeout)
            if kmindex >= len(kmixes):
                empty_kmix = KeyMix()
                return empty_kmix

        # Read one Key Mix

        kmix = kmixes[kmindex]
        self.kmindex += 1

        return kmix

    #
    # Fetch 1 Frame of Mixes, having each carry 1 Closed Pack of Bytes
    #

    def _demand_kframe_of_kmixes_(self, timeout: float | None) -> None:
        """Fetch 1 Frame of Mixes, having each carry 1 Closed Pack of Bytes"""

        kmixes = self.kmixes
        kmindex = self.kmindex

        kpacks = self.kpacks
        kpindex = self.kpindex

        # Read more Key Mixes only when needed

        assert kmindex == len(kmixes), (kmindex, kmixes[kmindex:])

        # Fill with Key Packs, else quit now

        if kpindex >= len(kpacks):
            self._demand_kframe_of_kpacks_(timeout=timeout)
            if kpindex >= len(kpacks):
                return

        # Drain the Key Packs

        while kpindex < len(kpacks):
            kpack = kpacks[kpindex]

            self.kpindex += 1
            kpindex = self.kpindex  # replaces

            kencode = kpack.to_kbytes()
            kmix = KeyMix(kencode)

            kmixes.append(kmix)

            logger.info(f"in {kmix}")

    #
    # Fetch 1 Frame of Closed Packs of Bytes
    #

    def _demand_kframe_of_kpacks_(self, timeout: float | None) -> None:
        """Fetch 1 Frame of Closed Packs of Bytes"""

        kpacks = self.kpacks
        kpindex = self.kpindex

        kbytearray = self.kbytearray
        kbindex = self.kbindex

        option_kt_join = KeyMix.OPTION_KT_JOIN  # '∂' for ⌥D

        # Read more Key Packs only when needed

        assert kpindex == len(kpacks), (kpindex, kpacks[kpindex:])
        assert kbindex == len(kbytearray), (kbindex, kbytearray[kbindex:])

        # Fill with Bytes, else quit now

        self._demand_kframe_of_kbytearray_(timeout)  # don't care if .squeries sent

        if kbindex >= len(kbytearray):
            return

        # Drain the Bytes

        kpack = KeyPack(b"")
        while kbindex < len(kbytearray):
            kbytes = bytes(kbytearray[kbindex:])

            # Do-not take a closing ⎋[0N DSR_0 reply to ⎋[5N DSR_5 into the previous Key Pack

            if kbytes == b"\033[0n":
                if kpack:
                    kpack.close()
                    kpacks.append(kpack)
                    kpack = KeyPack(b"")

            # Append Bytes till Key Pack closes

            kbyte = kbytes[:1]

            extra = kpack.take_one_kbyte_if(kbyte)
            if not extra:
                self.kbindex += 1
                kbindex = self.kbindex  # replaces

            if kpack.closed or extra:

                kpack.close()
                kpacks.append(kpack)
                kpack = KeyPack(b"")

                continue

            # Except close the Key Pack early, if Text is an ⌥ Option/Alt Key Pack

            text = kpack.text
            if len(kpacks) == kpindex:
                if text and (text in option_kt_join):  # '∂' for ⌥D

                    kpack.close()
                    kpacks.append(kpack)
                    kpack = KeyPack(b"")

                    continue

        # Take the last of the Bytes arriving all at once as a Key Pack

        if kpack:

            kpack.close()
            kpacks.append(kpack)
            kpack = KeyPack(b"")

        # Transcode a Burst of Arrows into Pn Arrows

        young_kpacks = kpacks[kpindex:]
        younger_kpacks = self._transcode_kframe_of_kpacks_if_(young_kpacks)
        if younger_kpacks:
            del kpacks[kpindex:]
            kpacks.extend(younger_kpacks)

        # todo2: test ⎋[⇧M Csi Mouse Report then ⎋[⇧Z etc with ⎋[5n and ⎋[0n

    def _transcode_kframe_of_kpacks_if_(self, kpacks: list[KeyPack]) -> tuple[KeyPack, ...]:
        """Transcode a Burst of Arrows into Pn Arrows, if enough arrived at once"""

        assert DSR_0 == "\033[" "0n"  # ⎋[0N

        # Don't transcode if too short

        if len(kpacks) < (4 + 1):  # 5 = Four Arrows plus one ⎋[0N DSR_0
            return tuple()

            # our ⌃V ⌃V shows Runs of >= 3 Arrows come easily from mashing Keypad of ← ↑ ↓ →

        # Transcode to an explicit Pn >= 1 per Arrow,
        # no matter if Byte Length rises because encoding enough Pn = 1

        last_kbytes = kpacks[-1].to_kbytes()
        if last_kbytes != b"\033[0n":
            return tuple()

        steps = bytearray()
        for kpack in kpacks[:-1]:
            kbytes = kpack.to_kbytes()
            (kintsmark, kints) = KeyMix.to_csi_ints_if(kbytes)
            if kints or (kintsmark not in (b"A", b"B", b"C", b"D")):
                return tuple()

                # doesn't transcode anything but a run of Arrows, each without Pn

            steps.extend(kintsmark)

        runs = list(f"\033[{len(list(g))}{chr(k)}" for k, g in itertools.groupby(steps))
        transcodes = tuple(KeyPack(_.encode()) for _ in runs)

        # Succeed

        return transcodes  # (b'\033[1A', b'\033[2D', b'\033[1A')

    #
    # Fetch 1 Frame of Bytes, from the Inputs of Tap/ Click/ Drag/ Key Release
    #

    def _demand_kframe_of_kbytearray_(self, timeout: float | None) -> tuple[str, ...]:
        """Fetch 1 Frame of Bytes, from the Inputs of Tap/ Click/ Drag/ Key Release"""

        ts = self.terminal_studio
        sw = self.screen_writer
        kbytearray = self.kbytearray
        kbindex = self.kbindex

        encode_start_set = EncodeStartSet

        # Name the Queries, Replies, and Marks that place Input Bytes in context

        assert DSR_5 == "\033[" "5n"  # ⎋[5N
        assert DSR_0 == "\033[" "0n"  # ⎋[0N

        # Read more Key Bytes only when needed

        assert kbindex == len(kbytearray), (kbindex, kbytearray[kbindex:])

        # Fetch 1 Key Byte to start with

        kbyte = ts.read_one_kbyte_if(timeout=timeout)  # fetches one or zero Key Bytes
        assert len(kbyte) == 1, (kbyte,)

        kbytearray.extend(kbyte)

        # Plan to fetch Key Packs till next ⎋[0N, if the Key Packs might be multipack or multibyte

        if kbyte not in encode_start_set:  # todo: some new --egg to try ⎋[5N more often?
            return tuple()

        # Read Key Bytes till next Reply Key Pack, if Query Key Pack written

        squery = "\033[5n"  # ⎋[5N
        kreply = "\033[0n"
        squeries = (squery,)

        sw.swrite(squery)
        while True:

            # Fetch 1 Key Byte into our .kbytearray Key Log/ KeyLogger

            kbyte = ts.read_one_kbyte_if(timeout=timeout)  # fetches one or zero Key Bytes
            assert len(kbyte) == 1, (kbyte,)

            kbytearray.extend(kbyte)

            # Take ⎋[0N as the Reply to one ⎋[5N

            if squery:
                if kbytearray.endswith(kreply.encode()):
                    return squeries

    # todo2: launch an app of many Keyboard Viewers:  plain, ⎋, ⌃, ⌥, ⇧, ⎋⌃, etc etc
    # todo2: how about one Keyboard Viewer at a time


#
# Amp up Import ArgParse
#


_ARGPARSE_3_10_ = (3, 10)  # Ubuntu 2022 Oct/2021 Python 3.10


@dataclasses.dataclass(order=True)  # , frozen=True)
class ArgDocParser:
    """Scrape Prog & Description & Epilog from Doc to form an ArgParse Argument Parser"""

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

        # 'add_help=False' for needs like 'cal -h', 'df -h', 'du -h', 'ls -h', etc

        # callers who need Options & Positional Arguments have to add them

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
        if len(args) == 1:  # because ArgParse chokes if '--' Sep present without Pos Args
            args_0 = args[0]
            if args_0.startswith("--") and ("--yolo".startswith(args_0)):
                shargs = ["--yolo"]

                # steals --y, or --yo, or --yol, or --yolo, as if --, when only Arg

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
    assert 1 <= precise <= 1000, (precise, abs_f, eng, f)  # todo: log if '== 1000' ever happens

    dotted = round(precise, 1)  # 1.0  # 9.9  # 10.0
    assert 1.0 <= dotted <= 1000.0, (dotted, abs_f, eng, f)

    concise = dotted
    if concise >= 10:
        concise = round(precise)  # 10  # 1000
        assert 10 <= concise <= 1000, (concise, abs_f, eng, f)

    log10_near = int(math.log10(near))
    if eng == log10_near:
        join = f"{neg}{concise}"  # unmarked
    elif eng <= 0:
        join = f"{neg}{concise}e{eng}{unit}"  # marked by 'e-' or 'e0'
    else:
        join = f"{neg}{concise}e+{eng}{unit}"  # marked by 'e+'

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

    sys.excepthook = with_excepthook

    if exc_type is SystemExit:
        assert sys.flags.interactive, (sys.flags.interactive, exc_type, exc_value)  # aka python3 -i
        return

        # consciously doesn't call: with_excepthook(exc_type, exc_value, exc_traceback)

    # Quit quickly quietly, if KeyboardInterrupt, unless --egg=sigint asked for a full Traceback

    if exc_type is KeyboardInterrupt:
        if not flags.sigint:
            with_stderr.write("KeyboardInterrupt\n")
            sys.exit(130)  # 0x80 + signal.SIGINT

    # Quit quickly quietly, if BdbQuit

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
class KeyMix:
    """Bundle one Input: Tap or Click released or pressed, or a Keyboard Chord pressed"""

    kface: str  # ''  # '⏎'  # '↑'
    kcaps: str  # ''  # '⌃M'  # '⎋[⇧A'
    kpack: KeyPack  # .head .neck .back .stash .tail
    kencode: bytes  # .kpack.to_kbytes()
    kdecode: str  # .decode of .encode, else Empty Str ""
    kintsmark: bytes  # neck-start + back + tail
    kints: list[int]  # via Csi Neck after Csi Next Start

    #
    # Init, Bool, Str, & ._require_simple_kmix_
    #

    def __init__(self, kencode: bytes = b"") -> None:

        # Collect

        kbytes = kencode

        kface = KeyMix.to_kface_if(kbytes)
        kcaps = KeyMix.to_kcaps_if(kbytes)

        kpack = KeyPack(kbytes)  # maybe .closed, maybe not
        kpack.close()

        try:
            kdecode = kencode.decode()
        except UnicodeDecodeError:
            kdecode = ""

        (kintsmark, kints) = KeyMix.to_csi_ints_if(kbytes)
        if kints:
            assert kintsmark, (kintsmark, kints, kbytes)
        if not kintsmark:
            (kintsmark, kints) = KeyMix.to_csi_shift_m6_ints_if(kbytes)
            assert bool(kintsmark) == bool(kints), (kintsmark, kints, kbytes)

        # Succeed

        self.kface = kface
        self.kcaps = kcaps
        self.kpack = kpack
        self.kencode = kencode
        self.kdecode = kdecode
        self.kintsmark = kintsmark
        self.kints = kints

        self._require_simple_kmix_()

    def __bool__(self) -> bool:

        kcaps = self.kcaps
        kencode = self.kencode

        truthy = bool(kcaps) or bool(kencode)  # don't care that Closed Key Pack is Truthy

        return truthy

    def __str__(self) -> str:

        kface = self.kface
        kcaps = self.kcaps
        kpack = self.kpack
        kintsmark = self.kintsmark
        kints = self.kints

        # Collect the distinctive Parts, but shrug off .kencode and .kdecode

        parts = list()

        kface_part = kface if kface else "<>"
        parts.append(kface_part)

        if kcaps and (kcaps != kface_part):  # not ⎋, not ␢
            parts.append(kcaps)

        kbytes = kpack.to_kbytes()
        if not kpack.text:
            parts.append(str(kbytes))
        elif kpack.text == " ":
            parts.append(r"'\x20'")  # ' ' Spacebar  # ␠  # ␣  # ␢
            assert len(kbytes) == len(kpack.text), (len(kbytes), len(kpack.text), kbytes)
        else:
            parts.append(repr(kpack.text))
            if len(kbytes) != len(kpack.text):
                parts.append(str(kbytes))

        if not kintsmark:
            assert not kints, (kints,)
        elif kints:
            parts.append(str(kints))  # lets the .kpack show the .kintsmark

        # Succeed

        join = " ".join(parts)
        assert join.isprintable(), (join,)

        return join

        # ⇧⇥ ⎋[⇧Z b'\x1b[' b'Z'  # Shift Rightwards-Arrow-to-Bar
        # ↑ ⎋[⇧A b'\x1b[' b'A'  # Upwards-Arrow

        # <> ⌥3 '£' b'\xc2\xa3'  # an example of shifted by Option
        # <> ⌥⇧@ '€' b'\xe2\x82\xac'  # an example of Option-Shift

        # ⇧→ ⎋[1;2⇧C b'\x1b[' b'1;2' b'C'  # Shift Rightwards-Arrow
        # ⎋⇧Fn ⎋⌃P b'\x1b' b'\x10'  # Meta Shift Fn   # only shifting keys, without substance
        # ⎋ ⎋ b'\x1b'  # an explicit Face same as its Caps

    def _require_simple_kmix_(self) -> None:
        """Raise Exception if some mutation gone wrong has damaged Self"""

        kface = self.kface
        kcaps = self.kcaps
        kpack = self.kpack
        kdecode = self.kdecode
        kencode = self.kencode
        kintsmark = self.kintsmark
        kints = self.kints

        if kface:
            assert kcaps, (kcaps, kface, kencode)

            # .kface == .kcaps happens at ␢, ⎋, ⎋⇧L, etc

        if kdecode:
            assert kdecode == kencode.decode(), (kdecode, kencode)
        if kencode:
            assert kpack, (kpack, kencode)

        if kints:
            assert kintsmark, (kintsmark, kints)

        if kencode and not kdecode:
            try:
                kencode.decode()
                assert False, (kencode,)
            except UnicodeDecodeError:
                pass

    #
    # Parsers for KeyMix'es
    #

    @staticmethod
    def to_csi_ints_if(kbytes: bytes) -> tuple[bytes, list[int]]:
        """Pick out the Nonnegative Int Literals of a Csi Escape Sequence"""

        kpack = KeyPack(kbytes)

        head = kpack.head
        neck = kpack.neck
        back = kpack.back
        tail = kpack.tail
        closed = kpack.closed

        assert CSI == "\033["

        # Fail if not a Csi Escape Sequence closed by its Tail

        empty_kintsmark = b""
        empty_kints: list[int] = list()

        if (head != b"\033[") or not closed:
            return (empty_kintsmark, empty_kints)

        # Find the leftmost Digits and Semicolons, else the End of the Neck

        kintsmark = bytes(back + tail)
        m = re.search(b"[0-9;]+", string=neck)
        if not m:
            m = re.search(b"$", string=neck)
            assert m, (m, neck, kbytes)

        splittables = m.group()
        splits = splittables.split(b";") if splittables else list()

        # Pass back the Ints, and all of the surrounding Bytes

        kints = list()
        kints = list((int(_) if _ else -1) for _ in splits)

        kprefix = neck[: m.start()]  # maybe empty
        ksuffix = neck[m.end() :]  # maybe empty
        kintsmark = bytes(kprefix + ksuffix + back + tail)

        # Succeed

        return (kintsmark, kints)

        # (b"A", [])
        # (b"H", [-1, 2])
        # (b"<m", [8, 80, 25])

    @staticmethod
    def to_csi_shift_m6_ints_if(kbytes: bytes) -> tuple[bytes, list[int]]:
        """Pick out the Nonnegative Int Literals of a Csi Mouse Report"""

        kpack = KeyPack(kbytes)
        kpack.close()

        head = kpack.head
        neck = kpack.neck
        back = kpack.back
        tail = kpack.tail

        assert CSI == "\033["

        # Fail if not a Csi ⇧M Escape Sequence, closed when full

        if head != b"\033[M":
            return (b"", list())

        assert (not neck) and (not tail), (neck, tail, kbytes)

        # Pass back the Ord's of 3 Bytes, no matter if Decodable as Characters

        kintsmark = b"::"  # our mark of 3 Bytes, not 3 Characters  # todo: no standard?

        if len(back) == 3:
            assert len(kbytes) == 6 == len(head) + len(back), (kbytes, head, back)

            kints_from_kbytes = list(back)
            return (kintsmark, kints_from_kbytes)

        # Pass back the Ord's of 3 Characters

        kintsmark = b":;"  # our mark of 3 Characters, not 3 Bytes  # todo: no standard?

        try:
            decode = back.decode()
        except UnicodeDecodeError:
            assert False, (back, kbytes)

        if len(head) + len(decode) == 6:

            kints_from_kchars = list(ord(_) for _ in decode)
            return (kintsmark, kints_from_kchars)

        # Else give up

        return (b"", list())

    @staticmethod
    def kencode_to_leap_if(kencode: bytes) -> bytes:
        """Form Mouse Press or Release in the Bytes of ⎋[<{f};{x};{y}M or ⇧M form, else empty"""

        kpack = KeyPack(kencode)  # todo: may raise ValueError
        kpack.close()

        # Accept the ⎋[<{f};{x};{y}... form with Backtails of ⇧M Press and M Release

        if kpack.head == b"\033[":

            fm = re.fullmatch(rb"<([0-9]+);([0-9]+);([0-9]+)", string=kpack.neck)
            if fm:
                backtail = bytes(kpack.back + kpack.tail)
                if backtail in (b"M", b"m"):

                    f = int(fm.group(1))
                    x = int(fm.group(2))
                    y = int(fm.group(3))

                    kdecode = "\033[" f"<{f};{x};{y}{backtail.decode()}"
                    alt_kencode = kdecode.encode()

                    return alt_kencode

        # Transcode the ⎋[⇧M{b}{x}{y} form

        (kintsmark, kints) = KeyMix.to_csi_shift_m6_ints_if(kbytes=kencode)
        assert bool(kintsmark) == bool(kints), (kintsmark, kints, kencode)
        if kintsmark:
            assert kintsmark in (b"::", b":;"), (kintsmark, kencode)
            assert kints, (kints, kencode)

            (bi, xi, yi) = kints

            f = bi
            x = (xi - 32) if (xi >= 33) else (256 + xi)
            y = (yi - 32) if (yi >= 33) else (256 + yi)

            backtail = b"m" if ((bi & 0b11) == 0b11) else b"M"  # M Release else ⇧M Press

            kdecode = "\033[" f"<{f};{x};{y}{backtail.decode()}"
            alt_kencode = kdecode.encode()

            return alt_kencode

        # Give up

        return b""

    #
    # Run slow and quick Self-Test's
    #

    @staticmethod
    def _try_key_mix_() -> None:
        """Run slow and quick Self-Test's of this Class"""

        # Speak of falsey Key Mixes

        kmix = KeyMix()
        assert not kmix, (kmix,)

        # Try for Key Caps of 6-Byte or 6-Character Mouse-Report

        xx_kcaps = KeyMix.to_kcaps_if(b"\033[M\xff\xff\xff")
        assert xx_kcaps == "⎋[⇧M:0b11011111:223:223", (xx_kcaps,)

        uuuu_uuuu_kcaps = KeyMix.to_kcaps_if("\033[M\U0010ffff\U0010ffff\U0010ffff".encode())
        assert uuuu_uuuu_kcaps == "⎋[⇧M:0b100001111111111011111;1114079;1114079", (uuuu_uuuu_kcaps,)

        # Try for Key Caps and Key Face at every Unicode Code Point

        for code in range(0x11000):
            decode = chr(code)

            if code in range(0xD800, 0xDFFF + 1):
                try:
                    encode = bytes(decode.encode())
                except UnicodeEncodeError:
                    continue
                assert False, (hex(code), code)

            encode = bytes(decode.encode())

            kcaps = KeyMix.to_kcaps_if(encode)
            if code == 0xF8FF:
                assert not decode.isprintable(), (hex(code), code)
                assert kcaps, (kcaps, encode, hex(code), code)
            elif decode.isprintable():
                assert kcaps, (kcaps, encode, hex(code), code)
            elif code >= 0x100:
                assert not kcaps, (kcaps, encode, hex(code), code)

            KeyMix.to_kface_if(encode)

            # ⌥⇧K is Apple Logo Icon  is \uF8FF is in the U+E000..U+F8FF Private Use Area (PUA)

    #
    # Choose 1 Keycap per Character to speak of the Bytes of 1 Keyboard Chord
    #

    @staticmethod
    def to_kcaps_if(kbytes: bytes) -> str:
        """Choose 1 Keycap per Character to speak of the Bytes of 1 Keyboard Chord"""

        assert KeyMix.KCAP_SEP == " "

        #
        # Choose Keycaps for Bytes
        #

        # Say no Keycaps if no Bytes

        if not kbytes:
            return ""

        # Say ⎋[⇧M Keycaps when 6 Characters or 6 Bytes start with ⎋[⇧M

        (kintsmark, kints) = KeyMix.to_csi_shift_m6_ints_if(kbytes)
        assert bool(kintsmark) == bool(kints), (kintsmark, kints, kbytes)
        if kintsmark:
            assert kintsmark in (b"::", b":;"), (kintsmark, kbytes)
            assert kints, (kints, kbytes)

            (fi, xi, yi) = kints

            f = (fi - 32) if (fi >= 32) else (256 + fi)
            x = (xi - 32) if (xi >= 33) else (256 + xi)
            y = (yi - 32) if (yi >= 33) else (256 + yi)

            kcaps = f"⎋[⇧M:{bin(f)};{x};{y}"  # '⎋[⇧M:0b11;80;25'
            if len(kbytes) == 6:  # aka has b"::" KIntsMark, not b":;" KIntsMark
                kcaps = f"⎋[⇧M:{bin(f)}:{x}:{y}"  # '⎋[⇧M:0b11:80:25'

            return kcaps

        # Say no Keycaps if Bytes don't encode any Characters

        try:
            ktext = kbytes.decode()
        except UnicodeDecodeError:
            return ""

        assert ktext, (ktext,)

        #
        # Choose Keycaps for Characters
        #

        # Say 1 Key Cap for 2 Characters

        if ktext == "j́":
            return "⌥EJ"

        elif ktext == "J́":
            return "⌥E⇧J"

        elif ktext.startswith("`") and (len(ktext) == 2):
            kt = ktext[-1]
            kc = "⌥`" + KeyMix._kt_to_kcap_if_(kt)
            return kc

        # Say 1 Key Cap per Character, if found

        kcaps = ""
        for kt in ktext:  # often 'len(ktext) == 1'
            kc = KeyMix._kt_to_kcap_if_(kt)
            kcaps += kc

            if not kc:
                return ""

        assert kcaps, (kcaps, kbytes)
        assert " " not in kcaps, (kcaps, kbytes)

        return kcaps

        # '⎋[25;80R' Cursor-Position-Report (CPR)
        # '⎋[25;80t' Rows x Column Terminal Size Report

        # '⎋[200~' and '⎋[201~' before/ after Paste to bracket it

    @staticmethod
    def _kt_to_kcap_if_(kt: str) -> str:
        """Form 1 Key Cap to speak of 1 Keyboard Chord"""

        ko = ord(kt)

        option_kt_str = KeyMix.OPTION_KT_STR  # '∂' for ⌥D
        option_ktext_by_kt = KeyMix.OPTION_KTEXT_BY_KT  # 'é' for ⌥EE

        assert KeyMix.SHIFTED_KEYCAPS == '!"#$%&()*+' ":<>?" "@" "^_" "{|}~"

        # Show the Key Cap of the Spacebar  # blank ' ' Space in macOS Keyboard Viewer

        if ko == 0x20:  # ' ' Spacebar  # ␠  # ␣  # ␢
            kc = "␢"

        # Show the Key Caps of shifted US-Ascii Punctuation

        elif kt in '!"#$%&()*+' ":<>?" "@" "^_" "{|}~":
            kc = "⇧" + kt

        # Show more Key Caps than US-Ascii mentions

        elif (kt != "`") and (kt in option_ktext_by_kt.keys()):  # Mac US Option Accents
            kcaps_list = option_ktext_by_kt[kt].split()
            assert len(kcaps_list) in (1, 2), (kcaps_list, ko, kt)  # ['⌥E', 'E']
            kc = "".join(kcaps_list)  # '⌥EE'
            assert " " not in kc, (kc, ko, kt)

        elif kt in option_kt_str:  # Mac US Option Key Caps
            kc = KeyMix._option_kt_to_kcap_(kt)  # maybe
            assert kc, (kc, ko, kt)
            assert " " not in kc, (kc, ko, kt)

        # Show the Key Caps of US-Ascii, plus the ⌃ ⇧ Control/ Shift Key Caps

        elif (ko < 0x20) or (ko == 0x7F):  # C0 Control Bytes, or \x7F Delete (DEL) ⌫
            kc = KeyMix._kt_control_to_kcap_(kt)
            assert kc, (kc, ko, kt)
            assert " " not in kc, (kc, ko, kt)

        elif "A" <= kt <= "Z":  # printable Upper Case English
            kc = "⇧" + chr(ko)  # shifted Key Cap '⇧A' from b'A'

        elif "a" <= kt <= "z":  # printable Lower Case English
            kc = chr(ko ^ 0x20)  # plain Key Cap 'A' from b'a'

        # Test that no Keyboard sends the C1 Control Bytes, nor the Quasi-C1 Bytes

        elif ko in range(0x80, 0xA0):  # C1 Control Bytes
            kc = repr(bytes([ko]))  # b'\x80'
        elif ko == 0xA0:  # 'No-Break Space'
            assert ((0xA0 & 0x7F) ^ 0x40) == 0x60 == ord("`")
            kc = "⌃`"  # macOS ⌥␢
        elif ko == 0xAD:  # 'Soft Hyphen'  # near to a C1 Control Byte
            kc = repr(bytes([ko]))  # b'\xad'

        # Show the US-Ascii or Unicode Char as if its own Key Cap

        else:
            assert ko < 0x11_0000, (ko, kt)
            kc = chr(ko)  # '!', '¡', etc
            if not kc.isprintable():
                return ""

            # todo: Got Key Caps Str "\u00A1" .. "\u00FF" for Bytes b"\xA1" .. b"\xFF" - Want better?

        # Succeed, but insist that Blank Space is never a Key Cap

        assert kc, (kc, ko, kt)
        assert kc.isprintable(), (kc, ko, kt)  # has no \x00..\x1f, \x7f, \xa0, \xad, etc
        assert " " not in kc, (kc, ko, kt)

        return kc

        # '⌃L'  # '⇧Z'
        # ⌥Y often comes through as \ U+005C Reverse-Solidus aka Backslash  # not ¥ Yen-Sign

    @staticmethod
    def _kt_control_to_kcap_(kt: str) -> str:

        ko = ord(kt)
        assert (ko < 0x20) or (ko == 0x7F), (ko, kt)

        if ko == 0x00:
            kc = "⌃⇧@"
        elif ko == 0x1B:
            kc = "⎋"  # ⌃[ Esc
        elif ko == 0x1E:  # Apple ⌃^ doesn't come through at all
            kc = "⌃⇧^"  # Apple ⌃⇧^ does come through as (0x5E ^ 0x40)
            if flags.google:
                kc = "⌃^"
        elif ko == 0x1F:  # Apple ⌃- doesn't come through as  (0x2D ^ 0x40)
            kc = "⌃-"  # Apple ⌃-  and ⌃⇧_ both do come through as (0x5F ^ 0x40)
            if flags.google:
                kc = "⌃⇧_"
        elif ko == 0x7F:
            kc = "⌃⇧?"  # ⌫  # Delete
        else:
            alt_kt = chr(ko ^ 0x40)
            assert alt_kt in r"ABCDEFGHIJKLMNO" r"PQRSTUVWXYZ" r"\]", (alt_kt, ko)  # not [ ⇧^ ⇧_
            kc = "⌃" + alt_kt

            # '^ 0x40' mixes ⌃ into one of @ A..Z [\]^_ ?, such as ⌃⇧^
            # '⌃⇧^' speaks of (ko == 0x1E == (0x5E ^ 0x40))

        return kc

        # '^ 0x40' speaks of ⌃⇧@ but not ⌃⇧2 and not ⌃␢ at b"\x00" here, but is ⌃␢ elsewhere
        # '^ 0x40' speaks of ⌃M but not Return ⏎ at b"\x0D"
        # '^ 0x40' speaks of ⌃? but not Delete ⌫ at b"\x7F"

        # ⌃` ⌃2 ⌃6 ⌃⇧~ don't work

    SHIFTED_KEYCAPS = '!"#$%&()*+' ":<>?" "@" "^_" "{|}~"
    # aka !"#$%&()*+ :<>? @ ^_ {|}~  # aka ~!@#$%^&*()_+ {}| :" <>?

    #
    # Decode Keys shifted by ⌥ Option/Alt, as at MacBook
    #

    # ("`", "´", "ˆ", "˜", "¨")  # aka ⌥⇧~ ⌥⇧E ⌥⇧I ⌥⇧N ⌥⇧U  # aka ⌥`␢ ⌥E␢ ⌥I␢ ⌥N␢ ⌥U␢

    OPTION_KTEXT_BY_KT = {
        # ⌥E
        "á": "⌥E A",
        "é": "⌥E E",
        "í": "⌥E I",
        # "j́": "⌥E J",  # without the (len("j́") == 2) of ⌥EJ here
        "ó": "⌥E O",
        "ú": "⌥E U",
        "´": "⌥⇧E",
        # ⌥I
        "â": "⌥I A",
        "ê": "⌥I E",
        "î": "⌥I I",
        "ô": "⌥I O",
        "û": "⌥I U",
        "ˆ": "⌥⇧I",
        # ⌥N
        "ã": "⌥N A",
        "ñ": "⌥N N",
        "õ": "⌥N O",
        "˜": "⌥⇧N",
        # ⌥U
        "ä": "⌥U A",
        "ë": "⌥U E",
        "ï": "⌥U I",
        "ö": "⌥U O",
        "ü": "⌥U U",
        "ÿ": "⌥U Y",
        "¨": "⌥⇧U",
        # ⌥`  # ` is the encode of ⌥⇧~ and is ⌥`␢ too
        "à": "⌥` A",
        "è": "⌥` E",
        "ì": "⌥` I",
        "ò": "⌥` O",
        "ù": "⌥` U",
        # "``": "⌥`",  # without the (len("``") == 2) of ⌥`` here
    }

    _KVALUES_ = sorted(OPTION_KTEXT_BY_KT.values())
    assert len(_KVALUES_) == len(set(_KVALUES_)), _KVALUES_

    for _KT_ in OPTION_KTEXT_BY_KT.keys():
        assert len(_KT_) == 1, (_KT_,)

    for _KTEXT_ in OPTION_KTEXT_BY_KT.values():
        kcaps_list = _KTEXT_.split()
        assert len(kcaps_list) in (1, 2), (len(kcaps_list), _KTEXT_)

    assert all(len(_) == 1 for _ in OPTION_KTEXT_BY_KT.keys())

    # hand-sorted by ⌥E ⌥I ⌥N ⌥U ⌥` order

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

    assert len(OPTION_KT_STR) == (0x7E - 0x20) + 1  # Defs per ⌥ KeyCap of a US-Ascii Printable

    _SPACELESS_OPTION_KT_STR_ = OPTION_KT_STR.replace(" ", "")
    assert len(_SPACELESS_OPTION_KT_STR_) == len(set(_SPACELESS_OPTION_KT_STR_))

    # List the Unicode Characters involved in finding ⌥ Option/Alt Key Caps at macOS

    _OPTION_KT_LIST_ = list(OPTION_KTEXT_BY_KT.keys()) + list(_SPACELESS_OPTION_KT_STR_)
    _OPTION_KT_LIST_.sort()

    OPTION_KT_JOIN = "".join(_OPTION_KT_LIST_)

    @staticmethod
    def _option_kt_to_kcap_(kt: str) -> str:
        """Convert to Mac US Option Key Caps from any of OPTION_KT_STR"""

        option_kt_str = KeyMix.OPTION_KT_STR  # '∂' for ⌥D, etc
        assert len(KeyMix.OPTION_KT_STR) == (0x7E - 0x20) + 1

        assert KeyMix.SHIFTED_KEYCAPS == '!"#$%&()*+' ":<>?" "@" "^_" "{|}~"

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

    #
    # Define Key Cap Names with no " " Space's in them, for many multibyte Control Byte Sequences
    #

    KCAP_SEP = " "  # separates '⎋⇧FnX' from '⎋⇧Fn X', etc

    @staticmethod
    def to_kface_if(kbytes: bytes) -> str:
        """Choose Keycaps to speak of the Bytes of 1 Keyboard Chord"""

        assert KeyMix.KCAP_SEP == " "  # promises no ' ' in each single .kface

        # Choose no Key Face for every Decode Error

        try:
            ktext = kbytes.decode()
        except UnicodeDecodeError:
            return ""

        # Choose 1 of our tabulated Key Faces

        kface_by_ktext = KeyMix.KFACE_BY_KTEXT  # '\033[A' for ↑ etc

        if ktext in kface_by_ktext.keys():
            kface = kface_by_ktext[ktext]
            assert kface, (kface, kbytes)

            assert " " not in kface, (kface, kbytes)
            return kface

            # '␢'  # '⇥'  # '⏎'  # '⎋'
            # '⌥←' from '⎋B', no matter if Apple Keyboard > Option as Meta Key
            # '⇧⇥' from '⎋[⇧Z' at '⇧⇥' and at '⌥⇧⇥' while not Apple Keyboard > Option as Meta Key

        # Choose no Key Face for any Key Text not starting with ⎋

        if not ktext.startswith("\033"):
            return ""

        # Choose >= 1 ⎋ followed by 1 of our tabulated Key Faces whose Key Text does start with ⎋

        esc_depth = len(ktext) - len(ktext.lstrip("\033"))
        assert esc_depth >= 1, (esc_depth, kbytes)

        esc_prefix_minus = (esc_depth - 1) * "\033"
        if esc_prefix_minus:
            esc_suffix_plus = ktext.removeprefix(esc_prefix_minus)
            assert esc_suffix_plus.startswith("\033"), (esc_suffix_plus, kbytes)

            if esc_suffix_plus in kface_by_ktext.keys():
                esc_kface_plus = kface_by_ktext[esc_suffix_plus]
                assert esc_kface_plus, (esc_kface_plus, kbytes)

                kface = (len(esc_prefix_minus) * "⎋") + esc_kface_plus
                assert kface, (kface, kbytes)

                assert " " not in kface, (kface, kbytes)
                return kface

                # '⎋⇧⇥' from '⎋⎋[⇧Z' while Apple Keyboard > Option as Meta Key

        # Choose >= 1 ⎋ followed by 1 of our tabulated Key Faces whose Key Text doesn't start with ⎋

        esc_prefix = esc_depth * "\033"
        esc_ktext = ktext.removeprefix(esc_prefix)
        assert not esc_ktext.startswith("\033"), (esc_ktext, kbytes)

        if esc_ktext in kface_by_ktext.keys():
            esc_kface = kface_by_ktext[esc_ktext]
            assert esc_kface, (esc_kface, kbytes)

            kface = (len(esc_prefix) * "⎋") + esc_kface
            assert kface, (kface, kbytes)

            assert " " not in kface, (kface, kbytes)
            return kface

            # ⎋⇥, ⎋⏎, ⎋⌫, like from Apple Keyboard > Option as Meta Key, or from pbpaste|

        # Choose ⎋ followed by 1 Text Character, like from Apple Keyboard > Option as Meta Key

        if len(esc_ktext) == 1:
            if " " not in esc_ktext:
                esc_kcaps = KeyMix.to_kcaps_if(esc_ktext.encode())
                assert esc_kcaps, (esc_kcaps, esc_ktext.encode())

                kface = (len(esc_prefix) * "⎋") + esc_kcaps

                assert " " not in kface, (kface, kbytes)
                return kface

                # ⎋L, ⎋⇧L, etc, while Apple Keyboard > Option as Meta Key, or from pbpaste|

        # Fail to choose a Key Face

        return ""

        # 'A'  # '⌃L'  # '⇧Z'  # '⎋⇧⇥'  # '⎋⏎'  # '⎋1'

    KFACE_BY_KTEXT = {  # r"←|↑|→|↓" and so on  # ⌃ ⌥ ⇧ ⌃⌥ ⌃⇧ ⌥⇧ ⌃⌥⇧ and so on
        "\x00": "⌃␢",  # ␀ ⌃@  # ⌃⇧2 (NUL)
        # "\x03": "Interrupt",  # ␃ ⌃C SigInt also found at Fn⏎ in iTerm2 Apple (ETX)
        # "\x04": "End-of-Transmission",  # ␄ ⌃D (EOT)
        # "\x08": "Backspace",  # ␈ ⌃H also found at ⌃⇧⌫ and ⌃⌥⇧⌫ in iTerm2 Apple (BS)
        "\x09": "⇥",  # ⇥ ␉ ⌃I '\t' Horizontal Character-Tabulation (HT)
        # "\x0a": "",  # ␊ ⌃J '\n' Line-Feed (LF)  # not ␤
        # "\x0b": "",  # ␋ ⌃K Vertical-Tabulation (VT)
        "\x0d": "⏎",  # ⏎ ⌃M '\r' Carriage-Return (CR)
        # "\x1a": "Substitute",  # ␄ ⌃Z SigTStp (SUB)
        # "\x1c": "Information-Separator-Four",  # ⌃\ SigQuit (FS of FS GS RS US)
        # "\x20": "␢",  # ' ' Spacebar  # ␠  # ␣  # ␢
        "\033": "⎋",  # Esc  # Meta  # includes ⎋␢ ⎋⇥ ⎋⏎ ⎋⌫ without ⌥ (ESC)
        "\033" "\x01": "⌥⇧Fn←",  # ⎋⇧Fn←   # coded with ⌃A
        "\033" "\x03": "⎋Fn⏎",  # coded with ⌃C  # not ⌥Fn⏎
        "\033" "\x04": "⌥⇧Fn→",  # ⎋⇧Fn→   # coded with ⌃D
        "\033" "\x08": "⎋⌃⌫",  # ⎋⌃⌫  # coded with ⌃H  # aka \b
        "\033" "\x0b": "⌥⇧Fn↑",  # ⎋⇧Fn↑   # coded with ⌃K
        "\033" "\x0c": "⌥⇧Fn↓",  # ⎋⇧Fn↓  # coded with ⌃L  # aka \f
        "\033" "\x10": "⎋⇧Fn",  # ⎋ Meta ⇧ Shift of FnF1..FnF12  # not ⌥⇧Fn  # coded with ⌃P
        "\033" "\033": "⎋⎋",  # Meta Esc  # not ⌥⎋
        "\033" "\033O" "A": "⌃⌥↑",  # Esc Ss3 ⇧A  # Google
        "\033" "\033O" "B": "⌃⌥↓",  # Esc Ss3 ⇧B  # Google
        "\033" "\033O" "C": "⌃⌥→",  # Esc Ss3 ⇧C  # Google
        "\033" "\033O" "D": "⌃⌥←",  # Esc Ss3 ⇧D  # Google
        "\033" "\033[" "3;5~": "⌥⌃Fn⌫",  # ⎋⌃Fn⌫  # Apple
        "\033" "\033[" "A": "⌥↑",  # Csi 04/01 Cursor Up (CUU)  # Option-as-Meta  # Google
        "\033" "\033[" "B": "⌥↓",  # Csi 04/02 Cursor Down (CUD)  # Option-as-Meta  # Google
        "\033" "\033[" "C": "⌥→",  # Csi 04/03 Cursor [Forward] Right (CUF_X)  # Google
        "\033" "\033[" "D": "⌥←",  # Csi 04/04 Cursor [Back] Left (CUB_X)  # Google
        "\033" "\033[" "Z": "⎋⇧⇥",  # ⇤  # Csi 05/10 CBT  # not ⌥⇧⇥
        "\033" "\x28": "⎋Fn⌫",  # not ⌥Fn⌫
        #
        "\033O" "P": "F1",  # Ss3 ⇧P  # but Apple takes ⇧F1 ⇧F2 ⇧F3 ⇧F4 from Terminal
        "\033O" "Q": "F2",  # Ss3 ⇧Q
        "\033O" "R": "F3",  # Ss3 ⇧R
        "\033O" "S": "F4",  # Ss3 ⇧S
        #
        "\033[" "15;2~": "⇧F5",  # iTerm2 Apple
        "\033[" "15;3~": "⌥F5",  # iTerm2 Apple
        "\033[" "15;4~": "⌥⇧F5",  # ⌥⇧F6  # iTerm2 Apple
        "\033[" "15;5~": "⌃F5",  # iTerm2 Apple
        "\033[" "15;6~": "⌃⇧F5",  # iTerm2 Apple
        "\033[" "15;7~": "⌃⌥F5",  # iTerm2 Apple
        "\033[" "15;8~": "⌃⌥⇧F5",  # iTerm2 Apple
        "\033[" "15~": "F5",  # Esc 07/14 is LS1R, but Csi 07/14 is unnamed
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
        "\033[" "1;2C": "⇧→",  # Csi 04/03 Cursor [Forward] Right (CUF_YX) Y=1 X=2  # Apple
        "\033[" "1;2D": "⇧←",  # Csi 04/04 Cursor [Back] Left (CUB_YX) Y=1 X=2  # Apple
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
        "\033[" "3;2~": "⇧Fn⌫",
        "\033[" "3;3~": "⌥Fn⌫",  # iTerm2 Apple
        "\033[" "3;4~": "⌥⇧Fn⌫",  # iTerm2 Apple
        "\033[" "3;5~": "⌃Fn⌫",  # Apple
        "\033[" "3;6~": "⌃⇧Fn⌫",  # iTerm2 Apple
        "\033[" "3;7~": "⌃⌥⌫",  # iTerm2 Apple
        "\033[" "3;8~": "⌃⌥⇧Fn⌫",  # iTerm2 Apple
        "\033[" "3~": "Fn⌫",
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
        "\033[" "A": "↑",  # Csi 04/01 Cursor Up (CUU)  # also ⌥↑ Apple
        "\033[" "B": "↓",  # Csi 04/02 Cursor Down (CUD)  # also ⌥↓ Apple
        "\033[" "C": "→",  # Csi 04/03 Cursor Right [Forward] (CUF)  # also ⌥→ Apple
        "\033[" "D": "←",  # Csi 04/04 Cursor [Back] Left (CUB)  # also ⌥← Apple
        "\033[" "F": "⇧Fn→",  # Apple  # Csi 04/06 Cursor Preceding Line (CPL)
        "\033[" "H": "⇧Fn←",  # Apple  # Csi 04/08 Cursor Position (CUP)
        "\033[" "Z": "⇧⇥",  # ⇤  # Csi 05/10 Cursor Backward Tabulation (CBT)
        "\033" "b": "⌥←",  # ⎋B  # ⎋←  # Emacs M-b Backword-Word  # Apple
        "\033" "f": "⌥→",  # ⎋F  # ⎋→  # Emacs M-f Forward-Word  # Apple
        "\x20": "␢",  # ' ' Spacebar  # ␠  # ␣ Open-Box  # ␢ Blank-Symbol
        # "``": "⌥` `",  # without the "``" Key Text here, because it comes as 2 Key Faces
        "\x7f": "⌫",  # ␡ ⌃⇧?  # ⌫  # ⌦  # Delete
        "\xa0": "⌥␢",  # '\N{No-Break Space}'
    }

    assert list(KFACE_BY_KTEXT.keys()) == sorted(KFACE_BY_KTEXT.keys())

    assert KCAP_SEP == " "
    for _KCAP in KFACE_BY_KTEXT.values():
        assert " " not in _KCAP, (_KCAP,)

    # Define each KText once, never more than once

    _KTEXT_LISTS_ = [
        list(KFACE_BY_KTEXT.keys()),
        list(OPTION_KTEXT_BY_KT.keys()),
        list(_SPACELESS_OPTION_KT_STR_),
    ]

    _KTEXT_UNROLL_ = list(_KTEXT_ for _KTEXT_LIST_ in _KTEXT_LISTS_ for _KTEXT_ in _KTEXT_LIST_)
    for _KTEXT_, _COUNT_ in collections.Counter(_KTEXT_UNROLL_).items():
        assert _COUNT_ == 1, (_COUNT_, _KTEXT_)


@dataclasses.dataclass(order=True)  # , frozen=True)
class KeyPack:
    """Bundle one whole Byte Sequence from a Terminal Keyboard, or no Bytes"""

    Headbook = (b"\033", b"\033O", b"\033[", b"\033]")  # ⎋ ⎋⇧O ⎋[ ⎋]

    text: str  # 0 or more Chars of Printable Text, mutates as the Pack grows

    head: bytearray  # 1 Leading Bytes, starts with Control Byte, from the .Headbook or not
    neck: bytearray  # Csi Parameter Bytes, in 0x30..0x3F (16 Codes)  # ...... 0123456789:;<=>?
    back: bytearray  # Csi Intermediate Bytes, in 0x20..0x2F (16 Codes)  # .... !"#$%&'()*+,-./
    stash: bytearray  # 1..4 Bytes taken while starts or is a decodable
    tail: bytearray  # Csi Final Byte, in 0x40..0x7E (63 Codes)

    closed: bool  # closed because completed, or because continuation undefined

    #
    # Init, Bool, Repr, Str, .to_kbytes, and ._require_simple_kpack_
    #

    def __init__(self, kbytes: bytes) -> None:

        self.text = str()

        self.head = bytearray()
        self.neck = bytearray()
        self.back = bytearray()
        self.stash = bytearray()
        self.tail = bytearray()

        self.closed = bool()

        extra = self.take_some_kbytes_if(kbytes)
        if extra:
            raise ValueError(extra, kbytes)  # raises the b'\x80' of b'\xc0\x80'

        self._require_simple_kpack_()

        # maybe .closed, maybe not

    def __bool__(self) -> bool:

        kbytes = self.to_kbytes()
        truthy = bool(kbytes or self.closed)

        self._require_simple_kpack_()

        return truthy

    def __repr__(self) -> str:

        cname = self.__class__.__name__  # 'KeyPack'

        text = self.text

        head_ = bytes(self.head)
        neck_ = bytes(self.neck)
        back_ = bytes(self.back)
        stash_ = bytes(self.stash)  # reps bytearray(b'') loosely, as b''
        tail_ = bytes(self.tail)

        closed = self.closed

        join = f"head={head_!r}, neck={neck_!r}, back={back_!r}, stash={stash_!r}, tail={tail_!r}"
        rep = f"{cname}({text=}, {join}, {closed=})"

        self._require_simple_kpack_()

        return rep

        # "KeyPack(text='', head=b'', neck=b'', back=b'', stash=b'', tail=b'', closed=False)"

    def __str__(self) -> str:

        text = self.text

        head_ = bytes(self.head)
        neck_ = bytes(self.neck)
        back_ = bytes(self.back)
        stash_ = bytes(self.stash)
        tail_ = bytes(self.tail)

        # Solve Text

        if text:
            if stash_:
                return repr(text) + " " + str(stash_)  # "'abc' b'\xc0'"
            return repr(text)  # "'abc'"

        # Solve Headless

        if not head_:
            if stash_:
                return str(stash_)  # "b'\xc0'"
            return repr(head_)  # "b''"

        # Solve Head

        join = str(head_)
        if neck_:  # 'Parameter' Bytes
            join += " " + str(neck_)
        if back_ or stash_ or tail_:  # 'Intermediate' Bytes and Final Byte
            assert (not stash_) or (not tail_), (stash_, tail_)
            join += " " + str(back_ + stash_ + tail_)

        # Succeed

        self._require_simple_kpack_()

        assert join.isprintable(), (join,)
        return join  # doesn't show if .closed or not

        # "b'\033[' b'6' b' q'"

    def to_kbytes(self) -> bytes:
        """List the Bytes taken"""

        text_ = self.text.encode()

        head_ = bytes(self.head)
        neck_ = bytes(self.neck)
        back_ = bytes(self.back)
        stash_ = bytes(self.stash)
        tail_ = bytes(self.tail)

        join = text_ + head_ + neck_ + back_ + stash_ + tail_

        self._require_simple_kpack_()

        return join  # doesn't show if .closed or not

    def _require_simple_kpack_(self) -> None:
        """Raise Exception if some mutation gone wrong has damaged Self"""

        text = self.text

        head = self.head
        neck = self.neck
        back = self.back
        stash = self.stash
        tail = self.tail

        closed = self.closed

        headbook = (b"\033", b"\033O", b"\033[", b"\033]")  # ⎋ ⎋⇧O ⎋[ ⎋]
        assert headbook == KeyPack.Headbook

        if (not text) and (not head):
            assert (not neck) and (not back), (neck, back, self)
            assert not tail, (tail, self)

        if text:
            assert not head, (head, text, self)
            assert (not neck) and (not back) and (not tail), (neck, back, tail, text, self)

        if head:
            assert not text, (text, head, self)
            if not any(head.endswith(_) for _ in [b"\033[", b"\033]", b"\033[M"]):
                assert (not neck) and (not back), (neck, back, head, self)
            if head == b"\033[M":
                assert (not neck) and (not tail), (neck, tail, head, self)

        if neck:
            assert head != b"\033[M", (head,)  # ⎋[M Mouse Report

        if neck or back or tail:
            assert head, (head, neck, back, tail, self)

            for h_end in headbook:
                if head.endswith(h_end):  # Head-End not-found in Headbook by ⎋[⇧M Csi Mouse Report
                    h_start = head.removesuffix(h_end)
                    assert h_start == (len(h_start) * b"\033"), (h_start, h_end, head, self)

        if stash:
            assert not tail, (tail, closed, stash, self)
            assert not closed, (closed, stash, self)

        if tail:
            assert head != b"\033[M", (head,)  # ⎋[M Mouse Report
            assert closed, (closed, tail, self)

        if closed:
            assert not stash, (stash, closed, self)

    #
    # Run slow and quick Self-Test's
    #

    @staticmethod
    def _try_key_pack_() -> None:
        """Run slow and quick Self-Test's of this Class"""

        KeyPack._try_open_(b"")  # empty
        KeyPack._try_headbook_()
        KeyPack._try_ends_later_()  # ~200ms
        KeyPack._try_one_more_kbyte_()
        KeyPack._try_some_control_()

    @staticmethod
    def _try_headbook_() -> None:
        """Accept the Bytes of any Head of the Headbook, without closing the Pack"""

        headbook = (b"\033", b"\033O", b"\033[", b"\033]")  # ⎋ ⎋⇧O ⎋[ ⎋]
        assert headbook == KeyPack.Headbook

        assert OSC == "\033]", (OSC,)

        for head in headbook:
            KeyPack._try_open_(head)

            if head == b"\033":
                KeyPack._try_open_(head + b"\033")
                KeyPack._try_close_(head, b"\t")
                KeyPack._try_close_(head, "\u20ac".encode())
                KeyPack._try_close_(head, b"\xf4\x8f\xbf\xff")
            elif head == b"\033O":
                KeyPack._try_extra_(head, extra=b"\033")
                KeyPack._try_close_(head, b"\t")
                KeyPack._try_close_(head, "\u20ac".encode())
                KeyPack._try_close_(head, b"\xf4\x8f\xbf\xff")
            elif head == b"\033[":
                KeyPack._try_extra_(head, extra=b"\033")
                KeyPack._try_extra_(head, extra=b"\t")
                KeyPack._try_extra_(head, extra="\u20ac".encode())
                KeyPack._try_extra_(head, extra=b"\xf4\x8f\xbf\xff")
            elif head == b"\033]":
                KeyPack._try_open_(head, b"\033")
                KeyPack._try_extra_(head, extra=head)
                KeyPack._try_extra_(head, extra=b"\t")
                KeyPack._try_open_(head, "\u20ac".encode())
                KeyPack._try_extra_(head, extra=b"\xf4\x8f\xbf\xff")
            else:
                assert False, (head,)

    StartBytes = tuple(bytes([_]) for _ in range(0xC2, 0xF4 + 1))  # what UTF-8 completes

    @staticmethod
    def _try_ends_later_() -> None:
        """Require each StartsWith accepted by .bytes_to_later_decode via the Endswiths"""

        start_set = set()
        for cp in range(0x110000):
            if 0xD800 <= cp <= 0xDFFF:  # skips surrogates
                continue
            kbytes = chr(cp).encode()
            for index in range(1, len(kbytes)):
                start = kbytes[:index]
                start_set.add(start)

        start_byte_set = set()
        for start in start_set:
            assert KeyPack.bytes_to_later_decode(start), (start,)
            start_byte_set.add(start[:1])

        start_bytes = tuple(sorted(start_byte_set))
        assert start_bytes == KeyPack.StartBytes, (start_bytes, KeyPack.StartBytes)

    @staticmethod
    def _try_one_more_kbyte_() -> None:
        """Try some Packets open to, or closed against, taking more Bytes"""

        # Decline Bytes after Closed

        KeyPack._try_open_(b"")
        KeyPack._try_extra_(b"\t", extra=b"\x41")

        # Take Bytes into Stash, while could be decodable

        KeyPack._try_open_("Superb", b"\xc2")
        KeyPack._try_open_(b"\xed\x80")  # Head of >= 3 Byte UTF-8 Encoding
        KeyPack._try_open_(b"\xf4\x80\x80")  # Head of >= 4 Byte UTF-8 Encoding

        # Take Bytes into 6-Char Mouse Report, while could be 6 Bytes or 6 Decoded Chars

        KeyPack._try_open_(b"\033[M", b"\xff\xff")  # 5 Undecodable Bytes
        KeyPack._try_open_(b"\033[M", b".\xc2\xa3")  # 6 Decodable Bytes but < 6 Chars
        KeyPack._try_open_(b"\033[M", b"\xf4\x8f\xbf\xbf" b"\xf4\x8f\xbf\xbf" b"\xf4\x8f\xbf")

        KeyPack._try_close_(b"\033[M", b"\xc2\x80\xff")  # 6 Undecodable Bytes
        KeyPack._try_close_(b"\033[M", b"\xf4\x8f\xbf\xbf" b"\xf4\x8f\xbf\xbf" b"\xf4\x8f\xbf\xbf")

        KeyPack._try_extra_(b"\033[M" b"\xff\xff", extra=b"\xc2\x80")

        # Take Bytes into Text

        KeyPack._try_open_("\u20ac", "\ufffd".encode()[:-1])

        # Decline 1..4 Unprintable Bytes after Text

        KeyPack._try_extra_(b"Text", extra=b"\x7f")
        KeyPack._try_extra_(b"Plain", extra="\uffff".encode())

    @staticmethod
    def _try_some_control_() -> None:

        # Take & close 1 Unprintable Char or 1..4 Undecodable Bytes as an Alt Head

        KeyPack._try_close_(b"\n")  # 7-bit Control Byte as Head alone
        KeyPack._try_close_(b"\xc0")  # 8-bit Control Byte as Head alone
        KeyPack._try_close_(b"\xc2\xad")  # 2 Byte UTF-8 of U+00AD Soft-Hyphen Control as Head alone
        KeyPack._try_close_(b"\xf5")  # 1 Byte Undecodable as Head alone
        KeyPack._try_close_(b"\xff")  # 1 Byte Undecodable as Head alone
        KeyPack._try_close_(b"\xf4\x8f\xbf\xc0")  # 4 Bytes Undecodable as Head alone

        # Take & close 1 Printable Char escaped by a Head simpler than Csi, Esc Csi, and Osc

        KeyPack._try_close_(b"\033", b"A")  # Head & Text Tail of a Two-Byte Esc Sequence
        KeyPack._try_close_(b"\033O", b"P")  # Head & Text Tail of a Three-Byte Ss3 Sequence

        # Take & close 1 Unprintable Char or 1..4 Undecodable Bytes escaped by a Simpler Head

        KeyPack._try_close_(b"\033", b"\t")  # Head & Control Tail of a Two-Byte Esc Sequence

        # Take or don't take 1 Decodable Char escaped by Osc or Csi or Esc Csi

        KeyPack._try_open_(b"\033[", b"6", b" ")  # Csi Head with Neck and Back but no Tail

        KeyPack._try_close_(b"\033[", b"1", b"M")  # Csi Tail ⇧M that isn't ⎋[⇧M Head
        KeyPack._try_close_(b"\033\033[", b"3;5", b"~")  # Esc Csi Head with Neck and Tail, no Back
        KeyPack._try_close_(b"\033[", b"3;5", b"H")  # Csi Head with Neck and Tail, no Back
        KeyPack._try_close_(b"\033[", b"6", b" q")  # Csi Head with Neck and Back & Tail

        KeyPack._try_close_(b"\033]", b"\x07")  # Osc with 007 Bel as Tail
        KeyPack._try_close_(b"\033]", b"\x1b" b"\\")  # Osc with ⎋\ String Terminator (ST) as Tail

        # Decline 1..4 Undecodable Bytes, when escaped by Csi or Esc Csi or Osc
        # Decline 1 Bytes of Unprintable or Multi-Byte Char
        # todo2: cleanup/ synch the English in these comments :P

        KeyPack._try_extra_(b"\x1b[", extra=b"\t")
        KeyPack._try_extra_(b"\x1b]", extra=b"\t")

        KeyPack._try_extra_(b"\x1b[", extra="\u20ac".encode())
        KeyPack._try_open_(b"\x1b]", "\u20ac".encode())

        KeyPack._try_extra_(b"\x1b[", extra=b"\xf4\x8f\xff")
        KeyPack._try_extra_(b"\x1b]", extra=b"\xf4\x8f\xff")

        # Try some commonly recurring choices

        assert _END_PASTE_ == "\033[" "201~"

        KeyPack._try_close_(b"\x1b[", b"201", b"~")

    @staticmethod
    def _try_extra_(kbytes: bytes, extra: bytes) -> None:
        """Require the Pack to reject these Bytes, after closing itself if need be"""

        kpack = KeyPack(kbytes)
        closed = kpack.closed

        returned_extra = kpack.take_some_kbytes_if(extra)
        assert returned_extra == extra, (returned_extra, extra, str(kpack))

        assert kpack.closed == closed, (kpack.closed, closed, extra, kpack)
        assert kpack == KeyPack(kbytes), (kpack, KeyPack(kbytes))

    @staticmethod
    def _try_open_(*args: str | bytes) -> None:
        """Require the Eval of the Str of the Pack equals its Bytes"""

        kpack = KeyPack._try_bytes_(*args)
        assert not kpack.closed, (kpack,)

    @staticmethod
    def _try_close_(*args: bytes) -> None:
        """Require the Eval of the Str of the Pack equals its Bytes"""

        kpack = KeyPack._try_bytes_(*args)
        assert kpack.closed, (kpack,)

    @staticmethod
    def _try_bytes_(*args: str | bytes) -> KeyPack:
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
    # Take in 1 Byte and return 0 Bytes, else return the 1..4 Bytes that don't fit
    #

    def take_some_kbytes(self, kbytes: bytes) -> None:
        """Take in N Bytes and return 0 Bytes, else raise ValueError"""

        extras = self.take_some_kbytes_if(kbytes)
        if extras:
            raise ValueError(extras, kbytes)

    def take_some_kbytes_if(self, kbytes: bytes) -> bytes:
        """Take in N Bytes and return 0 Bytes, else return the 1..(N+3) Bytes that don't fit"""

        for index in range(len(kbytes)):
            kbyte = kbytes[index:][:1]

            take_one_extra = self.take_one_kbyte_if(kbyte)
            if take_one_extra:
                take_some_extra = take_one_extra + kbytes[index:][1:]
                return take_some_extra

        return b""

    def take_one_kbyte_if(self, kbyte: bytes) -> bytes:
        """Take in next 1 Byte and return 0 Bytes, else return 1..4 Bytes that don't fit"""

        kbytes = self.to_kbytes()
        closed = self.closed

        self._require_simple_kpack_()

        extra = self._take_one_kbyte_if_(kbyte)

        if extra:
            assert extra.endswith(kbyte), (extra, kbyte, kbytes, self)
            assert self.closed == closed, (self.closed, closed, extra, kbyte, kbytes, self)

        self._require_simple_kpack_()

        return extra

    def _take_one_kbyte_if_(self, kbyte: bytes) -> bytes:
        """Take in next 1 Byte and return 0 Bytes, else return 1..4 Bytes that don't fit"""

        assert len(kbyte) == 1, (kbyte,)

        text = self.text
        head = self.head
        stash = self.stash
        closed = self.closed

        headbook = (b"\033", b"\033O", b"\033[", b"\033]")  # ⎋ ⎋⇧O ⎋[ ⎋]
        assert headbook == KeyPack.Headbook

        # Decline Bytes after Closed

        if closed:
            return kbyte

        # Take 0..N Esc Bytes and then an Item of the Headbook as a next guess of Head

        if (not stash) and (not text):

            head_plus = head + kbyte
            for end in headbook:
                if head_plus.endswith(end):

                    start = head_plus.removesuffix(end)
                    if start == (len(start) * b"\033"):
                        head.extend(kbyte)

                        return b""

                        # todo: accepts unbounded 0..N Esc Bytes as next guess of Head

        # Proceed

        extra = self._take_after_headbook_(kbyte)
        return extra

    def _take_after_headbook_(self, kbyte: bytes) -> bytes:
        """Take in next 1 Byte and return 0 Bytes, else return 1..4 Bytes that don't fit"""

        head = self.head
        neck = self.neck
        back = self.back
        stash = self.stash

        # Hold 1..3 Decodable Bytes

        encode = bytes(stash + kbyte)
        try:
            decode = encode.decode()
        except UnicodeDecodeError:
            decode = ""

        if not decode:
            if KeyPack.bytes_to_later_decode(encode):
                stash.extend(kbyte)
                return b""

        stash.clear()

        # Proceed differently by Head

        if not head:
            extra = self._take_before_head_if_(encode, decode=decode)
            return extra

        head_plus = head + encode
        if head_plus == b"\033[M":
            if (not neck) and (not back):
                head.extend(encode)  # chooses b"\033[M" as Head
                return b""

        if head.startswith(b"\033[M"):  # ⎋[⇧M
            extra = self._take_into_csi_shift_m6_if_(encode, decode=decode)
            return extra

        if head.endswith(b"\033["):
            extra = self._take_after_csi_if_(encode, decode=decode)
            return extra

        if head.endswith(b"\033]"):
            extra = self._take_after_osc_if_(encode, decode=decode)
            return extra

        extra = self._take_after_head_if_(encode, decode=decode)
        return extra

    Endswiths = (b"\xbf", b"\x80\x80", b"\xbf\xbf", b"\x80\x80\x80", b"\xbf\xbf\xbf")

    @staticmethod
    def bytes_to_later_decode(data: bytes) -> str:
        """Say if some Bytes start 1 or more UTF-8 Encodings of Chars"""

        endswiths = KeyPack.Endswiths

        for endswith in endswiths:
            encode = data + endswith
            try:
                decode = encode.decode()
                assert len(decode) >= 1, (decode,)
                return decode  # returns first found
            except UnicodeDecodeError:
                continue

        return ""

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

    # todo: invent UTF-8'ish Encoding beyond 1..4 Bytes for Unicode Codes > 0x10_FFFF ?

    def _take_before_head_if_(self, encode: bytes, decode: str) -> bytes:
        """Take 1..4 Bytes while no Head, and close if not Printable"""

        text = self.text
        head = self.head

        assert not head, (head, self)

        # Take Printable Chars into Text, without closing

        if decode and decode.isprintable():
            self.text += decode
            return b""

        # Reject Unprintable or Undecodable Bytes as Peek

        if text:
            return encode  # returns extra, but doesn't close

        # Take Unprintable or Undecodable Bytes as a Closed Alt Head, from outside the Headbook

        assert not encode.endswith(b"\033"), (encode, self)

        head.extend(encode)
        self.closed = True
        return b""

        # takes \b \t \n \r \x7f etc

        # doesn't take bytes([0x80 | 0x0B]) as meaning b"\033\x5b" Csi ⎋[
        # doesn't take bytes([0x80 | 0x0F]) as meaning b"\033\x4f" Ss3 ⎋O
        # doesn't take bytes([0x90 | 0x0D]) as meaning b"\033\x5d" Osc ⎋]

        # despite "Table 2b - Bit combinations" "the control functions of the C1 set in an 8-bit code"

    def _take_after_head_if_(self, encode: bytes, decode: str) -> bytes:
        """Take 1..4 Bytes after a basic Head, or reject 1 Esc Byte as a Peek, but always close"""

        head = self.head
        neck = self.neck
        back = self.back
        tail = self.tail

        assert CSI == "\033[", (CSI,)  # ⎋[
        assert OSC == "\033]", (OSC,)  # ⎋]

        assert head, (head,)
        assert not head.endswith(b"\033["), (head,)
        assert not head.endswith(b"\033]"), (head,)
        assert (not neck) and (not back), (neck, back, self)

        # Reject 1 Esc Byte as a Peek into the next KeyPack

        if encode == b"\033":
            return encode  # returns extra, but doesn't close

            # doesn't take ⎋⎋ ⎋⇧O⎋ ⎋[⎋ ⎋]⎋

        # Take 1..4 Printable or Unprintable or Undecodable Bytes as a Tail of the Head

        assert not encode.endswith(b"\033"), (encode, self)

        tail.extend(encode)
        self.closed = True
        return b""

        # does take ⎋\x10 ⎋\b ⎋\t ⎋\n ⎋\r ⎋\x7f etc

    def _take_into_csi_shift_m6_if_(self, encode: bytes, decode: str) -> bytes:
        """Take Bytes into a Csi Mouse Report of 6 Bytes or 6 Characters"""

        head = self.head
        neck = self.neck
        back = self.back
        tail = self.tail

        assert head == b"\033[M", (head,)  # ⎋[M Mouse Report
        assert (not neck) and (not tail), (neck, tail, head, self)
        assert len(decode) <= 1, (decode, encode)

        # Look into taking as Decodable Characters or as Undecodable Bytes

        back_plus = back + encode
        try:
            back_plus_decode = back_plus.decode()
        except UnicodeDecodeError:
            back_plus_decode = ""

        assert len(back_plus_decode) <= 3, (back_plus_decode, encode, self)

        # Take 3..15 Bytes into a 6 Character Mouse Report

        if back_plus_decode:
            back.extend(encode)
            if len(back_plus_decode) == 3:
                self.closed = True
            return b""

        # Decline 2..4 Bytes past 3..5 Bytes of 6 Byte Csi Mouse Report

        if len(back_plus) > 3:  # 6..15 Bytes
            return encode  # returns extra, but doesn't close

        # Take 1..3 Bytes into a 6 Byte Csi Mouse Report

        back.extend(encode)
        if len(back_plus) == 3:
            self.closed = True

        return b""

        # may take b"\033" into a 6 Byte Csi Mouse Report

    def _take_after_csi_if_(self, encode: bytes, decode: str) -> bytes:
        """Take 1..4 Bytes that fit with a Csi Head, else close & reject as a Peek"""

        head = self.head
        neck = self.neck
        back = self.back
        tail = self.tail

        assert CSI == "\033[", (CSI,)  # ⎋[
        assert head.endswith(b"\033["), (head,)

        # Declines 1..4 Bytes of 1 Unprintable or Undecodable Character

        if (not decode) or (not decode.isprintable()):
            return encode  # returns extra, but doesn't close

        # Declines 2..4 Bytes of Multibyte Character

        assert len(decode) == 1, decode
        code = ord(decode)

        if not (0x20 <= code <= 0x7F):
            return encode  # returns extra, but doesn't close

        assert len(encode) == 1, (encode, code, self)

        # Accept 1 Byte into Back, into Neck, or as Tail

        assert CSI_P_CHARS == "0123456789:;<=>?"
        assert CSI_I_CHARS == """ !'#$%&'()*+,-./"""
        assert CSI_F_CHARS == "@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~"

        if not back:
            if 0x30 <= code < 0x40:  # 16 Parameter Codes  # 0123456789:;<=>?
                neck.extend(encode)
                return b""

        if 0x20 <= code < 0x30:  # 16 Intermediate Codes  # ␢!"#$%&\'()*+,-./
            back.extend(encode)
            return b""

        if 0x40 <= code < 0x7F:  # 63 Final Codes  # @A Z[\\]^_`a z{|}~
            assert not tail, (tail,)
            tail.extend(encode)
            self.closed = True
            return b""

            # splits the '⎋[200~' Start and '⎋[201~' End apart from Bracketed Paste

        # Decline 1 Byte of any unfitting Character

        return encode  # returns extra, but doesn't close

        # todo: accepts unbounded Bytes into a Csi Escape Sequence

    def _take_after_osc_if_(self, encode: bytes, decode: str) -> bytes:
        """Take 1 Char into Osc Sequence, else return 1..4 Bytes that don't fit"""

        head = self.head
        neck = self.neck
        back = self.back
        tail = self.tail

        # Look only at unclosed Osc Sequence

        assert OSC == "\033]", (OSC,)  # ⎋]
        assert head.endswith(b"\033]"), (head,)

        assert bytes(head) == b"\033]", (head,)  # ⎋]

        # Accept \007 BEL into Tail

        if not back:
            if encode == b"\007":  # BEL
                tail.extend(encode)
                self.closed = True
                return b""

        # Accept \033 \134 Esc \ String Terminator (ST) into Back and Tail

        if not back:
            if encode == b"\033":
                back.extend(encode)
                return b""

        if back == b"\033":
            if encode == b"\134" == b"\x5c" == b"\\":
                tail.extend(encode)
                self.closed = True
                return b""

        # Decline \033 \135 Esc ] Osc late, as its ] arrives

        if back == b"\033":
            if encode == b"\135" == b"\x5d" == b"]":
                back.clear()
                return b"\033]"  # returns extra, but doesn't close

        # Declines 1..4 Bytes of 1 Unprintable Character

        if (not decode) or (not decode.isprintable()):
            return encode  # returns extra, but doesn't close

        # Accept Printable Bytes into this Osc Sequence

        neck.extend(encode)
        return b""

        # todo: accepts unbounded Bytes into an Osc Escape Sequence

    #
    # Close
    #

    def close(self) -> None:
        """Close, if not closed already"""

        head = self.head
        back = self.back
        neck = self.neck
        stash = self.stash
        tail = self.tail

        closed = self.closed

        # Close once

        if closed:
            return

        self.closed = True

        # Close a 6-Byte Mouse-Report, if held open in hope of 6 Characters

        if head == b"\033[M":
            assert (not neck) and (not tail), (neck, tail, self)

            back_plus = back + stash
            if len(back_plus) == 3:  # if exactly 6 Bytes total
                back.extend(stash)
                stash.clear()

        # Require

        self._require_simple_kpack_()  # raises AssertionError if .stash truthy


BEL = "\a"  # U+0007 Bell
CR = "\r"  # U+000D Carriage Return
ESC = "\033"  # U+001B Escape

DECSC = "\x1b" "7"  # ESC 03/07 Save Cursor [Checkpoint] (DECSC)
DECRC = "\x1b" "8"  # ESC 03/08 Restore Cursor [Revert] (DECRC)

SS3 = "\033O"  # 01/11 04/15 Single Shift Three
CSI = "\033["  # 01/11 05/11 Control Sequence Introducer
OSC = "\033]"  # 01/11 05/13 Operating System Command
ST = "\033\134"  # 05/11 05/12 String Terminator


CUU_Y = "\033[" "{}A"  # Csi 04/01 Cursor Up
CUD_Y = "\033[" "{}B"  # Csi 04/02 Cursor Down
CUF_X = "\033[" "{}C"  # Csi 04/03 Cursor [Forward] Right
CUB_X = "\033[" "{}D"  # Csi 04/04 Cursor [Back] Left

CUP_Y_X = "\033[" "{};{}H"  # Csi 04/08 [Choose] Cursor Position
ED_P = "\x1b" "[" "{}J"  # CSI 04/10 Erase in Display  # 0 Tail # 1 Head # 2 Rows # 3 Scrollback
DL_Y = "\033[" "{}M"  # Csi 04/13 Delete Line [Row]
DCH_X = "\033[" "{}" "P"  # Csi 05/00 Delete Character


SM_IRM = "\x1b" "[" "4h"  # CSI 06/08 4 Set Mode Insert, not Replace
RM_IRM = "\x1b" "[" "4l"  # CSI 06/12 4 Reset Mode Replace, not Insert

DSR_5 = "\033[" "5n"  # Csi 06/14 [Request] Device Status Report  # Ps 5 Request DSR_0
DSR_0 = "\033[" "0n"  # Csi 06/14 [Response] Device Status Report  # Ps 0 Response Ready

DSR_6 = "\033[" "6n"  # Csi 06/14 [Request] Device Status Report  # Ps 6 Request CPR
CPR_Y_X = "\033[" "{};{}R"  # Csi 05/02 [Response] Active [Cursor] Pos Rep

XTWINOPS_18 = "\033[" "18t"  # Csi 07/04 [Request] XTWINOPS_18
XTWINOPS_8_H_W = "\033[" "8;{};{}t"  # Csi 07/04 [Response] XTWINOPS_8


CSI_P_CHARS = """0123456789:;<=>?"""  # Csi Parameter Bytes
CSI_I_CHARS = """ !'#$%&'()*+,-./"""  # Csi Intermediate [Penultimate] Bytes
CSI_F_CHARS = "@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~"  # Csi Final Bytes

_START_PASTE_ = "\033[" "200~"  # ⎋[200⇧~ Start of Bracketed Paste
_END_PASTE_ = "\033[" "201~"  # ⎋[201⇧~ End of Bracketed Paste


_SM_SGR_MOUSE_ = "\033[" "?1000;1006h"  # codes Press/ Release as ⎋[{f};{x};{y} ⇧M and M
_RM_SGR_MOUSE_ = "\033[" "?1000;1006l"

_SM_SIX_MOUSE_ = "\033[" "?1000;1005h"  # codes Press/ Release as two ⎋[⇧M{xyz} Bytes/ Chars
_RM_SIX_MOUSE_ = "\033[" "?1000;1005l"

_SM_BRACKETED_PASTE_ = "\033[" "?2004h"  # codes Start/ End as ⎋[200~ and ⎋[201~
_RM_BRACKETED_PASTE_ = "\033[" "?2004l"

SM_DECTCEM = "\033[" "?25h"  # 06/08 Set Mode (SMS) 25 VT220 Show Cursor
RM_DECTCEM = "\033[" "?25l"  # 06/12 Reset Mode (RM) 25 VT220 Hide Cursor


#
# Say which Bytes need framing for closure, like by ⎋[5N ⎋[0N,
# to say if they started a burst of multiple Key Mixes or multiple Keuy Bytes,
# vs ended as quickly as they started
#


_S_ = set()
_S_.add(b"\033")  # for Byte Sequences started by ⎋ Esc
_S_.add(b"J")  # for len("J́") == 2
_S_.add(b"j")  # for len("j́") == 2
_S_.add(b"`")  # for the ⌥` Option/Alt Accents
_S_ |= set(KeyPack.StartBytes)  # for Unicode Encodes

EncodeStartSet = frozenset(_S_)


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
# todo: my Shell 'dt' is much broke
# todo: my Zsh accepts ⎋F ⎋B encodings of ⌥→ ⌥← but not iTerm2 ⎋[1;3C ⎋[1;3D
# todo: my Git Log Decorate chooses horribly bright & low-contrast Colors for iTerm2 Lightmode
# todo: please |pq transpose |pq uniq |pq transpose
# todo: j = |pq dot: our Codes need 1 Line of Text, got 44
# todo: somehow my 'p' creates an empty __pycache__/s.screen


# 3456789 123456789 123456789 123456789 123456789 123456789 123456789 123456789 123456789 123456789

# posted into:  https://github.com/pelavarre/less-beeps/blob/main/bin/less-beeps.py
# copied from:  git clone git@github.com:pelavarre/less-beeps.git
