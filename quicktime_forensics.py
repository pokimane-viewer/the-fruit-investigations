#!/usr/bin/env python3
"""
Usage: quicktime_forensics.py reference.mov broken.mov [output.mov]
"""
import argparse, os, sys, glob, shutil, tempfile, subprocess

def extract_autosave(tmpdir):
    autosave_dir = os.path.expanduser(
        "~/Library/Containers/com.apple.QuickTimePlayerX/Data/Library/Autosave Information"
    )
    try:
        if os.path.isdir(autosave_dir):
            for root, dirs, _ in os.walk(autosave_dir):
                for d in dirs:
                    if d.endswith(".qtxcomposition"):
                        pkg = os.path.join(root, d)
                        dst = os.path.join(tmpdir, "Autosave.pkg")
                        shutil.copytree(pkg, dst)
                        for r, _, files in os.walk(dst):
                            for f in files:
                                if f.lower().endswith(".mov"):
                                    src = os.path.join(r, f)
                                    out = os.path.join(tmpdir, "recovered_autosave.mov")
                                    shutil.copy2(src, out)
                                    print(f"Autosave extract: {out}")
                                    return
    except Exception as e:
        print(f"Autosave extraction failed: {e}", file=sys.stderr)

def run_untrunc(ref, broken):
    try:
        subprocess.run(["untrunc", "-sm", "-s", ref, broken], check=True)
    except subprocess.CalledProcessError as e:
        print(f"untrunc failed: {e}", file=sys.stderr)
        sys.exit(1)

def find_fixed(broken):
    base, ext = os.path.splitext(broken)
    pattern = f"{base}_fixed*.{ext.lstrip('.')}"
    matches = glob.glob(pattern)
    if not matches:
        print("untrunc did not produce a fixed file. Check warnings above.", file=sys.stderr)
        sys.exit(1)
    return max(matches, key=os.path.getmtime)

def dump_atoms(out, tmpdir):
    try:
        infofile = os.path.join(tmpdir, "mp4_info.txt")
        with open(infofile, "w") as f:
            subprocess.run(["MP4Box", "-info", out], stdout=f, stderr=subprocess.DEVNULL, check=True)
        print(f"Atom dump: {infofile}")
    except Exception as e:
        print(f"Atom dump failed: {e}", file=sys.stderr)

def collect_logs(tmpdir):
    try:
        logsfile = os.path.join(tmpdir, "qtplayer_logs.txt")
        predicate = 'process == "QuickTime Player"'
        start = "2025-04-19 13:00:00"
        end = "2025-04-19 14:00:00"
        with open(logsfile, "w") as f:
            subprocess.run(
                ["log", "show", "--predicate", predicate, "--start", start, "--end", end],
                stdout=f, stderr=subprocess.DEVNULL, check=True
            )
        print(f"QT logs: {logsfile}")
    except Exception as e:
        print(f"Log collection failed: {e}", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("reference")
    parser.add_argument("broken")
    parser.add_argument("output", nargs="?", default=None)
    args = parser.parse_args()
    ref, broken = args.reference, args.broken
    out = args.output or f"{os.path.splitext(broken)[0]}_forensic_recovered{os.path.splitext(broken)[1]}"
    tmpdir = tempfile.mkdtemp(prefix="qt_forensics_")
    extract_autosave(tmpdir)
    run_untrunc(ref, broken)
    fixed = find_fixed(broken)
    try:
        shutil.move(fixed, out)
        print(f"Recovered file: {out}")
    except Exception as e:
        print(f"Moving fixed file failed: {e}", file=sys.stderr)
        sys.exit(1)
    dump_atoms(out, tmpdir)
    collect_logs(tmpdir)

if __name__ == "__main__":
    main()