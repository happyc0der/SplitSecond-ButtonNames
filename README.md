# Split/Second ButtonNames: Xbox button names in the game's prompts

Play Split/Second (PC, 2010) with a controller and its hints read like a DirectInput debug screen:

> STEER **Axis X Neg** AND TAP **Axis Z Pos** TO DRIFT AND EARN POWER
> PRESS **Button 1** TO TRIGGER LEVEL 1 POWER PLAYS

With this mod they read the way they did on the Xbox:

> STEER **LS LEFT** AND TAP **LT** TO DRIFT AND EARN POWER
> PRESS **A** TO TRIGGER LEVEL 1 POWER PLAYS

It renames the controller entries in the game's English text table. Keyboard prompts already use normal key names
("LCtrl", "Enter", "PageUp") and stay as they are, apart from the one odd name, "RMenu", which becomes "RAlt".

## What gets renamed

| The game showed | Now shows | Controller input |
|---|---|---|
| Button 1 / 2 / 3 / 4 | A / B / X / Y | face buttons |
| Button 5 / 6 | LB / RB | bumpers |
| Button 7 / 8 | VIEW / MENU | Back / Start on a 360 pad |
| Button 9 / 10 | LS CLICK / RS CLICK | stick clicks |
| Axis Z Pos / Axis Z Neg | LT / RT | triggers (one shared axis) |
| Axis X Neg / Pos, Axis Y Neg / Pos | LS LEFT / RIGHT, LS UP / DOWN | left stick |
| Right Axis X Neg / Pos, Right Axis Y Neg / Pos | RS LEFT / RIGHT, RS UP / DOWN | right stick |
| Pov Button 1 | D-PAD | D-pad |
| RMenu (keyboard) | RAlt | Right Alt |

The names follow the wired Xbox 360 DirectInput layout, which is what the game expects from a controller. That is
what you get from a wired 360 pad, or from any Xbox controller with
[SplitSecond-PadFix](https://github.com/happyc0der/SplitSecond-PadFix) (needed for Bluetooth controllers). The names
are in capitals because every hint in the game is.

## Requirements

- Python 3.8 or newer, on Windows.
- **The game data from the community DLC port** (the build that adds the console DLC tracks and cars). Its
  `data\Resident.ark` keeps the text table uncompressed. The plain Steam release stores it compressed, so there the
  script finds none of the names and leaves the file alone; Steam support would need the archive format decoded.

## Use

Close the game first, then from a terminal:

```
python splitsecond-button-names.py            # show the current state
python splitsecond-button-names.py --apply    # rename
python splitsecond-button-names.py --restore  # put the original names back
```

The game folder is found through Steam's library list; add `--game "D:\path\to\SplitSecond"` to point at it
yourself. Run `--apply` again after Steam re-downloads `Resident.ark` (an update or "Verify integrity of game
files").

## How it works

The game builds its hints from templates in its text table, such as
`STEER *ACTION_TURN_L* AND TAP *ACTION_BREAK* TO DRIFT AND EARN POWER`. Each `*ACTION_…*` token is replaced by the
display name of the input bound to that action, taken from the same table. For a controller those names are
"Button 1", "Axis Z Pos" and so on.

The table addresses each string by its offset and ends it with a NUL byte. So the script:

1. scans `Resident.ark` for each original name as a complete NUL-terminated string, and refuses unless every name is
   found exactly once;
2. writes the new name over it, padded with NULs to the original length. Nothing is inserted or moved, the file size
   doesn't change, and no other string is touched;
3. records the offsets and original names in `splitsecond-button-names.json` next to the script, which `--restore`
   uses to write the originals back byte for byte (and only where it finds its own replacement).

It never edits while `SplitSecond.exe` is running.

## Limits

- These are text names, not button icons. Icons inside the hint text would mean rebuilding the game's Scaleform UI.
- English only. The renames live in the English table.
- New names can't be longer than the originals, which is why the sticks are "LS LEFT" rather than
  "LEFT STICK LEFT".

## License

GNU General Public License v3.0, see [LICENSE](LICENSE). Not affiliated with Disney Interactive or Black Rock Studio.
Split/Second and Xbox are trademarks of their respective owners. No game files or data are included.
