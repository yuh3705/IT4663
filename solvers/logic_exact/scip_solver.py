import math
import time

from ortools.linear_solver import pywraplp


def solve(N, D, A, B, F, time_limit=300):
    solver = pywraplp.Solver.CreateSolver("SCIP")
    if not solver:
        print("Khong the khoi tao bo giai SCIP.")
        return

    F_set = {i: set(F[i]) for i in range(1, N + 1)}

    x = {}
    for i in range(1, N + 1):
        for d in range(1, D + 1):
            if d in F_set[i]:
                x[i, d, 0] = solver.IntVar(1, 1, f"x_{i}_{d}_0")
                for s in range(1, 5):
                    x[i, d, s] = solver.IntVar(0, 0, f"x_{i}_{d}_{s}")
            else:
                for s in range(5):
                    x[i, d, s] = solver.IntVar(0, 1, f"x_{i}_{d}_{s}")

    for i in range(1, N + 1):
        for d in range(1, D + 1):
            solver.Add(sum(x[i, d, s] for s in range(5)) == 1)

    for i in range(1, N + 1):
        for d in range(1, D):
            solver.Add(x[i, d, 4] <= x[i, d + 1, 0])

    for d in range(1, D + 1):
        for s in range(1, 5):
            total_staff = sum(x[i, d, s] for i in range(1, N + 1))
            solver.Add(total_staff >= A)
            solver.Add(total_staff <= B)

    lower_bound = math.ceil((A * D) / N)
    max_night_shift = solver.IntVar(lower_bound, D, "max_night_shift")

    for i in range(1, N + 1):
        total_night_shift_i = sum(x[i, d, 4] for d in range(1, D + 1))
        solver.Add(max_night_shift >= total_night_shift_i)

    solver.Minimize(max_night_shift)
    solver.set_time_limit(time_limit * 1000)

    start_time = time.time()
    status = solver.Solve()
    runtime = time.time() - start_time

    if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE:
        for i in range(1, N + 1):
            row_result = []
            for d in range(1, D + 1):
                for s in range(5):
                    if x[i, d, s].solution_value() > 0.5:
                        row_result.append(str(s))
                        break
            print(" ".join(row_result))
    else:
        print("Khong tim thay phuong an xep ca hop le.")

    obj_val = (
        solver.Objective().Value()
        if status in [pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE]
        else None
    )

    return {
        "status": status,
        "obj": obj_val,
        "runtime": runtime,
    }
