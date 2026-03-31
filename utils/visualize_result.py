import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Đọc dữ liệu
csv_path = 'results/final_report.csv'
df = pd.read_csv(csv_path, encoding='utf-8-sig')

# Tiền xử lý: Tách Algo và Group
df[['Algo', 'Group']] = df['Thuật toán'].str.extract(r'(.+) \((.+)\)')

# Sắp xếp nhóm
category_order = ['easy', 'medium', 'hard', 'stress']
df['Group'] = pd.Categorical(df['Group'], categories=category_order, ordered=True)

# 2. Tạo bảng tổng hợp và ĐẶT LẠI TÊN CỘT RÕ RÀNG
summary_table = df.groupby(['Group', 'Algo'], observed=False).agg(
    avg_obj=('Giá trị hàm mục tiêu', 'mean'),
    avg_runtime=('Thời gian chạy(s)', 'mean')
).reset_index()

print("--- BẢNG TỔNG HỢP KẾT QUẢ TRUNG BÌNH ---")
print(summary_table)

# 3. Vẽ biểu đồ
plt.figure(figsize=(10, 6))
sns.set_style("whitegrid")

# Sử dụng tên cột mới đã đặt ở trên (avg_runtime)
sns.lineplot(
    data=summary_table, 
    x='Group', 
    y='avg_runtime', 
    hue='Algo', 
    marker='o', 
    linewidth=2.5
)

# Tùy chỉnh
plt.title('Performance Comparison: CP-SAT vs MILP', fontsize=14, fontweight='bold')
plt.xlabel('Dataset Scale', fontsize=12)
plt.ylabel('Average Runtime (seconds)', fontsize=12)
plt.yscale('log') # Giữ thang log để thấy rõ sự khác biệt ở stress test
plt.legend(title='Algorithms')

# Lưu và hiển thị
os.makedirs('results', exist_ok=True)
plt.savefig('results/performance_chart.png', dpi=300)
print("\n✅ Đã lưu biểu đồ thành công tại: results/performance_chart.png")
plt.show()