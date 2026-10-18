"""Split/Second: show real Xbox button names in prompts instead of DirectInput names.

The PC game fills prompt templates ("STEER *ACTION_TURN_L* AND TAP *ACTION_BREAK* TO DRIFT") with the bound input's
display name from the English text table inside data/Resident.ark: "Button 1", "Axis Z Pos", "Pov Button 1"...
This renames those entries in place to Xbox names (A, B, LT, RT, LS LEFT, D-PAD...). The table addresses strings by
offset and ends each with a NUL, so a shorter name padded with NULs leaves everything else where it was.

  splitsecond-button-names.py            show the current names
  splitsecond-button-names.py --apply    rename (records the original bytes in splitsecond-button-names.json)
  splitsecond-button-names.py --restore  put the original names back
Re-run --apply after Steam re-downloads Resident.ark (update / verify files). The game must be closed.
The game folder is found through Steam's library list; pass --game "<folder>" to point at it yourself.

Copyright (C) 2026 happyc0der. Licensed under the GNU General Public License v3.0 (see LICENSE).
"""
import argparse, json, os, re, subprocess, sys

APPID_DIR = "SplitSecond"  # steamapps/common/<this> for Steam app 297860
STATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "splitsecond-button-names.json")

# DirectInput name (as the game shows it) -> Xbox name. The pad is read in the wired-360 layout (see PadFix):
# buttons 1-10 = A B X Y LB RB View Menu LS-click RS-click, Z axis = LT (+) / RT (-), POV 1 = D-pad.
RENAMES = {
    "Button 1": "A",
    "Button 2": "B",
    "Button 3": "X",
    "Button 4": "Y",
    "Button 5": "LB",
    "Button 6": "RB",
    "Button 7": "VIEW",
    "Button 8": "MENU",
    "Button 9": "LS CLICK",
    "Button 10": "RS CLICK",
    "Pov Button 1": "D-PAD",
    "Axis X Neg": "LS LEFT",
    "Axis X Pos": "LS RIGHT",
    "Axis Y Neg": "LS UP",
    "Axis Y Pos": "LS DOWN",
    "Axis Z Pos": "LT",
    "Axis Z Neg": "RT",
    "Right Axis X Neg": "RS LEFT",
    "Right Axis X Pos": "RS RIGHT",
    "Right Axis Y Neg": "RS UP",
    "Right Axis Y Pos": "RS DOWN",
    # keyboard: everything else already reads naturally (LCtrl, LAlt, Enter, PageUp, CapsLock, Numpad +)
    "RMenu": "RAlt",
}


def find_game():
    """the Split/Second folder in any Steam library"""
    steam = r"C:\Program Files (x86)\Steam"
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as k:
            steam = winreg.QueryValueEx(k, "SteamPath")[0]
    except OSError:
        pass
    libs = [steam]
    vdf = os.path.join(steam, "steamapps", "libraryfolders.vdf")
    if os.path.exists(vdf):
        libs += [p.replace("\\\\", "\\") for p in re.findall(r'"path"\s+"([^"]+)"', open(vdf, encoding="utf-8").read())]
    for lib in libs:
        game = os.path.join(lib, "steamapps", "common", APPID_DIR)
        if os.path.exists(os.path.join(game, "data", "Resident.ark")):
            return game
    return None


def padded(new, orig):
    return new.encode("ascii") + b"\0" * (len(orig) - len(new))


def game_running():
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq SplitSecond.exe"], capture_output=True, text=True).stdout
    return "SplitSecond.exe" in out


def scan(path):
    """offsets of every NUL-delimited original name in the archive"""
    rx = re.compile(b"\0(" + b"|".join(re.escape(k.encode()) for k in sorted(RENAMES, key=len, reverse=True)) + b")(?=\0)")
    hits = {}
    with open(path, "rb") as f:
        pos, tail = 0, b""
        while chunk := f.read(64 << 20):
            buf = tail + chunk
            for m in rx.finditer(buf):
                hits.setdefault(m.group(1).decode(), set()).add(pos - len(tail) + m.start(1))
            tail, pos = buf[-40:], pos + len(chunk)
    return {k: sorted(v) for k, v in hits.items()}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--restore", action="store_true")
    ap.add_argument("--game", help="Split/Second folder (default: found through Steam)")
    a = ap.parse_args()
    game = a.game or find_game()
    if not game:
        sys.exit("Split/Second not found in any Steam library; pass --game \"<game folder>\"")
    ark = os.path.join(game, "data", "Resident.ark")
    if not os.path.exists(ark):
        sys.exit(f"{ark} not found")
    state = json.load(open(STATE)) if os.path.exists(STATE) else None
    if state and (state["size"] != os.path.getsize(ark)):
        print(f"note: Resident.ark changed size since the last --apply ({state['size']} -> {os.path.getsize(ark)}); old record ignored")
        state = None

    if a.restore:
        if not state:
            sys.exit("nothing to restore: no record of an applied rename for this Resident.ark")
        if game_running():
            sys.exit("close Split/Second first")
        with open(ark, "r+b") as f:
            for e in state["entries"]:
                f.seek(e["offset"])
                cur = f.read(len(e["orig"]))
                if cur == e["orig"].encode():
                    continue
                if cur != padded(e["new"], e["orig"]):
                    print(f"  skip {e['orig']!r} @ {e['offset']:#x}: unexpected bytes {cur!r}")
                    continue
                f.seek(e["offset"])
                f.write(e["orig"].encode())
                print(f"  {e['new']!r} -> {e['orig']!r}")
        os.replace(STATE, STATE + ".restored")
        print("restored the original names")
        return

    if not a.apply:
        if state:
            with open(ark, "rb") as f:
                for e in state["entries"]:
                    f.seek(e["offset"])
                    cur = f.read(len(e["orig"])).rstrip(b"\0").decode("latin-1")
                    print(f"  {e['orig']:<18} now shows as {cur!r}")
            print("Xbox names applied (--restore to undo)")
        else:
            found = scan(ark)
            if found:
                print(f"original names present: {len(found)} of {len(RENAMES)} (--apply to rename)")
            else:
                print("none of the original names found: already renamed by another copy of this script, "
                      "or a build that stores its text compressed (the plain Steam release)")
        return

    if game_running():
        sys.exit("close Split/Second first")
    if state:
        print("already applied; nothing to do (--restore first to re-apply)")
        return
    found = scan(ark)
    missing = [k for k in RENAMES if k not in found]
    dupes = {k: v for k, v in found.items() if len(v) != 1}
    if missing or dupes:
        sys.exit(f"Resident.ark does not have the expected text table (missing {len(missing)} of {len(RENAMES)} names, "
                 f"duplicated {list(dupes)}). The Steam release stores its text compressed; this works on the DLC-port data.")
    entries = []
    with open(ark, "r+b") as f:
        for orig, new in RENAMES.items():
            off = found[orig][0]
            assert len(new) <= len(orig), orig
            f.seek(off)
            f.write(padded(new, orig))
            entries.append({"offset": off, "orig": orig, "new": new})
        f.flush()
        for e in entries:  # read back
            f.seek(e["offset"])
            assert f.read(len(e["orig"])) == padded(e["new"], e["orig"]), e
    json.dump({"ark": ark, "size": os.path.getsize(ark), "entries": entries}, open(STATE, "w"), indent=1)
    for e in entries:
        print(f"  {e['orig']:<18} -> {e['new']}")
    print(f"renamed {len(entries)} names; record in {STATE}")


if __name__ == "__main__":
    main()
