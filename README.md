# Scheduler Simulator

Simulator penjadwalan CPU berbasis CLI dengan Python (tanpa dependency eksternal).
Mendukung 6 algoritma, Gantt chart text-based, tabel statistik, dan 15 test case
siap pakai.

## Requirement

- Python 3.8+ (diuji di 3.11.9). Tidak perlu `pip install` apa pun.

## Cara Run

Jalankan dari folder proyek:

```bash
cd Scheduler-Simulator
```

**1. Menu interaktif** (pilih algoritma, lalu pilih test case):

```bash
python scheduler.py
```

Alur menu:

```
=== CPU Scheduler Simulator ===
  1) FCFS
  2) SJF (Non-Preemptive)
  3) SRTF (Preemptive)
  4) Priority (Non-Preemptive)
  5) Priority (Preemptive)
  6) Round Robin
  7) Semua algoritma x semua test case
  0) Keluar
Pilih:
```

- Pilih `1`-`6` → program menanyakan test case (`1`-`15`, atau `0`/Enter = semua).
- Khusus Round Robin, diminta quantum (Enter = default `2`).
- Pilih `7` → jalankan semua algoritma untuk semua test case sekaligus.

**2. Mode non-interaktif** (langsung semua kombinasi):

```bash
python scheduler.py --all
```

**3. Jalankan self-check** (assert hasil-hasil kunci):

```bash
python test_scheduler.py
```

Contoh menjalankan satu skenario dari Python:

```python
import scheduler as s
s.run_case(s.TEST_CASES[0], "fcfs")        # TC1 dengan FCFS
s.run_case(s.TEST_CASES[3], "rr", 4)       # TC4 dengan Round Robin Q=4
```

## Algoritma

| Kode          | Algoritma                  | Preemptive |
| ------------- | -------------------------- | ---------- |
| `fcfs`        | FCFS                       | Tidak      |
| `sjf`         | SJF                        | Tidak      |
| `srtf`        | SRTF (preemptive SJF)      | Ya         |
| `priority_np` | Priority                   | Tidak      |
| `priority_p`  | Priority                   | Ya         |
| `rr`          | Round Robin (default Q=2)  | Ya         |

Catatan: angka **Priority lebih kecil = prioritas lebih tinggi**. Tie-breaker
selalu `arrival time` lalu `PID` terkecil.

## Contoh Output

```
==============================================================================
Test Case : TC1 - Convoy Effect (FCFS klasik)
Algoritma : FCFS
Gantt     : 0 [P1] 24 24 [P2] 27 27 [P3] 30

PID  Arrival  Burst  Priority  Finish  Turnaround  Waiting  Response
---  -------  -----  --------  ------  ----------  -------  --------
P1   0        24     1         24      24          0        0
P2   0        3      1         27      27          24       24
P3   0        3      1         30      30          27       27

Average Turnaround Time : 27.00
Average Waiting Time    : 17.00
Average Response Time   : 17.00
==============================================================================
```

Saat CPU menganggur, Gantt menampilkan `[IDLE]`, mis.
`0 [P1] 2 2 [IDLE] 10 10 [P2] 13`.

## Test Case

Semua test case ada di list `TEST_CASES` pada `scheduler.py`.

| No   | Skenario                                    |
| ---- | ------------------------------------------- |
| TC1  | Convoy effect FCFS (P1 burst 24, P2/P3 kecil) |
| TC2  | SJF ideal (arrival & burst bervariasi)      |
| TC3  | SRTF dengan preemption intens               |
| TC4  | Round Robin Q=2                             |
| TC5  | Round Robin Q=4 (pembanding TC4)            |
| TC6  | Priority non-preemptive (job telat berprioritas tinggi) |
| TC7  | Priority preemptive (preempt saat berjalan) |
| TC8  | Arrival berselang, burst identik            |
| TC9  | Arrival sama, burst menurun                 |
| TC10 | Interleaved short & long                    |
| TC11 | Late high priority                          |
| TC12 | Stress test 8 proses acak                   |
| TC13 | Zero burst / instant                        |
| TC14 | Identical everything (uji tie-breaker PID)  |
| TC15 | Large gaps / idle time                      |

### Menambah / Mengubah Test Case

Edit langsung `TEST_CASES` di `scheduler.py`:

```python
{"id": "TC16", "name": "Custom", "quantum": 3,
 "processes": [(pid, arrival, burst, priority), ...]},
```

`quantum` hanya dipakai oleh Round Robin; algoritma lain mengabaikannya.

## Struktur Kode

- `Process` — data satu proses + field hasil (finish, turnaround, waiting, response).
- `SchedulerSimulator` — tiap algoritma hanya membangun satu `timeline`
  `(start, end, pid)`; satu fungsi `_compute` menghitung semua statistik
  sehingga definisi TAT/WT/Response konsisten di semua algoritma.
- `TEST_CASES`, `ALGORITHMS` — data test case dan daftar algoritma.
- `run_case()` / `run_all()` / `menu()` — lapisan CLI dan output.
