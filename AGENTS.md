# thinkx-system/AGENTS.md
#
# Codex instructions mapped from the repository's Claude Code configuration.
#

This repository uses the existing `CLAUDE.md` hierarchy as the canonical project guidance. Codex must read and follow the root `CLAUDE.md`, `CLAUDE_GENERAL.md`, and every closer `<project>/CLAUDE.md` before investigating or editing that project. When coding, also read all applicable files under `docs/coding_guides/` as required by `CLAUDE.md`.

## Codex mapping

- Treat `.claude/settings.json` as a policy source, but never edit `.claude/**` or any `CLAUDE.md` unless the owner explicitly changes that policy.
- Never read, print, edit, or create `.env`, `.env.*`, SSH/AWS credentials, `*.pem`, `*.tfvars`, or `*.tfstate`. The owner handles secrets.
- Never edit `*_PLAN.md`, `ARCHIVE.md`, `docs/coding_guides/**`, generated `dist/**`, or vendored/submodule areas forbidden by `CLAUDE.md`.
- Ask before editing `docs/**`, `infra/docs/**`, or `infra/runbooks/**`. Findings files explicitly assigned by the owner are exempt.
- Ask before SSH, curl, Terraform apply/destroy, Homebrew installs, git restore, submodule deinit, or tag deletion. Obey `.codex/rules/default.rules` for command-level enforcement.
- Keep all project files, virtual environments, dependencies, caches, and generated data inside the relevant project directory. Python environments are `<project>/venv`, with exact-pinned `requirements.txt`.
- Do not modify the main-track plan or switch another worktree's branch while working on the parallel `k00bot2` track.
- Use one logical track per session and one commit per independently verifiable item. Restore state from the relevant roadmap, recent Git history, checksums, and findings before continuing interrupted work.
- For paste-ready zsh commands, include the starting `cd`, use explicit paths, and keep comments outside the command block.
- Do not invoke paid APIs or large-volume processing without the cost/usage confirmation required by `CLAUDE_GENERAL.md`.

The repository-local `.codex/config.toml`, hooks, and rules apply only when this repository is marked trusted in Codex.
