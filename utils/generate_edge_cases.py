import os
import random


OUT_DIR = os.path.join("data", "edge")


def write_case(filename, N, D, A, B, days_off):
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"{N} {D} {A} {B}\n")
        for i in range(1, N + 1):
            off = sorted(set(days_off.get(i, [])))
            if off:
                f.write(" ".join(map(str, off)) + " -1\n")
            else:
                f.write("-1\n")
    return path


def random_off_days(N, D, probability, seed):
    rng = random.Random(seed)
    return {
        i: [d for d in range(1, D + 1) if rng.random() < probability]
        for i in range(1, N + 1)
    }


def clustered_off_days(N, D, base_probability, clusters, seed):
    rng = random.Random(seed)
    days_off = random_off_days(N, D, base_probability, seed)
    for start, end, first_staff, last_staff in clusters:
        for i in range(first_staff, last_staff + 1):
            for d in range(start, end + 1):
                if 1 <= i <= N and 1 <= d <= D:
                    days_off[i].append(d)
    for i in days_off:
        days_off[i] = sorted(set(days_off[i]))
    return days_off


def main():
    cases = []

    cases.append(("tight_capacity_1.txt", 24, 10, 4, 5, random_off_days(24, 10, 0.05, 101)))
    cases.append(("tight_capacity_2.txt", 32, 14, 5, 6, random_off_days(32, 14, 0.06, 102)))
    cases.append(("tight_capacity_3.txt", 48, 21, 8, 9, random_off_days(48, 21, 0.08, 103)))

    cases.append(
        (
            "clustered_off_feasible_1.txt",
            60,
            20,
            8,
            12,
            clustered_off_days(60, 20, 0.04, [(8, 10, 1, 15), (15, 16, 20, 30)], 301),
        )
    )
    cases.append(
        (
            "clustered_off_feasible_2.txt",
            80,
            30,
            11,
            16,
            clustered_off_days(80, 30, 0.04, [(10, 13, 1, 18), (22, 24, 35, 48)], 302),
        )
    )
    cases.append(
        (
            "clustered_off_hard_1.txt",
            120,
            45,
            16,
            24,
            clustered_off_days(120, 45, 0.08, [(14, 18, 1, 25), (30, 35, 50, 75)], 303),
        )
    )

    shortage = random_off_days(20, 5, 0.0, 401)
    for i in range(1, 8):
        shortage[i].append(3)
    cases.append(("infeasible_daily_shortage.txt", 20, 5, 4, 5, shortage))

    cases.append(("infeasible_after_night_rest.txt", 4, 2, 1, 1, random_off_days(4, 2, 0.0, 402)))

    exact_too_tight = random_off_days(16, 4, 0.0, 403)
    cases.append(("infeasible_exact_staff_multi_day.txt", 16, 4, 4, 4, exact_too_tight))

    cases.append(("repair_pressure_1.txt", 96, 40, 14, 18, random_off_days(96, 40, 0.18, 501)))
    cases.append(
        (
            "repair_pressure_2.txt",
            150,
            60,
            20,
            30,
            clustered_off_days(150, 60, 0.16, [(20, 25, 1, 35), (40, 45, 70, 105)], 502),
        )
    )
    cases.append(("repair_pressure_3.txt", 220, 80, 40, 44, random_off_days(220, 80, 0.2, 503)))

    for case in cases:
        path = write_case(*case)
        print(path)


if __name__ == "__main__":
    main()
