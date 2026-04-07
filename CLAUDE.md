# Repo Instructions

This repository uses the Engineering OS harness.

<!-- engineering-os:start -->
@.claude/engineering-os/constitution.md
@.claude/engineering-os/workflow.md
<!-- engineering-os:end -->

## Git Workflow

- **Never push directly to `main`.** Always create a feature branch and open a PR.
- Branch naming: `feat/<short-description>`, `fix/<short-description>`, etc.

## Async Worker Lifecycle

When stopping or replacing async workers (screensavers, pollers, background tasks):

- **Never use `asyncio.sleep()` as a synchronization barrier.** Frame durations vary and the sleep will race.
- **Use a monotonic generation counter.** Bump it before launching a new worker. Each worker receives its generation at birth and exits when `self._generation != my_generation`.
- **Guard writes to widgets** that may have been removed from the DOM. A stale worker waking up after `remove_children()` must not crash the app — catch and exit silently.

# AI Engineering Flow

You are operating under the AI Engineering Flow framework.

## Required workflow

BEFORE implementing any non-trivial change (new features, multi-file changes, new components, behavior changes), you MUST:

1. Invoke `/flow:frame` — define intent, scope, constraints, decomposition
2. `/flow:assess` auto-triggers after frame — classifies risk, determines controls
3. Then implement
4. `/flow:verify` auto-triggers — progressive validation (tests, edge cases, metrics)
5. `/flow:review` auto-triggers — isolated subagent review with severity tiers

For trivial changes (typo fixes, single-line changes, config tweaks): skip the framework, just do it.

## Principles

1. **Resist automation bias.** Structural separation (reviewer ≠ implementer) is the defense.
2. **Rigor matches blast radius.** Low risk = fast. High risk = deep verification + human approval.
3. **Challenge every decision.** Lead challenges most. Assessment determines when to escalate to human.
4. **Verification artifacts are primary deliverables.** Evidence: test results, metrics, edge cases — not just code.
5. **Guard against local optimization.** Use existing patterns. Don't invent new abstractions.
6. **Unobservable code is debt.** If you can't verify it through metrics/tests/logs, it's debt.
7. **Structured context prevents cold starts.** Load and cite project memory.
8. **Small, reversible changes.** Decompose. Each piece gets its own verify-review cycle.
9. **Every artifact must earn its place.** Don't generate what won't be used.
10. **Mechanical sympathy through observability.** Metrics, alerts, logs — not code reading.
11. **Transparency and data are non-negotiable.** You cannot validate what you cannot measure.

## Lead behavior

- Handle minor/medium reviewer findings yourself. Only escalate major findings to human.
- Present to human at architecture level: components, contracts, behavior, numbers. Not code.
- Know when to pull human in: low risk = you decide. High risk = human decides.

## Change flow

/frame → /assess → implement → /verify → /review → merge → /learn
