from ortools.linear_solver import pywraplp
import time

def solve(N, D, A, B, F, time_limit=300):
    # Sử dụng SCIP backend cho bài toán MILP
    solver = pywraplp.Solver.CreateSolver('SCIP')
    if not solver:
        return {"status": "UNAVAILABLE", "obj": None, "runtime": 0}
        
    solver.SetTimeLimit(time_limit * 1000) # mili giây
    
    # Biến x[i, d, k]
    x = {}
    for i in range(1, N + 1):
        for d in range(1, D + 1):
            for k in range(4):
                x[i, d, k] = solver.IntVar(0, 1, f'x_{i}_{d}_{k}')
                
    # Ràng buộc 1: Tối đa 1 ca / ngày
    for i in range(1, N + 1):
        for d in range(1, D + 1):
            solver.Add(sum(x[i, d, k] for k in range(4)) <= 1)
            
    # Ràng buộc 2: Nghỉ sau ca đêm
    # x[i, d, 3] + sum(các ca ngày d+1) <= 1. 
    # Nếu x[i, d, 3] = 1 -> tổng các ca ngày d+1 phải = 0.
    for i in range(1, N + 1):
        for d in range(1, D):
            solver.Add(x[i, d, 3] + sum(x[i, d + 1, k] for k in range(4)) <= 1)
            
    # Ràng buộc 3: Nhân sự mỗi ca [A, B]
    for d in range(1, D + 1):
        for k in range(4):
            shift_workers = sum(x[i, d, k] for i in range(1, N + 1))
            solver.Add(shift_workers >= A)
            solver.Add(shift_workers <= B)
            
    # Ràng buộc 4: Nghỉ phép
    for i, off_days in F.items():
        for d in off_days:
            if 1 <= d <= D:
                for k in range(4):
                    solver.Add(x[i, d, k] == 0)
                    
    # Mục tiêu
    Z = solver.IntVar(0, D, 'Z')
    for i in range(1, N + 1):
        solver.Add(Z >= sum(x[i, d, 3] for d in range(1, D + 1)))
        
    solver.Minimize(Z)
    
    # Giải
    start_time = time.time()
    status = solver.Solve()
    runtime = time.time() - start_time
    
    # Trích xuất kết quả
    if status == pywraplp.Solver.OPTIMAL:
        status_str = "OPTIMAL"
        obj_val = solver.Objective().Value()
    elif status == pywraplp.Solver.FEASIBLE:
        status_str = "FEASIBLE"
        obj_val = solver.Objective().Value()
    elif status == pywraplp.Solver.INFEASIBLE:
        status_str = "INFEASIBLE"
        obj_val = None
    else:
        status_str = "TIMEOUT"
        obj_val = None
        
    return {
        "status": status_str,
        "obj": obj_val,
        "runtime": runtime
    }