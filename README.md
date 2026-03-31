# 🏥 Staff Rostering Optimization Project - IT4663 (HUST)

Dự án tối ưu hóa lịch trực nhân viên nhằm giải quyết bài toán điều phối nhân sự phức tạp, tập trung vào mục tiêu đảm bảo sức khỏe nhân viên qua việc **Minimize Max Night-shift** (Tối thiểu hóa số ca đêm lớn nhất của mỗi cá nhân).

## 📋 Mô tả bài toán
Xếp lịch cho $N$ nhân viên trong $D$ ngày. Mỗi ngày gồm 4 ca: Sáng, Trưa, Chiều, Đêm.
* **Ràng buộc cứng:**
    * Mỗi ngày một nhân viên làm tối đa 1 ca.
    * Nghỉ hoàn toàn vào ngày hôm sau nếu trực ca đêm.
    * Mỗi ca phải có số nhân viên trong khoảng $[A, B]$.
    * Tuân thủ lịch nghỉ phép riêng $F(i)$ của từng người.
* **Mục tiêu:** Tìm phương án sao cho số ca đêm lớn nhất của một nhân viên bất kỳ là nhỏ nhất.

## 📂 Cấu trúc dự án
```text
Staff_Rostering_Project/
├── data/                   # 40 Test cases chia vào 4 nhóm: easy, medium, hard, stress
├── results/                # Lưu trữ báo cáo benchmark_results.csv và biểu đồ
├── util/                   # Công cụ hỗ trợ (Generator, Dataloader, Logger)
├── solvers/                
│   ├── logic_exact/        # MILP & CP-SAT (Đã xong)
│   ├── swarm_intelligence/ # GA & ACO 
│   └── local_search/       # SA & TS 
├── main.py                 # File điều phối và chạy so sánh tổng hợp
└── requirements.txt