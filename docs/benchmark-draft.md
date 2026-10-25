# Benchmark (draft) for the CST Studio Suite 2024 Knowledge Base

## Purpose

This benchmark checks whether an agent finds the right Documents in the Knowledge Base folder for the questions agents and engineers actually ask. It was first written to tune a search ranker; since ADR 0014 it judges the folder itself: its pages, its entry files and its `AGENTS.md`. It has 39 questions in twelve categories, weighted towards the main jobs: generating VBA macros and Python scripts, grounding agents that drive CST through a Control Server, how-to answers, and theory.

Every expected source was found by hand in `.ingestion/2024/`. Each path, anchor and PDF page was checked mechanically to exist. The "why" lines are written in our own words. No vendor prose is copied.

## Scoring

`docs/benchmark.toml` holds these questions in the form the agent run uses. This file keeps the reasoning; change a question's sources, Area or text in both.

The benchmark is run by agents, not by a ranker (ADR 0014). For each question, an agent with file tools only (grep, glob, read) is opened in the Knowledge Base folder, reads `AGENTS.md`, and answers the question. Its tool calls are logged. `scripts/agent-run.py` does this for every scorable question, a question whose Areas are built and that is not scored by hand, and reports the counts below.

- **Hit:** the agent read an expected Document of the question. An Alias of it counts. For a PDF, the page it read must include the given page.
- **Calls:** the number of tool calls up to and including the first read of an expected Document, counting the `AGENTS.md` read as call 1. Report the distribution and the median.
- **Thresholds:** every scorable question is a hit, and the median is at most 4 calls. Set from the two runs of 2026-10-25 (`.scratch/cst-help-kb/files-only-experiment.md`), which both met them. Kept unchanged after the proof-of-concept slice (ticket 16): 26 of 27, median 3, maximum 5, no category's median above 4. The run fails on its one miss, REL-01, whose Release Notes the slice does not build.
- **API questions:** also check that the listed API Entry has a line in `api.md` pointing at the first expected source.

## How to read and edit

- Each question is one block. Its id prefix gives the category, for example `API-03` or `FIG-01`. Ids are not reused.
- **Sources** are listed best first. Paths are relative to the corpus root `.ingestion/2024/` and use the original file names, not Locators. Locators will be derived from them mechanically.
- **Anchor** is the literal `id` or `name` attribute in the HTML. Some contain spaces, for example `General Methods`. VBA method headings have no anchor of their own. For those, the anchor is the enclosing category, and **heading** names the method. Python anchors are the Sphinx ids, which equal the qualified names.
- **PDF page** is the physical page index. In all four PDFs cited here it equals the printed page number.
- **Area** is the filter an agent would plausibly use. `-` means none.
- **Risk** notes vocabulary or ranking traps worth watching. It is not part of the score.
- To correct a question, edit the fields in place. To drop one, set `Confidence: rejected` rather than deleting it, so the ids stay stable. To add one, copy a block and give it the next free id in its category.
- `Confidence: needs user check` marks questions where the documentation is ambiguous or where real-world use may differ from the documented behaviour.

## Category counts

| Category | Id prefix | Count |
|---|---|---:|
| Exact API lookup | API | 10 (3 VBA 3D, 2 VBA schematic, 2 WinWrap Basic, 3 Python) |
| Solver-specific | SOL | 4 |
| How-to and UI | HOW | 4 |
| Terminology mismatch | TERM | 3 |
| Theory and equations | THEO | 2 |
| Crosslink to follow | LINK | 2 |
| Figure matters | FIG | 3 (one answer exists only as an equation image) |
| PDF manuals | PDF | 2 |
| Example Projects (`EXP_*`) | EXP | 2 |
| Release notes | REL | 1 |
| Library (Result Templates and their idioms) | LIB | 5 |
| Not in the documentation (scored by hand) | NODOC | 1 |
| **Total** | | **39** |

Out of scope: GPU computing, MPI and licensing (their guides are not part of the corpus).

---

## 1. Exact API lookups

### API-01: set the frequency range in VBA
- **Question:** My macro needs to set the solver frequency range to 1–10 GHz. What's the VBA call?
- **Area:** `vba-3d`
- **Sources:**
  1. `Online Help/mergedProjects/VBA_3D/special_vbasolver/special_vbasolver_solver_object.htm` · anchor `General Methods` · heading `FrequencyRange`
- **API Entry:** `Solver.FrequencyRange`
- **Why:** The HF Solver object's `FrequencyRange(fmin, fmax)` sets the global frequency range. The entry also warns that changing it deletes existing results.
- **Confidence:** high
- **Risk:** A method named `FrequencyRange` also exists on `Monitor`, `PICSolver` and `TOUCHSTONE` (where it takes "Full" or "Limited"), and `MeshAdaption3D` has `SetFrequencyRange`. A second page, `special_vba_ems_solver_object.htm`, has the same title "Solver Object" (the LF variant).

### API-02: define a waveguide port in VBA
- **Question:** Write VBA that creates a waveguide port on the zmin boundary, covering the full cross-section, with 2 modes.
- **Area:** `vba-3d`
- **Sources:**
  1. `Online Help/mergedProjects/VBA_3D/special_vbaports/special_vbaports_port_object.htm` · anchor `Port_Creation` · heading `Create / Modify`
  2. same file · anchor `Port_Settings` · headings `Orientation`, `NumberOfModes`, `Coordinates`
- **API Entry:** `Port.Create`
- **Why:** The `Port` object defines waveguide ports. Its settings cover orientation (`"zmin"` and so on), the number of modes and the `"Full"` coordinate mode, and its examples show a complete `With Port ... .Create` block.
- **Confidence:** high
- **Risk:** The object is called `Port`, not "WaveguidePort". Discrete ports live on a separate `DiscretePort` object page.

### API-03: export S-parameters to Touchstone
- **Question:** How do I export the S-parameters as a Touchstone file from a macro, renormalized to 50 Ω?
- **Area:** `vba-3d`
- **Sources:**
  1. `Online Help/mergedProjects/VBA_3D/special_vbaimpexp/special_vbaimp_exp_touchstone.htm` · anchor `Methods` · headings `Impedance`, `Renormalize`, `Write`
  2. same file · anchor `Example`
- **API Entry:** `TOUCHSTONE.Write`
- **Why:** The `TOUCHSTONE` object sets the file name, reference impedance, renormalization, format and parameter type (S, Y or Z), then writes the `.sNp` file.
- **Confidence:** high
- **Risk:** The object name is all capitals. The asker says "export", but the method is `Write`.

### API-04: create and run an S-parameter task in the schematic
- **Question:** In a schematic (Design Studio) macro, how do I create an S-parameter task that sweeps 0–10 GHz, and then run it?
- **Area:** `vba-schematic`
- **Sources:**
  1. `Online Help/mergedProjects/VBA_DES/special_vbacommands/simulationtaskobject.htm` · anchor `General_Methods` · headings `Type`, `Name`, `Create`, `Update`
  2. same file · anchor `Special_Methods` · heading `SetSweepData`
- **API Entry:** `SimulationTask.SetSweepData`, `SimulationTask.Update`
- **Why:** `Type` takes `"s-parameters"` before `Create`. `SetSweepData(min, max, samples)` sets Fmin and Fmax for frequency-domain tasks. `Update` executes the named task.
- **Confidence:** high
- **Risk:** "Run" is called `Update` here. The page title is "Simulation Task Object", but the object is `SimulationTask`.

### API-05: add an inductor block and set its value
- **Question:** From VBA in the schematic, how do I add an inductor block and set its inductance to the parameter `Ind1`?
- **Area:** `vba-schematic`
- **Sources:**
  1. `Online Help/mergedProjects/VBA_DES/special_vbacommands/blockobject.htm` · anchor `Properties` · heading `SetDoubleProperty`
  2. `Online Help/mergedProjects/VBA_DES/special_vbacommands/blocktypes.htm`
  3. `Online Help/mergedProjects/VBA_DES/special_vbacommands/optimizerobject.htm` · anchor `Example1`
- **API Entry:** `Block.SetDoubleProperty`
- **Why:** The Block object page covers `Type`, `Position`, `Create` and the property setters. The Block Types page gives the type string `CircuitBasic\Inductor`. The only place the property name `"Inductance"` appears is the DSOptimizer example.
- **Confidence:** best judgement, verify in CST during the proof of concept (the property name is documented only through that example; the user could not confirm it)
- **Risk:** The property name is missing from the Block object page itself. The `VBA_DES/special_vbaexamples/lccircuit.htm` example creates inductors but never sets their values.

### API-06: write a CSV file from a macro
- **Question:** How do I write results line by line into a CSV file from a CST macro?
- **Area:** `winwrap-basic`
- **Sources:**
  1. `Online Help/sax_basic/ww_00178.htm` (Open Instruction)
  2. `Online Help/sax_basic/ww_00185.htm` (Print Instruction)
  3. `Online Help/sax_basic/ww_00035.htm` (Close Instruction)
- **API Entry:** `Open`, `Print #` (WinWrap Basic)
- **Why:** `Open ... For Output As #n` opens the stream, `Print #n` writes a line (with a newline unless the line ends in `;`), and `Close` finishes the file.
- **Confidence:** high
- **Risk:** The file names are numeric, so only titles and body text identify these pages. "CSV" appears in none of them.

### API-07: loop over files in a folder
- **Question:** In a macro, how can I loop over every `*.s2p` file in a folder?
- **Area:** `winwrap-basic`
- **Sources:**
  1. `Online Help/sax_basic/ww_00069.htm` (Dir$ Function)
- **API Entry:** `Dir$` (WinWrap Basic)
- **Why:** `Dir$(pattern)` returns the first match, and calling `Dir$()` again without arguments continues the same search until it returns an empty string. The page shows exactly that loop.
- **Confidence:** high
- **Risk:** The `$` in `Dir$` must survive tokenization. Agents may also search for "FileSystemObject", which WinWrap does not document.

### API-08: parametric results with cst.results
- **Question:** With `cst.results`, how do I get S1,1 for every run of a parameter sweep, together with the parameter values of each run?
- **Area:** `python`
- **Sources:**
  1. `Online Help/Python/source/cst.results.html` · anchor `cst.results.ResultModule.get_run_ids`
  2. same file · anchor `cst.results.ResultModule.get_result_item`
  3. same file · anchor `cst.results.ResultModule.get_parameter_combination`
- **API Entry:** `cst.results.ResultModule.get_run_ids`
- **Why:** `get_run_ids(treepath)` lists the runs of a tree item, `get_result_item(treepath, run_id)` loads one run, and `get_parameter_combination(run_id)` returns that run's parameter values. The page's examples use the tree path `1D Results\S-Parameters\S1,1`.
- **Confidence:** high

### API-09: reading results of a project that is open in CST
- **Question:** Can `cst.results` read a project that is open in CST right now, for example one my Control Server is driving?
- **Area:** `python`
- **Sources:**
  1. `Online Help/Python/source/cst.results.html` · anchor `cst.results.ProjectFile.init`
  2. same file · anchor `general-notes`
- **API Entry:** `cst.results.ProjectFile.init`
- **Why:** `allow_interactive=True` permits access to a project that is open in CST, but the data reflect only the last save. The general notes add that projects being simulated, packed projects and protected projects are not supported.
- **Confidence:** high
- **Risk:** The answer is split between a method entry and a general-notes Section further down the page.

### API-10: calling add_to_history twice with the same header
- **Question:** If I call `model3d.add_to_history` twice with the same header, does CST keep both history blocks?
- **Area:** `python` (then `vba-3d`)
- **Sources:**
  1. `Online Help/mergedProjects/VBA_3D/common_vbaapp/common_vbaappapplication_object.htm` · anchor `General Methods` · heading `AddToHistory`
  2. `Online Help/Python/source/cst.interface.html` · anchor `cst.interface.Model3D.add_to_history`
- **API Entry:** `cst.interface.Model3D.add_to_history`; VBA `AddToHistory` on the 3D "Project Object"
- **Why:** The Python entry gives only the signature and a one-line summary. The VBA `AddToHistory` entry explains that a new block replaces the immediately preceding block when both have the same caption, and that the call returns whether execution succeeded.
- **Confidence:** verify in CST during the proof of concept (does the Python call inherit this VBA behaviour exactly, and how does it report failure? Unknown to the user)
- **Risk:** The VBA page is titled "Project Object", although the file is named `...application_object.htm`. The VBA_DES `projectobject.htm` has the same title.

## 2. Solver-specific

### SOL-01: time domain accuracy setting
- **Question:** What does the time domain solver's Accuracy of −40 dB actually control, and how do I set it to −50 dB in VBA?
- **Area:** `3d` (then `vba-3d`)
- **Sources:**
  1. `Online Help/mergedProjects/3D/special_solvopt/special_solvopt_solver.htm` (field "Accuracy" in the Solver settings frame)
  2. `Online Help/mergedProjects/VBA_3D/special_vbasolver/special_vbasolver_solver_object.htm` · anchor `TD Steady State` · heading `SteadyStateLimit`
- **API Entry:** `Solver.SteadyStateLimit`
- **Why:** The dialog page explains that Accuracy is the steady-state energy criterion, which decides when the run stops and how much truncation error the FFT sees. It does not affect mesh error. `SteadyStateLimit` takes an integer dB value between −80 and 0, or `"No Check"`.
- **Confidence:** high
- **Risk:** The dialog says "Accuracy", while the VBA name says "steady state".

### SOL-02: which VBA object runs the integral equation solver
- **Question:** How do I run the integral equation solver from a macro? Is there an `IESolver.Start`, or does it go through `FDSolver`?
- **Area:** `vba-3d`
- **Sources:**
  1. `Online Help/mergedProjects/VBA_3D/special_vbasolver/special_vbasolver_fdsolver_object.htm` · anchor `FD Method` · heading `SetMethod`
  2. `Online Help/mergedProjects/VBA_3D/special_vbasolver/special_vbasolver_iesolver_object.htm` · anchor `IE_General`
  3. `Online Help/mergedProjects/VBA_3D/common_vbaapp/common_vbaappapplication_object.htm` · anchor `General Methods` · heading `ChangeSolverType`
- **API Entry:** `FDSolver.SetMethod`
- **Why:** `FDSolver` controls both the frequency domain and the integral equation solver, and `SetMethod` with a surface mesh and a "General purpose" sweep selects the IE solver. `IESolver` holds only IE-specific settings and has no `Start` method. `ChangeSolverType "HF IntegralEq"` switches the active solver.
- **Confidence:** verify in CST during the proof of concept (the enum value is `"Surface"`, but the prose says "Surface Mesh"; the interplay with `ChangeSolverType` is not spelled out; the user mainly works in the GUI)

### SOL-03: eigenmode solver limitations
- **Question:** Can the eigenmode solver handle open boundaries and lossy, dispersive materials, or only closed, lossless cavities?
- **Area:** `3d`
- **Sources:**
  1. `Online Help/mergedProjects/3D/special_overview/special_overview_eigenmodesolverover.htm`
- **Why:** All methods support lossless structures without open boundaries. JDM (hexahedral mesh) and Classical (tetrahedral mesh) handle only frequency-independent losses. Only the General (Lossy) tetrahedral method handles lossy, dispersive materials and open (SIBC) boundaries. The page recommends it for an accurate external Q per port and mode.
- **Confidence:** high

### SOL-04: AR filter for a high-Q structure in VBA
- **Question:** My high-Q filter takes forever in the time domain solver. How do I switch on the AR filter from VBA?
- **Area:** `vba-3d` (then `3d`)
- **Sources:**
  1. `Online Help/mergedProjects/VBA_3D/special_vbasolver/special_vbasolver_solver_object.htm` · anchor `TD AR-Filter` · heading `UseArfilter`
  2. `Online Help/mergedProjects/3D/special_overview/special_overview_arfilterover.htm` · anchor `Online_AR_Filter`
  3. `Online Help/mergedProjects/3D/common_overview/common_overview_problems_transient_solver.htm` · anchor `TD_MaxSimulationTimeWarning`
- **API Entry:** `Solver.UseArfilter`
- **Why:** `UseArfilter` enables the autoregressive filter during the run. The overview explains why strongly resonant devices need it. The problem-handling page recommends it when the maximum simulation time is reached before the energy has decayed.
- **Confidence:** high
- **Risk:** The method spelling (`Arfilter`, lower-case f) differs from the page's "AR-Filter", and the anchor contains a hyphen.

## 3. How-to and UI

### HOW-01: discrete port types
- **Question:** In the discrete port dialog, what's the difference between the S-parameter, voltage and current port types, and what does the impedance field do?
- **Area:** `3d`
- **Sources:**
  1. `Online Help/mergedProjects/3D/special_solvopt/special_solvopt_discreteports.htm` (Properties frame, "Port type")
  2. `Online Help/mergedProjects/3D/special_overview/special_overview_discrete_port_overview.htm`
- **Why:** The dialog page describes each port type. The S-parameter type is a current source with a parallel inner impedance that both excites and absorbs power, and only it yields S-parameters. The voltage and current types are pure sources, and each type normalizes its input signal differently.
- **Confidence:** high

### HOW-02: open boundary with extra space for an antenna
- **Question:** For an antenna model, which boundary setting adds free space for the farfield, and how does it combine with the extra space in the background settings?
- **Area:** `3d`
- **Sources:**
  1. `Online Help/mergedProjects/3D/special_solvopt/special_solvopt_boundary_conditions_boundaries.htm` (boundary type "Open (add space)")
  2. `Online Help/mergedProjects/3D/common_general/common_general_background.htm` (Lower/Upper X/Y/Z distance fields)
- **Why:** "Open (add space)" is the PML boundary plus extra space, and it is the recommended choice for antennas. Both pages state that when both mechanisms are used, the larger of the two distances wins.
- **Confidence:** high

### HOW-03: parameter sweep sequences
- **Question:** If I put two parameters into one sequence of the Parameter Sweep dialog, do I get every combination? How do I sweep them one after the other instead?
- **Area:** `3d`
- **Sources:**
  1. `Online Help/mergedProjects/3D/special_process/special_solvopt_parametersweep.htm` (Sequences frame)
  2. `Online Help/mergedProjects/3D/special_process/special_solvopt_parametersweeppar.htm`
- **Why:** Within one sequence every combination of its parameters is simulated. Separate sequences run independently, one after another. The second page covers the From, To and Samples fields for each parameter.
- **Confidence:** high
- **Risk:** A same-titled DES page exists at `mergedProjects/DES/analysis/parametersweep/special_solvopt_parametersweep.htm`. It is not an Alias, because its text differs.

### HOW-04: disable a history step without deleting it
- **Question:** How do I temporarily switch off a step in the history list without deleting it?
- **Area:** `3d`
- **Sources:**
  1. `Online Help/mergedProjects/3D/common_macro/common_macro_history_list.htm` (button "(Un-)hide")
- **Why:** "(Un-)hide" deactivates the selected commands, which then appear greyed out and are skipped. They stay in the list. "Delete" removes them permanently.
- **Confidence:** high
- **Risk:** The asker says "disable" or "switch off", while the page says "hide". This also matters for Control Server agents that edit the history.

## 4. Terminology mismatch

### TERM-01: "T-solver" from a macro
- **Question:** How do I make the T-solver the active solver from a macro before I start it?
- **Area:** `vba-3d`
- **Sources:**
  1. `Online Help/mergedProjects/VBA_3D/common_vbaapp/common_vbaappapplication_object.htm` · anchor `General Methods` · heading `ChangeSolverType`
  2. `Online Help/mergedProjects/VBA_3D/special_vbasolver/special_vbasolver_solver_object.htm` · anchor `TD General` · heading `Start`
- **API Entry:** `ChangeSolverType` (3D "Project Object"), then `Solver.Start`
- **Why:** `ChangeSolverType` takes solver names such as `"HF Time Domain"`. `Solver.Start` then runs the time domain solver.
- **Confidence:** high
- **Risk:** The solver letter "T-solver" appears on only five help pages and never on these two. The pages say "HF Time Domain", "transient solver" or "time domain solver". The release notes use "(T)", "(F)" and "(A)" as solver tags.

### TERM-02: "radiation pattern" means farfield monitor
- **Question:** The run finished, but there's no radiation pattern for my antenna in the results. What did I forget to set up?
- **Area:** `3d`
- **Sources:**
  1. `Online Help/mergedProjects/3D/special_solvopt/special_solvopt_monitor.htm` (monitor type "Farfield/RCS")
  2. `Online Help/mergedProjects/3D/special_overview/special_overview_frequency_domain_solver_settings.htm`
- **Why:** Patterns come from a farfield monitor, which must be defined before the solver runs. The FD solver settings page says this explicitly, and the Field Monitor dialog is where the monitor is created.
- **Confidence:** high
- **Risk:** The asker says "radiation pattern", while the documentation mostly says "farfield". The phrase does occur on 15 pages, mostly examples, which may outrank the answer.

### TERM-03: "time domain" circuit simulation means transient task
- **Question:** How do I run a time domain simulation of my circuit in the schematic, for example to get an eye diagram from a bit sequence?
- **Area:** `circuits`
- **Sources:**
  1. `Online Help/mergedProjects/DES/analysis/simulation/tasks/transientsimulationtask.htm`
  2. `Online Help/mergedProjects/DES/analysis/simulation/tasks/transient_simulation_task_settings.htm`
- **Why:** In the schematic, time domain simulation is the "Transient" task. It takes nonlinear blocks into account, uses external-port sources including bit sequences, and produces eye diagrams.
- **Confidence:** high
- **Risk:** The asker says "time domain", while the title says "Transient". The 3D "Time Domain Solver" pages are a strong lexical distractor.

## 5. Theory and equations (MathJax pages)

### THEO-01: loss and Q formulas
- **Question:** What formulas does CST use for dielectric and wall (surface) losses when it computes the Q factor?
- **Area:** `3d`
- **Sources:**
  1. `Online Help/mergedProjects/3D/special_overview/special_overview_loss_and_q_calculation_overview.htm`
  2. `Online Help/mergedProjects/3D/special_overview/special_overview_eigenmodesolverover.htm`
- **Why:** The first page gives the TeX formulas for volume loss (from tan δ and |E|²) and surface loss (a perturbation formula from σ, μ and the tangential H), and how they combine into Q. The eigenmode overview relates Q to the complex angular frequency.
- **Confidence:** high
- **Risk:** The equations are TeX inside running paragraphs, so they need to survive conversion.

### THEO-02: Ludwig 2 angle definitions
- **Question:** How does CST define azimuth and elevation in the Ludwig 2 coordinate systems (AE vs EA)? Which axis is the pole?
- **Area:** `3d`
- **Sources:**
  1. `Online Help/mergedProjects/3D/special_postpr/special_postpr_pp_farfield.htm` · anchor `Transverse_Components_in_Different_Coordinate_Systems`
  2. `Online Help/mergedProjects/3D/special_postpr/special_postpr_farfield_plot_special_settings_axes.htm`
- **Why:** The Section gives arcsin and arctan definitions of the angles for Spherical, Ludwig 2 AE, Ludwig 2 EA and Ludwig 3. The pole is y′ for AE and x′ for EA. It also gives the component transforms. The Axes page is where the coordinate system is chosen.
- **Confidence:** high

## 6. Crosslink to follow

### LINK-01: number format codes
- **Question:** How do I format a Double with exactly three decimal places in a CST macro?
- **Area:** `winwrap-basic`
- **Sources:**
  1. `Online Help/sax_basic/ww_00109.htm` (Format User Defined Number), the target
  2. `Online Help/sax_basic/ww_00105.htm` (Format$ Function), the hub that links to 1
- **API Entry:** `Format$` (WinWrap Basic)
- **Why:** `Format$` gives only the syntax and links to the format families. The `0` and `.` codes, and the note that the decimal point is localized, are on the user-defined number format page.
- **Confidence:** high
- **Risk:** The localized decimal point matters on non-English Windows. A comma separator can break files that other tools parse.

### LINK-02: subprojects in cst.results
- **Question:** `cst.results` `list_subprojects()` returns `Tasks\SP1`. What is that schematic task, and why does `get_tree_items()` not show its results?
- **Area:** `python` (then `circuits`)
- **Sources:**
  1. `Online Help/mergedProjects/DES/analysis/simulation/simulation_task_overview.htm` · anchor `Simulation_Project`, the target
  2. `Online Help/Python/source/cst.results.html` · anchor `cst.results.ProjectFile.list_subprojects` (see also `cst.results.ProjectFile.load_subproject`), the hub
- **API Entry:** `cst.results.ProjectFile.load_subproject`
- **Why:** The Python page explains that results of Generalized Simulation Tasks live in subprojects, which must be loaded explicitly. It links into the RoboHelp DES page, which explains what a Simulation Project task is.
- **Confidence:** high
- **Risk:** This crosslink runs from Sphinx into RoboHelp. Only 10 such links exist, all on this page.

## 7. Figure or screenshot matters

### FIG-01: microstrip waveguide port size
- **Question:** How big should the waveguide port be around a microstrip line? What exactly does the extension factor k multiply?
- **Area:** `3d`
- **Sources:**
  1. `Online Help/mergedProjects/3D/special_overview/special_overview_waveguideover.htm` · anchor `Port_Modes_Microstrips` (image `microstrip_dims_kh.png`)
  2. same file · anchor `Port_Definition___Construction_Microstrips` (image `dialog_microstrip_kh.png`)
- **Why:** The text gives a range of 5 to 10 for k and explains the trade-off with higher-order modes. Only the figure shows that every extension is k·h, the substrate height: sideways from each strip edge and upwards above the substrate. It is not a multiple of the strip width.
- **Confidence:** high (checked by viewing the image)
- **Risk:** The figure has empty alt text, so an agent that reads only text will guess wrongly.

### FIG-02: solver choice chart
- **Question:** Which high-frequency solver does CST recommend as my structure becomes electrically larger, or more strongly resonant?
- **Area:** `3d`
- **Sources:**
  1. `Online Help/mergedProjects/3D/special_overview/special_overview_whichsolver.htm` · anchor `CST_MICROWAVE_STUDIO_` (image `../common_preloadedmacro/which_solver.png`)
- **Why:** The chart puts the solvers on two axes. With rising Q it goes from time domain, to time domain with AR filter, to frequency domain. With rising frequency for weakly resonant devices it goes from frequency domain, to time domain, to integral equation, to asymptotic. The surrounding text discusses each solver on its own. Only the chart puts them on a common scale.
- **Confidence:** high (checked by viewing the image)
- **Risk:** The image file lives in another folder (`common_preloadedmacro/`). The anchor name is a legacy product name.

### FIG-03: power definitions used when combining results
- **Question:** How exactly does CST define the power quantities (stimulated, accepted, radiated power) that the schematic uses when it combines farfield results?
- **Area:** `circuits`
- **Sources:**
  1. `Online Help/mergedProjects/DES/theory/power_definitions_for_combine_results.htm` (images `theory/pictures/formula1.png` to `formula14.png`)
- **Why:** The page's formulas exist only as images, so the answer is visible only to an agent that requests them through `cst_help_images` or opens the image files. Added on purpose to measure that gap.
- **Confidence:** high for the source; the scoring checks retrieval of the page, and the agent check verifies that the images were viewed
- **Risk:** Without transcription (ADR 0006), the Section's text carries no formula, so ranking relies on the title and surrounding prose.

## 8. PDF manuals

### PDF-01: choosing a port type
- **Question:** Discrete edge port, discrete face port or waveguide port: which gives the most accurate S-parameters for a microstrip filter, and when is a discrete port good enough?
- **Area:** `manuals`
- **Sources:**
  1. `Documentation/CST Studio Suite - High Frequency Simulation.pdf` · pages 102–103 ("Choosing the Right Port Type")
  2. `Online Help/mergedProjects/3D/special_overview/special_overview_waveguideover.htm`
- **Why:** The manual compares the three port types. Waveguide ports are the most accurate. Face ports cause smaller discontinuities than edge ports on strip lines, and discrete ports are adequate up to about a tenth of a wavelength.
- **Confidence:** high
- **Risk:** The Section starts at the bottom of page 102, after the eigenmode workflow summary.

### PDF-02: silent installation
- **Question:** What's the command line for a silent, unattended install of CST Studio Suite?
- **Area:** `manuals` (or `-`)
- **Sources:**
  1. `Documentation/CST Studio Suite - Getting Started.pdf` · page 12 ("Automated Installation")
  2. `Online Help/advanced/central_shared_installation.htm`
- **Why:** The manual gives the `setup.exe` command line for a silent installation with default settings and names a knowledge-base article for details. The help page only mentions that an unattended mode exists.
- **Confidence:** high

## 9. Example projects (`EXP_*`)

### EXP-01: SAR with head and hand
- **Question:** Is there a ready-made example of a SAR simulation of a mobile phone next to a head and a hand?
- **Area:** `example-projects`
- **Sources:**
  1. `Online Help/mergedProjects/EXP_HF/examplesoverview/sar_head_hand_-_mobile_phone_calculation.htm`
- **Why:** The example describes a complete phone with head and hand models, broadband tissue materials and a matching network in the schematic, plus its SAR, farfield and MIMO results.
- **Confidence:** high
- **Risk:** The `EXP_*` projects are outside the root TOC and have almost no inbound links, so only search reaches them.

### EXP-02: electrical machine task tutorial
- **Question:** Is there a step-by-step tutorial for setting up a PMSM load / no-load drive scenario with the electrical machine task?
- **Area:** `example-projects`
- **Sources:**
  1. `Online Help/mergedProjects/EXP_LF/examplesoverview/tutorials/electrical_machine_task.htm` · anchor `Configure_the_Permanent_Magnet_Synchronous_Machine_Load___Noload_Drive_Scenario`
  2. `Online Help/mergedProjects/EXP_LF/examplesoverview/tutorials/electrical_machine_coupled_drive_scenarios.htm`
  3. `Online Help/mergedProjects/DES/analysis/simulation/tasks/machinetask/pmsm_noload_load.htm`
- **Why:** The tutorial walks through a surface-magnet PMSM from the EM model to adding a machine task and configuring the load / no-load scenario. The DES page is the reference for that scenario's settings.
- **Confidence:** high
- **Risk:** The asker writes "PMSM". The page uses the abbreviation, but the anchor spells it out in full.

## 10. Release notes

### REL-01: Python automation changes in 2024
- **Question:** What's new for Python automation in CST 2024? Can Python call VBA functions directly now?
- **Area:** `manuals`
- **Sources:**
  1. `Documentation/CST Studio Suite - Release Notes.pdf` · page 10 ("Release Highlights 2024", "Python Automation")
- **Why:** The highlights list a subset of 3D and schematic VBA functions as newly available from Python, plus extensions to the EDA/PCB Python API. Page 4 has a related service-pack item on the PCB API.
- **Confidence:** high
- **Risk:** The release notes do not say which VBA functions are in the subset, and `cst.interface.html` does not list them as such either.

## 11. Library

Sources here are relative to the corpus root and start with `Library/`. Procedure names stand in for anchors, because Sections of code files are procedures (decided in round 7).

### LIB-01: export a 3D field result
- **Question:** I want a result template that exports a 3D field result, for example the E-field at one frequency, to an ASCII file after every run. Is there a CST template I can build on?
- **Area:** `result-templates`
- **Sources:**
  1. `Library/Result Templates/2D and 3D Field Results/- Export 3D Field Result.rtp` · procedures `Define`, `Evaluate0D`
  2. `Online Help/mergedProjects/3D/common_macro/post_processing_template_layout.htm`
- **Display Name:** `2D and 3D Field Results / - Export 3D Field Result`
- **Why:** CST's own template for this job, which the user named. The layout page explains the `Define` / `Evaluate` contract that it follows.
- **Confidence:** high
- **Risk:** The leading `- ` marks templates that store results elsewhere instead of in the Tables folder, so name matching must ignore it.

### LIB-02: export farfields as a farfield source
- **Question:** How do I export my antenna's farfields as a farfield source, to use as the excitation in another project, ideally automatically after every run?
- **Area:** `result-templates`
- **Sources:**
  1. `Library/Result Templates/Farfield and Antenna Properties/Export Farfields As Source^+MWS+DS.rtp` · procedures `Define`, `Evaluate0D`
- **Display Name:** `Farfield and Antenna Properties / Export Farfields As Source` (Application Filter MWS, DS)
- **Why:** The template the user named. It also keeps a pre-2019 code path (`Define_BWC_v2018_and_earlier`), which shows how CST handles backward compatibility.
- **Confidence:** high
- **Risk:** It must outrank the other farfield export items (GRASP, SATIMO, ASCII, SCANeR, 3DEXPERIENCE).

### LIB-03: Touchstone export after every run
- **Question:** How can I write the S-parameters to a Touchstone file automatically after every step of a parameter sweep?
- **Area:** `result-templates` (or `-`)
- **Sources:**
  1. `Library/Result Templates/S-Parameters/- Touchstone Export^+MWS+DS.rtp` · procedures `Define`, `Evaluate1D`
  2. `Online Help/mergedProjects/VBA_3D/special_vbaimpexp/special_vbaimp_exp_touchstone.htm` · anchor `Methods` · heading `Write`
- **Display Name:** `S-Parameters / - Touchstone Export` (Application Filter MWS, DS)
- **Why:** The template the user named wraps the VBA TOUCHSTONE object (API-03) and runs as part of the post-processing after each sweep step.
- **Confidence:** high
- **Risk:** API-03 asks the plain-VBA version of this question. Both should be answered, the template here and the object there.

### LIB-04: how CST's templates build their dialogs
- **Question:** Build the settings dialog of my template the way CST's own templates do. How do they define the dialog, react to its events and open it from `Define`?
- **Area:** `result-templates`, `winwrap-basic`
- **Sources:**
  1. `Library/Result Templates/S-Parameters/- Touchstone Export^+MWS+DS.rtp` · procedure `Define` (one `Begin Dialog` block, the shortest of the three)
  2. `Library/Result Templates/2D and 3D Field Results/- Export 3D Field Result.rtp` · procedure `Define` (two `Begin Dialog` blocks)
  3. `Online Help/sax_basic/ww_00013.htm` ("Begin Dialog Definition")
- **Why:** This is the idiom question the user cares about. 148 of the 163 templates define dialogs, and the WinWrap Basic page documents the syntax.
- **Confidence:** best judgement (which template is the clearest model is a heuristic choice)
- **Risk:** Search has to weigh code Usages against the language reference. A Guide on dialogs is a likely follow-up.

### LIB-05: how templates remember their settings
- **Question:** How does a CST result template remember the user's settings between runs and after the project is reopened?
- **Area:** `vba-3d`, `result-templates`
- **Sources:**
  1. `Online Help/mergedProjects/VBA_3D/common_vbaapp/common_vbaappapplication_object.htm` · headings `StoreScriptSetting`, `GetScriptSetting`, `StoreTemplateSetting`
  2. `Library/Result Templates/S-Parameters/- Touchstone Export^+MWS+DS.rtp` · procedure `Define` (22 `GetScriptSetting`, 10 `StoreScriptSetting`, 2 `StoreTemplateSetting`)
- **API Entry:** `StoreScriptSetting`, `GetScriptSetting`, `StoreTemplateSetting` (all on the 3D "Project Object")
- **Why:** The help documents the calls, and the template shows the pattern of keyed script settings plus template-level settings. The Usage index should connect the two.
- **Confidence:** high for the sources
- **Risk:** The calls are made without an object, so the Usage scan has to map them to the Application object (ADR 0012).

## 12. Not in the documentation

Scored by hand during the agent check, not by the agent run.

### NODOC-01: select the TLM solver from VBA
- **Question:** Write a macro that switches the project to the TLM solver and sets up a hexahedral TLM mesh.
- **Area:** `vba-3d`
- **Expected outcome:** The agent states that no documented VBA call selects TLM and points to the GUI route. It must not invent a value such as `Mesh.MeshType "HexahedralTLM"`. A Library Usage or Undocumented Member is acceptable if it is labelled as such.
- **Related sources:**
  1. `Online Help/mergedProjects/3D/special_mesh/special_mesh_mesh_props_hex_new.htm` (the dialog choice "Hexahedral TLM")
  2. `Online Help/mergedProjects/VBA_3D/special_vbamesh/special_vbamesho.htm` (the `MeshType` values, none of them TLM)
- **Confidence:** high that it is undocumented in 2024. The user does not know the macro line either.

---

## Answers from the user (2026-10-24)

- **API-05, API-10, SOL-02:** the user could not confirm them. They are kept on best judgement and get verified in CST during the proof of concept.
- **Control Server failures, the TLM macro line, logs of agent questions:** none available. TLM became NODOC-01.
- **Schematic block properties:** rarely set from VBA, because writing CST VBA by hand is tedious. Making that easier is the point of this tool.
- **Python vs. VBA:** Python coverage is growing in newer releases (2026). The Python questions are release-sensitive and should be reviewed for each Release.
- **GPU, MPI and licensing:** out of scope.
- **Image-only answers:** wanted, so FIG-03 was added.
- **Library items used most:** 3D field result export, farfield source export and Touchstone export (LIB-01 to LIB-03). Pointing an agent at a template is mostly about its idioms, such as how dialogs are built and how data is stored (LIB-04, LIB-05).
- **Units:** values inside CST are in project units, and exported files state their units, so there is no dedicated units question.
