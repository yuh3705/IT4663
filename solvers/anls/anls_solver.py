import random
import time
import math

PENALTY_HARD = 1000000

def solve(N, D, A, B, days_off, time_limit=30):
    start_t = time.time()

    F = [[False] * D for _ in range(N + 1)]
    for i in range(1, N + 1):
        if i in days_off:
            for day in days_off[i]:
                d = int(day) - 1
                if 0 <= d < D:
                    F[i][d] = True

    # ============================================================
    # COST FUNCTION
    # ============================================================
    def calc_cost(X):
        night_count = [0] * (N + 1)
        penalty = 0
        
        for i in range(1, N + 1):
            for d in range(D):
                s = X[i][d]
                if s == 4:
                    night_count[i] += 1
                if s != 0 and F[i][d]:
                    penalty += PENALTY_HARD
                if s == 4 and d + 1 < D and X[i][d + 1] != 0:
                    penalty += PENALTY_HARD

        for d in range(D):
            shift_count = [0] * 5
            for i in range(1, N + 1):
                shift_count[X[i][d]] += 1
            for s in range(1, 5):
                if shift_count[s] < A:
                    penalty += (A - shift_count[s]) * PENALTY_HARD
                if shift_count[s] > B:
                    penalty += (shift_count[s] - B) * PENALTY_HARD

        max_night = max(night_count[1:]) if N > 0 else 0
        sum_sq = sum(c * c for c in night_count[1:])
        
        cost_score = penalty + (max_night * 10000) + sum_sq
        return cost_score, night_count

    # ============================================================
    # LNS REPAIR OPERATOR (Vẫn giữ Greedy để định hướng tìm kiếm)
    # ============================================================
    def repair_day(d, current_X, current_night, add_noise=True):
        shifts = [4, 1, 2, 3]
        for s in shifts:
            candidates = []
            for i in range(1, N + 1):
                if current_X[i][d] != 0: continue 
                if F[i][d]: continue              
                if d > 0 and current_X[i][d - 1] == 4: continue 
                if s == 4 and d + 1 < D and current_X[i][d + 1] != 0: continue 
                candidates.append(i)
            
            if len(candidates) < A:
                return False 
            
            candidates.sort(key=lambda x: current_night[x] * 100 + (random.randint(0, 50) if add_noise else 0))
            
            for k in range(A):
                emp = candidates[k]
                current_X[emp][d] = s
                if s == 4:
                    current_night[emp] += 1
        return True

    # ============================================================
    # 1. INITIALIZATION: PURE RANDOM
    # ============================================================
    X = [[0] * D for _ in range(N + 1)]
    current_night = [0] * (N + 1)
    
    for d in range(D):
        shifts = [4, 1, 2, 3]
        for s in shifts:
            candidates = []
            for i in range(1, N + 1):
                # Chỉ lọc sơ bộ những người chưa có ca hôm nay
                if X[i][d] == 0:
                    candidates.append(i)
            
            # CHỌN NGẪU NHIÊN hoàn toàn, không quan tâm luật ca đêm hay số lượng ca
            if len(candidates) >= A:
                chosen = random.sample(candidates, A)
            else:
                chosen = candidates
                
            for emp in chosen:
                X[emp][d] = s
                if s == 4:
                    current_night[emp] += 1

    current_cost, current_night = calc_cost(X)
    best_X = [row[:] for row in X]
    best_cost = current_cost
    
    print(f"--- STARTING ---")
    print(f"[Init] Random Score = {best_cost} (Penalty is massive!)")
    print(f"----------------")

    T = 5000.0      
    alpha = 0.9995     
    iters = 0

    while time.time() - start_t < time_limit and T > 0.01:
        iters += 1
        
        temp_X = [row[:] for row in X]
        temp_night = list(current_night)
        
        # DESTROY: Do ban đầu sai quá nhiều, ta mạnh tay phá 1 lúc 2-5 ngày
        d1 = random.randint(0, D - 1)
        length = random.randint(2, 5)
        d2 = min(D - 1, d1 + length - 1)
        
        for d in range(d1, d2 + 1):
            for i in range(1, N + 1):
                if temp_X[i][d] == 4:
                    temp_night[i] -= 1
                temp_X[i][d] = 0
                
        # REPAIR
        valid_repair = True
        for d in range(d1, d2 + 1):
            if not repair_day(d, temp_X, temp_night, add_noise=True):
                valid_repair = False
                break
                
        # SA ACCEPTANCE
        if valid_repair:
            new_cost, new_night = calc_cost(temp_X)
            
            if new_cost < current_cost or math.exp((current_cost - new_cost) / T) > random.random():
                X = temp_X
                current_cost = new_cost
                current_night = new_night
                
                if new_cost < best_cost:
                    best_cost = new_cost
                    best_X = [row[:] for row in X]
        
        T *= alpha

        # DEBUG: Theo dõi sự "thoát xác" từ INFEASIBLE sang OK
        if iters % 1000 == 0:
            curr_max_night = max(current_night[1:]) if N > 0 else 0
            _, best_nights = calc_cost(best_X)
            best_max_night = max(best_nights[1:]) if N > 0 else 0
            
            print(f"Iter {iters:5d} | Temp: {T:>8.0f} | "
                  f"Curr Cost: {current_cost:<8d} | "
                  f"Best Cost: {best_cost:<8d} (Max Night: {best_max_night})")

    # ============================================================
    # KẾT QUẢ ĐẦU RA
    # ============================================================
    _, final_nights = calc_cost(best_X)
    true_max_night = max(final_nights[1:]) if N > 0 else 0
    status = "OK" if best_cost < PENALTY_HARD else "INFEASIBLE"

    print(f"\nFinished | Total Iters = {iters} | Status = {status} | Final Score = {best_cost} | Max Night = {true_max_night}")

    return {
        "status": status,
        "obj": true_max_night if status == "OK" else best_cost,
        "matrix": best_X[1:], 
        "runtime": time.time() - start_t
    }