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


def solve(N, D, A, B, F, time_limit=300):
    start_time = time.time()

    if A > B or 4 * A > N:
        return {"status": "INFEASIBLE", "obj": None, "runtime": time.time() - start_time, "schedule": None}

    schedule = _empty_schedule(N, D)
    night_count = {i: 0 for i in range(1, N + 1)}
    work_count = {i: 0 for i in range(1, N + 1)}

    for d in range(1, D + 1):
        for shift in [NIGHT_SHIFT, 1, 2, 3]:
            candidates = [
                i for i in range(1, N + 1)
                if _can_work(schedule, i, d, shift, D, F)
            ]

            if shift == NIGHT_SHIFT:
                candidates.sort(
                    key=lambda i: (
                        night_count[i],
                        work_count[i],
                        -_future_capacity_after_night(schedule, i, d, N, D, F),
                        i,
                    )
                )
            else:
                candidates.sort(key=lambda i: (work_count[i], night_count[i], i))

            if len(candidates) < A:
                return {
                    "status": "NO_FEASIBLE_SOLUTION",
                    "obj": None,
                    "runtime": time.time() - start_time,
                    "schedule": None,
                }

            for i in candidates[:A]:
                schedule[i, d] = shift
                work_count[i] += 1
                if shift == NIGHT_SHIFT:
                    night_count[i] += 1

    if not _validate(schedule, N, D, A, B, F):
        return {"status": "INVALID", "obj": None, "runtime": time.time() - start_time, "schedule": None}

    return {
        "status": "GREEDY",
        "obj": _objective(schedule, N, D),
        "runtime": time.time() - start_time,
        "schedule": schedule,
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
