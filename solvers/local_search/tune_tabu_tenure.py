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
from solvers.local_search import tabu_search_solver


DEFAULT_TENURES = [5, 10, 25, 30, 50, 100]


def _run_tabu(test_file, tenure, time_limit, max_iterations, seed):
    data = read_input(test_file)
    if not data:
        raise ValueError(f"Cannot read test case: {test_file}")

    N, D, A, B, F = data
    result = tabu_search_solver.solve(
        N,
        D,
        A,
        B,
        F,
        time_limit=time_limit,
        max_iterations=max_iterations,
        tabu_tenure=tenure,
        seed=seed,
    )
    is_valid = bool(result.get("schedule") and tabu_search_solver._validate(result["schedule"], N, D, A, B, F))
    return result, is_valid


def _history_rows(tenure, result):
    history = result.get("history", [])
    violation_history = result.get("violation_history", [])
    rows = []

    for iteration, objective in enumerate(history):
        violations = violation_history[iteration] if iteration < len(violation_history) else 0
        rows.append(
            {
                "Tenure": tenure,
                "Iteration": iteration,
                "Objective": objective,
                "Violations": violations,
                "Feasible": violations == 0,
            }
        )

    return rows


def _plot_histories(df, summary_df, test_file, output_path):
    has_feasible = df["Feasible"].any()
    plt.figure(figsize=(13, 7))
    ax = plt.gca()

    if has_feasible:
        for tenure, group in df.groupby("Tenure"):
            feasible_group = group[group["Feasible"]]
            if feasible_group.empty:
                continue

            marker = "o" if len(feasible_group) <= 150 else None
            ax.plot(
                feasible_group["Iteration"],
                feasible_group["Objective"],
                marker=marker,
                markersize=3,
                linewidth=2,
                label=f"tenure={tenure}",
            )

        ax.set_title(f"Tabu tenure tuning - objective by iteration - {os.path.basename(test_file)}")
        ax.set_ylabel("Objective: max night shifts")
    else:
        for tenure, group in df.groupby("Tenure"):
            ax.plot(
                group["Iteration"],
                group["Violations"],
                linestyle="--",
                linewidth=1.5,
                alpha=0.8,
                label=f"tenure={tenure}",
            )

        ax.set_title(f"Tabu tenure tuning - repair violations by iteration - {os.path.basename(test_file)}")
        ax.set_ylabel("Hard constraint violations")

    ax.set_xlabel("Iteration")
    ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.5)
    ax.legend(loc="best")

    footer_parts = []
    for row in summary_df.to_dict("records"):
        footer_parts.append(
            f"{row['Tenure']}: {row['Status']}, obj={row['Objective']}, "
            f"valid={row['ValidSchedule']}, t={row['Runtime']:.2f}s"
        )
    plt.figtext(0.01, 0.01, " | ".join(footer_parts), ha="left", fontsize=8)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    plt.tight_layout(rect=(0, 0.06, 1, 1))
    plt.savefig(output_path, dpi=300)
    plt.close()


def _plot_small_multiples(df, test_file, output_path):
    tenures = list(df["Tenure"].drop_duplicates())
    cols = 2
    rows = (len(tenures) + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(14, 3.5 * rows), sharex=False, sharey=True)
    axes = axes.flatten() if hasattr(axes, "flatten") else [axes]

    has_feasible = df["Feasible"].any()
    y_col = "Objective" if has_feasible else "Violations"
    title_value = "objective" if has_feasible else "violations"

    for ax, tenure in zip(axes, tenures):
        group = df[df["Tenure"] == tenure]
        if has_feasible:
            group = group[group["Feasible"]]

        ax.plot(group["Iteration"], group[y_col], linewidth=2)
        ax.set_title(f"tabu_tenure={tenure}")
        ax.set_xlabel("Iteration")
        ax.set_ylabel(y_col)
        ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.5)

    for ax in axes[len(tenures):]:
        ax.axis("off")

    fig.suptitle(f"Tabu tenure tuning - {title_value} - {os.path.basename(test_file)}", fontsize=14)
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    plt.tight_layout(rect=(0, 0, 1, 0.96))
    plt.savefig(output_path, dpi=300)
    plt.close()


def _plot_summary(summary_df, output_path):
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))

    plot_df = summary_df.copy()
    plot_df["ObjectiveForPlot"] = plot_df["Objective"].fillna(float("nan"))

    axes[0].bar(plot_df["Tenure"].astype(str), plot_df["ObjectiveForPlot"])
    axes[0].set_title("Best objective")
    axes[0].set_xlabel("tabu_tenure")
    axes[0].set_ylabel("Objective")
    axes[0].grid(True, axis="y", linestyle="--", linewidth=0.5, alpha=0.5)

    axes[1].bar(plot_df["Tenure"].astype(str), plot_df["Runtime"])
    axes[1].set_title("Runtime")
    axes[1].set_xlabel("tabu_tenure")
    axes[1].set_ylabel("Seconds")
    axes[1].grid(True, axis="y", linestyle="--", linewidth=0.5, alpha=0.5)

    for ax in axes:
        for tick in ax.get_xticklabels():
            tick.set_rotation(0)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()


def main():
    parser = argparse.ArgumentParser(description="Run Tabu Search with multiple tabu_tenure values and plot histories.")
    parser.add_argument("--case", default="../../data/stress/test_2.txt", help="Path to a data/*.txt test case")
    parser.add_argument("--tenures", nargs="+", type=int, default=DEFAULT_TENURES)
    parser.add_argument("--time-limit", type=float, default=1200)
    parser.add_argument("--max-iterations", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", default="results/tabu_tenure_tuning.png")
    parser.add_argument("--small-multiples-output", default="results/tabu_tenure_small_multiples.png")
    parser.add_argument("--summary-output", default="results/tabu_tenure_summary.png")
    parser.add_argument("--csv", default="results/tabu_tenure_history.csv")
    parser.add_argument("--summary-csv", default="results/tabu_tenure_summary.csv")
    args = parser.parse_args()

    all_rows = []
    summary_rows = []

    for tenure in args.tenures:
        result, is_valid = _run_tabu(
            args.case,
            tenure,
            args.time_limit,
            args.max_iterations,
            args.seed,
        )
        all_rows.extend(_history_rows(tenure, result))
        summary_rows.append(
            {
                "Tenure": tenure,
                "Status": result.get("status"),
                "Objective": result.get("obj"),
                "Runtime": result.get("runtime", 0),
                "Iterations": len(result.get("history", [])),
                "BestViolationCount": result.get("best_violation_count", 0),
                "ValidSchedule": is_valid,
            }
        )
        print(
            f"tenure={tenure}: status={result.get('status')}, obj={result.get('obj')}, "
            f"valid={is_valid}, runtime={result.get('runtime', 0):.4f}s, "
            f"iterations={len(result.get('history', []))}"
        )

    if not all_rows:
        raise ValueError("No history was returned by Tabu Search.")

    history_df = pd.DataFrame(all_rows)
    summary_df = pd.DataFrame(summary_rows)

    os.makedirs(os.path.dirname(args.csv) or ".", exist_ok=True)
    history_df.to_csv(args.csv, index=False)
    summary_df.to_csv(args.summary_csv, index=False)
    _plot_histories(history_df, summary_df, args.case, args.output)
    _plot_small_multiples(history_df, args.case, args.small_multiples_output)
    _plot_summary(summary_df, args.summary_output)

    print(f"Saved history CSV: {args.csv}")
    print(f"Saved summary CSV: {args.summary_csv}")
    print(f"Saved plot: {args.output}")
    print(f"Saved small-multiples plot: {args.small_multiples_output}")
    print(f"Saved summary plot: {args.summary_output}")


if __name__ == "__main__":
    main()
