# thinkx-system/AGENTS.md
#
# Codex entry point mapped from the Claude Code project configuration.

This repository's canonical working instructions are `CLAUDE.md` and
`CLAUDE_GENERAL.md`. Codex must read and follow both before working. When a
directory or project has its own `CLAUDE.md`, read it before investigating or
editing that area. For infrastructure work, `infra/CLAUDE.md` is mandatory.

Apply the document precedence, one-session/one-plan discipline, restoration
procedure, coding-guide routing, branch rules, and owner-instruction recording
rules from `CLAUDE.md` without renaming or reinterpretation. `AGENTS.md` is only
the Codex adapter; it does not duplicate or replace those canonical rules.

Map `.claude/settings.json` safety boundaries to Codex as follows:

- Never read or modify secrets: `.env*`, `*.pem`, credentials, `~/.ssh/**`,
  `~/.aws/**`, or `~/.config/**`.
- Never read or modify `*.tfstate` or `*.tfvars`.
- Never modify `.claude/**`, `CLAUDE.md`, `*_PLAN.md`, `ARCHIVE.md`,
  `docs/coding_guides/**`, or generated `dist/**` files.
- Never force-push, hard-reset, clean, delete branches, recursively remove
  files, run `sudo`, or invoke destructive AWS IAM/EC2 commands.
- Terraform apply/destroy, SSH, documentation/runbook edits, package installs,
  and other actions marked `ask` in `.claude/settings.json` require explicit
  owner approval unless the owner has already directly requested that exact
  action in the current turn.
- Infrastructure state-changing operations must use the repository wrappers
  and approval gates described by `infra/CLAUDE.md`; do not issue bare
  Terraform mutation commands.

Claude's `PostToolUse` cost hook is not automatically run by Codex. When an edit
could affect infrastructure cost, run or account for
`infra/scripts/cost-hook.sh` explicitly, subject to the same project rules.

