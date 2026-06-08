# Changelog

## v0.1.0 - 2026-06-08

### Added during automation pass

- Added `update` / `edit` command so memories can be modified without delete-and-recreate workflows.
- Added `info` command for full memory details from the CLI.
- Added `--json` output for automation-oriented commands.
- Added explicit `--root` support across core subcommands for CI and scripts.
- Added `list --sort` and `--reverse`, and list output now shows `use_count` and `last_used`.
- Added `review --apply` for supported archive/promote suggestions.
- Added structured `estimate --json` token metrics.

Initial alpha release.

### Fixed during validation

- `estimate` is now read-only and no longer increments memory `use_count`.
- `delete --yes` now truly removes the memory from `index.json` and disk instead of leaving a recoverable `deleted` record.
- Role-based briefs no longer leak memories assigned only to other roles.
- `note` memories can now appear in relevant briefs instead of being silently ignored.
- Markdown front matter no longer stores stale `file` paths after archive/trash/restore moves.
- Empty memory content is rejected.
- Added regression tests for read-only estimation, role isolation, permanent delete, note inclusion, and stale path prevention.
- Updated project URLs and CI matrix for Python 3.13.
- Removed dead code in `generate_brief` so selected memory is built in one path.
- Hardened old-file removal against path traversal and symlink escape from `.recallgate/`.
- `status_dir("deleted")` now raises instead of silently mapping to trash.
- `recall-gate list --role all` now means no role filter, matching CLI user expectations.
- Automatic keyword extraction now skips common English stopwords.
- Slugs now preserve CJK characters so Chinese memories produce more readable file names.
- `brief` and `estimate` now read `default_budget` from `.recallgate/config.toml` when `--budget` is omitted.
- Tiny-budget trimming is now more predictable and keeps the injected brief within the local token estimate instead of using a fixed character fallback.
- Budget-starved briefs no longer emit empty section headings such as `Relevant Memory:` when no memory item can fit.
- `correct` now reads `default_budget` from `.recallgate/config.toml` when `--budget` is omitted, matching `brief` and `estimate`.

### Added

- Local `.recallgate/` memory workspace.
- Project and conversation memory separation.
- Active, archive, trash, and restore lifecycle.
- Role-based memory briefs for coder, tester, writer, reviewer, planner, and security roles.
- Correction brief to override stale model memory with local project truth.
- Local token estimator with injected, skipped, and saving-rate metrics.
- Budget-aware brief output.
- `search` command for keyword/full-text style local memory search.
- Review suggestions for stale, low-value, and conflicting memory.
- Zero runtime dependencies and no model/API calls by default.
