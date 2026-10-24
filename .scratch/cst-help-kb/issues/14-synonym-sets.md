# 14: Synonym Sets

**What to build:** The tool ships a small file of Synonym Sets, which users can extend. Search expands queries with them at a lower weight than the literal query.

**Blocked by:** 06, 07

**Status:** ready-for-agent

- [ ] The initial sets cover time domain / transient / T-solver / `Solver`, frequency domain / F-solver / `FDSolver`, integral equation / I-solver / `IESolver`, eigenmode / E-solver / `EigenmodeSolver`, and farfield / far field / radiation pattern.
- [ ] Users can add their own sets in the configuration.
- [ ] The TERM benchmark questions score at least as well as the baseline from ticket 07.
- [ ] Every set added later must be justified by a benchmark question that failed without it.
