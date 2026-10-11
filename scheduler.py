"""CPU Scheduler Simulator - 6 algoritma, CLI, 15 test case hardcoded.

Algoritma : FCFS, SJF (non-preemptive), SRTF (preemptive), Priority
            (non-preemptive), Priority (preemptive), Round Robin.
Catatan   : angka Priority lebih kecil = prioritas lebih tinggi.

Jalankan  : python scheduler.py          -> menu interaktif
            python scheduler.py --all    -> semua algoritma x semua test case
"""

from collections import deque

IDLE = "IDLE"
DEFAULT_QUANTUM = 2


# --------------------------------------------------------------------------- #
# Model
# --------------------------------------------------------------------------- #
class Process:
    """Satu proses; field hasil (finish/turnaround/...) diisi saat simulasi."""

    def __init__(self, pid, arrival, burst, priority=1):
        self.pid = pid
        self.arrival = arrival
        self.burst = burst
        self.priority = priority
        self.remaining = burst
        self.finish = self.turnaround = self.waiting = self.response = None

    def __repr__(self):
        return f"P{self.pid}"


# --------------------------------------------------------------------------- #
# Simulator
# --------------------------------------------------------------------------- #
class SchedulerSimulator:
    """Simulasi satu algoritma untuk satu kumpulan proses.

    Setiap algoritma hanya membangun `timeline` (daftar (start, end, label));
    perhitungan statistik dipusatkan di _compute sehingga semua algoritma
    memakai definisi finish/TAT/WT/response yang sama.
    """

    def __init__(self, processes, algorithm, quantum=DEFAULT_QUANTUM):
        self.specs = processes  # list of (pid, arrival, burst, priority)
        self.algorithm = algorithm
        self.quantum = quantum

    def simulate(self):
        procs = [Process(*spec) for spec in self.specs]
        timeline = getattr(self, "_" + self.algorithm)(procs)
        self._compute(procs, timeline)
        return procs, timeline

    # -- timeline helper: gabung slice bersebelahan milik proses yang sama -- #
    @staticmethod
    def _emit(timeline, label, start, end):
        if end <= start:
            return  # slice panjang nol (mis. burst 0) tidak digambar
        if timeline and timeline[-1][2] == label and timeline[-1][1] == start:
            s, _, lb = timeline[-1]
            timeline[-1] = (s, end, lb)
        else:
            timeline.append((start, end, label))

    @staticmethod
    def _compute(procs, timeline):
        first, last = {}, {}
        for start, end, label in timeline:
            if label == IDLE:
                continue
            first.setdefault(label, start)
            last[label] = end
        for p in procs:
            if p.burst == 0:  # edge case: selesai instan tanpa CPU
                p.finish = p.arrival
            else:
                p.finish = last[p.pid]
            p.turnaround = p.finish - p.arrival
            p.waiting = p.turnaround - p.burst
            p.response = (first[p.pid] - p.arrival) if p.pid in first else 0

    # ------------------------------ algoritma ------------------------------ #
    def _fcfs(self, procs):
        return self._nonpreemptive(procs, key=lambda p: (p.arrival, p.pid))

    def _sjf(self, procs):
        return self._nonpreemptive(procs, key=lambda p: (p.burst, p.arrival, p.pid))

    def _priority_np(self, procs):
        return self._nonpreemptive(
            procs, key=lambda p: (p.priority, p.arrival, p.pid)
        )

    def _srtf(self, procs):
        return self._preemptive(
            procs, key=lambda p: (p.remaining, p.arrival, p.pid)
        )

    def _priority_p(self, procs):
        return self._preemptive(
            procs, key=lambda p: (p.priority, p.arrival, p.pid)
        )

    def _nonpreemptive(self, procs, key):
        timeline, pending, t = [], sorted(procs, key=lambda p: (p.arrival, p.pid)), 0
        while pending:
            ready = [p for p in pending if p.arrival <= t]
            if not ready:
                t = self._idle(timeline, t, min(p.arrival for p in pending))
                continue
            chosen = min(ready, key=key)
            pending.remove(chosen)
            if chosen.burst > 0:
                self._emit(timeline, chosen.pid, t, t + chosen.burst)
                t += chosen.burst
        return timeline

    def _preemptive(self, procs, key):
        timeline, unfinished, t = [], list(procs), 0
        while unfinished:
            ready = [p for p in unfinished if p.arrival <= t]
            if not ready:
                t = self._idle(timeline, t, min(p.arrival for p in unfinished))
                continue
            cur = min(ready, key=key)
            future = [p.arrival for p in unfinished if p.arrival > t]
            run = cur.remaining if not future else min(cur.remaining, min(future) - t)
            self._emit(timeline, cur.pid, t, t + run)
            t += run
            cur.remaining -= run
            if cur.remaining == 0:
                unfinished.remove(cur)
        return timeline

    def _rr(self, procs):
        timeline, t, i = [], 0, 0
        pending = sorted(procs, key=lambda p: (p.arrival, p.pid))
        queue = deque()
        while queue or i < len(pending):
            if not queue and pending[i].arrival > t:
                t = self._idle(timeline, t, pending[i].arrival)
            while i < len(pending) and pending[i].arrival <= t:
                queue.append(pending[i])
                i += 1
            if not queue:
                continue
            cur = queue.popleft()
            run = min(self.quantum, cur.remaining)
            if run > 0:
                self._emit(timeline, cur.pid, t, t + run)
                t += run
                cur.remaining -= run
            while i < len(pending) and pending[i].arrival <= t:
                queue.append(pending[i])
                i += 1
            if cur.remaining > 0:
                queue.append(cur)
        return timeline

    @staticmethod
    def _idle(timeline, t, next_arrival):
        SchedulerSimulator._emit(timeline, IDLE, t, next_arrival)
        return next_arrival

    # -------------------------------- output ------------------------------- #
    def algs_name(self):
        name = dict(ALGORITHMS)[self.algorithm]
        return f"{name} (Q={self.quantum})" if self.algorithm == "rr" else name

    def report(self, tc_label):
        procs, timeline = self.simulate()
        rows = []
        for p in sorted(procs, key=lambda x: x.pid):
            rows.append([
                f"P{p.pid}", p.arrival, p.burst, p.priority,
                p.finish, p.turnaround, p.waiting, p.response,
            ])
        n = len(procs)
        avg = lambda f: sum(f(p) for p in procs) / n if n else 0.0
        gantt = " ".join(
            f"{s} [{('P%d' % lb) if lb != IDLE else IDLE}] {e}"
            for s, e, lb in timeline
        )
        out = [
            "=" * 78,
            f"Test Case : {tc_label}",
            f"Algoritma : {self.algs_name()}",
            f"Gantt     : {gantt}" if gantt else "Gantt     : (tidak ada eksekusi)",
            "",
            _table(
                ["PID", "Arrival", "Burst", "Priority",
                 "Finish", "Turnaround", "Waiting", "Response"],
                rows,
            ),
            "",
            f"Average Turnaround Time : {avg(lambda p: p.turnaround):.2f}",
            f"Average Waiting Time    : {avg(lambda p: p.waiting):.2f}",
            f"Average Response Time   : {avg(lambda p: p.response):.2f}",
            "=" * 78,
        ]
        return "\n".join(out)


# --------------------------------------------------------------------------- #
# Tabel teks (rata kanan untuk kolom numerik)
# --------------------------------------------------------------------------- #
def _table(headers, rows):
    cols = list(zip(*([headers] + rows)))
    widths = [max(len(str(c)) for c in col) for col in cols]

    def numeric(col):
        return all(str(c).lstrip("-").isdigit() for c in col)

    aligns = [">" if numeric(col) else "<" for col in cols]
    fmt = lambda row: "  ".join(
        f"{str(c):{a}{w}}" for c, a, w in zip(row, aligns, widths)
    )
    sep = "  ".join("-" * w for w in widths)
    return "\n".join([fmt(headers), sep] + [fmt(r) for r in rows])


# --------------------------------------------------------------------------- #
# Test cases: (pid, arrival, burst, priority)
# --------------------------------------------------------------------------- #
TEST_CASES = [
    {"id": "TC1", "name": "Convoy Effect (FCFS klasik)", "quantum": 2,
     "processes": [(1, 0, 24, 1), (2, 0, 3, 1), (3, 0, 3, 1)]},

    {"id": "TC2", "name": "SJF Ideal (arrival & burst bervariasi)", "quantum": 2,
     "processes": [(1, 0, 8, 2), (2, 1, 4, 1), (3, 2, 9, 4),
                   (4, 3, 5, 3), (5, 5, 2, 5)]},

    {"id": "TC3", "name": "SRTF Preemption intens", "quantum": 2,
     "processes": [(1, 0, 10, 3), (2, 1, 4, 2), (3, 2, 2, 1),
                   (4, 3, 1, 4)]},

    {"id": "TC4", "name": "Round Robin Q=2", "quantum": 2,
     "processes": [(1, 0, 5, 1), (2, 0, 4, 1), (3, 0, 3, 1),
                   (4, 0, 6, 1)]},

    {"id": "TC5", "name": "Round Robin Q=4 (pembanding TC4)", "quantum": 4,
     "processes": [(1, 0, 5, 1), (2, 0, 4, 1), (3, 0, 3, 1),
                   (4, 0, 6, 1)]},

    {"id": "TC6", "name": "Priority Non-Preemptive (high prio telat)", "quantum": 2,
     "processes": [(1, 0, 10, 5), (2, 1, 4, 4), (3, 2, 2, 1),
                   (4, 4, 3, 2)]},

    {"id": "TC7", "name": "Priority Preemptive (preempt saat berjalan)", "quantum": 2,
     "processes": [(1, 0, 10, 3), (2, 2, 4, 1), (3, 5, 3, 2)]},

    {"id": "TC8", "name": "Mixed Arrival, Burst Identik (4)", "quantum": 2,
     "processes": [(1, 0, 4, 1), (2, 1, 4, 2), (3, 2, 4, 3),
                   (4, 3, 4, 4), (5, 4, 4, 5)]},

    {"id": "TC9", "name": "Same Arrival, Burst Menurun", "quantum": 2,
     "processes": [(1, 0, 10, 1), (2, 0, 8, 1), (3, 0, 6, 1),
                   (4, 0, 4, 1), (5, 0, 2, 1)]},

    {"id": "TC10", "name": "Interleaved Short & Long", "quantum": 2,
     "processes": [(1, 0, 10, 2), (2, 1, 2, 1), (3, 2, 9, 3),
                   (4, 3, 3, 4)]},

    {"id": "TC11", "name": "Late High Priority (burst kecil, prio 1)", "quantum": 2,
     "processes": [(1, 0, 10, 3), (2, 4, 1, 1), (3, 6, 2, 2)]},

    {"id": "TC12", "name": "Stress Test (8 proses acak)", "quantum": 2,
     "processes": [(1, 0, 7, 3), (2, 3, 2, 1), (3, 5, 9, 4), (4, 8, 1, 2),
                   (5, 10, 6, 5), (6, 12, 3, 1), (7, 14, 5, 3), (8, 15, 4, 2)]},

    {"id": "TC13", "name": "Zero Burst / Instant", "quantum": 2,
     "processes": [(1, 0, 0, 1), (2, 0, 5, 1)]},

    {"id": "TC14", "name": "Identical Everything (tie-breaker PID)", "quantum": 2,
     "processes": [(1, 0, 4, 1), (2, 0, 4, 1), (3, 0, 4, 1)]},

    {"id": "TC15", "name": "Large Gaps / Idle Time", "quantum": 2,
     "processes": [(1, 0, 2, 1), (2, 10, 3, 1)]},
]

ALGORITHMS = [
    ("fcfs", "FCFS"),
    ("sjf", "SJF (Non-Preemptive)"),
    ("srtf", "SRTF (Preemptive)"),
    ("priority_np", "Priority (Non-Preemptive)"),
    ("priority_p", "Priority (Preemptive)"),
    ("rr", "Round Robin"),
]


# --------------------------------------------------------------------------- #
# Runner
# --------------------------------------------------------------------------- #
def run_case(tc, alg_key, quantum=None):
    q = tc.get("quantum", DEFAULT_QUANTUM) if quantum is None else quantum
    sim = SchedulerSimulator(tc["processes"], alg_key, q)
    print(sim.report(f'{tc["id"]} - {tc["name"]}'))
    print()


def run_all(alg_key=None):
    for key, _ in (ALGORITHMS if alg_key is None else [(alg_key, "")]):
        for tc in TEST_CASES:
            run_case(tc, key)


def ask(prompt, default=None):
    raw = input(prompt).strip()
    return default if raw == "" else raw


def menu():
    while True:
        print("\n=== CPU Scheduler Simulator ===")
        for i, (_, name) in enumerate(ALGORITHMS, 1):
            print(f"  {i}) {name}")
        print(f"  {len(ALGORITHMS) + 1}) Semua algoritma x semua test case")
        print("  0) Keluar")
        choice = ask("Pilih: ")
        if choice == "0":
            print("Selesai.")
            return
        if choice == str(len(ALGORITHMS) + 1):
            run_all()
            continue
        if not choice.isdigit() or not 1 <= int(choice) <= len(ALGORITHMS):
            print("Pilihan tidak valid.")
            continue

        key, name = ALGORITHMS[int(choice) - 1]
        quantum = None
        if key == "rr":
            quantum = int(ask(f"Quantum (default {DEFAULT_QUANTUM}): ", DEFAULT_QUANTUM))

        sub = ask(f"Test case untuk {name} [1-{len(TEST_CASES)}, 0=semua]: ", "0")
        if sub == "0":
            run_all(key)
        elif sub.isdigit() and 1 <= int(sub) <= len(TEST_CASES):
            run_case(TEST_CASES[int(sub) - 1], key, quantum)
        else:
            print("Pilihan tidak valid.")


def main():
    import sys

    if "--all" in sys.argv:
        run_all()
    else:
        menu()


if __name__ == "__main__":
    main()
