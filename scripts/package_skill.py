"""Build dist/samepage.skill from skills/samepage/ reproducibly (ADR-0016).

Usage: python3 scripts/package_skill.py [OUT]

The zip has one root folder, samepage/, with fixed timestamps and sorted
entries, so the same source always gives the same bytes. tests/test_skill.py
fails when the committed dist/samepage.skill differs from a fresh build.
"""
import io
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(ROOT, "skills", "samepage")
DEFAULT_OUT = os.path.join(ROOT, "dist", "samepage.skill")
SKIP = {"__pycache__", ".DS_Store"}


def build_bytes():
    files = []
    for folder, dirs, names in os.walk(SOURCE):
        dirs[:] = sorted(d for d in dirs if d not in SKIP)
        for name in sorted(names):
            if name in SKIP or name.endswith(".pyc"):
                continue
            full = os.path.join(folder, name)
            files.append((os.path.join("samepage", os.path.relpath(full, SOURCE)).replace(os.sep, "/"), full))
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for arcname, full in sorted(files):
            info = zipfile.ZipInfo(arcname, date_time=(1980, 1, 1, 0, 0, 0))
            info.external_attr = 0o644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            with open(full, "rb") as handle:
                archive.writestr(info, handle.read())
    return buffer.getvalue()


def main(out=DEFAULT_OUT):
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "wb") as handle:
        handle.write(build_bytes())
    return out


if __name__ == "__main__":
    print("wrote %s" % main(*sys.argv[1:2]))
