
from pathlib import Path

# Directories that are usually irrelevant to source-code analysis.
IGNORED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".next",
    "dist",
    "build",
}

# Keep the first version focused on readable source and config files.
ALLOWED_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx",
    ".java", ".go", ".rs", ".cpp", ".c", ".h",
    ".json", ".yaml", ".yml", ".toml",
    ".md", ".html", ".css", ".sql",
}


class CodeSearch:
    def __init__(self, repo_path: str):
        # Resolve the root once so all tools use the same boundary.
        self.root = Path(repo_path).resolve()

        if not self.root.is_dir():
            raise ValueError("Repository path must be a directory")

    def _safe_path(self, relative_path: str) -> Path:
        """Resolve a path and reject paths outside the repository."""
        target = (self.root / relative_path).resolve()

        if not target.is_relative_to(self.root):
            raise ValueError("Access outside the repository is forbidden")

        if not target.is_file():
            raise FileNotFoundError(relative_path)

        return target

    def _source_files(self):
        """Yield supported files, excluding generated directories."""
        for path in self.root.rglob("*"):
            if not path.is_file():
                continue

            # Avoid files inside dependency and generated directories.
            if any(part in IGNORED_DIRS for part in path.relative_to(self.root).parts):
                continue

            # Skip unsupported files and symbolic links.
            if path.is_symlink():
                continue

            if path.suffix.lower() in ALLOWED_EXTENSIONS:
                yield path

    def search_files(self, query: str, limit: int = 20) -> list[dict]:
        """Find filenames containing the query."""
        if not query.strip():
            raise ValueError("Query cannot be empty")

        if not 1 <= limit <= 100:
            raise ValueError("Limit must be between 1 and 100")

        matches = []

        for path in self._source_files():
            if query.casefold() in path.name.casefold():
                matches.append({
                    "path": path.relative_to(self.root).as_posix()
                })

                if len(matches) >= limit:
                    break

        return matches

    def search_code(self, query: str, limit: int = 20) -> list[dict]:
        """Find literal, case-insensitive matches with line numbers."""
        if not query.strip():
            raise ValueError("Query cannot be empty")

        if not 1 <= limit <= 100:
            raise ValueError("Limit must be between 1 and 100")

        matches = []

        for path in self._source_files():
            try:
                lines = path.read_text(
                    encoding="utf-8",
                    errors="replace"
                ).splitlines()
            except OSError:
                continue

            for line_number, line in enumerate(lines, start=1):
                if query.casefold() in line.casefold():
                    matches.append({
                        "path": path.relative_to(self.root).as_posix(),
                        "line": line_number,
                        "text": line.strip()[:300],
                    })

                    if len(matches) >= limit:
                        return matches

        return matches

    def read_file(
        self,
        relative_path: str,
        start_line: int = 1,
        end_line: int = 100,
    ) -> dict:
        """Read a bounded range of lines from a repository file."""
        if start_line < 1 or end_line < start_line:
            raise ValueError("Invalid line range")

        if end_line - start_line + 1 > 200:
            raise ValueError("Read at most 200 lines per request")

        target = self._safe_path(relative_path)

        if target.suffix.lower() not in ALLOWED_EXTENSIONS:
            raise ValueError("File type is not supported")

        lines = target.read_text(
            encoding="utf-8",
            errors="replace"
        ).splitlines()

        selected = lines[start_line - 1:end_line]

        return {
            "path": target.relative_to(self.root).as_posix(),
            "start_line": start_line,
            "end_line": min(end_line, len(lines)),
            "content": "\n".join(
                f"{line_number}: {line}"
                for line_number, line in enumerate(
                    selected,
                    start=start_line
                )
            ),
        }
