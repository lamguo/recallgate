# RecallGate

> **Give every AI agent only the memory it needs — and nothing else.**

RecallGate is a **token-efficient, controllable memory gate for AI coding agents**.

It helps Claude Code, Codex CLI, Cursor, Gemini CLI, Copilot-style agents, and multi-agent coding workflows stop wasting context on irrelevant history.

Instead of dumping your whole chat history or project notes into a model, RecallGate reads memory locally, filters it locally, and injects only the shortest role-specific brief.

```text
Local reads are free. Model context is expensive.
RecallGate reads broadly, filters locally, and injects minimally.
```

## Why developers will want this

AI agents forget the wrong things, remember the wrong things, and burn tokens rereading the same context.

RecallGate gives you a local memory firewall:

- Keep project rules, decisions, pitfalls, and task memory in Git-friendly files.
- Put stale memory into archive or trash so agents cannot read it.
- Restore memory when it becomes useful again.
- Correct stale model memory with a tiny local truth brief.
- Give coder, tester, writer, reviewer, planner, and security agents different memory.
- Estimate token cost before you paste memory into an agent.
- Search memory by keyword when your local memory grows past a few dozen entries.
- Use it offline with **zero model calls by default**.

This is not another giant memory server. It is a cheap, practical gate between your repo and your AI agents.

## The problem

Most AI coding workflows have three hidden costs:

1. **Wrong memory** — the model remembers another project, old rules, or stale user preferences.
2. **Bloated context** — agents repeatedly read huge notes, logs, or summaries.
3. **No memory lifecycle** — memory is either used forever or deleted forever.

RecallGate fixes this with:

```text
active   -> readable by default
archive  -> hidden but recoverable
trash    -> blocked from agents, still recoverable
deleted  -> permanently removed from index and disk
```

## Install

From source:

```bash
git clone https://github.com/lamguo/recallgate.git
cd recallgate
python -m pip install -e .
```

Run:

```bash
recall-gate --help
```

You can also use:

```bash
recallgate --help
```

## Quick start

```bash
recall-gate init
```

Add project memory:

```bash
recall-gate add "Keep zero core dependencies." --scope project --type rule --role coder --priority high --importance 10
recall-gate add "Tests must use temp fixtures, not fragile example files." --scope project --type pitfall --role tester --priority high
recall-gate add "README and CHANGELOG must stay in sync with public CLI behavior." --scope project --type rule --role writer
```

Generate a memory brief for a coding agent:

```bash
recall-gate brief "fix GitHub Actions test failure" --role tester --budget 300
```

Edit a memory without deleting and recreating it:

```bash
recall-gate update mem_0001 --priority critical --short "Keep zero core dependencies."
# alias also works
recall-gate edit mem_0001 --keywords python,cli,release
```

Inspect full memory details:

```bash
recall-gate info mem_0001
```

Example output:

```text
RecallGate Tester Brief

Memory Authority:
- Current user instruction has highest priority.
- Local active memory overrides model memory.
- Ignore archived or trashed memories.

Relevant Memory:
- Keep zero core dependencies.
- Tests must use temp fixtures, not fragile example files.

Current Task:
- fix GitHub Actions test failure

Token Estimate:
- Full active memory: ~1,240 tokens
- Injected brief: ~95 tokens
- Skipped locally: ~1,145 tokens
- Estimated saving: ~92.3%
```

## Correct stale model memory

If the model starts acting like it remembers the wrong project:

```bash
recall-gate correct "model thinks this is a WordPress project"
```

Output:

```text
RecallGate Correction

- Use current user instruction first.
- Use local active memory over model memory.
- Ignore archived or trashed memories.
- This is a Python CLI project.
- Keep zero core dependencies.
- Correction target: model thinks this is a WordPress project
```

Paste that into your coding agent to pull it back onto the right track.

## Memory lifecycle

List active memory with usage signals:

```bash
recall-gate list --status active --sort use_count --reverse
```

Show one full memory record:

```bash
recall-gate info mem_0001
```

Edit a memory:

```bash
recall-gate update mem_0001 --content "Updated project rule." --priority high --keywords project,rule
```

Archive memory:

```bash
recall-gate archive mem_0001
```

Trash memory:

```bash
recall-gate trash mem_0001
```

Restore memory:

```bash
recall-gate restore mem_0001
```

Permanent delete removes the memory from the index and disk, so use `trash` first unless you are sure:

```bash
recall-gate delete mem_0001 --yes
```

## Project memory vs conversation memory

RecallGate separates long-term project truth from temporary task context.

Project memory:

```bash
recall-gate add "This project is a Python CLI tool." --scope project --type fact
```

Conversation memory:

```bash
recall-gate add "Current task only focuses on CI reliability." --scope conversation --type task
```

Promote reusable conversation memory into project memory:

```bash
recall-gate promote mem_0007 --to project
```

## Role-based memory

Every memory can target one or more roles:

```bash
--role coder
--role tester
--role writer
--role reviewer
--role planner
--role security
--role all
```

For `add`, `--role all` means the memory is shared across roles.
For `list`, `--role all` means no role filter, so every memory is shown.
For `brief`, `--role all` disables role guessing and allows all active memories to compete by relevance.

Generate different briefs:

```bash
recall-gate brief "fix tests" --role tester
recall-gate brief "update README" --role writer
recall-gate brief "review release readiness" --role reviewer
```

The goal is simple:

```text
Shared outline, private depth.
```

Every agent gets the big picture. Only the specialist agent gets the deep memory it needs.

## Token estimation

Estimate before injecting memory:

```bash
recall-gate estimate --task "fix tests" --role tester
```

By default, `brief`, `correct`, and `estimate` read `.recallgate/config.toml`:

```toml
# Approximate max tokens for generated briefs before token reports.
default_budget = 300
```

Override it per command when needed:

```bash
recall-gate brief "fix tests" --role tester --budget 180
```

RecallGate does token estimation locally. It does **not** call a model.

First version uses a cheap local approximation:

```text
English: about 1 token per 4 characters
Chinese: about 1-2 tokens per character
```

This is not provider-perfect, but it is fast, free, offline, and good enough for budget control.

## Search memory

For larger projects, search memory without opening `index.json` manually:

```bash
recall-gate search "fixtures"
recall-gate search "README" --role writer
recall-gate search "token" --status active --limit 5
```

Search checks memory content, short text, keywords, IDs, scope, type, and priority.

## JSON output and automation

Most commands support `--json` for scripts, CI, wrappers, or future MCP/plugin integrations:

```bash
recall-gate list --json
recall-gate info mem_0001 --json
recall-gate estimate --task "fix tests" --json
recall-gate review --json
```

`estimate --json` returns structured token fields such as `full_active_memory_tokens`, `injected_brief_tokens`, `skipped_tokens`, and `estimated_saving_percent`.

Most commands also support `--root` so automation does not depend on the current working directory:

```bash
recall-gate add "Keep zero core dependencies." --root /path/to/repo
recall-gate brief "fix tests" --root /path/to/repo --role tester
```

## Review memory quality

```bash
recall-gate review
```

RecallGate suggests low-value, duplicate, or reusable memory candidates.

By default, it only suggests actions:

```bash
recall-gate review
```

Apply supported safe actions automatically:

```bash
recall-gate review --apply
```

`--apply` currently performs supported `archive` and `promote` suggestions. Dedupe suggestions are reported but left manual.

## Local keyword behavior

When you do not pass `--keywords`, RecallGate extracts cheap local keywords from the memory text.
Common English stopwords are ignored, so a sentence like `This is a Python CLI project` becomes keywords such as `python`, `cli`, and `project`.

Pure Chinese memory also gets readable file names because CJK characters are preserved in slugs.

```text
System suggests.
User decides.
```

## Local workspace

RecallGate creates:

```text
.recallgate/
├── project/
├── conversations/
│   └── history/
├── roles/
├── corrections/
├── global/
├── archive/
├── trash/
├── reports/
├── index.json
└── config.toml
```

Memory is stored as Markdown plus a JSON index. It is easy to inspect, edit, commit, diff, archive, and restore.

## About injection

`brief` prints plain text by design in v0.1.0. You copy the output into Claude Code, Codex CLI, Cursor, Gemini CLI, Copilot Chat, or any other coding agent.

Automatic injection is intentionally not included in the first version because the core tool should stay local, predictable, and provider-agnostic. Future integrations can add MCP, editor plugins, or agent hooks on top of the same brief engine.

## What RecallGate is not

RecallGate is not:

- a hosted memory service
- a vector database
- a full AI agent framework
- a replacement for Claude Code, Codex, Cursor, or Copilot
- a tool that blindly remembers everything

RecallGate is:

- a local memory gate
- a memory firewall
- a token-saving brief generator
- a role-based memory router
- a stale model memory correction layer

## Design goal

RecallGate is built for extreme cost performance.

```text
Default model calls: 0
Default API keys: 0
Default runtime dependencies: 0
Default storage: local Markdown + JSON
Default test discovery: python -m unittest discover
```

## Status

`v0.1.0` is an alpha MVP.

Implemented:

- `init`
- `add`
- `update` / `edit`
- `info`
- `list`
- `archive`
- `trash`
- `restore`
- `delete --yes`
- `brief`
- `correct`
- `estimate`
- `search`
- `review`
- `review --apply`
- `promote`
- `--json` output for automation
- `--root` for explicit workspace targeting

Planned:

- conflict detection
- optional tokenizer support
- optional AI compression
- MCP server
- Claude Code / Codex / Cursor integration examples
- VS Code extension

## License

MIT
