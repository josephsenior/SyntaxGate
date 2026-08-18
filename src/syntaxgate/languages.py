"""Extension and language-name normalization."""

from __future__ import annotations

from pathlib import Path

EXTENSIONS: dict[str, str] = {
    ".py": "python", ".pyi": "python", ".js": "javascript",
    ".mjs": "javascript", ".cjs": "javascript", ".jsx": "javascript",
    ".ts": "typescript", ".tsx": "tsx", ".go": "go", ".rs": "rust",
    ".java": "java", ".c": "c", ".h": "c", ".cpp": "cpp",
    ".cc": "cpp", ".cxx": "cpp", ".hpp": "cpp", ".cs": "c_sharp",
    ".kt": "kotlin", ".kts": "kotlin", ".rb": "ruby", ".php": "php",
    ".lua": "lua", ".html": "html", ".htm": "html", ".css": "css",
    ".scss": "scss", ".vue": "vue", ".svelte": "svelte", ".json": "json",
    ".json5": "json", ".yaml": "yaml", ".yml": "yaml", ".toml": "toml",
    ".xml": "xml", ".sh": "bash", ".bash": "bash", ".zsh": "bash",
    ".fish": "fish", ".ps1": "powershell", ".sql": "sql",
    ".graphql": "graphql", ".gql": "graphql", ".proto": "proto",
    ".tf": "hcl", ".dockerfile": "dockerfile", ".cmake": "cmake",
    ".swift": "swift", ".dart": "dart", ".ex": "elixir", ".exs": "elixir",
}

ALIASES = {
    "py": "python",
    "js": "javascript",
    "ts": "typescript",
    "cs": "c_sharp",
    "c#": "c_sharp",
    "sh": "bash",
    "yml": "yaml",
}


def language_for_path(path: str | Path, explicit: str | None = None) -> str | None:
    if explicit:
        return ALIASES.get(explicit.lower().lstrip("."), explicit.lower())
    name = Path(path).name.lower()
    if name == "dockerfile":
        return "dockerfile"
    return EXTENSIONS.get(Path(name).suffix)
