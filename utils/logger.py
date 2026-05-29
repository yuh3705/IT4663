import pandas as pd 
import os

class ExperimentLogger:
    def __init__(self, filepath):
        self.filepath = filepath
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
            # "Gap time" : gap_time
        })

    def save(self):
        # Nếu danh sách rỗng (thuật toán không được chạy) thì không tạo file
        if not self.results:
            return 
            
        # Tạo thư mục nếu chưa tồn tại dựa trên filepath
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        df = pd.DataFrame(self.results)
        df.to_csv(self.filepath, index=False, encoding='utf-8-sig')