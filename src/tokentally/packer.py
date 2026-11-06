"""
Codebase and repository packing engine for LLM context prompts.
Scans files, respects ignore patterns, counts tokens per file, and generates clean prompts.
"""

from dataclasses import dataclass, asdict
import fnmatch
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from .counter import count_tokens
from .calculator import estimate_cost


DEFAULT_IGNORE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    "dist",
    "build",
    ".egg-info",
    ".idea",
    ".vscode",
    "target",
    "bin",
    "obj",
}

DEFAULT_IGNORE_EXTENSIONS = {
    # Images & Media
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico", ".bmp",
    ".mp3", ".wav", ".ogg", ".mp4", ".mov", ".avi", ".mkv",
    # Binaries & Archives
    ".exe", ".dll", ".so", ".dylib", ".bin", ".zip", ".tar", ".gz", ".7z", ".rar",
    # Fonts
    ".woff", ".woff2", ".ttf", ".eot", ".otf",
    # Compiled
    ".pyc", ".pyo", ".pyd", ".class", ".o", ".a",
    # Large data / lockfiles
    ".pdf", ".iso", ".sqlite", ".db"
}


@dataclass
class FileStat:
    relative_path: str
    tokens: int
    bytes_count: int
    pct_of_total: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PackResult:
    root_dir: str
    total_files: int
    total_tokens: int
    total_bytes: int
    model: str
    estimated_cost_usd: float
    file_stats: List[FileStat]
    packed_content: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "root_dir": self.root_dir,
            "total_files": self.total_files,
            "total_tokens": self.total_tokens,
            "total_bytes": self.total_bytes,
            "model": self.model,
            "estimated_cost_usd": self.estimated_cost_usd,
            "file_stats": [s.to_dict() for s in self.file_stats],
        }

    def write_to(self, target_path: str) -> None:
        """Save the packed LLM prompt to the target file."""
        out = Path(target_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            f.write(self.packed_content)


class RepositoryPacker:
    """Traverse directories and pack clean context prompts for LLMs."""

    def __init__(
        self,
        custom_ignore_dirs: Optional[Set[str]] = None,
        custom_ignore_exts: Optional[Set[str]] = None,
    ):
        self.ignore_dirs = set(DEFAULT_IGNORE_DIRS)
        if custom_ignore_dirs:
            self.ignore_dirs.update(custom_ignore_dirs)

        self.ignore_exts = set(DEFAULT_IGNORE_EXTENSIONS)
        if custom_ignore_exts:
            self.ignore_exts.update(custom_ignore_exts)

    def _read_ignore_files(self, root: Path) -> List[str]:
        patterns: List[str] = []
        for ignore_name in [".gitignore", ".tokentallyignore", ".ignore"]:
            p = root / ignore_name
            if p.is_file():
                try:
                    with open(p, "r", encoding="utf-8", errors="ignore") as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith("#"):
                                patterns.append(line)
                except OSError:
                    pass
        return patterns

    def _should_ignore(self, path: Path, rel_str: str, gitignore_patterns: List[str]) -> bool:
        # Check parent folder parts
        for part in path.parts:
            if part in self.ignore_dirs:
                return True

        # Check file extension
        if path.suffix.lower() in self.ignore_exts:
            return True

        # Check gitignore patterns
        rel_posix = rel_str.replace("\\", "/")
        for pattern in gitignore_patterns:
            pat_clean = pattern.rstrip("/")
            if fnmatch.fnmatch(rel_posix, pat_clean) or fnmatch.fnmatch(path.name, pat_clean):
                return True
            if pattern.endswith("/") and (f"{rel_posix}/".startswith(pattern) or path.is_dir()):
                return True

        return False

    def pack(
        self,
        directory: str,
        output_file: Optional[str] = None,
        model: str = "gpt-4o",
        max_tokens: Optional[int] = None,
        format_type: str = "xml",
        extra_ignore_patterns: Optional[List[str]] = None,
    ) -> PackResult:
        """
        Scan and assemble context from directory files.
        'format_type' can be 'xml' or 'markdown'.
        """
        root_path = Path(directory).resolve()
        if not root_path.is_dir():
            raise NotADirectoryError(f"Directory not found: {directory}")

        gitignore_patterns = self._read_ignore_files(root_path)
        if extra_ignore_patterns:
            gitignore_patterns.extend(extra_ignore_patterns)

        collected_files: List[Path] = []
        for dirpath, dirnames, filenames in os.walk(root_path):
            current_dir = Path(dirpath)
            rel_dir = current_dir.relative_to(root_path)

            # Filter out ignored subdirectories in-place
            dirnames[:] = [
                d for d in dirnames
                if not self._should_ignore(current_dir / d, str(rel_dir / d), gitignore_patterns)
            ]

            for fname in filenames:
                fpath = current_dir / fname
                rel_fpath = fpath.relative_to(root_path)
                if not self._should_ignore(fpath, str(rel_fpath), gitignore_patterns):
                    collected_files.append(fpath)

        collected_files.sort()

        # Read and count tokens per file
        file_entries: List[Dict[str, Any]] = []
        total_tokens = 0
        total_bytes = 0

        for fpath in collected_files:
            rel_str = str(fpath.relative_to(root_path)).replace("\\", "/")
            try:
                with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
            except OSError:
                continue

            f_bytes = len(content.encode("utf-8"))
            f_tokens = count_tokens(content, model=model)

            # Check if adding this file exceeds max_tokens limit
            if max_tokens and (total_tokens + f_tokens > max_tokens):
                # Budget reached
                break

            total_tokens += f_tokens
            total_bytes += f_bytes
            file_entries.append({
                "rel_path": rel_str,
                "content": content,
                "tokens": f_tokens,
                "bytes": f_bytes,
            })

        # Calculate percentages
        file_stats: List[FileStat] = []
        for entry in file_entries:
            pct = (entry["tokens"] / total_tokens * 100.0) if total_tokens > 0 else 0.0
            file_stats.append(FileStat(
                relative_path=entry["rel_path"],
                tokens=entry["tokens"],
                bytes_count=entry["bytes"],
                pct_of_total=round(pct, 2),
            ))

        # Build output prompt document
        lines = []
        if format_type == "xml":
            lines.append("<repository_context>")
            lines.append(f"  <summary total_files=\"{len(file_entries)}\" total_tokens=\"{total_tokens}\">")
            for stat in file_stats:
                lines.append(f"    <file path=\"{stat.relative_path}\" tokens=\"{stat.tokens}\" />")
            lines.append("  </summary>\n")

            for entry in file_entries:
                lines.append(f"  <file path=\"{entry['rel_path']}\">")
                lines.append(entry["content"])
                lines.append("  </file>\n")
            lines.append("</repository_context>")
        else:
            lines.append(f"# Repository Context: {root_path.name}")
            lines.append(f"- **Files Included**: {len(file_entries)}")
            lines.append(f"- **Total Estimated Tokens**: {total_tokens:,}")
            lines.append("\n## File Manifest")
            for stat in file_stats:
                lines.append(f"- `{stat.relative_path}` ({stat.tokens:,} tokens, {stat.pct_of_total}%)")
            lines.append("\n---\n")

            for entry in file_entries:
                ext = Path(entry["rel_path"]).suffix.lstrip(".") or "text"
                lines.append(f"## File: {entry['rel_path']}\n```{ext}")
                lines.append(entry["content"])
                lines.append("```\n")

        packed_text = "\n".join(lines)
        cost_eval = estimate_cost(total_tokens, model=model)

        result = PackResult(
            root_dir=str(root_path),
            total_files=len(file_entries),
            total_tokens=total_tokens,
            total_bytes=total_bytes,
            model=model,
            estimated_cost_usd=cost_eval.total_cost_usd,
            file_stats=file_stats,
            packed_content=packed_text,
        )

        if output_file:
            result.write_to(output_file)

        return result


_DEFAULT_PACKER = RepositoryPacker()


def pack_repository(
    directory: str,
    output_file: Optional[str] = None,
    model: str = "gpt-4o",
    max_tokens: Optional[int] = None,
    format_type: str = "xml",
    extra_ignore_patterns: Optional[List[str]] = None,
) -> PackResult:
    """Convenience helper to pack a repository folder."""
    return _DEFAULT_PACKER.pack(
        directory=directory,
        output_file=output_file,
        model=model,
        max_tokens=max_tokens,
        format_type=format_type,
        extra_ignore_patterns=extra_ignore_patterns,
    )
