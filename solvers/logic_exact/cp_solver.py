from ortools.sat.python import cp_model
import time

def solve(N, D, A, B, F, time_limit = 300):
    model = cp_model.CpModel()

    # x[i, d, k]: Nhân viên i làm ngày d ca k (0: sáng, 1: trưa, 2: chiều, 3: đêm)
    x = {}
    for i in range(1, N + 1):
        for d in range(D + 1):
            for k in range(4):
                x[i, d, k] = model.NewBoolVar(f'x_{i}_{d}_{k}')

    # Ràng buộc 1: Mỗi ngày một nhân viên làm nhiều nhất 1 ca
    for i in range(1, N + 1):
        for d in range(D + 1):
            model.Add(sum(x[i, d, k] for k in range(4)) <= 1)

    # Ràng buộc 2: Trực đêm (k=3) thì hôm sau (d+1) được nghỉ
    for i in range(1, N + 1):
        for d in range(D):
            model.Add(x[i, d, 3] + sum(x[i, d + 1, k] for k in range(4)) <= 1)

    # Ràng buộc 3: Mỗi ca có ít nhất A và nhiều nhất B nhân viên
    for d in range(D + 1):
        for k in range(4):
            shift_workers = sum(x[i, d, k] for i in range(1, N + 1))
            model.Add(shift_workers >= A)
            model.Add(shift_workers <= B)

    # Ràng buộc 4: F(i) danh sách ngày nghỉ phép
    for i, off_days in F.items():
        for d in off_days:
            if 1 <= d <= D:
                for k in range(4):
                    model.Add(x[i, d, k] == 0)

    # Mục tiêu: Số ca đêm nhiều nhất phân cho 1 nhân viên là nhỏ nhất
    max_night_shifts = model.NewIntVar(0, D, 'max_night_shifts')
    for i in range(1, N + 1):
        # max_night_shifts >= Tổng số ca đêm của nhân viên i
        night_shifts = sum(x[i, d, 3] for d in range(1, D + 1))
        model.Add(night_shifts <= max_night_shifts)

    model.Minimize(max_night_shifts)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit

    start_time = time.time()
    status = solver.Solve(model)
    runtime = time.time() - start_time

    status_str = solver.StatusName(status)
    obj_val = solver.ObjectiveValue() if status in [cp_model.OPTIMAL, cp_model.FEASIBLE] else None
    
    return {
        "status": status_str,
        "obj": obj_val,
        "runtime": runtime
    }
