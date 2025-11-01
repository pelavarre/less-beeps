#!/usr/bin/env python3

r"""
usage: less-beeps.py [--help] [-y Y] [-x X] [-h H] [-w W] [-f] [CHORD ...]

give away nine classic simple terminal games for you to fork

positional arguments:
  CHORD        taken as if pressed, such as 'F2' or 'Esc' or '^'

options:
  --help       show this help message and exit
  -y Y         don't write above Row Y
  -x X         don't write left of Column X
  -h H         don't write more than H Rows
  -w W         don't write more than W Columns
  -f, --force  ask fewer questions

notes:
  distributed as a single .py file, now that a million words isn't many
  distributed alongside an Easter-Eggs .md file

examples:
  ./bin/less-beeps.py --
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
import tty  # for tty.setraw and tty.setcbreak
import types
import typing


_: object  # blocks Mypy from narrowing the Datatype of '_ =' at first mention

default_eq_None = None  # shoves back on Dict Get refusing the explicit ', default=' syntax

if not __debug__:
    raise NotImplementedError([__debug__])  # because 'python3 better than python3 -O'


#
# Describe the enclosing Shell in its Terminal Window Pane
#


@dataclasses.dataclass(order=True)  # , frozen=True)
class Flags:

    apple: bool = sys.platform == "darwin"  # flags.apple
    google: bool = bool(os.environ.get("CLOUD_SHELL", default_eq_None))  # flags.google
    terminal: bool = (
        os.environ.get("TERM_PROGRAM", default_eq_None) == "Apple_Terminal"
    )  # flags.terminal

    portrait: bool = False  # flags.portrait, for when lots more high than wide
    barefoot: bool = False  # flags.barefoot, for when no rows beneath a Southern Keyboard

    keyboard_interrupt_repl: bool = False  # flags.keyboard_interrupt_repl


flags = Flags()

# flags.keyboard_interrupt_repl = True


#
# Run from the Shell, but tell uncaught Exceptions to launch the Py Repl
#


def main() -> None:
    """Run from the Shell, but tell uncaught Exceptions to launch the Py Repl"""

    sys.excepthook = excepthook

    parser = arg_doc_to_parser(__main__.__doc__ or "")
    shell_args_take_in(args=sys.argv[1:], parser=parser)

    with TerminalStudio() as ts:
        ts.speak_first()
        ts.chat_awhile()
        ts.stop_chatting()


def arg_doc_to_parser(doc: str) -> ArgDocParser:
    """Declare the Positional Arguments & Options"""

    assert argparse.ZERO_OR_MORE == "*"

    parser = ArgDocParser(doc, add_help=False)

    chord_help = "taken as if pressed, such as 'F2' or 'Esc' or '^'"
    parser.add_argument("chords", metavar="CHORD", nargs="*", help=chord_help)

    help_help = "show this help message and exit"
    y_help = "don't write above Row Y"
    x_help = "don't write left of Column X"
    h_help = "don't write more than H Rows"
    w_help = "don't write more than W Columns"
    force_help = "ask fewer questions"

    parser.add_argument("--help", action="help", help=help_help)
    parser.add_argument("-y", metavar="Y", help=y_help)
    parser.add_argument("-x", metavar="X", help=x_help)
    parser.add_argument("-h", metavar="H", help=h_help)
    parser.add_argument("-w", metavar="W", help=w_help)
    parser.add_argument("-f", "--force", action="count", help=force_help)

    return parser


def shell_args_take_in(args: list[str], parser: ArgDocParser) -> argparse.Namespace:
    """Take in the Shell Command-Line Args"""

    ns = parser.parse_args_if(args)

    assert not ns.chords, (ns.chords, ns)

    assert not ns.y, (ns.y, ns)
    assert not ns.x, (ns.x, ns)
    assert not ns.h, (ns.h, ns)
    assert not ns.w, (ns.w, ns)

    if ns.force:
        KeyPack._try_key_pack_()

    ns_keys = list(vars(ns).keys())
    assert ns_keys == ["chords", "y", "x", "h", "w", "force"], (ns_keys, ns)

    return ns


#
# Run inside 1 Terminal Window Pane, till Quit
#


class TerminalStudio:
    """Run from the Shell Command Line, and launch the Py Repl vs uncaught Exceptions"""

    stdio: typing.TextIO
    fileno: int
    tcgetattr: list[int | list[bytes | int]]  # replaced by .__enter__

    screen_writer: ScreenWriter
    keyboard_reader: KeyboardReader

    selves: list[TerminalStudio] = list()

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
        self.keyboard_reader = kr

    def __enter__(self) -> TerminalStudio:

        stdio = self.stdio
        fileno = self.fileno
        tcgetattr = self.tcgetattr

        assert _SM_BRACKETED_PASTE_ == "\033[" "?2004h"

        # Enter once

        if tcgetattr:
            return self

        # Flush Output, drain Input, and change Input Mode

        stdio.flush()  # before each 'tty.setraw' of TerminalStudio.__enter__

        with_tcgetattr = termios.tcgetattr(fileno)
        assert with_tcgetattr, (with_tcgetattr,)

        self.tcgetattr = with_tcgetattr  # replaces

        # Stop line-buffering Input, stop replacing \n Output with \r\n, etc

        if not flags.keyboard_interrupt_repl:
            tty.setraw(fileno, when=termios.TCSADRAIN)  # todo: .when defaults to .TCSAFLUSH
        else:
            tty.setcbreak(fileno, when=termios.TCSADRAIN)  # todo: .when defaults to .TCSAFLUSH

        # Ask for Bracketed Paste, as if Unbracketed Paste given by default

        stdio.write("\033[" "?2004h")

        # Succeed

        return self

        # todo: try termios.TCSAFLUSH to discard Input at entry
        # todo: try tty.setcbreak, especially when debugging hangs

    def __exit__(self, *args: object) -> None:

        stdio = self.stdio
        fileno = self.fileno
        tcgetattr = self.tcgetattr

        assert _RM_BRACKETED_PASTE_ == "\033[" "?2004l"

        # Exit once

        if not tcgetattr:
            return

        # Ask for Unbracketed Paste, as if Bracketed Paste asked for by .__enter__ etc

        stdio.write("\033[" "?2004l")

        # Flush Output, drain Input, and change Input Mode

        stdio.flush()  # before each 'termios.tcsetattr' of TerminalStudio.__exit__

        fd = fileno
        when = termios.TCSADRAIN
        attributes = tcgetattr
        termios.tcsetattr(fd, when, attributes)

        self.tcgetattr = list()  # replaces

        # todo: try termios.TCSAFLUSH to discard Input at exit

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
    # Launch, run, quit - read & eval & print
    #

    def speak_first(self) -> None:
        """Launch quickly"""

        sw = self.screen_writer
        sw.sprint("⌃D to quit,  Fn F1 for more help,  or ⌥-Click far from the Cursor")

    def chat_awhile(self) -> None:
        r"""Loop and don't quit till one of ⌃C ⌃D ⌃Z ⌃\ """

        sw = self.screen_writer

        sw.sprint()
        while True:
            self.loop_back()
            self.trace_key_mixes()

    def loop_back(self) -> None:

        kr = self.keyboard_reader
        sw = self.screen_writer

        kmindex = -1
        while True:

            if kmindex >= 0:

                kbytearray = bytearray()
                for kmi in range(kmindex, kr.kmindex):
                    kmix = kr.kmixes[kmi]
                    kpack = kmix.kpack
                    kbytes = kpack.to_kbytes()
                    kbytearray.extend(kbytes)

                kpack = KeyPack(b"")
                for (index, kord) in enumerate(kbytearray):
                    rindex = index - len(kbytearray)

                    kbyte = bytes([kord])
                    extra = kpack.take_one_kbyte_if(kbyte)
                    if extra:
                        break

                    kbytes = kpack.to_kbytes()
                    if kpack.closed:
                        kdecode = kbytes.decode()

                        # sw.swrite(repr(kdecode))
                        sw.swrite(kdecode)

                        kmindex = -1

            kmix = kr.read_one_key_mix()

            if kmix.kcaps in ("⌃Q", "⌃V"):
                break

            ok = False
            # ok = ok or self.answer_printable_kdecode(kmix.kdecode)
            ok = ok or self.answer_controls_kmix(kmix)
            ok = ok or self.answer_arrows_kface(kmix.kface)
            if not ok:
                if kmix.kface == "⎋":
                    sw.sprint(kmix.kface, end="")
                    kmindex = kr.kmindex - 1
                elif kmix.kface:
                    sw.sprint("", kmix.kface, end=" ")
                elif kmix.kcaps:
                    sw.sprint(kmix.kcaps, end="")
                else:
                    sw.sprint("", kmix.kencode, end=" ")

            if kmix.kcaps in ("⌃C", "⌃D", "⌃Z", "⌃\\"):
                sw.sprint("")
                sys.exit()

        # todo1: livelocks less wild in Keyboard/ Screen loopback

    def trace_key_mixes(self) -> None:

        kr = self.keyboard_reader
        sw = self.screen_writer

        kmixes = kr.kmixes
        old_kmix = kmixes[-1]
        assert old_kmix.kcaps in ("⌃Q", "⌃V")

        kcaps = old_kmix.kcaps

        sw.swrite("\0337")
        sw.swrite(kcaps)
        sw.swrite("\0338")

        kmix = kr.read_one_key_mix()

        sw.swrite("\0337")
        sw.sprint(kcaps, kmix)
        sw.swrite("\0338")
        sw.swrite("\n")

        kmindex = len(kr.kmixes)
        while kr.kmindex < kmindex:
            kmix = kr.read_one_key_mix()

            sw.swrite("\0337")
            sw.sprint(kcaps, kmix)
            sw.swrite("\0338")
            sw.swrite("\n")

        if kmix.kcaps == kcaps:
            while True:
                kmix = kr.read_one_key_mix()

                sw.swrite("\0337")
                sw.sprint(kcaps + kcaps, kmix)
                sw.swrite("\0338")
                sw.swrite("\n")

                if kmix.kcaps == kcaps:
                    break

    def stop_chatting(self) -> None:
        """Drain the Buffered Input just before Quitting"""

        kr = self.keyboard_reader
        sw = self.screen_writer

        # Drain the Keyboard Buffer

        while self.kbhit(timeout=0.100):
            km = kr.read_one_key_mix()
            sw.sprint(km)

        # Drain the Keyboard Bytes fetched ahead

        kbytes = bytes(kr.kbytearray[kr.kbindex :])
        if kbytes:  # todo: empty except when Exception unhandled?
            sw.sprint(kbytes)
            sw.sprint()

        sw.sprint("bye")

        # todo3: revive the App to loop Keyboard to Screen
        # todo3: ⌃Q and ⌃V quote till first KeyboardReader .kbytearray gone

        # todo2: revive the Apps at 'git checkout main' App's

    #
    # Choose Outputs for each Input
    #

    def answer_printable_kdecode(self, kdecode: str) -> bool:
        """Loop Printable Key Bytes to Screen"""

        sw = self.screen_writer

        if kdecode and kdecode.isprintable():
            sw.swrite(kdecode)
            return True

        return False

    def answer_controls_kmix(self, kmix: KeyMix) -> bool:
        """Loop basic Control Sequences to Screen"""

        sw = self.screen_writer

        #

        swrite_by_kface = {
            # "⌫": "\b" "\033[P",  # todo3: overwrite/ insert mode
            "⌫": "\b",  # Delete
            "⏎": "\r",  # Return
            "⇥": "\t",  # Tab
            "⇧⇥": "\033[Z",  # ⇧Tab
        }

        kface = kmix.kface
        if kface in swrite_by_kface.keys():
            swrite = swrite_by_kface[kface]
            sw.swrite(swrite)
            return True

        #

        swrite_by_kcaps = {
            "⌃H": "\b",
            "⌃J": "\n",
            "⌃K": "\x0B",
        }

        kcaps = kmix.kcaps
        if kcaps in swrite_by_kcaps.keys():
            swrite = swrite_by_kcaps[kcaps]
            sw.swrite(swrite)
            return True

        #

        return False

    def answer_arrows_kface(self, kface: str) -> bool:
        """Loop Arrows and shifted Arrows to Screen"""

        sw = self.screen_writer

        swrite_by_kf = {
            "↑": "\033[A",
            "↓": "\033[B",
            "→": "\033[C",
            "←": "\033[D",
        }

        ok = False
        for kf in ("←", "↑", "→", "↓"):
            if kf in kface:
                swrite = swrite_by_kf[kf]
                sw.swrite(swrite)
                ok = True

        return ok


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
        stdio.write(text)

        # todo2: ScreenWriter snoop ⎋[⇧?2004L and ⎋[⇧?2004H to know toggled Bracketed Paste
        # todo2: snoop ⎋[⇧?1006H and ⎋[⇧?1006L to know toggled Csi ⇧M M Sgr Mouse
        # todo2: snoop ⎋[⇧?1005H and ⎋[⇧?1005L to know toggled Csi ⇧M ⇧M Six Mouse


@dataclasses.dataclass(order=True)  # , frozen=True)
class KeyboardReader:
    """Mirror the Reads from a Terminal Keyboard"""

    terminal_studio: TerminalStudio
    screen_writer: ScreenWriter

    kmixes: list[KeyMix]
    kmindex: int

    kpacks: list[KeyPack]
    kpindex: int

    kbytearray: bytearray
    kbindex: int

    def __init__(self, terminal_studio: TerminalStudio, screen_writer: ScreenWriter) -> None:

        self.terminal_studio = terminal_studio
        self.screen_writer = screen_writer

        self.kmixes = list()
        self.kmindex = 0

        self.kpacks = list()
        self.kpindex = 0

        self.kbytearray = bytearray()
        self.kbindex = 0

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
            self._fill_kmixes_(timeout=timeout)
            if kmindex >= len(kmixes):
                empty_kmix = KeyMix(b"")
                return empty_kmix

        # Read one Key Mix

        kmix = kmixes[kmindex]
        self.kmindex += 1

        return kmix

    def _fill_kmixes_(self, timeout: float | None) -> None:
        """Read enough Key Packs to close the next Key Mix"""

        kmixes = self.kmixes
        kmindex = self.kmindex

        kpacks = self.kpacks
        kpindex = self.kpindex

        option_ktext_by_kt = KeyMix.OPTION_KTEXT_BY_KT

        # Read more Key Mixes only when needed

        assert kmindex == len(kmixes), (kmindex, kmixes[kmindex:])

        # Fill with Key Packs, else quit now

        kqa_tuple: tuple[tuple[str, str], ...] = tuple()
        if kpindex >= len(kpacks):
            kqa_tuple = self._fill_kpacks_(timeout=timeout)
            if kpindex >= len(kpacks):
                return

        # Drain the Key Packs

        while kpindex < len(kpacks):
            kpack = kpacks[kpindex]
            self.kpindex += 1
            kpindex = self.kpindex  # replaces

            # Form a 1st Draft Key Mix

            kencode = kpack.to_kbytes()

            try:
                kdecode = kencode.decode()
            except UnicodeDecodeError:
                kdecode = ""

            kmix = KeyMix(kbytes=kencode, kqa_tuple=kqa_tuple)

            # Take up 1 or the 1st of 2 Key Mixes from 1 or 2 Key Packs

            kmixes.append(kmix)

            # Take up 2 Key Mixes from 1 Key Pack, when sent by an Option/Alt ⌥ Accent E plus J or ⇧J

            if kencode in (b"j\xcc\x81", b"J\xcc\x81"):
                option_e_j_kcaps = "J́" if kencode == b"j\xcc\x81" else "⇧J́"
                assert kmix.kcaps == option_e_j_kcaps, (kmix.kcaps, kdecode, kencode)
                kmix.kcaps = "⌥E"

                option_e_j_kmix = KeyMix(kbytes=kencode[:1])  # '⇧J'
                assert not option_e_j_kmix.kface, (option_e_j_kmix.kface, kencode)

                kmixes.append(option_e_j_kmix)
                continue

            # Take up 2 Key Mixes from 1 Key Pack, when sent by an Option/Alt ⌥ Accent Key

            option_accent_key_mix_pair = kdecode in option_ktext_by_kt.keys()
            if kdecode and (kdecode[0] == "`") and (kdecode[1:]):
                option_accent_key_mix_pair = True

            if option_accent_key_mix_pair:
                assert kdecode, (kdecode, kencode)  # option_ktext or ``
                assert not kmix.kface, (kmix.kface, kdecode, kencode)  # option_ktext or ``

                if kdecode.startswith("`"):
                    ktext = "⌥`"
                    assert kmix.kcaps.startswith("`"), (kmix.kcaps, kdecode, kencode)
                    kcaps_list = [ktext, kmix.kcaps[1:]]
                    kmix.kcaps = ktext
                else:
                    assert len(kdecode) == 1, (kdecode, kencode)
                    ktext = option_ktext_by_kt[kdecode]
                    kcaps_list = ktext.split()

                    kcaps_0 = kcaps_list[0]  # '⌥E'
                    assert kmix.kcaps == kcaps_0, (kmix.kcaps, kcaps_0, ktext)

                    if kcaps_list[1:]:
                        if kcaps_0.startswith("⌥⇧"):  # (kcaps_0 == "⌥`") is already ok
                            assert kcaps_0.count("⇧") == 1, (kcaps_0, kencode)  # '⌥⇧E'
                            alt_kcaps_0 = kcaps_0.replace("⌥⇧", "⌥")  # '⌥E'
                            kmix.kcaps = alt_kcaps_0

                # Patch up the 1st Key Face of the 2 Key Mixes

                assert len(kcaps_list) in (1, 2), (kcaps_list, kdecode, kencode)  # ['⌥E', 'E']
                if kcaps_list[1:]:

                    kcaps_0 = kcaps_list[0]  # '⌥E'
                    assert "⇧" not in kcaps_0, (kcaps_0, kencode)

                    # Patch up the 2nd Key Face of the 2 Key Mixes

                    option_accent_kmix = KeyMix(kbytes=b"")

                    assert not kmix.kface, (kmix.kface, kencode)  # because kbytes=b""
                    assert not option_accent_kmix.kcaps, (
                        option_accent_kmix.kcaps,
                    )  # because kbytes=b""

                    option_accent_kmix.kcaps = kcaps_list[-1]  # 'I'

                    kmixes.append(option_accent_kmix)
                    continue

    def _fill_kpacks_(self, timeout: float | None) -> tuple[tuple[str, str], ...]:
        """Read enough Key Bytes to close the next Key Pack"""

        kpacks = self.kpacks
        kpindex = self.kpindex

        kbytearray = self.kbytearray
        kbindex = self.kbindex

        option_kt_join = KeyMix.OPTION_KT_JOIN  # '∂' for ⌥D

        # Read more Key Packs only when needed

        assert kpindex == len(kpacks), (kpindex, kpacks[kpindex:])

        # Fill with Bytes, else quit now

        kqa_tuple: tuple[tuple[str, str], ...] = tuple()
        if kbindex >= len(kbytearray):
            kqa_tuple = self._fill_kbytearray_(timeout)
            if kbindex >= len(kbytearray):
                assert not kqa_tuple, (kqa_tuple,)
                return kqa_tuple

        # Drain the Bytes

        kpack = KeyPack(b"")
        while kbindex < len(kbytearray):
            kbyte = bytes(kbytearray[kbindex:][:1])

            # Append Bytes till Key Pack closes

            extra = kpack.take_one_kbyte_if(kbyte)
            if not extra:
                self.kbindex += 1
                kbindex = self.kbindex  # replaces

            if kpack.closed:
                kpacks.append(kpack)
                kpack = KeyPack(b"")
                continue

            assert not extra, (extra, kpack, kbyte)

            # Take the Key Pack early, if Text is an ⌥ Option/Alt Key Pack

            text = kpack.text
            if len(kpacks) == kpindex:
                if text and (text in option_kt_join):  # '∂' for ⌥D
                    kpacks.append(kpack)
                    kpack = KeyPack(b"")
                    continue

            # todo3: question/answer ⎋[⇧R ⎋[T on top of ⎋[5N to do ⌥ Release Bursts

        # Take the last of the Bytes arriving all at once as a Key Pack

        if kpack:
            kpacks.append(kpack)

        # Succeed

        return kqa_tuple

        # todo2: test ⎋[⇧M Csi Mouse Report then ⎋[⇧Z etc with ⎋[5n and ⎋[0n

    def _fill_kbytearray_(self, timeout: float | None) -> tuple[tuple[str, str], ...]:
        """Fetch Bytes into Self"""

        ts = self.terminal_studio
        sw = self.screen_writer
        kbytearray = self.kbytearray
        kbindex = self.kbindex

        encode_start_set = EncodeStartSet

        # Read more Key Bytes only when needed

        assert kbindex == len(kbytearray), (kbindex, kbytearray[kbindex:])

        # Fetch 1 Key Byte to start with

        kbyte = ts.read_one_kbyte_if(timeout=timeout)  # fetches one or zero Key Bytes
        kbytearray.extend(kbyte)

        question_index = len(kbytearray)

        # Plan to fetch Key Packs till next ⎋[0N, if the Key Packs might be multibyte or multiple

        question = answer = ""
        if kbyte in encode_start_set:
            question = "\033[5n"
            answer = "\033[0n"

        questions = list()
        if question:
            sw.swrite(question)
            questions.append(question)

        # Fetch Key Packs till next Answer, if Question asked

        open_questions = list(questions)
        answers = list()

        while open_questions:

            # Fetch 1 Key Byte

            kbyte = ts.read_one_kbyte_if(timeout=timeout)  # fetches one or zero Key Bytes
            kbytearray.extend(kbyte)

            # Don't take ⎋[0N as End-of-Input when immediately after explicit ⎋[200~ Start-of-Paste

            if kbytearray[kbindex:] == b"\033[200~":
                question_index = len(kbytearray) + 1

            # Do take ⎋[0N as End-of-Input when received after sending ⎋[5 to ask for it

            answer_encode = answer.encode()
            n = len(answer_encode)

            assert answer_encode, answer_encode  # because truthy .open_questions
            if kbytearray[question_index:].endswith(answer_encode):
                del kbytearray[-n:]

                open_questions.remove(question)
                answers.append(answer)

        # Succeed

        kqa_tuple = tuple(zip(questions, answers))  # maybe empty
        return kqa_tuple

        # todo2: launch an app of many Keyboard Viewers:  plain, ⎋, ⌃, ⌥, ⇧, ⎋⌃, etc etc
        # todo2: how about one Keyboard Viewer at a time


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
                shargs = list()

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

    if exc_type is SystemExit:  # todo: doc how raise SystemExit calls .excepthook in python3 -i
        # with_excepthook(exc_type, exc_value, exc_traceback)
        return

    # Quit now for visible cause, if KeyboardInterrupt

    if not flags.keyboard_interrupt_repl:
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
class KeyMix:
    """Bundle one Tap or Click or Keyboard Input"""

    kface: str  # '⏎'  # '<>'
    kcaps: str  # '⌃M'  # '⌃[[A'
    kpack: KeyPack  # .head .neck .back .stash .tail
    kencode: bytes  # .kpack.to_kbytes()
    kdecode: str  # .decode of .encode, else Empty Str ""
    kintsmark: bytes  # neck-start + back + tail
    kints: list[int]  # via Csi Neck after Csi Next Start
    kqa_tuple: tuple[tuple[str, str], ...]  # questions asked, answers given

    def __init__(self, kbytes: bytes, kqa_tuple: tuple[tuple[str, str], ...] = ()) -> None:

        # Collect

        kface = KeyMix.to_kface_if(kbytes)
        kcaps = KeyMix.to_kcaps_if(kbytes)
        kpack = KeyPack(kbytes)  # maybe .closed, maybe not

        kencode = kbytes
        try:
            kdecode = kbytes.decode()
        except UnicodeDecodeError:
            kdecode = ""

        (kintsmark, kints) = KeyMix.to_csi_ints_if(kbytes)
        if (not kintsmark) and (not kints):
            (kintsmark, kints) = KeyMix.to_csi_m_ints_if(kbytes)

        # Succeed

        self.kface = kface
        self.kcaps = kcaps
        self.kpack = kpack
        self.kencode = kencode
        self.kdecode = kdecode
        self.kintsmark = kintsmark
        self.kints = kints
        self.kqa_tuple = kqa_tuple

        self._require_simple_kmix_()

    def __bool__(self) -> bool:

        kcaps = self.kcaps
        kpack = self.kpack

        truthy = bool(kcaps) or bool(kpack)

        return truthy

    def __str__(self) -> str:

        kface = self.kface
        kcaps = self.kcaps
        kpack = self.kpack
        kintsmark = self.kintsmark
        kints = self.kints
        kqa_tuple = self.kqa_tuple

        # Collect the distinctive Parts, but shrug off .kencode and .kdecode

        parts = list()

        parts.append(kface if kface else "<>")

        if kcaps:
            parts.append(kcaps)

        kbytes = kpack.to_kbytes()
        parts.append(str(kpack))
        if kpack.text:
            if len(kbytes) > len(kpack.text):
                parts.append(str(kbytes))

        if not kintsmark:
            assert not kints, (kints,)
        elif kints:
            parts.append(str(kints))  # lets the .kpack show the .kintsmark

        # Mark the end strongly with the Questions asked and their Answers

        if kqa_tuple:

            kqa_texts = list()
            for kq, ka in kqa_tuple:
                for k in (kq, ka):
                    k_bytes = k.encode()
                    k_caps = KeyMix.to_kcaps_if(k_bytes)
                    assert k_caps.startswith("⌃["), (k_caps, k_bytes)
                    k_face = "⎋" + k_caps.removeprefix("⌃[")  # '⎋[0N'
                    kqa_texts.append(k_face)

            part = " ".join(kqa_texts)  # '⎋[5N ⎋[0N'

            parts.append(part)

        # Succeed

        join = " ".join(parts)
        assert join.isprintable(), (join,)

        return join

        # ⇧⇥ ⌃[[⇧Z b'\x1b[' b'Z' []
        # ↑ ⌃[[⇧A b'\x1b[' b'A' []
        # ⎋F1 ⌃[⌃[⇧O⇧P b'\x1b\x1bO' b'P'
        # ⇧→ ⌃[[1;2⇧C b'\x1b[' b'1;2' b'C' [1, 2]

        # ⌥3 '£' b'\xc2\xa3'
        # ⌥⇧@ '€' b'\xe2\x82\xac'

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
            if kface != "Spacebar":
                assert kcaps, (kcaps, kface, kencode)

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

        kintsmark = b""
        kints: list[int] = list()

        if (head != b"\033[") or not closed:
            return (kintsmark, kints)

        # Fail if no ';' Semicolon Marks and no Decimal Digits

        kintsmark = bytes(back + tail)
        m = re.search(b"[0-9;]+", string=neck)
        if not m:
            return (kintsmark, kints)

        # Pass back the Ints

        kints = list((int(_) if _ else -1) for _ in m.group().split(b";"))

        kprefix = neck[: m.start()]
        ksuffix = neck[m.end() :]
        kintsmark = bytes(kprefix + ksuffix + back + tail)

        return (kintsmark, kints)

        # (b"A", [])
        # (b"H", [-1, 2])
        # (b"<m", [8, 80, 25])

    @staticmethod
    def to_csi_m_ints_if(kbytes: bytes) -> tuple[bytes, list[int]]:
        """Pick out the Nonnegative Int Literals of a Csi Mouse Report"""

        kpack = KeyPack(kbytes)

        head = kpack.head
        neck = kpack.neck
        back = kpack.back
        tail = kpack.tail
        closed = kpack.closed

        assert CSI == "\033["

        # Fail if not a Csi ⇧M Escape Sequence, closed when full

        kintsmark = b""
        kints: list[int] = list()

        if (head != b"\033[M") or not closed:
            return (kintsmark, kints)

        assert (not neck) and (not tail), (neck, tail, kbytes)

        # Pass back the Ord's of 3 Bytes, no matter if Decodable as Characters

        kintsmark = b"M"
        if len(back) == 3:
            kints = list(back)
            return (kintsmark, kints)

        # Pass back the Ord's of 3 Characters

        try:
            decode = back.decode()
        except UnicodeDecodeError:
            assert False, (back, kbytes)

        kints = list(ord(_) for _ in decode)
        return (kintsmark, kints)

    #
    # Choose 1 Keycap per Character to speak of the Bytes of 1 Keyboard Chord
    #

    @staticmethod
    def to_kcaps_if(kbytes: bytes) -> str:
        """Choose 1 Keycap per Character to speak of the Bytes of 1 Keyboard Chord"""

        assert KeyMix.KCAP_SEP == " "

        if not kbytes:
            return ""

        try:
            ktext = kbytes.decode()
        except UnicodeDecodeError:
            return ""

        assert ktext, (ktext,)

        kcaps = ""
        for kt in ktext:  # often 'len(ktext) == 1'
            if kt == " ":
                return ""

            kc = KeyMix._kt_to_kcap_(kt)
            kcaps += kc

        assert kcaps, (kcaps, kbytes)
        assert " " not in kcaps, (kcaps, kbytes)

        return kcaps

        # '⎋[25;80R' Cursor-Position-Report (CPR)
        # '⎋[25;80t' Rows x Column Terminal Size Report

        # '⎋[200~' and '⎋[201~' before/ after Paste to bracket it

    @staticmethod
    def _kt_to_kcap_(kt: str) -> str:
        """Form 1 Key Cap to speak of 1 Keyboard Chord"""

        ko = ord(kt)

        option_kt_str = KeyMix.OPTION_KT_STR  # '∂' for ⌥D
        option_ktext_by_kt = KeyMix.OPTION_KTEXT_BY_KT  # 'é' for ⌥EE

        assert KeyMix.SHIFTED_KEYCAPS == '!"#$%&()*+' ":<>?" "@" "^_" "{|}~"

        # Show more Key Caps than US-Ascii mentions

        if kt in '!"#$%&()*+' ":<>?" "@" "^_" "{|}~":
            kc = "⇧" + kt

        elif (kt != "`") and (kt in option_ktext_by_kt.keys()):  # Mac US Option Accents
            kcaps_list = option_ktext_by_kt[kt].split()
            assert len(kcaps_list) in (1, 2), (kcaps_list, ko, kt)  # ['⌥E', 'E']
            kc = kcaps_list[0]  # trusts Caller to fix up the Ambiguity of len

        elif kt in option_kt_str:  # Mac US Option Key Caps
            kc = KeyMix._option_kt_to_kcap_(kt)
            assert " " not in kc, (kc, ko, kt)

        # Show the Key Caps of US-Ascii, plus the ⌃ ⇧ Control/ Shift Key Caps

        elif (ko < 0x20) or (ko == 0x7F):  # C0 Control Bytes, or \x7F Delete (DEL) ⌫
            if ko == 0x1B:
                kc = "⎋"  # could be ⌃[
            elif ko == 0x1F:  # Apple ⌃- doesn't come through as  (0x2D ^ 0x40)
                kc = "⌃-"  # Apple ⌃-  and ⌃⇧_ do come through as (0x5F ^ 0x40)
            else:
                kc = "⌃" + chr(ko ^ 0x40)  # '^ 0x40' mixes ⌃ into one of @ A..Z [\]^_ ?, such as ⌃^

                # '⌃^' speaks of (ko == 0x1E == (0x5E ^ 0x40))

            # '^ 0x40' speaks of ⌃@ but not ⌃⇧@ and not ⌃⇧2 and not ⌃Spacebar at b"\x00"
            # '^ 0x40' speaks of ⌃M but not Return ⏎ at b"\x0D"
            # '^ 0x40' speaks of ⌃[ ⌃\ ⌃] ⌃_ but not ⎋ and not ⌃⇧_ and not ⌃⇧{ ⌃⇧| ⌃⇧} ⌃-
            # '^ 0x40' speaks of ⌃? but not Delete ⌫ at b"\x7F"

            # ⌃` ⌃2 ⌃6 ⌃⇧~ don't work

        elif "A" <= kt <= "Z":  # printable Upper Case English
            kc = "⇧" + chr(ko)  # shifted Key Cap '⇧A' from b'A'

        elif "a" <= kt <= "z":  # printable Lower Case English
            kc = chr(ko ^ 0x20)  # plain Key Cap 'A' from b'a'

        # Test that no Keyboard sends the C1 Control Bytes, nor the Quasi-C1 Bytes

        elif ko in range(0x80, 0xA0):  # C1 Control Bytes
            kc = repr(bytes([ko]))  # b'\x80'
        elif ko == 0xA0:  # 'No-Break Space'
            assert ((0xA0 & 0x7F) ^ 0x40) == 0x60 == ord("`")
            kc = "⌃`"  # macOS ⌥Spacebar
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
        # ⌥Y often comes through as \ U+005C Reverse-Solidus aka Backslash  # not ¥ Yen-Sign

    SHIFTED_KEYCAPS = '!"#$%&()*+' ":<>?" "@" "^_" "{|}~"  # !"#$%&()*+ :<>? @ ^_ {|}~

    #
    # Decode Keys shifted by ⌥ Option/Alt, as at MacBook
    #

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
        # ⌥`
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

    OPTION_KT_ENCODE_START_SET = set(_.encode()[:1] for _ in OPTION_KT_JOIN)
    OPTION_KT_ENCODE_START_SET.add(b"``"[:1])  # the two bytes b'``' encode the KeyMix ⌥``

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

        # Choose ⎋ followed by 1 of our tabulated Key Faces, when encoded as ⎋...

        if not ktext.startswith("\033"):
            return ""

        esc_depth = len(ktext) - len(ktext.lstrip("\033"))

        esc_prefix_minus = (esc_depth - 1) * "\033"
        if esc_prefix_minus:
            esc_ktext_plus = ktext.removeprefix(esc_prefix_minus)
            if esc_ktext_plus in kface_by_ktext.keys():
                esc_kface_plus = kface_by_ktext[esc_ktext_plus]
                assert esc_kface_plus, (esc_kface_plus, kbytes)

                kface = (len(esc_prefix_minus) * "⎋") + esc_kface_plus
                assert kface, (kface, kbytes)

                assert " " not in kface, (kface, kbytes)
                return kface

                # ⎋⇧⇥, like from Apple Keyboard > Option as Meta Key

        # Choose ⎋ followed by 1 of our tabulated Key Faces, when not encoded as ⎋...

        esc_prefix = esc_depth * "\033"
        esc_ktext = ktext.removeprefix(esc_prefix)
        if esc_ktext in kface_by_ktext.keys():
            esc_kface = kface_by_ktext[esc_ktext]
            assert esc_kface, (esc_kface, kbytes)

            kface = (len(esc_prefix) * "⎋") + esc_kface
            assert kface, (kface, kbytes)

            assert " " not in kface, (kface, kbytes)
            return kface

            # ⎋⇥, ⎋⏎, ⎋⌫, like from Apple Keyboard > Option as Meta Key

        # Choose ⎋ followed by 1 Text Character, like from Apple Keyboard > Option as Meta Key

        if len(esc_ktext) == 1:
            if " " not in esc_ktext:
                esc_kcaps = KeyMix.to_kcaps_if(esc_ktext.encode())
                assert esc_kcaps, (esc_kcaps, esc_ktext.encode())

                kface = (len(esc_prefix) * "⎋") + esc_kcaps

                assert " " not in kface, (kface, kbytes)
                return kface

        # Fail to choose a Key Face

        return ""

        # 'A'  # '⌃L'  # '⇧Z'  # '⎋⇧⇥'  # '⎋⏎'  # '⎋1'

    KFACE_BY_KTEXT = {  # r"←|↑|→|↓" and so on  # ⌃ ⌥ ⇧ ⌃⌥ ⌃⇧ ⌥⇧ ⌃⌥⇧ and so on
        "\x00": "⌃Spacebar",  # ⌃@  # ⌃⇧2
        # "\x03": "Interrupt",  # ⌃C also found at Fn⏎ in iTerm2 Apple
        # "\x08": "Backspace",  # ⌃H also found at ⌃⇧⌫ and ⌃⌥⇧⌫ in iTerm2 Apple
        "\x09": "⇥",  # '\t' ⇥
        "\x0d": "⏎",  # '\r' ⏎
        "\033": "⎋",  # Esc  # Meta  # includes ⎋Spacebar ⎋⇥ ⎋⏎ ⎋⌫ without ⌥
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
        "\x20": "Spacebar",  # ' '  # ␠  # ␣  # ␢
        # "``": "⌥` `",  # without the "``" Key Text here, because it comes as 2 Key Faces
        "\x7f": "⌫",  # ␡  # ⌫  # ⌦  # Delete
        "\xa0": "⌥Spacebar",  # '\N{No-Break Space}'
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

        if neck or back or tail:
            assert head, (head, neck, back, tail, self)

            ends = list()
            for end in headbook:
                if head.endswith(end):  # Head End not-found in Headbook by ⎋[⇧M Csi Mouse Report
                    ends.append(end)

                    start = head.removesuffix(end)
                    assert start == (len(start) * b"\033"), (start, end, head, self)

            if tail:
                assert closed, (closed, tail, self)

        if stash:
            assert not tail, (tail, closed, stash, self)
            assert not closed, (closed, stash, self)

        if closed:
            assert not stash, (stash, closed, self)

    #
    # Run quick and slow Self-Test's
    #

    @staticmethod
    def _try_key_pack_() -> None:
        """Run quick and slow Self-Test's"""

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

    StartBytes = tuple(bytes([_]) for _ in range(0xE0, 0xF4 + 1))  # what UTF-8 completes

    @staticmethod
    def _try_ends_later_() -> None:
        """Require each StartsWith accepted by .bytes_to_later_decode via the Endswiths"""

        start_set = set()
        for cp in range(0x110000):
            if 0xD800 <= cp <= 0xDFFF:  # skips surrogates
                continue
            kbytes = chr(cp).encode()
            for index in range(1, len(kbytes) - 1):
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

    @staticmethod
    def _try_extra_(kbytes: bytes, extra: bytes) -> None:
        """Require the Pack to reject these Bytes, after closing itself if need be"""

        kpack = KeyPack(kbytes)
        actual_extra = kpack.take_some_kbytes_if(extra)
        assert actual_extra == extra, (actual_extra, extra, str(kpack))

        assert kpack.closed, (kpack,)

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

        self._require_simple_kpack_()

        extra = self._take_one_kbyte_if_(kbyte)
        if extra:
            self.close()

        self._require_simple_kpack_()

        return extra

    def _take_one_kbyte_if_(self, kbyte: bytes) -> bytes:
        """Take in next 1 Byte and return 0 Bytes, else return 1..4 Bytes that don't fit"""

        assert len(kbyte) == 1, (kbyte,)

        closed = self.closed
        stash = self.stash
        text = self.text
        head = self.head

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
            head.extend(encode)  # chooses b"\033[M" as Head
            return b""

        if head.startswith(b"\033[M"):  # ⎋[⇧M
            extra = self._take_after_csi_shift_em_if_(encode, decode=decode)
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
            return encode

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
            self.closed = True
            return encode

            # doesn't take ⎋⎋ ⎋⇧O⎋ ⎋[⎋ ⎋]⎋

        # Take 1..4 Printable or Unprintable or Undecodable Bytes as a Tail of the Head

        assert not encode.endswith(b"\033"), (encode, self)

        tail.extend(encode)
        self.closed = True
        return b""

        # does take ⎋\x10 ⎋\b ⎋\t ⎋\n ⎋\r ⎋\x7f etc

    def _take_after_csi_shift_em_if_(self, encode: bytes, decode: str) -> bytes:
        """Take Bytes into a Csi Mouse Report of 6 Bytes or 6 Characters"""

        head = self.head
        back = self.back

        assert head == b"\033[M", (head,)  # ⎋[M Mouse Report
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
            self.closed = True
            return encode

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
            self.closed = True
            return encode

        # Declines 2..4 Bytes of Multibyte Character

        assert len(decode) == 1, decode
        code = ord(decode)

        if not (0x20 <= code <= 0x7F):
            self.closed = True
            return encode

        assert len(encode) == 1, (encode, code, self)

        # Accept 1 Byte into Back, into Neck, or as Tail

        assert CSI_P_CHARS == "0123456789:;<=>?"
        assert CSI_I_CHARS == """ !'#$%&'()*+,-./"""
        assert CSI_F_CHARS == "@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~"

        if not back:
            if 0x30 <= code < 0x40:  # 16 Parameter Codes  # 0123456789:;<=>?
                neck.extend(encode)
                return b""

        if 0x20 <= code < 0x30:  # 16 Intermediate Codes  # Spacebar !"#$%&\'()*+,-./
            back.extend(encode)
            return b""

        if 0x40 <= code < 0x7F:  # 63 Final Codes  # @A Z[\\]^_`a z{|}~
            assert not tail, (tail,)
            tail.extend(encode)
            self.closed = True
            return b""

            # splits the '⎋[200~' Start and '⎋[201~' End apart from Bracketed Paste

        # Decline 1 Byte of any unfitting Character

        self.closed = True
        return encode

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
                self.closed = True
                return b"\033]"

        # Declines 1..4 Bytes of 1 Unprintable Character

        if (not decode) or (not decode.isprintable()):
            return encode

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
        stash = self.stash
        closed = self.closed

        # Close once

        if closed:
            return

        self.closed = True

        # Close a 6-Byte Mouse-Report, if held open in hope of 6 Characters

        if head == b"\033[M":
            back_plus = back + stash
            if len(back_plus) == 3:  # if exactly 6 Bytes total
                back.extend(stash)
                stash.clear()

            # doesn't call .close_if_csi_shift_m

        # Require

        self._require_simple_kpack_()

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

                self._require_simple_kpack_()

                return True

        self._require_simple_kpack_()

        return False


@dataclasses.dataclass(order=True)  # , frozen=True)
class KeyByte:
    """Mirror one Os Read of one Byte, or zero Bytes, from a Terminal Keyboard"""

    t0: int  # time of Call
    kbytes: bytes  # empty at timeout, else 1 Byte
    t1: int  # time of Return

    # todo2: start testing Class KeyByte


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
# Say which Bytes need closure, like by ⎋[5N ⎋[0N,
# to say if they started a burst of Key Mixes,
# or started a burst of Key Bytes,
# or ended as quickly as they started
#


_S_ = set()
_S_.add(b"\033")  # for Byte Sequences started by ⎋ Esc
_S_.add(b"J")  # for len("J́") == 2
_S_.add(b"j")  # for len("j́") == 2
_S_ |= set(KeyPack.StartBytes)  # for Unicode Encodes
_S_ |= set(KeyMix.OPTION_KT_ENCODE_START_SET)  # for ⌥ Option/Alt Accents

EncodeStartSet = frozenset(_S_)


#
# Run a very few Self-Test's very quickly
#


_ = KeyMix(b"")  # < 20us


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


# 3456789 123456789 123456789 123456789 123456789 123456789 123456789 123456789 123456789 123456789

# posted into:  https://github.com/pelavarre/less-beeps/blob/main/bin/less-beeps.py
# copied from:  git clone git@github.com:pelavarre/less-beeps.git
