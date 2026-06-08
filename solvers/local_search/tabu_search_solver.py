import math
import random
import time
import sys

SHIFT_COUNT = 4
NIGHT_SHIFT = 3  # Lưu ý: Ở file này ca đêm của bạn đánh số từ 0..3 nên ca đêm là kíp số 3


def _empty_schedule(N, D):
    return {(i, d): None for i in range(1, N + 1) for d in range(1, D + 1)}


def _build_shift_members(schedule, N, D):
    members = {(d, k): set() for d in range(1, D + 1) for k in range(SHIFT_COUNT)}
    for i in range(1, N + 1):
        for d in range(1, D + 1):
            shift = schedule[i, d]
            if shift is not None:
                members[d, shift].add(i)
    return members


def _night_counts(schedule, N, D):
    return {
        i: sum(1 for d in range(1, D + 1) if schedule[i, d] == NIGHT_SHIFT)
        for i in range(1, N + 1)
    }


def _can_work(schedule, i, d, shift, D, F):
    if d in F.get(i, []):
        return False
    if d > 1 and schedule[i, d - 1] == NIGHT_SHIFT:
        return False
    if shift == NIGHT_SHIFT and d < D and schedule[i, d + 1] is not None:
        return False
    return True


# =========================================================================
# THAY ĐỔI LỚN: HÀM KHỞI TẠO NGẪU NHIÊN HOÀN TOÀN (PURE RANDOM CONSTRUCT)
# =========================================================================
def _construct_random_initial_solution(N, D, A, B, F, rng):
    if A > B or SHIFT_COUNT * A > N:
        return None

    schedule = _empty_schedule(N, D)

    for d in range(1, D + 1):
        # Lấy danh sách các kíp trực {0, 1, 2, 3}
        shifts = list(range(SHIFT_COUNT))
        # Xáo trộn thứ tự gán kíp ngẫu nhiên
        rng.shuffle(shifts)

        for shift in shifts:
            # Tìm nhân viên chưa có ca ngày d và đủ điều kiện làm kíp này
            candidates = [
                i for i in range(1, N + 1)
                if schedule[i, d] is None and _can_work(schedule, i, d, shift, D, F)
            ]
            
            # Nếu không đủ số người tối thiểu A -> Thất bại, cần restart
            if len(candidates) < A:
                return None
            
            # Bốc ngẫu nhiên hoàn toàn A người từ tập ứng viên hợp lệ
            chosen_staff = rng.sample(candidates, A)
            for i in chosen_staff:
                schedule[i, d] = shift

    # Kiểm tra ràng buộc toàn cục (bao gồm cả cận tối đa B)
    return schedule if _validate(schedule, N, D, A, B, F) else None


def _build_initial_solution(N, D, A, B, F, rng, start_time, time_limit, max_restarts=1000):
    if time.time() - start_time >= time_limit:
        return None

    return _construct_random_initial_solution(N, D, A, B, F, rng)
# =========================================================================


def _validate(schedule, N, D, A, B, F):
    for i in range(1, N + 1):
        for d in range(1, D + 1):
            shift = schedule[i, d]
            if shift is None:
                continue
            if shift < 0 or shift >= SHIFT_COUNT:
                return False
            if d in F.get(i, []):
                return False
            if d > 1 and schedule[i, d - 1] == NIGHT_SHIFT:
                return False

    members = _build_shift_members(schedule, N, D)
    for d in range(1, D + 1):
        for shift in range(SHIFT_COUNT):
            count = len(members[d, shift])
            if count < A or count > B:
                return False
    return True


def _objective(schedule, N, D):
    return max(_night_counts(schedule, N, D).values()) if N > 0 else 0


def _apply_swap(schedule, move):
    i, j, d = move
    schedule[i, d], schedule[j, d] = schedule[j, d], schedule[i, d]


def _is_swap_valid(schedule, move, D, F):
    i, j, d = move
    shift_i = schedule[i, d]
    shift_j = schedule[j, d]

    schedule[i, d], schedule[j, d] = None, None
    ok = True
    if shift_j is not None:
        ok = ok and _can_work(schedule, i, d, shift_j, D, F)
    if shift_i is not None:
        ok = ok and _can_work(schedule, j, d, shift_i, D, F)
    schedule[i, d], schedule[j, d] = shift_i, shift_j
    return ok

def _candidate_moves_improved(schedule, N, D, night_count, rng, sample_size=40):
    """
    Mở rộng tập lân cận: kết hợp giữa cứu người overload và swap ngẫu nhiên 
    để tăng tính đa dạng, tránh kẹt local optima.
    """
    moves = []
    max_nights = max(night_count.values())
    overloaded = [i for i, count in night_count.items() if count == max_nights]
    
    # 1. Ưu tiên các nước đi giảm tải cho người bận nhất
    for i in overloaded:
        night_days = [d for d in range(1, D + 1) if schedule[i, d] == NIGHT_SHIFT]
        for d in night_days:
            candidates = [j for j in range(1, N + 1) if j != i and schedule[j, d] != NIGHT_SHIFT]
            rng.shuffle(candidates)
            for j in candidates[:15]: 
                moves.append((i, j, d))
                
    # 2. Thêm một số nước đi ngẫu nhiên hoàn toàn để tăng tính đa dạng
    all_days = list(range(1, D + 1))
    rng.shuffle(all_days)
    for d in all_days[:5]:
        for _ in range(15):
            i = rng.randint(1, N)
            j = rng.randint(1, N)
            if i != j and schedule[i, d] != schedule[j, d]:
                moves.append((i, j, d))

    rng.shuffle(moves)
    return moves[:sample_size]


def _construct_relaxed_initial_solution(N, D, A, rng):
    schedule = _empty_schedule(N, D)

    for d in range(1, D + 1):
        staff = list(range(1, N + 1))
        rng.shuffle(staff)
        cursor = 0

        for shift in range(SHIFT_COUNT):
            for i in staff[cursor:cursor + A]:
                schedule[i, d] = shift
            cursor += A

    return schedule


def _constraint_violations(schedule, N, D, A, B, F):
    violations = 0

    for i in range(1, N + 1):
        for d in range(1, D + 1):
            shift = schedule[i, d]
            if shift is None:
                continue
            if shift < 0 or shift >= SHIFT_COUNT:
                violations += 1
            if d in F.get(i, []):
                violations += 1
            if d > 1 and schedule[i, d - 1] == NIGHT_SHIFT:
                violations += 1

    members = _build_shift_members(schedule, N, D)
    for d in range(1, D + 1):
        for shift in range(SHIFT_COUNT):
            count = len(members[d, shift])
            if count < A:
                violations += A - count
            elif count > B:
                violations += count - B

    return violations


def _score(schedule, N, D, A, B, F):
    return (_constraint_violations(schedule, N, D, A, B, F), _objective(schedule, N, D))


def _is_better_score(score, best_score):
    return best_score is None or score < best_score


def _violating_staff_days(schedule, N, D, F):
    targets = set()

    for i in range(1, N + 1):
        for d in range(1, D + 1):
            if schedule[i, d] is None:
                continue
            if d in F.get(i, []):
                targets.add((i, d))
            if d > 1 and schedule[i, d - 1] == NIGHT_SHIFT:
                targets.add((i, d))

    return list(targets)


def _candidate_repair_moves(schedule, N, D, F, rng, sample_size=120):
    moves = []
    targets = _violating_staff_days(schedule, N, D, F)
    rng.shuffle(targets)

    for i, d in targets[:sample_size]:
        candidates = list(range(1, N + 1))
        rng.shuffle(candidates)
        for j in candidates[:30]:
            if i != j and schedule[i, d] != schedule[j, d]:
                moves.append((i, j, d))

    all_days = list(range(1, D + 1))
    rng.shuffle(all_days)
    for d in all_days[:max(1, min(D, 10))]:
        for _ in range(sample_size // 2):
            i = rng.randint(1, N)
            j = rng.randint(1, N)
            if i != j and schedule[i, d] != schedule[j, d]:
                moves.append((i, j, d))

    rng.shuffle(moves)
    return moves[:sample_size]


def _assignment_penalty(schedule, i, d, shift, D, F):
    penalty = 0
    if d in F.get(i, []):
        penalty += 1
    if d > 1 and schedule[i, d - 1] == NIGHT_SHIFT:
        penalty += 1
    if shift == NIGHT_SHIFT and d < D and schedule[i, d + 1] is not None:
        penalty += 1
    return penalty


def _build_repaired_day(schedule, N, D, A, F, d, rng):
    new_day = {i: None for i in range(1, N + 1)}
    assigned = set()
    shifts = list(range(SHIFT_COUNT))
    rng.shuffle(shifts)

    for shift in shifts:
        candidates = [i for i in range(1, N + 1) if i not in assigned]
        rng.shuffle(candidates)
        candidates.sort(key=lambda i: (_assignment_penalty(schedule, i, d, shift, D, F), i))

        chosen = candidates[:A]
        if len(chosen) < A:
            return None

        for i in chosen:
            new_day[i] = shift
            assigned.add(i)

    return new_day


def _apply_rebuilt_day(schedule, new_day, d):
    old_day = {i: schedule[i, d] for i in new_day}
    for i, shift in new_day.items():
        schedule[i, d] = shift
    return old_day


def _restore_day(schedule, old_day, d):
    for i, shift in old_day.items():
        schedule[i, d] = shift


def _repair_actions(schedule, N, D, A, F, rng, sample_size=120):
    actions = [("swap", move) for move in _candidate_repair_moves(schedule, N, D, F, rng, sample_size)]
    targets = _violating_staff_days(schedule, N, D, F)
    target_days = list({d for _, d in targets})
    rng.shuffle(target_days)

    for d in target_days[:8]:
        new_day = _build_repaired_day(schedule, N, D, A, F, d, rng)
        if new_day is not None:
            actions.append(("rebuild_day", (d, new_day)))

    return actions


def _solve_feasible_only(N, D, A, B, F, time_limit=60, max_iterations=20000, tabu_tenure=30, seed=42):
    start_time = time.time()
    rng = random.Random(seed)

    if A > B or 4 * A > N:
        return {"status": "INFEASIBLE", "obj": None, "runtime": time.time() - start_time, "schedule": None, "history": []}

    current = _build_initial_solution(N, D, A, B, F, rng, start_time, time_limit, max_restarts=2000)

    if current is None or not _validate(current, N, D, A, B, F):
        return {"status": "NO_FEASIBLE_SOLUTION", "obj": None, "runtime": time.time() - start_time, "schedule": None, "history": []}

    best = current.copy()
    best_obj = _objective(best, N, D)
    current_obj = best_obj
    lower_bound = math.ceil(D * A / N)
    
    tabu_until = {} # Lưu cặp: ((person, day, shift), iteration)
    iteration = 0
    history = [current_obj]
    
    stable_iterations = 0
    max_stable = 300  # Nếu sau 300 vòng không giảm được best_obj -> Thực hiện Diversification

    if best_obj == lower_bound:
        return {"status": "OPTIMAL", "obj": best_obj, "runtime": time.time() - start_time, "schedule": best, "history": history}

    while iteration < max_iterations and time.time() - start_time < time_limit:
        iteration += 1
        stable_iterations += 1
        
        # --- CƠ CHẾ DIVERSIFICATION (NẾU BỊ KẸT QUÁ LÂU) ---
        if stable_iterations > max_stable:
            # Khởi tạo lại một nghiệm ngẫu nhiên mới hoàn toàn để thoát hố
            new_start = _build_initial_solution(N, D, A, B, F, rng, start_time, time_limit, max_restarts=500)
            if new_start is not None:
                current = new_start
                current_obj = _objective(current, N, D)
                tabu_until.clear() # Xóa lịch sử tabu cũ
                stable_iterations = 0
                continue

        night_count = _night_counts(current, N, D)
        moves = _candidate_moves_improved(current, N, D, night_count, rng, sample_size=50)

        best_move = None
        best_move_obj = float('inf')

        for move in moves:
            if not _is_swap_valid(current, move, D, F):
                continue

            i, j, d = move
            shift_i = current[i, d]
            shift_j = current[j, d]

            # Thử nghiệm đi trước để tính Obj
            _apply_swap(current, move)
            obj = _objective(current, N, D)
            _apply_swap(current, move) # Trả về trạng thái cũ

            # Kiểm tra Tabu: Cấm cả i và j quay lại kíp cũ tại ngày d
            is_tabu = (tabu_until.get((i, d, shift_i), 0) > iteration or 
                       tabu_until.get((j, d, shift_j), 0) > iteration)
            
            # Aspiration Criterion: Nếu nước đi cực tốt (phá kỷ lục) thì bỏ qua Tabu
            if is_tabu and obj < best_obj:
                is_tabu = False 

            if not is_tabu:
                # Chọn nước đi tối ưu nhất trong tập lân cận (kể cả khi obj > current_obj)
                if obj < best_move_obj:
                    best_move = move
                    best_move_obj = obj

        # Nếu thực sự bế tắc không tìm được move nào hợp lệ 
        if best_move is None:
            stable_iterations = max_stable + 1 # Kích hoạt Đa dạng hóa ở vòng sau
            continue

        # Áp dụng nước đi tốt nhất tìm được
        i, j, d = best_move
        shift_i = current[i, d]
        shift_j = current[j, d]
        
        _apply_swap(current, best_move)
        current_obj = best_move_obj
        history.append(current_obj)

        # Ghi vào danh sách Tabu: Cấm i nhận lại shift_i, j nhận lại shift_j tại ngày d
        tabu_until[(i, d, shift_i)] = iteration + tabu_tenure
        tabu_until[(j, d, shift_j)] = iteration + tabu_tenure

        # Cập nhật Kỷ lục
        if current_obj < best_obj:
            best = current.copy()
            best_obj = current_obj
            stable_iterations = 0 # Reset bộ đếm ổn định
            if best_obj == lower_bound:
                break

    return {
        "status": "OPTIMAL" if best_obj == lower_bound else "HEURISTIC",
        "obj": best_obj,
        "runtime": time.time() - start_time,
        "schedule": best,
        "history": history
    }


def solve(N, D, A, B, F, time_limit=60, max_iterations=20000, tabu_tenure=30, seed=42):
    start_time = time.time()
    rng = random.Random(seed)

    if A > B or SHIFT_COUNT * A > N:
        return {
            "status": "INFEASIBLE",
            "obj": None,
            "runtime": time.time() - start_time,
            "schedule": None,
            "history": [],
            "violation_history": [],
        }

    lower_bound = math.ceil(D * A / N)

    current = _build_initial_solution(
        N, D, A, B, F, rng, start_time, min(time_limit, 1), max_restarts=200
    )
    if current is None:
        current = _construct_relaxed_initial_solution(N, D, A, rng)

    current_score = _score(current, N, D, A, B, F)
    best_score = current_score
    best_any = current.copy()
    best_feasible = current.copy() if current_score[0] == 0 else None
    best_feasible_obj = current_score[1] if current_score[0] == 0 else None

    tabu_until = {}
    history = [current_score[1]]
    violation_history = [current_score[0]]
    stable_iterations = 0
    max_stable = 500
    best_restart_score = current_score

    iteration = 0
    while iteration < max_iterations and time.time() - start_time < time_limit:
        if best_feasible_obj == lower_bound:
            break

        iteration += 1
        stable_iterations += 1

        if stable_iterations > max_stable:
            current = _construct_relaxed_initial_solution(N, D, A, rng)
            current_score = _score(current, N, D, A, B, F)
            best_restart_score = current_score
            tabu_until.clear()
            stable_iterations = 0

        if current_score[0] == 0:
            night_count = _night_counts(current, N, D)
            actions = [("swap", move) for move in _candidate_moves_improved(current, N, D, night_count, rng, sample_size=80)]
        else:
            actions = _repair_actions(current, N, D, A, F, rng, sample_size=60)

        if not actions:
            actions = _repair_actions(current, N, D, A, F, rng, sample_size=60)

        chosen_action = None
        chosen_score = None
        fallback_action = None
        fallback_score = None

        for action_type, payload in actions:
            if current_score[0] == 0 and action_type == "swap" and not _is_swap_valid(current, payload, D, F):
                continue

            if action_type == "swap":
                i, j, d = payload
                shift_i = current[i, d]
                shift_j = current[j, d]
                _apply_swap(current, payload)
                undo_data = ("swap", payload)
                tabu_keys = [(i, d, shift_i), (j, d, shift_j)]
            else:
                d, new_day = payload
                old_day = _apply_rebuilt_day(current, new_day, d)
                undo_data = ("rebuild_day", (d, old_day))
                tabu_keys = [("rebuild_day", d, None)]

            if current_score[0] == 0:
                move_score = (0, _objective(current, N, D))
            else:
                move_score = _score(current, N, D, A, B, F)

            if undo_data[0] == "swap":
                _apply_swap(current, undo_data[1])
            else:
                _, (d, old_day) = undo_data
                _restore_day(current, old_day, d)

            is_tabu = any(tabu_until.get(key, 0) > iteration for key in tabu_keys)
            if is_tabu and move_score < best_score:
                is_tabu = False

            if _is_better_score(move_score, fallback_score):
                fallback_action = (action_type, payload, tabu_keys)
                fallback_score = move_score

            if not is_tabu and _is_better_score(move_score, chosen_score):
                chosen_action = (action_type, payload, tabu_keys)
                chosen_score = move_score

        if chosen_action is None:
            chosen_action = fallback_action
            chosen_score = fallback_score

        if chosen_action is None:
            stable_iterations = max_stable + 1
            continue
        action_type, payload, tabu_keys = chosen_action

        if action_type == "swap":
            _apply_swap(current, payload)
        else:
            d, new_day = payload
            _apply_rebuilt_day(current, new_day, d)
        current_score = chosen_score
        history.append(current_score[1])
        violation_history.append(current_score[0])

        for key in tabu_keys:
            tabu_until[key] = iteration + tabu_tenure

        if current_score < best_restart_score:
            best_restart_score = current_score
            if current_score < best_score:
                best_score = current_score
                best_any = current.copy()
            stable_iterations = 0

        if current_score[0] == 0:
            if best_feasible is None or current_score[1] < best_feasible_obj:
                best_feasible = current.copy()
                best_feasible_obj = current_score[1]
                stable_iterations = 0

    runtime = time.time() - start_time
    if best_feasible is None:
        return {
            "status": "NO_FEASIBLE_SOLUTION",
            "obj": None,
            "runtime": runtime,
            "schedule": None,
            "history": history,
            "violation_history": violation_history,
            "best_violation_count": best_score[0],
            "best_relaxed_schedule": best_any,
        }

    return {
        "status": "OPTIMAL" if best_feasible_obj == lower_bound else "FEASIBLE",
        "obj": best_feasible_obj,
        "runtime": runtime,
        "schedule": best_feasible,
        "history": history,
        "violation_history": violation_history,
    }


def _read_input_from_stdin():
    first_line = sys.stdin.readline().strip()
    if not first_line:
        return None

    N, D, A, B = map(int, first_line.split())
    days_off = {}

    for i in range(1, N + 1):
        parts = list(map(int, sys.stdin.readline().split()))
        days_off[i] = [day for day in parts if day != -1]

    return N, D, A, B, days_off


def main():
    time_limit = 60
    data = _read_input_from_stdin()
    if not data:
        return

    N, D, A, B, F = data
    result = solve(N, D, A, B, F, time_limit=time_limit)
    schedule = result["schedule"]
    if schedule is None:
        print("NO_SOLUTION")
        return

    for i in range(1, N + 1):
        row = []
        for d in range(1, D + 1):
            shift = schedule[i, d]
            row.append("0" if shift is None else str(shift + 1))
        print(" ".join(row))


if __name__ == "__main__":
    main()

