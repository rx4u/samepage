# samepage

`docs/architecture/README.md` is binding for every change. Read it first. Builders implement one work package brief at a time and never decide a table, column, read or dependency. Anything outside the brief stops work and becomes a proposed ADR.

- Python standard library only (ADR-0012). No new dependency without an ADR.
- No em dashes in any file.
- Every list read is capped at 50 rows; default page size is 20.
