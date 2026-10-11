"""Self-check cepat: python test_scheduler.py (tanpa framework)."""
from scheduler import SchedulerSimulator, TEST_CASES


def sim(tc_idx, alg, q=None):
    tc = TEST_CASES[tc_idx]
    s = SchedulerSimulator(tc["processes"], alg, q or tc["quantum"])
    procs, timeline = s.simulate()
    by = {p.pid: p for p in procs}
    return by, timeline


def gantt(timeline):
    return [(s, e, lb) for s, e, lb in timeline]


# TC1 FCFS: convoy klasik
by, tl = sim(0, "fcfs")
assert gantt(tl) == [(0, 24, 1), (24, 27, 2), (27, 30, 3)]
assert (by[1].finish, by[2].finish, by[3].finish) == (24, 27, 30)
assert by[1].waiting == 0 and by[3].waiting == 27

# TC1 SJF: short jobs melompati long job
by, tl = sim(0, "sjf")
assert gantt(tl) == [(0, 3, 2), (3, 6, 3), (6, 30, 1)]

# TC4 RR Q=2: slice & context switch
by, tl = sim(3, "rr")
assert by[1].finish == 16 and by[4].finish == 18
assert (by[1].response, by[4].response) == (0, 6)

# TC5 RR Q=4: quantum besar -> lebih sedikit slice
_, tl4 = sim(4, "rr")
assert len(tl4) < len(tl)

# TC7 Priority preemptive: P2 (prio 1) mem-preempt P1
by, tl = sim(6, "priority_p")
assert gantt(tl) == [(0, 2, 1), (2, 6, 2), (6, 9, 3), (9, 17, 1)]
assert by[2].response == 0

# TC13 zero burst: selesai instan, tidak ada slice CPU
by, tl = sim(12, "fcfs")
assert by[1].finish == 0 and by[1].turnaround == 0 and by[1].response == 0
assert gantt(tl) == [(0, 5, 2)]

# TC14 tie-breaker PID untuk semua algoritma non-RR
for alg in ("fcfs", "sjf", "srtf", "priority_np", "priority_p"):
    _, tl = sim(13, alg)
    assert [lb for _, _, lb in tl] == [1, 2, 3], alg

# TC15 idle time tergambar di Gantt
_, tl = sim(14, "fcfs")
assert gantt(tl) == [(0, 2, 1), (2, 10, "IDLE"), (10, 13, 2)]

print("Semua self-check lulus.")
