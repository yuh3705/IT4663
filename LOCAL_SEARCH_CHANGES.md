# Tóm tắt thay đổi trong Local Search

File này tóm tắt các thay đổi hiện tại trong hai solver:

- `solvers/local_search/hill_climbing_solver.py`
- `solvers/local_search/tabu_search_solver.py`

## Luồng xử lý chung

Cả hai solver hiện chạy theo luồng:

1. Thử khởi tạo ngẫu nhiên một nghiệm feasible đúng 1 lần.
2. Nếu thất bại, tạo một nghiệm relaxed.
3. Repair nghiệm relaxed bằng cách giảm số vi phạm ràng buộc cứng.
4. Khi đã có nghiệm feasible, mới tối ưu hàm mục tiêu ban đầu: giảm số ca đêm lớn nhất của một nhân viên.

Hai solver không còn dùng nhiều lần random restart trong `_build_initial_solution()` nữa. Hàm này hiện chỉ thử khởi tạo ngẫu nhiên một lần.

## Khởi tạo nghiệm ngẫu nhiên

`_build_initial_solution()` hiện chỉ gọi `_construct_random_initial_solution()` đúng một lần.

Nếu lần random đó tạo được lịch hợp lệ, solver bắt đầu ngay từ nghiệm feasible:

```text
violation_count = 0
```

Nếu random thất bại, solver không trả `NO_FEASIBLE_SOLUTION` ngay, mà chuyển sang tạo nghiệm relaxed rồi repair.

## Nghiệm relaxed

Cả hai solver được thêm hàm `_construct_relaxed_initial_solution()`.

Hàm này tạo một lịch đầy đủ, mỗi ngày mỗi ca có đúng `A` nhân viên. Tuy nhiên lịch này có thể vi phạm ràng buộc cứng, ví dụ:

- nhân viên làm vào ngày nghỉ
- nhân viên làm ngay sau ngày trực đêm
- gán ca đêm làm ảnh hưởng ngày hôm sau

Mục đích của nghiệm relaxed là tạo một điểm bắt đầu để local search có thể repair, thay vì dừng ngay khi không khởi tạo được nghiệm feasible.

## Điểm repair

Trong pha repair, solver đánh giá nghiệm bằng:

```text
(violation_count, objective)
```

Trong đó:

- `violation_count` là số vi phạm ràng buộc cứng
- `objective` là số ca đêm lớn nhất của một nhân viên

Solver ưu tiên giảm `violation_count` trước. Khi `violation_count > 0`, giá trị objective chưa nên được hiểu là kết quả hợp lệ của bài toán.

Chỉ khi:

```text
violation_count = 0
```

thì nghiệm mới feasible và objective mới có ý nghĩa.

## Các nước đi repair

Pha repair hiện có hai loại action:

1. `swap`
   - Đổi ca của hai nhân viên trong cùng một ngày.

2. `rebuild_day`
   - Gán lại toàn bộ ca của một ngày đang có vấn đề.
   - Mỗi ca vẫn được gán đúng `A` nhân viên.
   - Khi chọn nhân viên, solver ưu tiên người có penalty thấp hơn.

Penalty khi gán một nhân viên vào một ca xét các lỗi:

- nhân viên nghỉ phép vào ngày đó
- nhân viên vừa trực đêm hôm trước
- nếu gán ca đêm thì có thể xung đột với ngày hôm sau

Nhờ `rebuild_day`, repair mạnh hơn so với chỉ swap cục bộ.

## Thay đổi trong Hill Climbing

Bản `solve()` cũ được đổi tên thành `_solve_feasible_only()` để giữ lại tham khảo.

`solve()` mới có hai pha:

1. Pha repair
   - Chạy khi `violation_count > 0`.
   - Chọn action repair tốt nhất nếu action đó cải thiện score.
   - Nếu bị kẹt nhiều bước không cải thiện, solver restart bằng một nghiệm relaxed mới.

2. Pha tối ưu
   - Chạy khi `violation_count == 0`.
   - Dùng logic Hill Climbing cũ để giảm số ca đêm lớn nhất.
   - Chỉ nhận nước đi nếu tốt hơn hiện tại.

Hill Climbing vẫn dễ kẹt hơn Tabu vì nó tham lam, chỉ nhận move cải thiện trực tiếp.

## Thay đổi trong Tabu Search

Bản `solve()` cũ được đổi tên thành `_solve_feasible_only()`.

`solve()` mới cũng có hai pha:

1. Repair khi nghiệm còn vi phạm ràng buộc.
2. Optimize khi đã có nghiệm feasible.

Trong pha repair, Tabu có thể chọn:

- `swap`
- `rebuild_day`

Tabu list được dùng để tránh quay lại các move gần đây. Với `rebuild_day`, tabu key dựa trên ngày vừa rebuild.

Khác Hill Climbing, Tabu có thể chấp nhận move không cải thiện ngay nếu đó là move tốt nhất không bị tabu. Vì vậy Tabu có khả năng thoát local optimum tốt hơn.

## History trả về

Cả hai solver hiện trả thêm:

```python
"history"
"violation_history"
```

`history` lưu giá trị objective theo từng iteration được log.

`violation_history` lưu số vi phạm ràng buộc cứng tại cùng iteration.

Nếu:

```text
violation_history[i] > 0
```

thì nghiệm tại iteration đó chưa feasible, nên objective ở iteration đó không nên được xem là kết quả hợp lệ.

## Ý nghĩa status

Các status chính:

- `OPTIMAL`
  - Tìm được nghiệm feasible có objective bằng lower bound lý thuyết.

- `FEASIBLE`
  - Tìm được nghiệm feasible nhưng chưa đạt lower bound.

- `NO_FEASIBLE_SOLUTION`
  - Không tìm được nghiệm feasible trong giới hạn thời gian hoặc số iteration.

- `INFEASIBLE`
  - Input vi phạm điều kiện cần cơ bản, ví dụ `A > B` hoặc `4 * A > N`.

## Ghi chú về vẽ plot

`solvers/local_search/run_coverage.py` hiện dùng `history` và `violation_history` để vẽ quá trình chạy.

Nếu solver chưa từng tìm được nghiệm feasible, plot sẽ ẩn objective và chỉ vẽ số vi phạm ràng buộc cứng.

Nếu solver có cả repair phase và optimize phase, plot thể hiện:

- đường violation trong pha repair
- đường objective sau khi `violation_count` về 0

Cách vẽ này tránh nhầm lẫn giữa objective của nghiệm infeasible và objective thật của bài toán.
