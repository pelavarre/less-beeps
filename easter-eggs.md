# Easter-Eggs | Less-Beeps

## Easter Eggs we have coded but not named

### Beware

This work is experimental, and Python in the Terminal is a sharp scalpel

Please do show up prepared for when software goes wrong in its usual ways.
In particular, you can lose your whole Terminal Window, not just one Tab or Pane of the Window.
And we can imagine you could lose more than one Tab of a Browser, if you're running Python there

This last happened to us near to 12n Fri 7/Nov.
Python running in one Tab of a macOS iTerm2 Window hung the whole Window

### 3+ Eggs

1 ) There may be more than nine games, or less than one

2 ) You can press any of the classic ⌃C ⌃D ⌃Z ⌃\ to quit, you don't have to choose

3 ) You can press ⌃Q to close ⌃V ⌃V, you can press ⌃V to close ⌃Q ⌃Q

And our .md Markdown Sourcefiles do have more words in them,
found inside each of their invisible \<\!-- --\> Html tags

## Easter Eggs we have coded and named

Three

    --egg=leaper  # tap to move cursor, especially the ⌥ option/alt click
    --egg=native  # loops your Keyboard to Screen with no friendly distortions
    --egg=sigint  # for ⌃C to work (and for ⌃J to come across as ⌃M ⌃J)

<!-- --egg=sigtstp  # for ⌃Z to work -->
<!-- --egg=sigquit  # for ⌃\ to work -->

## Consequences of --egg=sigint

⌃C does dump a full Traceback and launch a (Pdb) Repl

⌃Q works better than ⌃V,
because you can still press ⌃Q to mean ⌃Q and ⌃Q ⌃Q to mean ⌃Q ⌃Q.
But you have to press ⌃V ⌃V to mean ⌃V, you have to press ⌃V ⌃V ⌃V ⌃V to mean ⌃V ⌃V

## Consequences of --egg=native

1 )

Expect most of your shifted Keyboard Chords won't reply visibly

We stop working to make your Terminal feel friendlier.
We stop working to limit what you can type out on the Keyboard

+ Press ⌃H to do the work of ← but by writing ⌃H to do it,
    not by writing ⎋[⇧D like ← does
+ Press ⌃J above the Southernmost Row to do the work of ↓ but by writing ⌃J to do it,
    not by writing ⎋[⇧A like ↓ does
+ Press ⌃J in the Southernmost Row to also scroll up,
    not stop there like ↓ does
+ Press ⌃K and ⌃L as aliases of the ⌃J that is scroll plus ↓,
    no longer as aliases of ↑ and →
+ Put ⏎ into Paste to write only b'\r' Carriage Return (CR),
    not to also step down
+ Press any of ← ↑ → ↓ to move the Cursor off of the Gameboard,
    not only inside

And so on and on and on

Toss in this Easter Egg, and you can pick Terminals apart by how they behave

Look for choices held in common, as minimum standards

+ Do expect ⎋C to leap into the far Northwest and wipe the Screen
+ Do expect ⎋8 to leap back to where you last said ⎋7,
    and initially to the Northwest Corner

Look for happy surprises at a macOS Terminal

+ Do expect ⎋L to leap into the far Northwest of a macOS Terminal,
+ Do expect ⇧Fn← to leap into the far Northwest of a macOS Terminal,
    because there that comes in coded as ⎋[⇧H
+ Do expect ⇧Fn→ to go Far West and a bit North across a macOS Terminal,
    because there that comes in coded as ⎋[⇧F,

Look for sad surprises

+ Don't expect ⌥← and ⌥→ to move the Cursor around a macOS Terminal,
    because there they come in coded for Emacs as ⎋B and ⎋F
+ Don't expect ⎋⇧D to include the ⌃M
    like it does at a macOS Terminal
+ Don't expect ⎋L to work
    away from the macOS Terminal
+ Don't expect ⌃⇧^ and ⌃^ to work
    away from macOS iTerm2,
    for the macOS Terminal takes only the one and the Google Cloud Shell takes only the other
+ Don't expect ⌃⇧? to work
    away from the macOS iTerm2,
    for the macOS Terminal beeps at it and the Google Cloud Shell disappears it

Please do tell us which surprises are worth mentioning here?

2 )

No Keyboard Chord Sequence you press will quit our launched Process.
To quit playing --egg=native, you'll have to close your Terminal Window Pane

Unless you think to add up front more ways to quit, such as calling for some of
    --egg=sigint, --egg=sigtstp, --egg=sigquit

## Terminal Screen-Write Cheat-Sheet

Keycap Symbols are ⎋ Esc, ⌃ Control, ⌥ Option/ Alt, ⇧ Shift, ⌘ Command/ Os

    ⌃G ⌃H ⌃I ⌃J ⌃M mean \a \b \t \n \r, and ⌃[ means \e, also known as ⎋ Esc
    ⇥ Tab means ⌃I \t, and ⏎ Return means ⌃M \r, and ⌫ ⌃? Delete means \b

The famous Esc ⎋ Byte Pairs are ⎋ 7 8 C L ⇧D ⇧E ⇧M

    ⎋7 cursor-checkpoint  ⎋8 cursor-revert (defaults to Y 1 X 1)
    ⎋C screen-erase  ⎋L row-column-leap
    ⎋⇧D \r+↓ else \r+\n  ⎋⇧E \r+↓ else \r+\n  ⎋⇧M ↑ else scroll+↑

The famous Csi ⎋[ Sequences are ⎋[ ⇧ @ ABCDE GHIJKLM P ST Z and ⎋[ D H LMN Q T

    ⎋[⇧A ↑  ⎋[⇧B ↓  ⎋[⇧C →  ⎋[⇧D ←
    ⎋[I ⌃I  ⎋[⇧Z ⇧Tab
    ⎋[D row-leap  ⎋[⇧G column-leap  ⎋[⇧H row-column-leap

    ⎋[1⇧M rows-delete  ⎋[⇧L rows-insert  ⎋[⇧P chars-delete  ⎋[⇧@ chars-insert
    ⎋[⇧J after-erase  ⎋[1⇧J before-erase  ⎋[2⇧J screen-erase  ⎋[3⇧J scrollback-erase
    ⎋[⇧K row-tail-erase  ⎋[1⇧K row-head-erase  ⎋[2⇧K row-erase
    ⎋[⇧T scrolls-down  ⎋[⇧S scrolls-up

    ⎋[4H insert  ⎋[4L replace  ⎋[6 Q bar  ⎋[4 Q skid  ⎋[ Q unstyled

    ⎋[1M bold  ⎋[4M underline  ⎋[7M reverse/inverse
    ⎋[31M red  ⎋[32M green  ⎋[34M blue  ⎋[38;5;130M orange
    ⎋[M plain

    ⎋[5N call for reply ⎋[0N
    ⎋[6N call for reply ⎋[{y};{x}⇧R  ⎋[18T call for reply ⎋[8;{rows};{columns}T

    ⎋['⇧} cols-insert  ⎋['⇧~ cols-delete

<!-- Consciously don't mention ⎋['⇧ ⎋['⇧~ as 'famous', because macOS Terminal lacks those two -->

## Links

+ [GitHub Repository](https://github.com/pelavarre/less-beeps/blob/main/easter-eggs.md)
+ [Questions/Feedback](https://twitter.com/intent/tweet?text=/@PELaVarre%20%23LessBeeps)

<!-- git clone git@github.com:pelavarre/less-beeps.git -->
