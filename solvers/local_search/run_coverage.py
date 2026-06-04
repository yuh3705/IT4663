import argparse
import os
import sys

import matplotlib.pyplot as plt
import pandas as pd


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utils.data_loader import read_input
from solvers.local_search import hill_climbing_solver, tabu_search_solver


SOLVERS = {
    "hill": ("Hill Climbing", hill_climbing_solver),
    "tabu": ("Tabu Search", tabu_search_solver),
}


def _run_one_solver(solver_key, test_file, time_limit, max_iterations, seed):
    data = read_input(test_file)
    if not data:
        raise ValueError(f"Cannot read test case: {test_file}")

    N, D, A, B, F = data
    solver_name, solver_module = SOLVERS[solver_key]
    result = solver_module.solve(
        N,
        D,
        A,
        B,
        F,
        time_limit=time_limit,
        max_iterations=max_iterations,
        seed=seed,
    )
    return solver_name, result


def _history_rows(solver_name, result):
    history = result.get("history", [])
    violation_history = result.get("violation_history", [])

    rows = []
    for iteration, objective in enumerate(history):
        violations = violation_history[iteration] if iteration < len(violation_history) else 0
        rows.append(
            {
                "Iteration": iteration,
                "Solver": solver_name,
                "Objective": objective,
                "Violations": violations,
            }
        )
    return rows


def _plot_objective_history(df, output_path, test_file, results):
    plt.figure(figsize=(11, 6))
    ax = plt.gca()
    has_feasible_objective = any((group["Violations"] == 0).any() for _, group in df.groupby("Solver"))

    if has_feasible_objective:
        for solver_name, group in df.groupby("Solver"):
            feasible_group = group[group["Violations"] == 0]
            if feasible_group.empty:
                continue

            marker = "o" if len(feasible_group) <= 200 else None
            ax.plot(
                feasible_group["Iteration"],
                feasible_group["Objective"],
                marker=marker,
                markersize=3,
                linewidth=2,
                label=f"{solver_name} objective",
            )

    title_prefix = "Objective by Iteration" if has_feasible_objective else "Repair Violations by Iteration"
    ax.set_title(f"{title_prefix} - {os.path.basename(test_file)}")
    ax.set_xlabel("Iteration")
    ax.set_ylabel("Objective: max night shifts" if has_feasible_objective else "Hard constraint violations")
    ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.5)

    if "Violations" in df and df["Violations"].max() > 0 and has_feasible_objective:
        ax2 = ax.twinx()
        for solver_name, group in df.groupby("Solver"):
            marker = "o" if len(group) <= 200 else None
            ax2.plot(
                group["Iteration"],
                group["Violations"],
                marker=marker,
                markersize=2,
                linestyle="--",
                linewidth=1.4,
                alpha=0.65,
                label=f"{solver_name} violations",
            )
        ax2.set_ylabel("Hard constraint violations")

        lines, labels = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        if lines or lines2:
            ax.legend(lines + lines2, labels + labels2, loc="best")
    elif "Violations" in df and df["Violations"].max() > 0:
        for solver_name, group in df.groupby("Solver"):
            ax.plot(
                group["Iteration"],
                group["Violations"],
                linestyle="--",
                linewidth=1.4,
                alpha=0.75,
                label=f"{solver_name} violations",
            )
        ax.legend(loc="best")
    else:
        ax.legend(loc="best")

    if not has_feasible_objective:
        plt.figtext(
            0.01,
            0.045,
            "No feasible schedule found; objective is hidden during repair. "
            "Dashed lines show hard constraint violations.",
            ha="left",
            fontsize=8,
        )

    footer_parts = []
    for solver_name, result in results:
        footer_parts.append(
            f"{solver_name}: status={result.get('status')}, obj={result.get('obj')}, "
            f"runtime={result.get('runtime', 0):.4f}s"
        )
    plt.figtext(0.01, 0.01, " | ".join(footer_parts), ha="left", fontsize=8)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    plt.tight_layout(rect=(0, 0.05, 1, 1))
    plt.savefig(output_path, dpi=300)
    plt.close()


def main():
    parser = argparse.ArgumentParser(description="Plot objective value over local-search iterations.")
    parser.add_argument("--case", default="../../data/stress/test_2.txt", help="Path to a data/*.txt test case")
    parser.add_argument(
        "--solver",
        choices=["all", "hill", "tabu"],
        default="all",
        help="Solver to plot. Use 'all' to compare Hill Climbing and Tabu Search.",
    )
    parser.add_argument("--time-limit", type=float, default=1800)
    parser.add_argument("--max-iterations", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", default="results/convergence_plot.png")
    parser.add_argument("--csv", default="results/convergence_history.csv")
    args = parser.parse_args()

    solver_keys = ["hill", "tabu"] if args.solver == "all" else [args.solver]
    results = []
    rows = []

    for solver_key in solver_keys:
        solver_name, result = _run_one_solver(
            solver_key,
            args.case,
            args.time_limit,
            args.max_iterations,
            args.seed,
        )
        results.append((solver_name, result))
        rows.extend(_history_rows(solver_name, result))
        print(
            f"{solver_name}: status={result.get('status')}, obj={result.get('obj')}, "
            f"runtime={result.get('runtime', 0):.4f}s"
        )

    if not rows:
        raise ValueError("No history returned by selected solver(s).")

    df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(args.csv) or ".", exist_ok=True)
    df.to_csv(args.csv, index=False)
    _plot_objective_history(df, args.output, args.case, results)

    print(f"Saved history CSV: {args.csv}")
    print(f"Saved objective plot: {args.output}")


if __name__ == "__main__":
    main()
