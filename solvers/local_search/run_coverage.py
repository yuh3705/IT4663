import os
import sys
import time
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))

# Thêm thư mục gốc vào hệ thống tìm kiếm của Python nếu chưa có
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from solvers.local_search import hill_climbing_solver, tabu_search_solver

def read_test_case(filepath):
    """Hàm đọc file dataset .txt của bạn"""
    with open(filepath, 'r') as f:
        lines = f.readlines()
        
    first_line = lines[0].strip()
    N, D, A, B = map(int, first_line.split())
    days_off = {}
    
    line_idx = 1
    for i in range(1, N + 1):
        if line_idx < len(lines):
            parts = list(map(int, lines[line_idx].split()))
            days_off[i] = [day for day in parts if day != -1]
            line_idx += 1
            
    return N, D, A, B, days_off

def main():
    # 1. Đường dẫn tới 1 file test nhóm HARD hoặc STRESS của bạn
    # SỬA LẠI ĐƯỜNG DẪN NÀY CHO ĐÚNG VỚI MÁY BẠN
    test_file = "/Users/binhminh/Desktop/IT4663 PRJ/IT4663/data/stress/test_1.txt" 
    
    print(f"Đang đọc dữ liệu từ: {test_file}")
    N, D, A, B, F = read_test_case(test_file)
    
    # 2. Tạo thư mục kết quả nếu chưa có
    os.makedirs("results/hill_climbing", exist_ok=True)
    os.makedirs("results/tabu", exist_ok=True)
    
    # 3. Chạy thuật toán
    print("Đang chạy Hill Climbing...")
    res_hc = hill_climbing_solver.solve(N, D, A, B, F, time_limit=20)
    history_hc = res_hc.get("history", [])
    
    print("Đang chạy Tabu Search...")
    res_tabu = tabu_search_solver.solve(N, D, A, B, F, time_limit=300, max_iterations=1000)
    history_tabu = res_tabu.get("history", [])
    
    # 4. Cân bằng độ dài mảng (Vì Hill Climbing hay bị kẹt và dừng sớm)
    # Ta sẽ kéo dài mảng của Hill Climbing thành một đường nằm ngang để dễ vẽ so sánh
    max_len = max(len(history_hc), len(history_tabu))
    
    if len(history_hc) < max_len:
        last_val = history_hc[-1]
        history_hc.extend([last_val] * (max_len - len(history_hc)))
    
    if len(history_tabu) < max_len:
        last_val = history_tabu[-1]
        history_tabu.extend([last_val] * (max_len - len(history_tabu)))
        
    # 5. Lưu ra file CSV
    df = pd.DataFrame({
        "Iteration": range(max_len),
        "Hill_Climbing_Obj": history_hc,
        "Tabu_Search_Obj": history_tabu
    })
    
    df.to_csv("results/hill_climbing/iterations.csv", index=False)
    df.to_csv("results/tabu/iterations.csv", index=False)
    print(" Đã lưu lịch sử vòng lặp ra thư mục 'results/'")
    
    # 6. Vẽ biểu đồ đường hội tụ (Convergence Plot)
    plt.figure(figsize=(12, 6))
    sns.set_theme(style="darkgrid")
    
    plt.plot(df["Iteration"], df["Hill_Climbing_Obj"], label='Hill Climbing (Kẹt cục bộ)', color='red', linewidth=2)
    plt.plot(df["Iteration"], df["Tabu_Search_Obj"], label='Tabu Search (Thoát cục bộ)', color='blue', linewidth=2, alpha=0.8)
    
    plt.title("Biểu đồ Hội tụ so sánh khả năng thoát cực tiểu cục bộ (Convergence Plot)", fontsize=14, fontweight='bold', pad=15)
    plt.xlabel("Số vòng lặp (Iterations)", fontsize=12)
    plt.ylabel("Giá trị Hàm mục tiêu (Max Night-shifts)", fontsize=12)
    plt.legend(fontsize=12)
    
    # Giới hạn trục Y để nhìn rõ độ nhấp nhô của Tabu
    if history_hc and history_tabu:
        min_y = min(min(history_hc), min(history_tabu)) - 1
        max_y = max(max(history_hc), max(history_tabu)) + 1
    elif history_hc: # Chỉ Hill Climbing có dữ liệu
        min_y = min(history_hc) - 1
        max_y = max(history_hc) + 1
    elif history_tabu: # Chỉ Tabu Search có dữ liệu
        min_y = min(history_tabu) - 1
        max_y = max(history_tabu) + 1
    else: # Cả hai đều rỗng (Không thuật toán nào tìm được nghiệm)
        min_y = 0
        max_y = B  #
    plt.ylim(min_y, max_y)
    
    plt.tight_layout()
    plt.savefig("results/convergence_plot.png", dpi=300)
    print(" Đã vẽ xong biểu đồ! Kiểm tra file 'results/convergence_plot.png'")
    plt.show()

if __name__ == "__main__":
    main()
