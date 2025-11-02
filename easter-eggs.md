# Easter-Eggs | Less-Beeps

## Easter Eggs we have coded but not named

### Three Eggs

1 ) There may be more than nine games, or less than one

2 ) You can press any of of the classic ⌃C ⌃D ⌃Z ⌃\ to quit, you don't have to choose

3 ) You can press ⌃Q to close ⌃V ⌃V, you can press ⌃V to close ⌃Q ⌃Q

## Easter Eggs we have coded and named

Two

    --egg=native  # loops your Keyboard to Screen with no friendly distortions
    --egg=sigint  # for ⌃C to work (and for ⌃J to come across as ⌃M ⌃J)

<!-- --egg=sigtstp  # for ⌃Z to work -->
<!-- --egg=sigquit  # for ⌃\ to work -->

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
+ Don't expect ⌥← and ⌥→ to move the Cursor,
    because they come in coded as ⎋B and ⎋F
+ Do expect ⇧Fn← to leap into the far Northwest,
    because it comes in coded as ⎋[⇧H by macOS Terminal,
    or as ⎋[1;2H by macOS iTerm2

And so on and on and on

Please do tell us which surprises are worth mentioning here?


2 )

No Keyboard Chord Sequence you press will quit our launched Process.
To quit playing --egg=native, you'll have to close your Terminal Window Pane

Unless you think to add up front more ways to quit, such as calling for some of
    --egg=sigint, --egg=sigtstp, --egg=sigquit

## Links

+ [GitHub Repository](https://github.com/pelavarre/less-beeps/blob/main/easter-eggs.md)
+ [Questions/Feedback](https://twitter.com/intent/tweet?text=/@PELaVarre%20%23LessBeeps)

<!-- git clone git@github.com:pelavarre/less-beeps.git -->
