# import random
# import sys
# import time


# SHIFT_COUNT = 4
# NIGHT_SHIFT = 4


# def _empty_schedule(N, D):
#     return {(i, d): 0 for i in range(1, N + 1) for d in range(1, D + 1)}


# def _night_counts(schedule, N, D):
#     return {
#         i: sum(1 for d in range(1, D + 1) if schedule[i, d] == NIGHT_SHIFT)
#         for i in range(1, N + 1)
#     }


# def _objective(schedule, N, D):
#     counts = _night_counts(schedule, N, D)
#     return max(counts.values()) if counts else 0


# def _score(night_count):
#     return tuple(sorted(night_count.values(), reverse=True))


# def _can_assign(schedule, i, d, shift, D, F):
#     if shift == 0:
#         return True
#     if d in F.get(i, []):
#         return False
#     if d > 1 and schedule[i, d - 1] == NIGHT_SHIFT:
#         return False
#     if shift == NIGHT_SHIFT and d < D and schedule[i, d + 1] != 0:
#         return False
#     return True


# def _future_capacity_after_night(schedule, i, d, N, D, F):
#     if d >= D:
#         return 0

#     unavailable = 1
#     for staff in range(1, N + 1):
#         if staff == i:
#             continue
#         if d + 1 in F.get(staff, []):
#             unavailable += 1
#         elif schedule[staff, d] == NIGHT_SHIFT:
#             unavailable += 1
#     return N - unavailable


# def _ordered_candidates(schedule, candidates, shift, d, N, D, F, night_count, work_count):
#     if shift == NIGHT_SHIFT:
#         return sorted(
#             candidates,
#             key=lambda i: (
#                 night_count[i],
#                 work_count[i],
#                 -_future_capacity_after_night(schedule, i, d, N, D, F),
#                 len(F.get(i, [])),
#                 i,
#             ),
#         )

#     return sorted(candidates, key=lambda i: (work_count[i], night_count[i], len(F.get(i, [])), i))


# def _pick_candidates(candidates, A, rng, randomized):
#     if not randomized:
#         return candidates[:A]

#     pool_size = min(len(candidates), max(A, 3 * A))
#     return rng.sample(candidates[:pool_size], A)


# def _construct_initial_solution(N, D, A, B, F, rng, randomized, reverse_days=False):
#     if A > B or SHIFT_COUNT * A > N:
#         return None

#     schedule = _empty_schedule(N, D)
#     night_count = {i: 0 for i in range(1, N + 1)}
#     work_count = {i: 0 for i in range(1, N + 1)}

#     day_range = range(D, 0, -1) if reverse_days else range(1, D + 1)
#     for d in day_range:
#         remaining_shifts = {1, 2, 3, NIGHT_SHIFT}

#         while remaining_shifts:
#             options = []
#             for shift in remaining_shifts:
#                 candidates = [
#                     i for i in range(1, N + 1)
#                     if _can_assign(schedule, i, d, shift, D, F) and schedule[i, d] == 0
#                 ]
#                 if len(candidates) < A:
#                     return None
#                 options.append((len(candidates), 0 if shift == NIGHT_SHIFT else 1, shift, candidates))

#             _, _, shift, candidates = min(options)
#             candidates = _ordered_candidates(schedule, candidates, shift, d, N, D, F, night_count, work_count)
#             for i in _pick_candidates(candidates, A, rng, randomized):
#                 schedule[i, d] = shift
#                 work_count[i] += 1
#                 if shift == NIGHT_SHIFT:
#                     night_count[i] += 1

#             remaining_shifts.remove(shift)

#     return schedule if _validate(schedule, N, D, A, B, F) else None


# def _build_initial_solution(N, D, A, B, F, rng, start_time, time_limit, max_restarts):
#     for attempt in range(max_restarts):
#         if time.time() - start_time >= time_limit:
#             break

#         schedule = _construct_initial_solution(
#             N, D, A, B, F, rng,
#             randomized=attempt > 1,
#             reverse_days=attempt % 2 == 1,
#         )
#         if schedule is not None:
#             return schedule

#     return None


# def _validate(schedule, N, D, A, B, F):
#     for i in range(1, N + 1):
#         for d in range(1, D + 1):
#             shift = schedule[i, d]
#             if shift == 0:
#                 continue
#             if shift < 1 or shift > SHIFT_COUNT:
#                 return False
#             if d in F.get(i, []):
#                 return False
#             if d > 1 and schedule[i, d - 1] == NIGHT_SHIFT:
#                 return False

#     for d in range(1, D + 1):
#         for shift in range(1, SHIFT_COUNT + 1):
#             count = sum(1 for i in range(1, N + 1) if schedule[i, d] == shift)
#             if count < A or count > B:
#                 return False
#     return True


# def _is_swap_valid(schedule, i, j, d, D, F):
#     shift_i = schedule[i, d]
#     shift_j = schedule[j, d]
#     if shift_i == shift_j:
#         return False

#     schedule[i, d], schedule[j, d] = 0, 0
#     ok = _can_assign(schedule, i, d, shift_j, D, F) and _can_assign(schedule, j, d, shift_i, D, F)
#     schedule[i, d], schedule[j, d] = shift_i, shift_j
#     return ok


# def _apply_swap(schedule, night_count, i, j, d):
#     shift_i = schedule[i, d]
#     shift_j = schedule[j, d]
#     schedule[i, d], schedule[j, d] = shift_j, shift_i

#     if shift_i == NIGHT_SHIFT:
#         night_count[i] -= 1
#         night_count[j] += 1
#     elif shift_j == NIGHT_SHIFT:
#         night_count[i] += 1
#         night_count[j] -= 1


# def _candidate_moves(schedule, N, D, night_count, rng, sample_per_day):
#     max_nights = max(night_count.values())
#     overloaded = [i for i, count in night_count.items() if count == max_nights]
#     rng.shuffle(overloaded)

#     moves = []
#     for i in overloaded:
#         night_days = [d for d in range(1, D + 1) if schedule[i, d] == NIGHT_SHIFT]
#         rng.shuffle(night_days)

#         for d in night_days:
#             candidates = [
#                 j for j in range(1, N + 1)
#                 if j != i and schedule[j, d] != NIGHT_SHIFT and night_count[j] + 1 <= max_nights
#             ]
#             candidates.sort(key=lambda j: (night_count[j], schedule[j, d] != 0, j))
#             for j in candidates[:sample_per_day]:
#                 moves.append((i, j, d))

#     rng.shuffle(moves)
#     return moves


# def solve(N, D, A, B, F, time_limit=300, max_iterations=20000, seed=42, max_restarts=200):
#     start_time = time.time()
#     rng = random.Random(seed)

#     schedule = _build_initial_solution(N, D, A, B, F, rng, start_time, time_limit, max_restarts)
#     if schedule is None:
#         return {"status": "NO_FEASIBLE_SOLUTION", "obj": None, "runtime": time.time() - start_time, "schedule": None}

#     night_count = _night_counts(schedule, N, D)
#     best_score = _score(night_count)
#     iterations = 0
#     improved = True


#     history = [max(night_count.values())]
#     while improved and iterations < max_iterations and time.time() - start_time < time_limit:
#         improved = False
#         iterations += 1

#         moves = _candidate_moves(schedule, N, D, night_count, rng, sample_per_day=40)
#         for i, j, d in moves:
#             if time.time() - start_time >= time_limit:
#                 break
#             if not _is_swap_valid(schedule, i, j, d, D, F):
#                 continue

#             _apply_swap(schedule, night_count, i, j, d)
#             new_score = _score(night_count)
#             if new_score < best_score:
#                 best_score = new_score
#                 improved = True
#                 break

#             _apply_swap(schedule, night_count, i, j, d)
#         history.append(max(night_count.values()))

#     status = "HEURISTIC"
#     if time.time() - start_time >= time_limit:
#         status = "TIME_LIMIT"

#     return {
#         "status": status,
#         "obj": max(night_count.values()),
#         "runtime": time.time() - start_time,
#         "schedule": schedule,
#         "iterations": iterations,
#         "history": history
#     }


# def _read_input_from_stdin():
#     first_line = sys.stdin.readline().strip()
#     if not first_line:
#         return None

#     N, D, A, B = map(int, first_line.split())
#     days_off = {}

#     for i in range(1, N + 1):
#         parts = list(map(int, sys.stdin.readline().split()))
#         days_off[i] = [day for day in parts if day != -1]

#     return N, D, A, B, days_off


# def main():
#     data = _read_input_from_stdin()
#     if not data:
#         return

#     N, D, A, B, F = data
#     result = solve(N, D, A, B, F)
#     schedule = result["schedule"]
#     if schedule is None:
#         print("NO_SOLUTION")
#         return

#     for i in range(1, N + 1):
#         print(" ".join(str(schedule[i, d]) for d in range(1, D + 1)))


# if __name__ == "__main__":
#     main()




# RANDOM


import random
import math
import sys
import time
import math

SHIFT_COUNT = 4
NIGHT_SHIFT = 4


def _empty_schedule(N, D):
    return {(i, d): 0 for i in range(1, N + 1) for d in range(1, D + 1)}


def _night_counts(schedule, N, D):
    return {
        i: sum(1 for d in range(1, D + 1) if schedule[i, d] == NIGHT_SHIFT)
        for i in range(1, N + 1)
    }


def _objective(schedule, N, D):
    counts = _night_counts(schedule, N, D)
    return max(counts.values()) if counts else 0


def _score(night_count):
    return tuple(sorted(night_count.values(), reverse=True))


def _status_from_obj(obj, N, D, A):
    return "OPTIMAL" if obj == math.ceil(D * A / N) else "FEASIBLE"


def _can_assign(schedule, i, d, shift, D, F):
    if shift == 0:
        return True
    if d in F.get(i, []):
        return False
    if d > 1 and schedule[i, d - 1] == NIGHT_SHIFT:
        return False
    if shift == NIGHT_SHIFT and d < D and schedule[i, d + 1] != 0:
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
        # Lấy danh sách các ca trực cần gán {1, 2, 3, 4}
        shifts = list(range(1, SHIFT_COUNT + 1))
        # Xáo trộn thứ tự gán kíp trong ngày để tăng tính ngẫu nhiên
        rng.shuffle(shifts)

        for shift in shifts:
            # Tìm tất cả những người hợp lệ có thể làm ca này tại ngày d
            candidates = [
                i for i in range(1, N + 1)
                if _can_assign(schedule, i, d, shift, D, F) and schedule[i, d] == 0
            ]
            
            # Nếu số lượng người hợp lệ không đủ lấp đầy ca tối thiểu A -> Thất bại
            if len(candidates) < A:
                return None
            
            # Chọn NGẪU NHIÊN HOÀN TOÀN A nhân viên từ tập ứng viên (Không sắp xếp tải)
            chosen_staff = rng.sample(candidates, A)
            for i in chosen_staff:
                schedule[i, d] = shift

    # Kiểm tra tính hợp lệ toàn cục trước khi trả về nghiệm bàn đạp
    return schedule if _validate(schedule, N, D, A, B, F) else None


def _build_initial_solution(N, D, A, B, F, rng, start_time, time_limit, max_restarts):
    # Sử dụng chiến lược Random nhiều lần (Multi-start) để dò tìm một khung hợp lệ
    if time.time() - start_time >= time_limit:
        return None

    return _construct_random_initial_solution(N, D, A, B, F, rng)
# =========================================================================


def _validate(schedule, N, D, A, B, F):
    for i in range(1, N + 1):
        for d in range(1, D + 1):
            shift = schedule[i, d]
            if shift == 0:
                continue
            if shift < 1 or shift > SHIFT_COUNT:
                return False
            if d in F.get(i, []):
                return False
            if d > 1 and schedule[i, d - 1] == NIGHT_SHIFT:
                return False

    for d in range(1, D + 1):
        for shift in range(1, SHIFT_COUNT + 1):
            count = sum(1 for i in range(1, N + 1) if schedule[i, d] == shift)
            if count < A or count > B:
                return False
    return True


def _is_swap_valid(schedule, i, j, d, D, F):
    shift_i = schedule[i, d]
    shift_j = schedule[j, d]
    if shift_i == shift_j:
        return False

    schedule[i, d], schedule[j, d] = 0, 0
    ok = _can_assign(schedule, i, d, shift_j, D, F) and _can_assign(schedule, j, d, shift_i, D, F)
    schedule[i, d], schedule[j, d] = shift_i, shift_j
    return ok


def _apply_swap(schedule, night_count, i, j, d):
    shift_i = schedule[i, d]
    shift_j = schedule[j, d]
    schedule[i, d], schedule[j, d] = shift_j, shift_i

    if shift_i == NIGHT_SHIFT:
        night_count[i] -= 1
        night_count[j] += 1
    elif shift_j == NIGHT_SHIFT:
        night_count[i] += 1
        night_count[j] -= 1


def _candidate_moves(schedule, N, D, night_count, rng, sample_per_day):
    max_nights = max(night_count.values())
    overloaded = [i for i, count in night_count.items() if count == max_nights]
    rng.shuffle(overloaded)

    moves = []
    for i in overloaded:
        night_days = [d for d in range(1, D + 1) if schedule[i, d] == NIGHT_SHIFT]
        rng.shuffle(night_days)

        for d in night_days:
            candidates = [
                j for j in range(1, N + 1)
                if j != i and schedule[j, d] != NIGHT_SHIFT and night_count[j] + 1 <= max_nights
            ]
            candidates.sort(key=lambda j: (night_count[j], schedule[j, d] != 0, j))
            for j in candidates[:sample_per_day]:
                moves.append((i, j, d))

    rng.shuffle(moves)
    return moves


def _construct_relaxed_initial_solution(N, D, A, rng):
    schedule = _empty_schedule(N, D)

    for d in range(1, D + 1):
        staff = list(range(1, N + 1))
        rng.shuffle(staff)
        cursor = 0

        for shift in range(1, SHIFT_COUNT + 1):
            for i in staff[cursor:cursor + A]:
                schedule[i, d] = shift
            cursor += A

    return schedule


def _constraint_violations(schedule, N, D, A, B, F):
    violations = 0

    for i in range(1, N + 1):
        for d in range(1, D + 1):
            shift = schedule[i, d]
            if shift == 0:
                continue
            if shift < 1 or shift > SHIFT_COUNT:
                violations += 1
            if d in F.get(i, []):
                violations += 1
            if d > 1 and schedule[i, d - 1] == NIGHT_SHIFT:
                violations += 1

    for d in range(1, D + 1):
        for shift in range(1, SHIFT_COUNT + 1):
            count = sum(1 for i in range(1, N + 1) if schedule[i, d] == shift)
            if count < A:
                violations += A - count
            elif count > B:
                violations += count - B

    return violations


def _repair_score(schedule, N, D, A, B, F):
    return (_constraint_violations(schedule, N, D, A, B, F), _objective(schedule, N, D))


def _is_better_repair_score(score, best_score):
    return best_score is None or score < best_score


def _violating_staff_days(schedule, N, D, F):
    targets = set()

    for i in range(1, N + 1):
        for d in range(1, D + 1):
            if schedule[i, d] == 0:
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


def _swap_cells(schedule, i, j, d):
    schedule[i, d], schedule[j, d] = schedule[j, d], schedule[i, d]


def _assignment_penalty(schedule, i, d, shift, D, F):
    penalty = 0
    if d in F.get(i, []):
        penalty += 1
    if d > 1 and schedule[i, d - 1] == NIGHT_SHIFT:
        penalty += 1
    if shift == NIGHT_SHIFT and d < D and schedule[i, d + 1] != 0:
        penalty += 1
    return penalty


def _build_repaired_day(schedule, N, D, A, F, d, rng):
    new_day = {i: 0 for i in range(1, N + 1)}
    assigned = set()
    shifts = list(range(1, SHIFT_COUNT + 1))
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


def _solve_feasible_only(N, D, A, B, F, time_limit=300, max_iterations=20000, seed=42, max_restarts=1000):
    start_time = time.time()
    rng = random.Random(seed)

    # Khởi tạo nghiệm ngẫu nhiên
    schedule = _build_initial_solution(N, D, A, B, F, rng, start_time, time_limit, max_restarts)
    if schedule is None:
        return {"status": "NO_FEASIBLE_SOLUTION", "obj": None, "runtime": time.time() - start_time, "schedule": None}

    night_count = _night_counts(schedule, N, D)
    best_score = _score(night_count)
    iterations = 0
    improved = True

    history = [max(night_count.values())]
    while improved and iterations < max_iterations and time.time() - start_time < time_limit:
        improved = False
        iterations += 1

        moves = _candidate_moves(schedule, N, D, night_count, rng, sample_per_day=40)
        for i, j, d in moves:
            if time.time() - start_time >= time_limit:
                break
            if not _is_swap_valid(schedule, i, j, d, D, F):
                continue

            _apply_swap(schedule, night_count, i, j, d)
            new_score = _score(night_count)
            if new_score < best_score:
                best_score = new_score
                improved = True
                break

            _apply_swap(schedule, night_count, i, j, d)
        history.append(max(night_count.values()))

    obj = max(night_count.values())

    return {
        "status": _status_from_obj(obj, N, D, A),
        "obj": obj,
        "runtime": time.time() - start_time,
        "schedule": schedule,
        "iterations": iterations,
        "history": history
    }


def solve(N, D, A, B, F, time_limit=300, max_iterations=20000, seed=42, max_restarts=1000):
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

    schedule = _build_initial_solution(
        N, D, A, B, F, rng, start_time, min(time_limit, 1), min(max_restarts, 200)
    )
    if schedule is None:
        schedule = _construct_relaxed_initial_solution(N, D, A, rng)

    current_score = _repair_score(schedule, N, D, A, B, F)
    best_relaxed_schedule = schedule.copy()
    best_relaxed_score = current_score
    best_feasible = schedule.copy() if current_score[0] == 0 else None
    best_feasible_obj = current_score[1] if current_score[0] == 0 else None

    iterations = 0
    history = [current_score[1]]
    violation_history = [current_score[0]]
    no_improve_steps = 0
    lower_bound = math.ceil(D * A / N)

    while iterations < max_iterations and time.time() - start_time < time_limit:
        if best_feasible_obj == lower_bound:
            break

        iterations += 1

        if current_score[0] > 0:
            best_action = None
            best_action_score = None
            actions = _repair_actions(schedule, N, D, A, F, rng, sample_size=60)

            for action_type, payload in actions:
                if action_type == "swap":
                    i, j, d = payload
                    _swap_cells(schedule, i, j, d)
                    undo_data = ("swap", payload)
                else:
                    d, new_day = payload
                    old_day = _apply_rebuilt_day(schedule, new_day, d)
                    undo_data = ("rebuild_day", (d, old_day))

                move_score = _repair_score(schedule, N, D, A, B, F)

                if undo_data[0] == "swap":
                    _, (i, j, d) = undo_data
                    _swap_cells(schedule, i, j, d)
                else:
                    _, (d, old_day) = undo_data
                    _restore_day(schedule, old_day, d)

                if _is_better_repair_score(move_score, best_action_score):
                    best_action = (action_type, payload)
                    best_action_score = move_score

            if best_action is not None and best_action_score < current_score:
                action_type, payload = best_action
                if action_type == "swap":
                    _swap_cells(schedule, *payload)
                else:
                    d, new_day = payload
                    _apply_rebuilt_day(schedule, new_day, d)
                current_score = best_action_score
                no_improve_steps = 0
            else:
                no_improve_steps += 1
                if no_improve_steps >= 50:
                    schedule = _construct_relaxed_initial_solution(N, D, A, rng)
                    current_score = _repair_score(schedule, N, D, A, B, F)
                    no_improve_steps = 0

            if current_score < best_relaxed_score:
                best_relaxed_score = current_score
                best_relaxed_schedule = schedule.copy()

            if current_score[0] == 0:
                best_feasible = schedule.copy()
                best_feasible_obj = current_score[1]

            history.append(current_score[1])
            violation_history.append(current_score[0])
            continue

        night_count = _night_counts(schedule, N, D)
        best_score = _score(night_count)
        improved = False

        moves = _candidate_moves(schedule, N, D, night_count, rng, sample_per_day=40)
        for i, j, d in moves:
            if time.time() - start_time >= time_limit:
                break
            if not _is_swap_valid(schedule, i, j, d, D, F):
                continue

            _apply_swap(schedule, night_count, i, j, d)
            new_score = _score(night_count)
            if new_score < best_score:
                best_score = new_score
                improved = True
                break

            _apply_swap(schedule, night_count, i, j, d)

        current_score = (0, max(night_count.values()))
        if best_feasible is None or current_score[1] < best_feasible_obj:
            best_feasible = schedule.copy()
            best_feasible_obj = current_score[1]

        history.append(current_score[1])
        violation_history.append(0)

        if not improved:
            break

    runtime = time.time() - start_time
    if best_feasible is None:
        return {
            "status": "NO_FEASIBLE_SOLUTION",
            "obj": None,
            "runtime": runtime,
            "schedule": None,
            "iterations": iterations,
            "history": history,
            "violation_history": violation_history,
            "best_violation_count": best_relaxed_score[0],
            "best_relaxed_schedule": best_relaxed_schedule,
        }

    return {
        "status": _status_from_obj(best_feasible_obj, N, D, A),
        "obj": best_feasible_obj,
        "runtime": runtime,
        "schedule": best_feasible,
        "iterations": iterations,
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
    data = _read_input_from_stdin()
    if not data:
        return

    N, D, A, B, F = data
    result = solve(N, D, A, B, F)
    schedule = result["schedule"]
    if schedule is None:
        print("NO_SOLUTION")
        return

    for i in range(1, N + 1):
        print(" ".join(str(schedule[i, d]) for d in range(1, D + 1)))


if __name__ == "__main__":
    main()


