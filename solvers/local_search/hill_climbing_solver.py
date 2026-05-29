import random
import sys
import time


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


def _future_capacity_after_night(schedule, i, d, N, D, F):
    if d >= D:
        return 0

    unavailable = 1
    for staff in range(1, N + 1):
        if staff == i:
            continue
        if d + 1 in F.get(staff, []):
            unavailable += 1
        elif schedule[staff, d] == NIGHT_SHIFT:
            unavailable += 1
    return N - unavailable


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
    return rng.sample(candidates[:pool_size], A)


def _construct_initial_solution(N, D, A, B, F, rng, randomized, reverse_days=False):
    if A > B or SHIFT_COUNT * A > N:
        return None

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
                    if _can_assign(schedule, i, d, shift, D, F) and schedule[i, d] == 0
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


def _build_initial_solution(N, D, A, B, F, rng, start_time, time_limit, max_restarts):
    for attempt in range(max_restarts):
        if time.time() - start_time >= time_limit:
            break

        schedule = _construct_initial_solution(
            N, D, A, B, F, rng,
            randomized=attempt > 1,
            reverse_days=attempt % 2 == 1,
        )
        if schedule is not None:
            return schedule

    return None


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


def solve(N, D, A, B, F, time_limit=300, max_iterations=20000, seed=42, max_restarts=200):
    start_time = time.time()
    rng = random.Random(seed)

    schedule = _build_initial_solution(N, D, A, B, F, rng, start_time, time_limit, max_restarts)
    if schedule is None:
        return {"status": "NO_FEASIBLE_SOLUTION", "obj": None, "runtime": time.time() - start_time, "schedule": None}

    night_count = _night_counts(schedule, N, D)
    best_score = _score(night_count)
    iterations = 0
    improved = True

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

    status = "HEURISTIC"
    if time.time() - start_time >= time_limit:
        status = "TIME_LIMIT"

    return {
        "status": status,
        "obj": max(night_count.values()),
        "runtime": time.time() - start_time,
        "schedule": schedule,
        "iterations": iterations,
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
