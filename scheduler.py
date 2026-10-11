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
