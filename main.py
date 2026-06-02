import glob
import contextlib
import io
import os

from utils.data_loader import read_input
from utils.logger import ExperimentLogger
from solvers.anls import anls_solver
from solvers.branch_bound import branch_bound_solver
from solvers.greedy import greedy_solver
from solvers.local_search import hill_climbing_solver, tabu_search_solver
from solvers.logic_exact import cp_solver, ilp_solver


SOLVERS = [
    ("CP-SAT", cp_solver),
    ("ILP", ilp_solver),
    ("Branch and Bound", branch_bound_solver),
    ("Greedy", greedy_solver),
    ("Hill Climbing", hill_climbing_solver),
    ("Tabu Search", tabu_search_solver),
    ("ANLS", anls_solver),
]

CUSTOM_SOLVERS = {
    "Branch and Bound",
    "Greedy",
    "Hill Climbing",
    "Tabu Search",
    "ANLS",
}


def normalize_library_status(solver_name, status):
    if solver_name != "ILP":
        return status

    status_map = {
        0: "OPTIMAL",
        1: "FEASIBLE",
        2: "INFEASIBLE",
        3: "UNBOUNDED",
        4: "ABNORMAL",
        6: "NOT SOLVED",
    }
    return status_map.get(status, status)


def normalize_status(status, obj):
    status_text = str(status).upper() if status is not None else ""
    if status_text in {"OPTIMAL", "FEASIBLE", "NOT SOLVED"}:
        return status_text

    if obj is not None and status_text in {"OK", "TIME_LIMIT", "TIME_LIMIT_EXCEEDED"}:
        return "FEASIBLE"

    return "NOT SOLVED"


def run_solver(solver_name, solver_module, N, D, A, B, F, time_limit):
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            result = solver_module.solve(N, D, A, B, F, time_limit=time_limit)
        if result is None:
            return {"status": "NO_RESULT", "obj": None, "runtime": 0}
        if solver_name in CUSTOM_SOLVERS:
            result["status"] = normalize_status(result.get("status"), result.get("obj"))
        else:
            result["status"] = normalize_library_status(solver_name, result.get("status"))
        return result
    except Exception as exc:
        return {"status": "NOT SOLVED", "obj": None, "runtime": 0, "error": type(exc).__name__}


def main():
    logger = ExperimentLogger("results/final_report.csv")
    time_limit = 60

    test_files = glob.glob("data/**/*.txt", recursive=True)
    test_files.sort()

    for fpath in test_files:
        category = os.path.basename(os.path.dirname(fpath))
        fname = os.path.basename(fpath)
        print(f"\nRunning {category}/{fname}...")

        data = read_input(fpath)
        if not data:
            continue

        N, D, A, B, F = data

        for solver_name, solver_module in SOLVERS:
            print(f"  - {solver_name}")
            result = run_solver(solver_name, solver_module, N, D, A, B, F, time_limit)
            logger.log(
                f"{solver_name} ({category})",
                fname,
                N,
                D,
                result.get("status"),
                result.get("obj"),
                result.get("runtime", 0),
            )

    logger.save()


if __name__ == "__main__":
    main()
