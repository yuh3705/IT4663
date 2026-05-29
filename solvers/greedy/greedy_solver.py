import random
import math
import sys
import time


SHIFT_COUNT = 4
NIGHT_SHIFT = 4


def _empty_schedule(N, D):
    return {(i, d): 0 for i in range(1, N + 1) for d in range(1, D + 1)}


def _can_work(schedule, i, d, shift, D, F):
    if d in F.get(i, []):
        return False
    if d > 1 and schedule[i, d - 1] == NIGHT_SHIFT:
        return False
    if shift == NIGHT_SHIFT and d < D and schedule[i, d + 1] != 0:
        return False
    return schedule[i, d] == 0


def _future_capacity_after_night(schedule, i, d, N, D, F):
    if d >= D:
        return 0

    unavailable = 0
    for staff in range(1, N + 1):
        if staff == i:
            unavailable += 1
        elif d + 1 in F.get(staff, []):
            unavailable += 1
        elif schedule[staff, d] == NIGHT_SHIFT:
            unavailable += 1
    return N - unavailable


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


def _objective(schedule, N, D):
    return max(
        sum(1 for d in range(1, D + 1) if schedule[i, d] == NIGHT_SHIFT)
        for i in range(1, N + 1)
    )


def _ordered_candidates(schedule, candidates, shift, d, N, D, F, night_count, work_count):
    if shift == NIGHT_SHIFT:
        return sorted(
            candidates,
            key=lambda i: (
                night_count[i],
                work_count[i],
                -_future_capacity_after_night(schedule, i, d, N, D, F),
                len(F.get(i, [])),
                i,
            ),
        )

    return sorted(candidates, key=lambda i: (work_count[i], night_count[i], len(F.get(i, [])), i))


def _pick_candidates(candidates, A, rng, randomized):
    if not randomized:
        return candidates[:A]

    pool_size = min(len(candidates), max(A, 3 * A))
    pool = candidates[:pool_size]
    return rng.sample(pool, A)


def _construct_solution(N, D, A, B, F, rng, randomized, reverse_days=False):
    schedule = _empty_schedule(N, D)
    night_count = {i: 0 for i in range(1, N + 1)}
    work_count = {i: 0 for i in range(1, N + 1)}

    day_range = range(D, 0, -1) if reverse_days else range(1, D + 1)
    for d in day_range:
        remaining_shifts = {1, 2, 3, NIGHT_SHIFT}

        while remaining_shifts:
            options = []
            for shift in remaining_shifts:
                candidates = [
                    i for i in range(1, N + 1)
                    if _can_work(schedule, i, d, shift, D, F)
                ]
                if len(candidates) < A:
                    return None
                options.append((len(candidates), 0 if shift == NIGHT_SHIFT else 1, shift, candidates))

            _, _, shift, candidates = min(options)
            candidates = _ordered_candidates(schedule, candidates, shift, d, N, D, F, night_count, work_count)

            for i in _pick_candidates(candidates, A, rng, randomized):
                schedule[i, d] = shift
                work_count[i] += 1
                if shift == NIGHT_SHIFT:
                    night_count[i] += 1

            remaining_shifts.remove(shift)

    return schedule if _validate(schedule, N, D, A, B, F) else None


def solve(N, D, A, B, F, time_limit=300, max_restarts=200, seed=42):
    start_time = time.time()
    rng = random.Random(seed)

    if A > B or 4 * A > N:
        return {"status": "INFEASIBLE", "obj": None, "runtime": time.time() - start_time, "schedule": None}

    best_schedule = None
    best_obj = None
    attempts = 0
    lower_bound = math.ceil(D * A / N)

    while attempts < max_restarts and time.time() - start_time < time_limit:
        schedule = _construct_solution(
            N, D, A, B, F, rng,
            randomized=attempts > 1,
            reverse_days=attempts % 2 == 1,
        )
        attempts += 1
        if schedule is None:
            continue

        obj = _objective(schedule, N, D)
        if best_obj is None or obj < best_obj:
            best_schedule = schedule
            best_obj = obj
            if best_obj == lower_bound:
                break

    if best_schedule is None:
        return {"status": "NO_FEASIBLE_SOLUTION", "obj": None, "runtime": time.time() - start_time, "schedule": None}

    return {
        "status": "GREEDY",
        "obj": best_obj,
        "runtime": time.time() - start_time,
        "schedule": best_schedule,
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
