# Repo Instructions

This repository uses the Engineering OS harness.

<!-- engineering-os:start -->
@.claude/engineering-os/constitution.md
@.claude/engineering-os/workflow.md
<!-- engineering-os:end -->

## Async Worker Lifecycle

When stopping or replacing async workers (screensavers, pollers, background tasks):

- **Never use `asyncio.sleep()` as a synchronization barrier.** Frame durations vary and the sleep will race.
- **Use a monotonic generation counter.** Bump it before launching a new worker. Each worker receives its generation at birth and exits when `self._generation != my_generation`.
- **Guard writes to widgets** that may have been removed from the DOM. A stale worker waking up after `remove_children()` must not crash the app — catch and exit silently.
