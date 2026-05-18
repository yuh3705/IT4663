import random
import time
import sys


SHIFT_COUNT = 4
NIGHT_SHIFT = 3


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


def _construct_initial_solution(N, D, A, F, rng):
    schedule = _empty_schedule(N, D)
    night_count = {i: 0 for i in range(1, N + 1)}

    for d in range(1, D + 1):
        assigned_today = set()
        for shift in [NIGHT_SHIFT, 0, 1, 2]:
            candidates = [
                i for i in range(1, N + 1)
                if i not in assigned_today and _can_work(schedule, i, d, shift, D, F)
            ]
            rng.shuffle(candidates)
            if shift == NIGHT_SHIFT:
                candidates.sort(key=lambda i: (night_count[i], len(F.get(i, []))))

            if len(candidates) < A:
                return None

            for i in candidates[:A]:
                schedule[i, d] = shift
                assigned_today.add(i)
                if shift == NIGHT_SHIFT:
                    night_count[i] += 1

    return schedule


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


def _candidate_moves(schedule, N, D, night_count, rng, sample_size):
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
            rng.shuffle(candidates)
            for j in candidates[:sample_size]:
                moves.append((i, j, d))
    rng.shuffle(moves)
    return moves[:sample_size * max(1, len(overloaded))]


def solve(N, D, A, B, F, time_limit=300, max_iterations=10000, tabu_tenure=25, seed=42):
    start_time = time.time()
    rng = random.Random(seed)

    if A > B or 4 * A > N:
        return {"status": "INFEASIBLE", "obj": None, "runtime": time.time() - start_time, "schedule": None}

    current = None
    for _ in range(100):
        current = _construct_initial_solution(N, D, A, F, rng)
        if current is not None:
            break

    if current is None or not _validate(current, N, D, A, B, F):
        return {"status": "NO_FEASIBLE_SOLUTION", "obj": None, "runtime": time.time() - start_time, "schedule": None}

    best = current.copy()
    best_obj = _objective(best, N, D)
    current_obj = best_obj
    tabu_until = {}
    iteration = 0

    while iteration < max_iterations and time.time() - start_time < time_limit:
        iteration += 1
        night_count = _night_counts(current, N, D)
        moves = _candidate_moves(current, N, D, night_count, rng, sample_size=30)

        best_move = None
        best_move_obj = None
        for move in moves:
            if not _is_swap_valid(current, move, D, F):
                continue

            _apply_swap(current, move)
            obj = _objective(current, N, D)
            _apply_swap(current, move)

            tabu_key = (move[1], move[2], NIGHT_SHIFT)
            is_tabu = tabu_until.get(tabu_key, 0) > iteration
            if is_tabu and obj >= best_obj:
                continue

            if best_move is None or obj < best_move_obj:
                best_move = move
                best_move_obj = obj

        if best_move is None:
            break

        _apply_swap(current, best_move)
        current_obj = best_move_obj
        leaving_employee, _, day = best_move
        tabu_until[leaving_employee, day, NIGHT_SHIFT] = iteration + tabu_tenure

        if current_obj < best_obj:
            best = current.copy()
            best_obj = current_obj

    return {
        "status": "HEURISTIC",
        "obj": best_obj,
        "runtime": time.time() - start_time,
        "schedule": best
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
