import pandas as pd 
import os

class ExperimentLogger:
    def __init__(self):
        self.results = []

    def log(self, solver_name, dataset, N, D, status, obj, runtime):
        self.results.append({
            "Thuật toán" : solver_name,
            "Bộ dữ liệu" : dataset,
            "Số nhân viên" : N,
            "Số ngày" : D,
            "Trạng thái" : status,
            "Giá trị hàm mục tiêu" : obj,
            "Thời gian chạy(s)" : round(runtime, 4)
        })

    def save(self, filepath):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        df = pd.DataFrame(self.results)
        df.to_csv(filepath, index=False, encoding='utf-8-sig')

    