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

