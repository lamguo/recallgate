from __future__ import annotations

import json
import math
import re
import textwrap
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union

MEMORY_DIR = ".recallgate"
VALID_SCOPES = {"project", "conversation", "global", "repo", "task"}
VALID_TYPES = {"rule", "preference", "decision", "pitfall", "task", "fact", "correction", "note"}
VALID_STATUSES = {"active", "archived", "trash", "deleted"}
VALID_PRIORITIES = {"low", "medium", "high", "critical"}
VALID_ROLES = {"coder", "tester", "writer", "reviewer", "planner", "security", "all"}

ROLE_KEYWORDS = {
    "coder": {"code", "cli", "api", "function", "class", "compat", "behavior", "refactor", "bug"},
    "tester": {"test", "tests", "fixture", "ci", "coverage", "pytest", "unittest", "github actions"},
    "writer": {"readme", "docs", "documentation", "changelog", "release", "copy", "description"},
    "reviewer": {"review", "risk", "quality", "compat", "release", "audit", "check"},
    "planner": {"plan", "roadmap", "task", "scope", "priority", "milestone"},
    "security": {"secret", "key", "token", "password", "security", "safe", "danger"},
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def slugify(text: str, max_len: int = 42) -> str:
    """Create a readable, filesystem-safe slug.

    ASCII words and CJK characters are preserved so Chinese memories do not all
    collapse to ``memory``. The memory id still guarantees uniqueness.
    """
    parts = re.findall(r"[a-zA-Z0-9\u4e00-\u9fff]+", text.lower())
    slug = "-".join(parts).strip("-")
    return (slug or "memory")[:max_len].strip("-") or "memory"


def estimate_tokens(text: str) -> int:
    """Cheap local token estimate. Does not call any model or API."""
    if not text:
        return 0
    cjk = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
    non_cjk = len(text) - cjk
    return max(1, math.ceil(cjk * 1.5 + non_cjk / 4))


def shorten(text: str, max_chars: int = 96) -> str:
    clean = " ".join(text.strip().split())
    if len(clean) <= max_chars:
        return clean
    cut = clean[: max_chars - 1].rsplit(" ", 1)[0]
    return (cut or clean[: max_chars - 1]).rstrip(".,;:") + "."


def split_keywords(value: Optional[Union[str, Sequence[str]]]) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        raw = re.split(r"[,\s]+", value.strip())
    else:
        raw = list(value)
    return sorted({item.strip().lower() for item in raw if item and item.strip()})


STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "has", "have", "in", "is", "it", "its", "of", "on", "or", "that",
    "the", "this", "to", "was", "were", "will", "with", "your", "you",
}


def extract_keywords(text: str, limit: int = 8) -> List[str]:
    """Extract cheap local keywords without model calls.

    This intentionally avoids stopwords so automatically generated keywords are
    useful for ranking. Explicit user-provided keywords still use split_keywords
    without stopword filtering.
    """
    tokens = re.findall(r"[a-zA-Z0-9_\-]+|[\u4e00-\u9fff]{2,}", text.lower())
    seen = []
    for token in tokens:
        token = token.strip("_- ")
        if not token or token in STOPWORDS or len(token) < 2:
            continue
        if token not in seen:
            seen.append(token)
        if len(seen) >= limit:
            break
    return seen


@dataclass
class Paths:
    root: Path

    @property
    def memory(self) -> Path:
        return self.root / MEMORY_DIR

    @property
    def index(self) -> Path:
        return self.memory / "index.json"

    @property
    def config(self) -> Path:
        return self.memory / "config.toml"

    def status_dir(self, status: str, scope: str = "project") -> Path:
        if status == "active":
            if scope in {"repo", "project"}:
                return self.memory / "project"
            if scope == "conversation":
                return self.memory / "conversations" / "history"
            if scope == "global":
                return self.memory / "global"
            if scope == "task":
                return self.memory / "conversations" / "history"
            return self.memory / "project"
        if status == "archived":
            return self.memory / "archive"
        if status == "trash":
            return self.memory / "trash"
        if status == "deleted":
            raise ValueError("Deleted memories do not have a storage directory.")
        raise ValueError(f"Invalid memory status: {status}")


def find_root(start: Optional[Path] = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for path in [current, *current.parents]:
        if (path / MEMORY_DIR).exists():
            return path
    return current


def init_workspace(root: Optional[Path] = None) -> Path:
    root = (root or Path.cwd()).resolve()
    paths = Paths(root)
    dirs = [
        paths.memory,
        paths.memory / "project",
        paths.memory / "conversations" / "history",
        paths.memory / "roles",
        paths.memory / "corrections",
        paths.memory / "global",
        paths.memory / "archive",
        paths.memory / "trash",
        paths.memory / "reports",
    ]
    for directory in dirs:
        directory.mkdir(parents=True, exist_ok=True)

    if not paths.index.exists():
        save_index(paths, {"version": 1, "next_id": 1, "memories": []})
    if not paths.config.exists():
        paths.config.write_text(
            "# RecallGate config\n"
            "default_budget = 300\n"
            "default_roles = [\"coder\", \"tester\", \"writer\", \"reviewer\"]\n",
            encoding="utf-8",
        )
    for name in ["coder", "tester", "writer", "reviewer", "planner", "security"]:
        role_path = paths.memory / "roles" / f"{name}.md"
        if not role_path.exists():
            role_path.write_text(f"# {name.title()} Memory\n\n", encoding="utf-8")
    return paths.memory


def load_index(paths: Paths) -> Dict[str, Any]:
    if not paths.index.exists():
        init_workspace(paths.root)
    with paths.index.open("r", encoding="utf-8") as f:
        data = json.load(f)
    data.setdefault("version", 1)
    data.setdefault("next_id", 1)
    data.setdefault("memories", [])
    return data


def save_index(paths: Paths, data: Dict[str, Any]) -> None:
    paths.memory.mkdir(parents=True, exist_ok=True)
    tmp = paths.index.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(paths.index)


def read_config(paths: Paths) -> Dict[str, Any]:
    """Read the tiny local config without adding a TOML dependency.

    RecallGate only needs a few simple values in v0.1.x. Unknown or malformed
    lines are ignored so a hand-edited config never breaks core commands.
    """
    defaults: Dict[str, Any] = {
        "default_budget": 300,
        "default_roles": ["coder", "tester", "writer", "reviewer"],
    }
    if not paths.config.exists():
        return defaults
    config = dict(defaults)
    for raw in paths.config.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = [part.strip() for part in line.split("=", 1)]
        if key == "default_budget":
            try:
                config[key] = max(1, int(value))
            except ValueError:
                continue
        elif key == "default_roles":
            roles = re.findall(r'"([^"\n]+)"', value)
            if roles:
                config[key] = roles
    return config


def resolve_budget(paths: Paths, budget: Optional[int]) -> int:
    if budget is not None:
        return max(1, int(budget))
    return int(read_config(paths).get("default_budget", 300))


def memory_to_markdown(memory: Dict[str, Any]) -> str:
    # Store a human-readable snapshot. The physical file path is tracked only in
    # index.json so the Markdown front matter never contains stale paths after
    # archive/trash/restore moves.
    meta = {k: v for k, v in memory.items() if k not in {"content", "file"}}
    front = "---\n" + "\n".join(f"{k}: {json.dumps(v, ensure_ascii=False)}" for k, v in meta.items()) + "\n---\n\n"
    return front + memory.get("content", "").strip() + "\n"


def write_memory_file(paths: Paths, memory: Dict[str, Any]) -> str:
    status = memory.get("status", "active")
    scope = memory.get("scope", "project")
    directory = paths.status_dir(status, scope)
    directory.mkdir(parents=True, exist_ok=True)
    filename = f"{memory['id']}-{slugify(memory.get('short') or memory.get('content', 'memory'))}.md"
    path = directory / filename
    path.write_text(memory_to_markdown(memory), encoding="utf-8")
    return str(path.relative_to(paths.memory))


def remove_old_file(paths: Paths, relative_path: Optional[str]) -> None:
    """Remove a previously written memory file safely.

    The relative path is normally generated by write_memory_file, but this guard
    prevents path traversal or symlink escape if index.json is edited manually or
    corrupted.
    """
    if not relative_path:
        return
    base = paths.memory.resolve()
    candidate = (paths.memory / relative_path).resolve()
    if not candidate.is_relative_to(base):
        raise ValueError(f"Refusing to remove path outside memory workspace: {relative_path}")
    if candidate.exists() and candidate.is_file():
        candidate.unlink()


def normalize_scope(scope: str) -> str:
    scope = scope.lower().strip()
    if scope == "repo":
        return "project"
    if scope not in VALID_SCOPES:
        raise ValueError(f"Invalid scope: {scope}. Valid: {', '.join(sorted(VALID_SCOPES))}")
    return scope


def normalize_type(type_: str) -> str:
    type_ = type_.lower().strip()
    if type_ not in VALID_TYPES:
        raise ValueError(f"Invalid type: {type_}. Valid: {', '.join(sorted(VALID_TYPES))}")
    return type_


def normalize_priority(priority: str) -> str:
    priority = priority.lower().strip()
    if priority not in VALID_PRIORITIES:
        raise ValueError(f"Invalid priority: {priority}. Valid: {', '.join(sorted(VALID_PRIORITIES))}")
    return priority


def normalize_roles(roles: Optional[Union[str, Sequence[str]]]) -> List[str]:
    values = split_keywords(roles)
    if not values:
        return ["all"]
    bad = [r for r in values if r not in VALID_ROLES]
    if bad:
        raise ValueError(f"Invalid role(s): {', '.join(bad)}. Valid: {', '.join(sorted(VALID_ROLES))}")
    return values


def add_memory(
    content: str,
    *,
    root: Optional[Path] = None,
    scope: str = "project",
    type_: str = "note",
    roles: Optional[Union[str, Sequence[str]]] = None,
    priority: str = "medium",
    short: Optional[str] = None,
    keywords: Optional[Union[str, Sequence[str]]] = None,
    source: str = "user",
    confidence: float = 1.0,
    importance: int = 5,
) -> Dict[str, Any]:
    if not content or not content.strip():
        raise ValueError("Memory content cannot be empty.")
    root = find_root(root)
    init_workspace(root)
    paths = Paths(root)
    data = load_index(paths)
    mem_id = f"mem_{int(data['next_id']):04d}"
    data["next_id"] = int(data["next_id"]) + 1
    memory = {
        "id": mem_id,
        "scope": normalize_scope(scope),
        "type": normalize_type(type_),
        "status": "active",
        "audience": normalize_roles(roles),
        "priority": normalize_priority(priority),
        "importance": max(1, min(10, int(importance))),
        "confidence": max(0.0, min(1.0, float(confidence))),
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "last_used": None,
        "use_count": 0,
        "keywords": split_keywords(keywords) if keywords is not None else extract_keywords(content),
        "content": content.strip(),
        "short": (short.strip() if short else shorten(content)),
        "source": source,
        "file": None,
    }
    memory["file"] = write_memory_file(paths, memory)
    data["memories"].append(memory)
    save_index(paths, data)
    return memory


def get_memory(data: Dict[str, Any], mem_id: str) -> Dict[str, Any]:
    for memory in data.get("memories", []):
        if memory.get("id") == mem_id:
            return memory
    raise KeyError(f"Memory not found: {mem_id}")


def change_status(mem_id: str, status: str, *, root: Optional[Path] = None) -> Dict[str, Any]:
    status = status.lower().strip()
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status: {status}")
    root = find_root(root)
    paths = Paths(root)
    data = load_index(paths)
    memory = get_memory(data, mem_id)
    old_file = memory.get("file")
    memory["status"] = status
    memory["updated_at"] = now_iso()
    remove_old_file(paths, old_file)
    if status == "deleted":
        memory["file"] = None
    else:
        memory["file"] = write_memory_file(paths, memory)
    save_index(paths, data)
    return memory


def delete_memory(mem_id: str, *, root: Optional[Path] = None) -> Dict[str, Any]:
    """Permanently remove a memory from the index and delete its Markdown file."""
    root = find_root(root)
    paths = Paths(root)
    data = load_index(paths)
    memory = get_memory(data, mem_id)
    remove_old_file(paths, memory.get("file"))
    data["memories"] = [m for m in data.get("memories", []) if m.get("id") != mem_id]
    save_index(paths, data)
    return memory


def info_memory(mem_id: str, *, root: Optional[Path] = None) -> Dict[str, Any]:
    root = find_root(root)
    data = load_index(Paths(root))
    return dict(get_memory(data, mem_id))


def update_memory(
    mem_id: str,
    *,
    root: Optional[Path] = None,
    content: Optional[str] = None,
    short: Optional[str] = None,
    scope: Optional[str] = None,
    type_: Optional[str] = None,
    roles: Optional[Union[str, Sequence[str]]] = None,
    priority: Optional[str] = None,
    keywords: Optional[Union[str, Sequence[str]]] = None,
    importance: Optional[int] = None,
    confidence: Optional[float] = None,
    source: Optional[str] = None,
) -> Dict[str, Any]:
    root = find_root(root)
    paths = Paths(root)
    data = load_index(paths)
    memory = get_memory(data, mem_id)
    old_file = memory.get("file")
    changed = False

    if content is not None:
        if not content.strip():
            raise ValueError("Memory content cannot be empty.")
        memory["content"] = content.strip()
        changed = True
    if short is not None:
        if not short.strip():
            raise ValueError("Short memory cannot be empty.")
        memory["short"] = short.strip()
        changed = True
    elif content is not None:
        memory["short"] = shorten(content)
    if scope is not None:
        memory["scope"] = normalize_scope(scope)
        changed = True
    if type_ is not None:
        memory["type"] = normalize_type(type_)
        changed = True
    if roles is not None:
        memory["audience"] = normalize_roles(roles)
        changed = True
    if priority is not None:
        memory["priority"] = normalize_priority(priority)
        changed = True
    if keywords is not None:
        memory["keywords"] = split_keywords(keywords)
        changed = True
    elif content is not None:
        memory["keywords"] = extract_keywords(content)
    if importance is not None:
        memory["importance"] = max(1, min(10, int(importance)))
        changed = True
    if confidence is not None:
        memory["confidence"] = max(0.0, min(1.0, float(confidence)))
        changed = True
    if source is not None:
        memory["source"] = source
        changed = True

    if not changed and content is None:
        raise ValueError("No update fields provided.")
    memory["updated_at"] = now_iso()
    remove_old_file(paths, old_file)
    memory["file"] = write_memory_file(paths, memory)
    save_index(paths, data)
    return memory


def sort_memories(memories: Iterable[Dict[str, Any]], sort_by: str = "created_at", reverse: bool = False) -> List[Dict[str, Any]]:
    valid = {"id", "created_at", "updated_at", "last_used", "use_count", "priority", "importance", "status", "scope", "type"}
    if sort_by not in valid:
        raise ValueError(f"Invalid sort field: {sort_by}. Valid: {', '.join(sorted(valid))}")

    def key(memory: Dict[str, Any]) -> Any:
        if sort_by == "priority":
            return priority_value(memory.get("priority", "medium"))
        if sort_by in {"use_count", "importance"}:
            return int(memory.get(sort_by, 0) or 0)
        return str(memory.get(sort_by) or "")

    return sorted(memories, key=key, reverse=reverse)


def list_memories(
    *,
    root: Optional[Path] = None,
    status: Optional[str] = None,
    scope: Optional[str] = None,
    role: Optional[str] = None,
    sort_by: str = "created_at",
    reverse: bool = False,
) -> List[Dict[str, Any]]:
    root = find_root(root)
    data = load_index(Paths(root))
    memories = data.get("memories", [])
    if status:
        memories = [m for m in memories if m.get("status") == status]
    if scope:
        norm_scope = normalize_scope(scope)
        memories = [m for m in memories if m.get("scope") == norm_scope]
    if role:
        role = role.lower().strip()
        if role not in VALID_ROLES:
            raise ValueError(f"Invalid role: {role}. Valid: {', '.join(sorted(VALID_ROLES))}")
        # For list, --role all means no role filter. Memories with audience=[all]
        # are already visible in every specific role filter.
        if role != "all":
            memories = role_filtered(memories, role)
    return sort_memories(memories, sort_by=sort_by, reverse=reverse)


def priority_value(value: str) -> int:
    return {"critical": 5, "high": 4, "medium": 3, "low": 2}.get(value, 1)


def keyword_score(memory: Dict[str, Any], query: str) -> int:
    query_l = query.lower()
    score = 0
    for kw in memory.get("keywords", []):
        if kw and kw in query_l:
            score += 3
    for token in re.findall(r"[a-zA-Z0-9_\-]+", query_l):
        if token and token in memory.get("short", "").lower():
            score += 1
    return score


def role_score(memory: Dict[str, Any], role: Optional[str]) -> int:
    if not role:
        return 0
    audience = memory.get("audience", [])
    if role in audience:
        return 8
    if "all" in audience:
        return 3
    return -5


def role_matches(memory: Dict[str, Any], role: Optional[str]) -> bool:
    if not role:
        return True
    audience = memory.get("audience", [])
    return "all" in audience or role in audience


def role_filtered(memories: Iterable[Dict[str, Any]], role: Optional[str]) -> List[Dict[str, Any]]:
    return [memory for memory in memories if role_matches(memory, role)]


def task_role_guess(query: str) -> Optional[str]:
    q = query.lower()
    best: Tuple[Optional[str], int] = (None, 0)
    for role, keywords in ROLE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in q)
        if score > best[1]:
            best = (role, score)
    return best[0]


def rank_memories(memories: Iterable[Dict[str, Any]], query: str, role: Optional[str]) -> List[Dict[str, Any]]:
    scored = []
    for memory in memories:
        score = 0
        score += priority_value(memory.get("priority", "medium")) * 5
        score += int(memory.get("importance", 5)) * 2
        score += int(memory.get("use_count", 0))
        score += keyword_score(memory, query)
        score += role_score(memory, role)
        if memory.get("type") == "correction":
            score += 4
        if memory.get("type") == "rule":
            score += 3
        scored.append((score, memory))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [memory for _, memory in scored]


def trim_text_to_budget(text: str, budget: int) -> str:
    """Trim text to an approximate local token budget.

    This is intentionally conservative: a 10-token budget should not keep a
    40-character line just because of a fallback minimum.
    """
    if budget <= 0 or estimate_tokens(text) <= budget:
        return text
    kept_chars = max(1, budget * 4)
    trimmed = text[:kept_chars].rstrip()
    while trimmed and estimate_tokens(trimmed) > budget:
        kept_chars = max(1, int(kept_chars * 0.85))
        trimmed = text[:kept_chars].rstrip()
    return trimmed or text[:1]


def trim_lines_to_budget(lines: List[str], budget: int) -> List[str]:
    if budget <= 0:
        return lines
    kept: List[str] = []
    for line in lines:
        candidate = "\n".join([*kept, line])
        if estimate_tokens(candidate) <= budget:
            kept.append(line)
        elif not kept:
            kept.append(trim_text_to_budget(line, budget))
            break
        else:
            break
    return kept


def active_memory_tokens(memories: Sequence[Dict[str, Any]]) -> int:
    return sum(estimate_tokens(m.get("content", "") + "\n" + m.get("short", "")) for m in memories if m.get("status") == "active")


def generate_brief(
    query: str,
    *,
    root: Optional[Path] = None,
    role: Optional[str] = None,
    budget: Optional[int] = None,
    include_estimate: bool = True,
    update_usage: bool = True,
) -> str:
    root = find_root(root)
    paths = Paths(root)
    budget = resolve_budget(paths, budget)
    data = load_index(paths)
    explicit_all_role = bool(role and role.lower().strip() == "all")
    if explicit_all_role:
        role = None
    else:
        role = role or task_role_guess(query)
    active = [m for m in data.get("memories", []) if m.get("status") == "active"]
    candidates = role_filtered(active, role)
    ranked = rank_memories(candidates, query, role)

    authority = [
        "Memory Authority:",
        "- Current user instruction has highest priority.",
        "- Local active memory overrides model memory.",
        "- Ignore archived or trashed memories.",
        "",
    ]
    header = ["RecallGate Brief", ""]
    if role:
        header = [f"RecallGate {role.title()} Brief", ""]

    corrections = [m for m in ranked if m.get("type") == "correction"][:2]
    rules = [m for m in ranked if m.get("type") in {"rule", "preference"}][:6]
    pitfalls = [m for m in ranked if m.get("type") == "pitfall"][:3]
    decisions = [m for m in ranked if m.get("type") in {"decision", "fact"}][:3]
    notes = [m for m in ranked if m.get("type") == "note"][:3]
    conversations = [m for m in ranked if m.get("scope") in {"conversation", "task"}][:3]

    selected: List[Dict[str, Any]] = []
    seen_selected: set[str] = set()
    for group in [rules, pitfalls, decisions, notes, conversations]:
        for memory in group:
            mem_id = memory.get("id")
            if mem_id not in seen_selected:
                selected.append(memory)
                seen_selected.add(mem_id)

    fixed_lines = header + authority
    fixed_lines = trim_lines_to_budget(fixed_lines, budget)
    used_ids: set[str] = set()
    content_lines = list(fixed_lines)

    def can_fit(lines: Sequence[str]) -> bool:
        if budget <= 0:
            return True
        return estimate_tokens("\n".join([*content_lines, *lines])) <= budget

    def try_add(line: str, mem_id: Optional[str] = None) -> bool:
        if not can_fit([line]):
            return False
        content_lines.append(line)
        if mem_id:
            used_ids.add(mem_id)
        return True

    def try_add_section(title: str, items: Sequence[tuple[str, Optional[str]]]) -> bool:
        """Add a titled section only if at least one item fits.

        This prevents empty headings such as ``Relevant Memory:`` when the
        configured token budget is already exhausted by the authority block.
        """
        section_lines = [title]
        section_ids: List[str] = []
        for line, mem_id in items:
            candidate = [*section_lines, line]
            if budget <= 0 or estimate_tokens("\n".join([*content_lines, *candidate])) <= budget:
                section_lines.append(line)
                if mem_id:
                    section_ids.append(mem_id)
        if len(section_lines) == 1:
            return False
        content_lines.extend(section_lines)
        used_ids.update(section_ids)
        try_add("")
        return True

    if corrections:
        try_add_section(
            "Correction:",
            [(f"- {memory.get('short')}", memory.get("id")) for memory in corrections],
        )

    if selected:
        try_add_section(
            "Relevant Memory:",
            [(f"- {memory.get('short')}", memory.get("id")) for memory in selected[:12]],
        )
    else:
        try_add_section("Relevant Memory:", [("- No role-relevant active memory found.", None)])

    try_add_section("Current Task:", [(f"- {query.strip()}", None)])

    brief = "\n".join(content_lines).strip() + "\n"

    injected = estimate_tokens(brief)
    full = active_memory_tokens(active)
    skipped = max(0, full - injected)
    saving = 0.0 if full == 0 else max(0.0, (1 - injected / full) * 100)

    if include_estimate:
        brief += "\nToken Estimate:\n"
        brief += f"- Full active memory: ~{full:,} tokens\n"
        brief += f"- Injected brief: ~{injected:,} tokens\n"
        brief += f"- Skipped locally: ~{skipped:,} tokens\n"
        brief += f"- Estimated saving: ~{saving:.1f}%\n"

    if update_usage and used_ids:
        changed = False
        for memory in data.get("memories", []):
            if memory.get("id") in used_ids:
                memory["last_used"] = now_iso()
                memory["use_count"] = int(memory.get("use_count", 0)) + 1
                changed = True
        if changed:
            save_index(paths, data)
    return brief


def generate_correction(issue: str, *, root: Optional[Path] = None, budget: Optional[int] = None) -> str:
    root = find_root(root)
    paths = Paths(root)
    budget = resolve_budget(paths, budget)
    memories = list_memories(root=root, status="active")
    project_rules = [m for m in rank_memories(memories, issue, None) if m.get("scope") == "project"][:4]
    lines = [
        "RecallGate Correction",
        "",
        "- Use current user instruction first.",
        "- Use local active memory over model memory.",
        "- Ignore archived or trashed memories.",
    ]
    for memory in project_rules:
        lines.append(f"- {memory.get('short')}")
    lines.append(f"- Correction target: {issue.strip()}")
    lines = trim_lines_to_budget(lines, budget)
    text = "\n".join(lines).strip() + "\n"
    text += f"\nEstimated tokens: ~{estimate_tokens(text)}\n"
    return text


def estimate_data(*, root: Optional[Path] = None, query: Optional[str] = None, role: Optional[str] = None, budget: Optional[int] = None) -> Dict[str, Any]:
    root = find_root(root)
    paths = Paths(root)
    resolved_budget = resolve_budget(paths, budget)
    memories = list_memories(root=root)
    active = [m for m in memories if m.get("status") == "active"]
    archived = [m for m in memories if m.get("status") == "archived"]
    trash = [m for m in memories if m.get("status") == "trash"]
    full = active_memory_tokens(active)
    brief_text = generate_brief(
        query or "general task",
        root=root,
        role=role,
        budget=resolved_budget,
        include_estimate=False,
        update_usage=False,
    )
    injected = estimate_tokens(brief_text)
    skipped = max(0, full - injected)
    saving = 0.0 if full == 0 else max(0.0, (1 - injected / full) * 100)
    return {
        "active_memories": len(active),
        "archived_memories": len(archived),
        "trash_memories": len(trash),
        "full_active_memory_tokens": full,
        "injected_brief_tokens": injected,
        "skipped_tokens": skipped,
        "estimated_saving_percent": round(saving, 1),
        "budget": resolved_budget,
        "model_api_calls": 0,
    }


def estimate_report(*, root: Optional[Path] = None, query: Optional[str] = None, role: Optional[str] = None, budget: Optional[int] = None) -> str:
    data = estimate_data(root=root, query=query, role=role, budget=budget)
    return textwrap.dedent(
        f"""
        RecallGate Token Estimate

        Active memories: {data['active_memories']} (~{data['full_active_memory_tokens']:,} tokens)
        Archived memories: {data['archived_memories']} (not injected)
        Trash memories: {data['trash_memories']} (not injected)
        Estimated injected brief: ~{data['injected_brief_tokens']:,} tokens
        Estimated skipped locally: ~{data['skipped_tokens']:,} tokens
        Estimated saving: ~{data['estimated_saving_percent']:.1f}%
        Model/API calls used for this estimate: {data['model_api_calls']}
        """
    ).strip() + "\n"


def search_memories(
    query: str,
    *,
    root: Optional[Path] = None,
    status: Optional[str] = None,
    scope: Optional[str] = None,
    role: Optional[str] = None,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    if not query or not query.strip():
        raise ValueError("Search query cannot be empty.")
    memories = list_memories(root=root, status=status, scope=scope, role=role)
    q = query.lower().strip()
    q_tokens = set(re.findall(r"[a-zA-Z0-9_\-]+|[\u4e00-\u9fff]{2,}", q))
    results: List[Tuple[int, Dict[str, Any]]] = []
    for memory in memories:
        haystacks = [
            memory.get("id", ""),
            memory.get("short", ""),
            memory.get("content", ""),
            " ".join(memory.get("keywords", [])),
            memory.get("scope", ""),
            memory.get("type", ""),
            memory.get("priority", ""),
        ]
        hay = " ".join(haystacks).lower()
        score = 0
        if q in hay:
            score += 10
        for token in q_tokens:
            if token in hay:
                score += 3
        if score:
            score += priority_value(memory.get("priority", "medium"))
            results.append((score, memory))
    results.sort(key=lambda item: item[0], reverse=True)
    return [memory for _, memory in results[: max(1, int(limit))]]


def review_suggestions(*, root: Optional[Path] = None) -> List[Dict[str, Any]]:
    root = find_root(root)
    memories = list_memories(root=root)
    active = [m for m in memories if m.get("status") == "active"]
    suggestions: List[Dict[str, Any]] = []

    for memory in active:
        if int(memory.get("use_count", 0)) == 0 and int(memory.get("importance", 5)) <= 3:
            suggestions.append({
                "action": "archive",
                "id": memory["id"],
                "reason": "low importance and never used",
                "short": memory.get("short"),
                "apply_supported": True,
            })
        if memory.get("scope") in {"conversation", "task"} and memory.get("type") in {"rule", "pitfall"} and int(memory.get("use_count", 0)) >= 2:
            suggestions.append({
                "action": "promote",
                "id": memory["id"],
                "reason": "conversation memory has been reused",
                "short": memory.get("short"),
                "to_scope": "project",
                "apply_supported": True,
            })

    by_short: Dict[str, List[Dict[str, Any]]] = {}
    for memory in active:
        key = memory.get("short", "").lower().strip(" .")
        if key:
            by_short.setdefault(key, []).append(memory)
    for group in by_short.values():
        if len(group) > 1:
            suggestions.append({
                "action": "dedupe",
                "ids": [m["id"] for m in group],
                "reason": "same short memory appears multiple times",
                "short": group[0].get("short"),
                "apply_supported": False,
            })
    return suggestions


def apply_review_suggestions(*, root: Optional[Path] = None) -> List[Dict[str, Any]]:
    root = find_root(root)
    applied: List[Dict[str, Any]] = []
    for suggestion in review_suggestions(root=root):
        if not suggestion.get("apply_supported"):
            continue
        action = suggestion.get("action")
        mem_id = suggestion.get("id")
        if action == "archive" and mem_id:
            change_status(str(mem_id), "archived", root=root)
            applied.append(suggestion)
        elif action == "promote" and mem_id:
            promote_memory(str(mem_id), root=root, to_scope=str(suggestion.get("to_scope") or "project"))
            applied.append(suggestion)
    return applied


def review_memories(*, root: Optional[Path] = None, apply: bool = False) -> str:
    suggestions = review_suggestions(root=root)
    title = "RecallGate Review"
    if not suggestions:
        return f"{title}\n\nNo obvious cleanup suggestions. Active memory looks clean.\n"

    lines = [title, ""]
    if apply:
        applied = apply_review_suggestions(root=root)
        lines.append("Applied actions:")
        if applied:
            for item in applied:
                lines.append(f"- {item['action'].title()} {item['id']}: {item['reason']}.\n  {item.get('short')}")
        else:
            lines.append("- No auto-applicable suggestions.")
        skipped = [s for s in suggestions if not s.get("apply_supported")]
        if skipped:
            lines.extend(["", "Skipped manual-only suggestions:"])
            for item in skipped:
                ids = ", ".join(item.get("ids", []))
                lines.append(f"- {item['action'].title()} {ids}: {item['reason']}.")
        return "\n".join(lines) + "\n"

    lines.append("Suggested actions:")
    for item in suggestions:
        if item.get("id"):
            lines.append(f"- {item['action'].title()} {item['id']}: {item['reason']}.\n  {item.get('short')}")
        else:
            ids = ", ".join(item.get("ids", []))
            lines.append(f"- {item['action'].title()} {ids}: {item['reason']}.")
    lines.append("")
    lines.append("No changes were made. Use --apply to run supported archive/promote suggestions.")
    return "\n".join(lines) + "\n"


def promote_memory(mem_id: str, *, root: Optional[Path] = None, to_scope: str = "project") -> Dict[str, Any]:
    root = find_root(root)
    paths = Paths(root)
    data = load_index(paths)
    memory = get_memory(data, mem_id)
    old_file = memory.get("file")
    memory["scope"] = normalize_scope(to_scope)
    memory["updated_at"] = now_iso()
    remove_old_file(paths, old_file)
    memory["file"] = write_memory_file(paths, memory)
    save_index(paths, data)
    return memory
