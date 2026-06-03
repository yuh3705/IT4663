import pandas as pd 
import os

class ExperimentLogger:
    def __init__(self, filepath="results/final_report.csv"):
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
        # 1. Nếu file report chưa tồn tại hoặc đang rỗng -> Ghi mới hoàn toàn rồi thoát
        if not os.path.exists(self.filepath) or os.path.getsize(self.filepath) == 0:
            df = pd.DataFrame(self.results)
            df.to_csv(self.filepath, index=False, encoding='utf-8')
            self.results = []
            return

        # 2. Nếu file đã có dữ liệu cũ -> Đọc toàn bộ file lên bộ nhớ
        df_old = pd.read_csv(self.filepath)

        # 3. Duyệt qua danh sách kết quả vừa chạy xong ở lượt này
        for new_res in self.results:
        
            match_condition = (df_old['Thuật toán'] == new_res['Thuật toán']) & \
                            (df_old['Bộ dữ liệu'] == new_res['Bộ dữ liệu'])
            
            if match_condition.any():
                idx = df_old[match_condition].index[0]
                
                algo_name = new_res['Thuật toán'].lower()
                
                # Nếu trạng thái đã là chuỗi chữ sẵn (như 'OPTIMAL', 'FEASIBLE') thì bỏ qua không map lại nữa
                if isinstance(new_res['Trạng thái'], str):
                    pass 
                # Nếu là số 0 (theo chuẩn ILP của bạn) thì chuyển về OPTIMAL
                elif new_res['Trạng thái'] == 0:
                    new_res['Trạng thái'] = 'OPTIMAL'
                # Nếu là số 1 (theo chuẩn ILP của bạn) thì chuyển về FEASIBLE
                elif new_res['Trạng thái'] == 1:
                    new_res['Trạng thái'] = 'FEASIBLE'
                # Các trường hợp số khác hoặc lỗi
                else:
                    new_res['Trạng thái'] = 'INFEASIBLE/UNKNOWN'
            
                df_old.at[idx, 'Trạng thái'] = str(new_res['Trạng thái'])
                df_old.at[idx, 'Giá trị hàm mục tiêu'] = new_res['Giá trị hàm mục tiêu']
                df_old.at[idx, 'Thời gian chạy(s)'] = new_res['Thời gian chạy(s)']
                
                print(f" Đã cập nhật hàng: {new_res['Thuật toán']} | {new_res['Bộ dữ liệu']}")
            else:
                # Khi tạo hàng mới tinh, ta cũng ép kiểu toàn bộ df mới sang object/string cho đồng bộ
                df_new_row = pd.DataFrame([new_res]).astype(object)
                df_old = pd.concat([df_old, df_new_row], ignore_index=True)
                print(f" Đã thêm mới hàng: {new_res['Thuật toán']} | {new_res['Bộ dữ liệu']}")

        # 4. Ghi đè toàn bộ bảng dữ liệu đã được cập nhật/sửa đổi quay trở lại file CSV
        df_old.to_csv(self.filepath, index=False, encoding='utf-8')
        
        # Reset lại danh sách bộ nhớ tạm để tránh trùng lặp cho lần gọi save() tiếp theo
        self.results = []