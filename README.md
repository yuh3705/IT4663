# IT4663 - Staff Rostering Optimization

Mini project for the IT4663 planning optimization course. The project solves a staff rostering problem with a fairness objective: minimize the maximum number of night shifts assigned to any employee.

## Problem Overview

Given:

- `N` employees.
- `D` consecutive working days.
- Four working shifts per day: morning `1`, noon `2`, afternoon `3`, night `4`.
- Shift staffing bounds `[A, B]`.
- A day-off list `F(i)` for each employee.

The solver must build an `N x D` schedule where each cell is:

- `0`: day off.
- `1`: morning shift.
- `2`: noon shift.
- `3`: afternoon shift.
- `4`: night shift.

Hard constraints:

- Each employee works at most one shift per day.
- Each shift on each day has between `A` and `B` employees.
- Employees cannot work on declared days off.
- If an employee works a night shift on day `d`, that employee must rest on day `d + 1`.

Objective:

```text
minimize max_i(number of night shifts assigned to employee i)
```

In other words, the project tries to distribute night shifts as fairly as possible.

## Project Structure

```text
IT4663/
+-- data/
|   +-- easy/                 # Small benchmark cases
|   +-- medium/               # Medium benchmark cases
|   +-- hard/                 # Large benchmark cases
|   +-- stress/               # Very large benchmark cases
|   +-- edge/                 # Edge and infeasibility cases
|   +-- hustack/              # Additional large cases
+-- results/
|   +-- final_report.csv      # Main benchmark table
|   +-- ...                   # Local-search plots and CSV histories
+-- solvers/
|   +-- logic_exact/
|   |   +-- cp_solver.py      # OR-Tools CP-SAT model
|   |   +-- scip_solver.py    # OR-Tools linear solver / SCIP model
|   +-- branch_bound/
|   |   +-- branch_bound_solver.py
|   +-- greedy/
|   |   +-- greedy_solver.py
|   +-- local_search/
|       +-- hill_climbing_solver.py
|       +-- tabu_search_solver.py
|       +-- run_coverage.py
|       +-- tune_tabu_tenure.py
+-- utils/
|   +-- data_loader.py
|   +-- generator.py
|   +-- generate_edge_cases.py
|   +-- logger.py
|   +-- visualize_result.py
+-- main.py                   # Benchmark runner
+-- requirements.txt
+-- README.md
```

## Input Format

Each test case is a text file:

```text
N D A B
F(1)
F(2)
...
F(N)
```

Each `F(i)` line contains the day-off list for employee `i`, ending with `-1`.

Example:

```text
8 6 1 3
1 -1
3 -1
4 -1
5 -1
2 4 -1
-1
-1
3 -1
```

This means:

- `N = 8` employees.
- `D = 6` days.
- Each shift needs at least `A = 1` and at most `B = 3` employees.
- Employee 1 is off on day 1.
- Employee 5 is off on days 2 and 4.
- A line containing only `-1` means the employee has no requested day off.

## Output Format

A feasible solver output is an `N x D` schedule:

```text
0 1 3 1 4 0
4 0 0 1 2 2
2 4 0 0 2 2
3 1 4 0 0 4
1 0 2 0 1 1
3 2 1 2 3 3
2 3 2 4 0 3
1 3 0 3 1 1
```

Each row is one employee. Each column is one day.

## Implemented Solvers

### CP-SAT

File: `solvers/logic_exact/cp_solver.py`

Uses Google OR-Tools CP-SAT with Boolean variables and finite-domain integer constraints. This is the strongest exact solver in the current experiments, especially for larger logical scheduling constraints.

### SCIP

File: `solvers/logic_exact/scip_solver.py`

Uses OR-Tools `pywraplp` with SCIP-style integer linear programming constraints. It can find optimal solutions, but runtime increases heavily on large cases.

### Branch and Bound

File: `solvers/branch_bound/branch_bound_solver.py`

Custom recursive Branch and Bound implementation. It works on small cases, but recent reruns show that it hits Python recursion stack growth on larger instances. In `results/final_report.csv`, Branch and Bound results from `medium` to `stress` are therefore marked as `RECURSION_ERROR` instead of being treated as valid benchmark results.

### Greedy

File: `solvers/greedy/greedy_solver.py`

Constructs a feasible schedule quickly using heuristic assignment rules. It is fast and often matches the exact objective on generated benchmark cases, but it does not provide an optimality proof.

### Hill Climbing

File: `solvers/local_search/hill_climbing_solver.py`

Local-search solver that starts from a feasible schedule when possible and tries to improve the objective through neighborhood moves.

### Tabu Search

File: `solvers/local_search/tabu_search_solver.py`

Metaheuristic local search with tabu memory. The implementation searches from one feasible initial schedule and uses tabu tenure to avoid immediate cycling.

## Setup

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Check that OR-Tools imports correctly:

```powershell
python -c "from ortools.sat.python import cp_model; from ortools.linear_solver import pywraplp; print('deps ok')"
```

## Running Experiments

The main runner is `main.py`. It reads test cases, calls selected solvers, and writes benchmark rows to `results/final_report.csv` through `utils/logger.py`.

Run the current benchmark configuration:

```powershell
python main.py
```

Important: `main.py` may be edited to choose which dataset folder and which solvers are active. In the current local workflow, some solver calls are commented out when rerunning only one solver.

To switch dataset groups, update this line in `main.py`:

```python
test_files = glob.glob("data/medium/*.txt", recursive=True)
```

Examples:

```python
test_files = glob.glob("data/easy/*.txt", recursive=True)
test_files = glob.glob("data/hard/*.txt", recursive=True)
test_files = glob.glob("data/stress/*.txt", recursive=True)
test_files = glob.glob("data/**/*.txt", recursive=True)
```

## Running a Solver from Standard Input

Several solver files support direct input through stdin. Example for Branch and Bound:

```powershell
Get-Content data\easy\test_1.txt | python -m solvers.branch_bound.branch_bound_solver
```

For CP-SAT, SCIP, Greedy, Hill Climbing, and Tabu Search, prefer the `solve(...)` function from Python or the configured `main.py` benchmark runner.

## Visualizing Results

Generate the runtime comparison chart from `results/final_report.csv`:

```powershell
python utils\visualize_result.py
```

This writes:

```text
results/performance_chart.png
```

The visualization script groups rows by algorithm and dataset scale, then plots average runtime on a log scale.

## Local Search Diagnostics

Run local-search coverage history:

```powershell
python solvers\local_search\run_coverage.py --case data\stress\test_2.txt --time-limit 300
```

Tune Tabu Search tenure:

```powershell
python solvers\local_search\tune_tabu_tenure.py --case data\stress\test_2.txt --time-limit 1200 --max-iterations 20000
```

Outputs include:

```text
solvers/local_search/results/convergence_history.csv
solvers/local_search/results/convergence_plot.png
solvers/local_search/results/tabu_tenure_history.csv
solvers/local_search/results/tabu_tenure_summary.csv
solvers/local_search/results/tabu_tenure_tuning.png
solvers/local_search/results/tabu_tenure_small_multiples.png
solvers/local_search/results/tabu_tenure_summary.png
```

## Reading `final_report.csv`

Columns:

- `Thuat toan`: solver name and dataset group.
- `Bo du lieu`: test file name.
- `So nhan vien`: number of employees.
- `So ngay`: number of days.
- `Trang thai`: solver status.
- `Gia tri ham muc tieu`: objective value.
- `Thoi gian chay(s)`: runtime in seconds.

Common statuses:

- `OPTIMAL`: solver found and proved the best objective.
- `FEASIBLE`: solver found a valid schedule but did not prove optimality.
- `NO_FEASIBLE_SOLUTION`: no feasible schedule was found by that solver.
- `INFEASIBLE`: model proved infeasibility.
- `INFEASIBLE/UNKNOWN`: exact solver could not prove a feasible result under the current run limit.
- `TIMEOUT`: solver stopped after the time limit.
- `NOT_RUN`: solver was intentionally skipped.
- `RECURSION_ERROR`: recursive Branch and Bound exceeded Python's recursion depth / stack capacity.

## Current Branch and Bound Note

The custom Branch and Bound solver is recursive. During the latest rerun, it produced `RecursionError: maximum recursion depth exceeded` on larger benchmark groups. For report accuracy:

- `easy`: Branch and Bound results are kept as valid.
- `medium`: Branch and Bound is marked `RECURSION_ERROR`.
- `hard`: Branch and Bound is marked `RECURSION_ERROR`.
- `stress`: Branch and Bound is marked `RECURSION_ERROR`.
- selected `edge` cases may still show `OPTIMAL`, `TIMEOUT`, `NO_FEASIBLE_SOLUTION`, or `NOT_RUN` depending on whether they were actually executed.

This means Branch and Bound should not be used as evidence of scalability beyond small cases unless the recursive implementation is rewritten into an iterative/search-stack version or protected with a robust depth strategy.

## Regenerating Edge Cases

Generate additional edge-case inputs:

```powershell
python utils\generate_edge_cases.py
```

The generated files are stored under `data/edge/`.

## Development Notes

- Keep generated caches out of Git: `__pycache__/`, `.pytest_cache/`, virtual environments, and temporary logs are ignored.
- Keep source files, benchmark data, and important CSV/PNG report artifacts tracked when they are part of the final report.
- Be careful when rerunning `main.py`: `utils/logger.py` updates rows in `results/final_report.csv` by matching solver name and dataset file.
- If a solver crashes, update the result row with the real failure status instead of leaving stale successful results.
