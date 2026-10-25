# 14: Synonym Sets

**What to build:** The tool ships a small file of Synonym Sets, which users can extend. Search expands queries with them at a lower weight than the literal query.

**Blocked by:** 06, 07

**Status:** wontfix

- [ ] The initial sets cover time domain / transient / T-solver / `Solver`, frequency domain / F-solver / `FDSolver`, integral equation / I-solver / `IESolver`, eigenmode / E-solver / `EigenmodeSolver`, and farfield / far field / radiation pattern.
- [ ] Users can add their own sets in the configuration.
- [ ] The TERM benchmark questions score at least as well as the baseline from ticket 07.
- [ ] Every set added later must be justified by a benchmark question that failed without it.

## Comments

**2026-10-25, retired.** There is no search to expand. The vendor's keyword index (`keywords.md`) is the synonym list, and in the experiment the agents bridged the one vocabulary gap ("radiation pattern" to farfield) themselves. See ADR 0014 and `../files-only-experiment.md`.
