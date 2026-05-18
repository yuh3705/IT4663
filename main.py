import os
import glob
from utils.data_loader import read_input
from utils.logger import ExperimentLogger
from solvers.logic_exact import cp_solver, milp_solver
from solvers.greedy import greedy_solver
from solvers.local_search import tabu_search_solver

def main():
    logger = ExperimentLogger()
    TIME_LIMIT = 60 # Giới hạn 60s cho mỗi test case
    
    # Dùng recursive=True để tìm tất cả file .txt trong mọi thư mục con của data/
    test_files = glob.glob("data/**/*.txt", recursive=True)
    test_files.sort() # Sắp xếp để chạy từ easy đến stress

    for fpath in test_files:
        # Lấy tên folder (easy/medium/...) và tên file
        category = os.path.basename(os.path.dirname(fpath))
        fname = os.path.basename(fpath)
        
        print(f"\n Running {category}/{fname}...")
        
        data = read_input(fpath)
        if not data: continue
        N, D, A, B, F = data
        
        # Chạy CP-SAT
        res_cp = cp_solver.solve(N, D, A, B, F, time_limit=TIME_LIMIT)
        # Ghi log kèm theo category để dễ vẽ biểu đồ sau này
        logger.log(f"CP-SAT ({category})", fname, N, D, res_cp['status'], res_cp['obj'], res_cp['runtime'])
        
        # Chạy MILP
        res_milp = milp_solver.solve(N, D, A, B, F, time_limit=TIME_LIMIT)
        logger.log(f"MILP ({category})", fname, N, D, res_milp['status'], res_milp['obj'], res_milp['runtime'])

        res_greedy = greedy_solver.solve(N, D, A, B, F, time_limit=TIME_LIMIT)
        logger.log(f"Greedy ({category})", fname, N, D, res_greedy['status'], res_greedy['obj'], res_greedy['runtime'])

        res_tabu = tabu_search_solver.solve(N, D, A, B, F, time_limit=TIME_LIMIT)
        logger.log(f"Tabu Search ({category})", fname, N, D, res_tabu['status'], res_tabu['obj'], res_tabu['runtime'])

    logger.save("results/final_report.csv")

if __name__ == "__main__":
    main()
