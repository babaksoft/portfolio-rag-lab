# Stage Records

Each stage lives in `docs/stages/<sequence>-<slug>/` and has two complementary
documents:

- `PLAN.md` records intended outcomes and reviewable slices. Create it just
  before implementation and update it when scope or sequence changes. Each
  slice states its outcome, scope boundary, expected artifacts, verification,
  documentation impact, and completion condition.
- `IMPLEMENTATION.md` records what happened: completed results, deviations,
  incidents, deliberate compromises, and follow-up work. Create it empty when
  implementation starts and update it as facts emerge.

Plans are prospective; implementation records are historical. Do not copy
durable architecture into either document—link to `DESIGN.md` or the relevant
ADR. Prefer four to eight independently verifiable slices per stage and keep
the plan adjustable as implementation provides evidence.
