from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from . import __version__
from .core import (
    add_memory,
    apply_review_suggestions,
    change_status,
    delete_memory,
    estimate_data,
    estimate_report,
    generate_brief,
    generate_correction,
    info_memory,
    init_workspace,
    list_memories,
    promote_memory,
    review_memories,
    review_suggestions,
    search_memories,
    update_memory,
)


def print_json(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def root_path(value: Optional[str]) -> Optional[Path]:
    return Path(value) if value else None


def add_common(parser: argparse.ArgumentParser, *, root: bool = True, json_output: bool = True) -> None:
    if root:
        parser.add_argument("--root", default=None, help="Project root. Default: nearest parent containing .recallgate, or current directory.")
    if json_output:
        parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output.")


def memory_summary(memory: Dict[str, Any]) -> str:
    roles = ",".join(memory.get("audience", []))
    last_used = memory.get("last_used") or "never"
    return (
        f"{memory['id']} [{memory['status']}] {memory['scope']}/{memory['type']} "
        f"priority={memory.get('priority')} used={memory.get('use_count', 0)} last={last_used} "
        f"({roles}) - {memory.get('short')}"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="recall-gate",
        description="Token-efficient controllable memory gate for AI coding agents.",
    )
    parser.add_argument("--version", action="version", version=f"recallgate {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Create a local .recallgate memory workspace.")
    p_init.add_argument("--root", default=".", help="Project root. Default: current directory.")
    p_init.add_argument("--json", action="store_true", help="Print machine-readable JSON output.")

    p_add = sub.add_parser("add", help="Add a memory.")
    add_common(p_add)
    p_add.add_argument("content", help="Memory content.")
    p_add.add_argument("--scope", default="project", help="project, conversation, global, task.")
    p_add.add_argument("--type", default="note", choices=["rule", "preference", "decision", "pitfall", "task", "fact", "correction", "note"])
    p_add.add_argument("--role", default="all", help="Comma-separated roles: coder,tester,writer,reviewer,planner,security,all.")
    p_add.add_argument("--priority", default="medium", choices=["low", "medium", "high", "critical"], help="low, medium, high, critical.")
    p_add.add_argument("--importance", default=5, type=int, help="1-10.")
    p_add.add_argument("--short", default=None, help="Short model-facing version.")
    p_add.add_argument("--keywords", default=None, help="Comma-separated keywords.")

    p_update = sub.add_parser("update", aliases=["edit"], help="Edit an existing memory.")
    add_common(p_update)
    p_update.add_argument("memory_id")
    p_update.add_argument("--content", default=None, help="Replace full memory content.")
    p_update.add_argument("--short", default=None, help="Replace short model-facing memory.")
    p_update.add_argument("--scope", default=None, help="project, conversation, global, task.")
    p_update.add_argument("--type", dest="type_", default=None, choices=["rule", "preference", "decision", "pitfall", "task", "fact", "correction", "note"])
    p_update.add_argument("--role", default=None, help="Comma-separated roles.")
    p_update.add_argument("--priority", default=None, choices=["low", "medium", "high", "critical"])
    p_update.add_argument("--importance", default=None, type=int, help="1-10.")
    p_update.add_argument("--confidence", default=None, type=float, help="0.0-1.0.")
    p_update.add_argument("--keywords", default=None, help="Comma-separated keywords. Pass empty string to clear.")
    p_update.add_argument("--source", default=None, help="Memory source label.")

    p_info = sub.add_parser("info", help="Show full memory details.")
    add_common(p_info)
    p_info.add_argument("memory_id")

    p_list = sub.add_parser("list", help="List memories.")
    add_common(p_list)
    p_list.add_argument("--status", default=None, help="active, archived, trash, deleted.")
    p_list.add_argument("--scope", default=None, help="project, conversation, global, task.")
    p_list.add_argument("--role", default=None, help="Filter by role. Use 'all' or omit this option to show every memory.")
    p_list.add_argument("--sort", default="created_at", choices=["id", "created_at", "updated_at", "last_used", "use_count", "priority", "importance", "status", "scope", "type"], help="Sort field.")
    p_list.add_argument("--reverse", action="store_true", help="Reverse sort order.")

    for command, help_text in [
        ("archive", "Move memory to archive so it is hidden but recoverable."),
        ("trash", "Move memory to trash so agents cannot read it, but it can be restored."),
        ("restore", "Restore archived or trashed memory back to active."),
    ]:
        p = sub.add_parser(command, help=help_text)
        add_common(p)
        p.add_argument("memory_id")

    p_delete = sub.add_parser("delete", help="Permanently remove a memory from the index and disk.")
    add_common(p_delete)
    p_delete.add_argument("memory_id")
    p_delete.add_argument("--yes", action="store_true", help="Confirm permanent deletion.")

    p_brief = sub.add_parser("brief", help="Generate a short role-specific memory brief.")
    add_common(p_brief)
    p_brief.add_argument("task", help="Current task or question.")
    p_brief.add_argument("--role", default=None, help="coder, tester, writer, reviewer, planner, security.")
    p_brief.add_argument("--budget", type=int, default=None, help="Approx max token budget for the brief before token report. Defaults to .recallgate/config.toml default_budget.")
    p_brief.add_argument("--no-estimate", action="store_true", help="Hide token estimate.")

    p_correct = sub.add_parser("correct", help="Generate a tiny correction brief for stale model memory.")
    add_common(p_correct)
    p_correct.add_argument("issue", help="What the model is getting wrong.")
    p_correct.add_argument("--budget", type=int, default=None, help="Approx max token budget. Defaults to .recallgate/config.toml default_budget.")

    p_est = sub.add_parser("estimate", help="Estimate local memory and injected brief token cost.")
    add_common(p_est)
    p_est.add_argument("--task", default="general task")
    p_est.add_argument("--role", default=None)
    p_est.add_argument("--budget", type=int, default=None, help="Defaults to .recallgate/config.toml default_budget.")

    p_search = sub.add_parser("search", help="Search memory content, short text, keywords, and metadata.")
    add_common(p_search)
    p_search.add_argument("query", help="Search query.")
    p_search.add_argument("--status", default=None, help="active, archived, trash, deleted.")
    p_search.add_argument("--scope", default=None, help="project, conversation, global, task.")
    p_search.add_argument("--role", default=None, help="Filter by role. Use 'all' or omit this option to search every memory.")
    p_search.add_argument("--limit", type=int, default=20, help="Maximum results to print.")

    p_review = sub.add_parser("review", help="Suggest memories to archive, trash, dedupe, or promote.")
    add_common(p_review)
    p_review.add_argument("--apply", action="store_true", help="Apply supported archive/promote suggestions automatically.")

    p_promote = sub.add_parser("promote", help="Promote a memory to project scope.")
    add_common(p_promote)
    p_promote.add_argument("memory_id")
    p_promote.add_argument("--to", default="project", help="Target scope. Default: project.")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = root_path(getattr(args, "root", None))
    json_mode = bool(getattr(args, "json", False))
    try:
        if args.command == "init":
            path = init_workspace(Path(args.root))
            if json_mode:
                print_json({"ok": True, "workspace": str(path)})
            else:
                print(f"RecallGate workspace ready: {path}")
            return 0

        if args.command == "add":
            memory = add_memory(
                args.content,
                root=root,
                scope=args.scope,
                type_=args.type,
                roles=args.role,
                priority=args.priority,
                short=args.short,
                keywords=args.keywords,
                importance=args.importance,
            )
            if json_mode:
                print_json(memory)
            else:
                print(f"Added {memory['id']}: {memory['short']}")
            return 0

        if args.command in {"update", "edit"}:
            memory = update_memory(
                args.memory_id,
                root=root,
                content=args.content,
                short=args.short,
                scope=args.scope,
                type_=args.type_,
                roles=args.role,
                priority=args.priority,
                importance=args.importance,
                confidence=args.confidence,
                keywords=args.keywords,
                source=args.source,
            )
            if json_mode:
                print_json(memory)
            else:
                print(f"Updated {memory['id']}: {memory['short']}")
            return 0

        if args.command == "info":
            memory = info_memory(args.memory_id, root=root)
            if json_mode:
                print_json(memory)
            else:
                print(memory_summary(memory))
                print(f"keywords: {', '.join(memory.get('keywords', [])) or '-'}")
                print(f"importance: {memory.get('importance')}  confidence: {memory.get('confidence')}  source: {memory.get('source')}")
                print(f"created_at: {memory.get('created_at')}")
                print(f"updated_at: {memory.get('updated_at')}")
                print(f"file: {memory.get('file')}")
                print("\ncontent:")
                print(memory.get("content", ""))
            return 0

        if args.command == "list":
            memories = list_memories(status=args.status, scope=args.scope, role=args.role, sort_by=args.sort, reverse=args.reverse, root=root)
            if json_mode:
                print_json(memories)
            elif not memories:
                print("No memories found.")
            else:
                for memory in memories:
                    print(memory_summary(memory))
            return 0

        if args.command in {"archive", "trash", "restore", "delete"}:
            if args.command == "delete" and not args.yes:
                print("Refusing to delete without --yes. Consider 'trash' first.", file=sys.stderr)
                return 2
            if args.command == "delete":
                memory = delete_memory(args.memory_id, root=root)
                if json_mode:
                    print_json({"ok": True, "action": "delete", "memory": memory})
                else:
                    print(f"Deleted {memory['id']} permanently.")
                return 0
            status = {"archive": "archived", "trash": "trash", "restore": "active"}[args.command]
            memory = change_status(args.memory_id, status, root=root)
            if json_mode:
                print_json({"ok": True, "action": args.command, "memory": memory})
            else:
                print(f"Moved {memory['id']} to {status}.")
            return 0

        if args.command == "brief":
            text = generate_brief(args.task, root=root, role=args.role, budget=args.budget, include_estimate=not args.no_estimate)
            if json_mode:
                print_json({"task": args.task, "role": args.role, "brief": text})
            else:
                print(text, end="")
            return 0

        if args.command == "correct":
            text = generate_correction(args.issue, root=root, budget=args.budget)
            if json_mode:
                print_json({"issue": args.issue, "correction": text})
            else:
                print(text, end="")
            return 0

        if args.command == "estimate":
            text = estimate_report(root=root, query=args.task, role=args.role, budget=args.budget)
            if json_mode:
                print_json(estimate_data(root=root, query=args.task, role=args.role, budget=args.budget))
            else:
                print(text, end="")
            return 0

        if args.command == "search":
            memories = search_memories(
                args.query,
                root=root,
                status=args.status,
                scope=args.scope,
                role=args.role,
                limit=args.limit,
            )
            if json_mode:
                print_json(memories)
            elif not memories:
                print("No matching memories found.")
            else:
                for memory in memories:
                    print(memory_summary(memory))
            return 0

        if args.command == "review":
            if json_mode:
                if args.apply:
                    print_json({"applied": apply_review_suggestions(root=root), "suggestions_after_apply": review_suggestions(root=root)})
                else:
                    print_json(review_suggestions(root=root))
            else:
                print(review_memories(root=root, apply=args.apply), end="")
            return 0

        if args.command == "promote":
            memory = promote_memory(args.memory_id, root=root, to_scope=args.to)
            if json_mode:
                print_json(memory)
            else:
                print(f"Promoted {memory['id']} to {memory['scope']}.")
            return 0

        parser.print_help()
        return 1
    except Exception as exc:  # intentionally broad for CLI ergonomics
        if json_mode:
            print_json({"ok": False, "error": str(exc)})
        else:
            print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
