# hanma.py — It builds your blog. That's mostly it.
# Copyright (C) 2026  Chris Hammer
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see
# <https://www.gnu.org/licenses/>.
"""Common utilities and constants for Hanma."""
import os
from pathlib import Path
from typing import Optional


# ── Constants ─────────────────────────────────────────────────────────────────
# Anchor for themes/ — same directory as hanma.py since all files are siblings
_THEMES_DIR = Path(__file__).parent.parent / "themes"


def get_root_rel(output_root: Optional[Path], out_path: Path) -> str:
  """Calculate the relative path from the output file's directory back to root.

  Returns a string like "../../" or "" (if at root).
  """
  if not output_root:
    return ""
  
  root_rel = os.path.relpath(output_root, out_path.parent).replace(os.sep, "/")
  if root_rel == ".":
    return ""
  
  return root_rel.rstrip("/") + "/"
