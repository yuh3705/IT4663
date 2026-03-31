import random
import os

def generate_test_case(N, D, A, B, prob_off = 0.1, file_path="data/input.txt"):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    with open(file_path, 'w') as f:
        f.write(f"{N} {D} {A} {B}\n")

        for _ in range(N):
            off_days = [str(d) for d in range(1, D + 1) if random.random() < prob_off]
            if off_days:
                f.write(" ".join(off_days) + " -1\n")
            else:
                f.write("-1\n")
    print(f"Đã tạo dữ liệu tại {file_path}")

if __name__ == "__main__":
    configs = [
        {"folder": "easy",   "N_range": (10, 20),  "D_range": (7, 10),   "prob": 0.1},
        {"folder": "medium", "N_range": (30, 50),  "D_range": (14, 21),  "prob": 0.15},
        {"folder": "hard",   "N_range": (60, 90),  "D_range": (28, 31),  "prob": 0.2},
        {"folder": "stress", "N_range": (120, 200), "D_range": (60, 90),  "prob": 0.25},
    ]

    for cfg in configs:
        for i in range(1, 11):
            # Pick random in range
            n_val = random.randint(*cfg["N_range"])
            d_val = random.randint(*cfg["D_range"])

            a_val = max(1, int(n_val * 0.15))
            b_val = max(a_val + 1, int(n_val * 0.35))
            
            filename = f"data/{cfg['folder']}/test_{i}.txt"
            generate_test_case(n_val, d_val, a_val, b_val, cfg["prob"], filename)
            
    print("--- Đã sinh xong 40 bộ test case đa dạng! ---")