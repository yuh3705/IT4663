from ortools.sat.python import cp_model
import time
import math

def solve(N, D, A, B, F, time_limit = 300):
    model = cp_model.CpModel()

    # x[i, d, k]: Nhân viên i làm ngày d ca k (0: nghỉ, 1: sáng, 2: trưa, 3: chiều, 4: đêm)
    x = {}
    for i in range(1, N + 1):
        for d in range(1, D + 1):
            if d in F[i]:
                x[i, d, 0] = model.NewConstant(1)
                for s in range(1, 5):
                    x[i, d, s] = model.NewConstant(0)
            else:
                for s in range(5):
                    x[i, d, s] = model.NewBoolVar(f'x_{i}_{d}_{s}')

    # Ràng buộc 1: Mỗi ngày một nhân viên làm nhiều nhất 1 ca
    for i in range(1, N + 1):
        for d in range(1, D + 1):
            model.Add(sum(x[i, d, s] for s in range(5)) == 1)

    # Ràng buộc 2: Trực đêm (k = 4) thì hôm sau (d + 1) được nghỉ
    for i in range(1, N + 1):
        for d in range(1, D):
            model.Add(x[i, d, 4] <= x[i, d + 1, 0])
             
    # Ràng buộc 3: Mỗi ca có ít nhất A và nhiều nhất B nhân viên
    for d in range(1, D + 1):
        for s in range(1, 5):
            total_staff_in_shift = sum(x[i, d, s] for i in range(1, N + 1))
            model.Add(total_staff_in_shift >= A)
            model.Add(total_staff_in_shift <= B)

    # Mục tiêu: Số ca đêm nhiều nhất phân cho 1 nhân viên là nhỏ nhất
    lower_bound = math.ceil((A * D) / N)
    
    # Khởi tạo max_night_shift với cận dưới là lower_bound thay vì số 0
    max_night_shifts = model.NewIntVar(lower_bound, D, 'max_night_shift')

    for i in range(1, N + 1):
        # max_night_shifts >= Tổng số ca đêm của nhân viên i
        night_shifts = sum(x[i, d, 4] for d in range(1, D + 1))
        model.Add(night_shifts <= max_night_shifts)

    model.Minimize(max_night_shifts)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit

    start_time = time.time()
    status = solver.Solve(model)
    runtime = time.time() - start_time

    # gap_time = solver.BestObjectiveBound() - solver.ObjectiveValue() if status == cp_model.INFEASIBLE else None

    status_str = solver.StatusName(status)
    obj_val = solver.ObjectiveValue() if status in [cp_model.OPTIMAL, cp_model.FEASIBLE] else None
    
    return {
        "status": status_str,
        "obj": obj_val,
        "runtime": runtime,
        # "gap_time": gap_time
    }


