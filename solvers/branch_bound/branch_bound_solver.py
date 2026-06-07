import math
import sys
import time


SHIFT_COUNT = 4
NIGHT_SHIFT = 4


def _empty_schedule(N, D):
    return {(i, d): 0 for i in range(1, N + 1) for d in range(1, D + 1)}


def _objective(schedule, N, D):
    return max(
        sum(1 for d in range(1, D + 1) if schedule[i, d] == NIGHT_SHIFT)
        for i in range(1, N + 1)
    )


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


def _can_work(schedule, i, d, shift, D, F):
    if schedule[i, d] != 0:
        return False
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


def _lower_bound(night_count, remaining_night_slots, N):
    if not night_count:
        return 0

    current_max = max(night_count.values())
    total_nights = sum(night_count.values()) + remaining_night_slots
    average_bound = math.ceil(total_nights / N)

    # Stronger balancing bound: distribute the remaining night shifts over the
    # currently least-loaded employees and find the smallest possible maximum.
    counts = sorted(night_count.values())
    remaining = remaining_night_slots
    level = counts[-1]
    for target in range(counts[0], counts[-1] + remaining_night_slots + 1):
        capacity = sum(max(0, target - count) for count in counts)
        if capacity >= remaining:
            level = target
            break

    return max(current_max, average_bound, level)


def _remaining_night_slots(tasks, task_idx, A):
    return sum(A for _, shift in tasks[task_idx:] if shift == NIGHT_SHIFT)


def _global_lower_bound(N, D, A):
    return math.ceil(D * A / N)


def _ordered_candidates(schedule, candidates, shift, d, D, F, night_count, work_count):
    def future_capacity_after_night(i):
        if shift != NIGHT_SHIFT or d >= D:
            return 0

        unavailable = 1
        for staff in night_count:
            if staff == i:
                continue
            if d + 1 in F.get(staff, []):
                unavailable += 1
            elif schedule[staff, d] == NIGHT_SHIFT:
                unavailable += 1
        return len(night_count) - unavailable

    if shift == NIGHT_SHIFT:
        return sorted(
            candidates,
            key=lambda i: (
                night_count[i],
                work_count[i],
                -future_capacity_after_night(i),
                len(F.get(i, [])),
                i,
            ),
        )

    return sorted(candidates, key=lambda i: (work_count[i], night_count[i], len(F.get(i, [])), i))


def _build_tasks(N, D, A, F):
    tasks = []
    for d in range(1, D + 1):
        for shift in [NIGHT_SHIFT, 1, 2, 3]:
            tasks.append((d, shift))

    return tasks


def solve(N, D, A, B, F, time_limit=300):
    start_time = time.time()

    if A > B or 4 * A > N:
        return {"status": "INFEASIBLE", "obj": None, "runtime": time.time() - start_time, "schedule": None}

    best_schedule = None
    best_obj = math.inf
    global_lb = _global_lower_bound(N, D, A)

    schedule = _empty_schedule(N, D)
    night_count = {i: 0 for i in range(1, N + 1)}
    work_count = {i: 0 for i in range(1, N + 1)}
    tasks = _build_tasks(N, D, A, F)
    timed_out = False
    optimal_reached = False
    nodes = 0

    def search(task_idx):
        nonlocal best_obj, best_schedule, timed_out, optimal_reached, nodes

        if optimal_reached:
            return

        if time.time() - start_time >= time_limit:
            timed_out = True
            return

        nodes += 1
        if _lower_bound(night_count, _remaining_night_slots(tasks, task_idx, A), N) >= best_obj:
            return

        if task_idx == len(tasks):
            if not _validate(schedule, N, D, A, B, F):
                return

            obj = _objective(schedule, N, D)
            if obj < best_obj:
                best_obj = obj
                best_schedule = schedule.copy()
                if best_obj == global_lb:
                    optimal_reached = True
            return

        d, shift = tasks[task_idx]
        assigned = [i for i in range(1, N + 1) if schedule[i, d] == shift]
        if len(assigned) >= A:
            search(task_idx + 1)
            return

        candidates = [
            i for i in range(1, N + 1)
            if _can_work(schedule, i, d, shift, D, F)
        ]
        candidates = _ordered_candidates(schedule, candidates, shift, d, D, F, night_count, work_count)

        need = A - len(assigned)
        if len(candidates) < need:
            return

        chosen = []

        def choose(start, remaining):
            if timed_out:
                return
            if remaining == 0:
                for i in chosen:
                    schedule[i, d] = shift
                    work_count[i] += 1
                    if shift == NIGHT_SHIFT:
                        night_count[i] += 1

                search(task_idx + 1)

                for i in chosen:
                    schedule[i, d] = 0
                    work_count[i] -= 1
                    if shift == NIGHT_SHIFT:
                        night_count[i] -= 1
                return

            if len(candidates) - start < remaining:
                return

            for idx in range(start, len(candidates)):
                i = candidates[idx]
                chosen.append(i)
                choose(idx + 1, remaining - 1)
                chosen.pop()
                if timed_out:
                    return

        choose(0, need)

    search(0)

    runtime = time.time() - start_time
    if best_schedule is None:
        return {"status": "TIMEOUT" if timed_out else "NO_FEASIBLE_SOLUTION", "obj": None, "runtime": runtime, "schedule": None}

    status = "FEASIBLE" if timed_out else "OPTIMAL"
    return {"status": status, "obj": best_obj, "runtime": runtime, "schedule": best_schedule, "nodes": nodes}


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
    if result["status"] == "TIMEOUT":
        print("TIME_LIMIT_EXCEEDED")
        return
    if schedule is None:
        print("NO_SOLUTION")
        return

    for i in range(1, N + 1):
        print(" ".join(str(schedule[i, d]) for d in range(1, D + 1)))


if __name__ == "__main__":
    main()
