def read_input(file_path):
    with open(file_path, 'r') as f:
        lines = f.read().splitlines()

    if not lines:
        return None
    
    # Read first line
    first_line = list(map(int, lines[0].split()))
    N, D, A, B = first_line[0], first_line[1], first_line[2], first_line[3]

    # Read employee off days 
    days_off = {}
    for i in range(1, N + 1):
        part = list(map(int, lines[i].split()))
        off_days = [p for p in part if p != '-1']
        days_off[i] = off_days
    
    return N, D, A, B, days_off


# F = [[False] * D for _ in range(N + 1)]
    
#     for i in range(1, N + 1):
#         if i in days_off:
#             for day in days_off[i]:
#                 # Ép kiểu về int nếu trong days_off vẫn đang để dạng chuỗi
#                 d_idx = int(day) 
                
#                 # Kiểm tra điều kiện biên để tránh tràn chỉ số (IndexError)
#                 # Giả định file input lưu index ngày từ 0 đến D-1.
#                 # Nếu file input lưu từ 1 đến D, bạn hãy sửa thành: 0 <= d_idx - 1 < D và F[i][d_idx - 1] = True
#                 if 0 <= d_idx - 1 < D:
#                     F[i][d_idx - 1] = True

