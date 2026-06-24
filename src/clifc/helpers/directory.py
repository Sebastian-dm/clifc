import os
import sys
from pathlib import Path
from typing import List


class DirectoryHelper:
    def collect_ifc_file_paths(self, paths: List[str]) -> List[str]:
        ifc_files: List[str] = []
        for p in paths:
            path = Path(p)
            if path.is_file() and path.suffix.lower() == ".ifc":
                ifc_files.append(str(path))
            elif path.is_dir():
                for file in path.rglob("*.ifc"):
                    ifc_files.append(str(file))
            else:
                print(f"[yellow]Warning: path '{p}' is not an .ifc file or directory; skipping.[/yellow]")
        return sorted(ifc_files)