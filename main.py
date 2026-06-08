import glob
import contextlib
import io
import os

from utils.data_loader import read_input
from utils.logger import ExperimentLogger
from solvers.logic_exact import cp_solver, scip_solver
from solvers.greedy import greedy_solver
from solvers.local_search import hill_climbing_solver, tabu_search_solver
from solvers.branch_bound import branch_bound_solver


SOLVERS = [
    ("CP-SAT", cp_solver),
    ("SCIP", scip_solver),
    ("Branch and Bound", branch_bound_solver),
    ("Greedy", greedy_solver),
    ("Hill Climbing", hill_climbing_solver),
    ("Tabu Search", tabu_search_solver),
]

CUSTOM_SOLVERS = {
    "Branch and Bound",
    "Greedy",
    "Hill Climbing",
    "Tabu Search",
    "ANLS",
}


def normalize_library_status(solver_name, status):
    if solver_name != "SCIP":
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
    except RecursionError:
        return {"status": "RECURSION_ERROR", "obj": None, "runtime": None, "schedule": None}
    except Exception as exc:
        return {"status": "NOT SOLVED", "obj": None, "runtime": 0, "error": type(exc).__name__}


def main():
    logger = ExperimentLogger()
    TIME_LIMIT = 600 
    
    # Dùng recursive=True để tìm tất cả file .txt trong mọi thư mục con của data/
    test_files = glob.glob("data/stress/*.txt", recursive=True)
    # test_files = ["/Users/binhminh/Desktop/IT4663 PRJ/IT4663/data/stress/test_9.txt", "/Users/binhminh/Desktop/IT4663 PRJ/IT4663/data/stress/test_8.txt"]
    test_files.sort() # Sắp xếp để chạy từ easy đến stress

    for fpath in test_files:
        category = os.path.basename(os.path.dirname(fpath))
        fname = os.path.basename(fpath)
        print(f"\nRunning {category}/{fname}...")

        data = read_input(fpath)
        if not data:
            continue

        N, D, A, B, F = data
        
        # # Chạy CP-SAT
        # res_cp = cp_solver.solve(N, D, A, B, F, time_limit=TIME_LIMIT)
        # logger.log(f"CP-SAT ({category})", fname, N, D, res_cp['status'], res_cp['obj'], res_cp['runtime'])
        
        # # Chạy SCIP
        # res_scip = scip_solver.solve(N, D, A, B, F, time_limit=TIME_LIMIT)
        # logger.log(f"SCIP ({category})", fname, N, D, res_scip['status'], res_scip['obj'], res_scip['runtime'])

        # res_greedy = greedy_solver.solve(N, D, A, B, F, time_limit=TIME_LIMIT)
        # logger.log(f"Greedy ({category})", fname, N, D, res_greedy['status'], res_greedy['obj'], res_greedy['runtime'])

        #branch_bound
        # res_bb = run_solver("Branch and Bound", branch_bound_solver, N, D, A, B, F, TIME_LIMIT)
        # logger.log(f"Branch and Bound ({category})", fname, N, D, res_bb['status'], res_bb['obj'], res_bb['runtime'])

        res_hill = hill_climbing_solver.solve(N, D, A, B, F, time_limit=TIME_LIMIT)
        logger.log(f"Hill Climbing ({category})", fname, N, D, res_hill['status'], res_hill['obj'], res_hill['runtime'])

        res_tabu = tabu_search_solver.solve(N, D, A, B, F, time_limit=TIME_LIMIT)
        logger.log(f"Tabu Search ({category})", fname, N, D, res_tabu['status'], res_tabu['obj'], res_tabu['runtime'])

    logger.save()

if __name__ == "__main__":
    main()
