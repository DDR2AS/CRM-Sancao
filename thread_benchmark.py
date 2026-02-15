"""
Threading Benchmark: GIL vs Free-threaded Python
Compares sequential vs threaded execution for CPU-bound and I/O-bound tasks.
"""

"""
Here are the results side by side:

  Results Comparison

  ┌──────────────────────┬───────────────────┬──────────────────────────────┐
  │      Benchmark       │ Python 3.11 (GIL) │ Python 3.14t (Free-threaded) │
  ├──────────────────────┼───────────────────┼──────────────────────────────┤
  │ CPU-bound sequential │ 7.19s             │ 7.81s                        │
  ├──────────────────────┼───────────────────┼──────────────────────────────┤
  │ CPU-bound 4 threads  │ 6.88s             │ 2.69s                        │
  ├──────────────────────┼───────────────────┼──────────────────────────────┤
  │ CPU-bound speedup    │ 1.05x             │ 2.90x                        │
  ├──────────────────────┼───────────────────┼──────────────────────────────┤
  │ I/O-bound sequential │ 2.00s             │ 2.00s                        │
  ├──────────────────────┼───────────────────┼──────────────────────────────┤
  │ I/O-bound 4 threads  │ 0.50s             │ 0.51s                        │
  ├──────────────────────┼───────────────────┼──────────────────────────────┤
  │ I/O-bound speedup    │ 3.97x             │ 3.95x                        │
  └──────────────────────┴───────────────────┴──────────────────────────────┘

  Key Takeaways

  1. CPU-bound work: Python 3.11 got only 1.05x speedup with 4 threads (the GIL serializes everything). Python 3.14t got 2.90x speedup — threads are truly running in parallel.
  2. I/O-bound work: Both versions got ~4x speedup, because the GIL is released during I/O operations anyway.
  3. Single-threaded overhead: Python 3.14t's sequential time is slightly slower (7.81s vs 7.19s) — this is the ~10% single-threaded performance cost of the free-threading machinery. This tradeoff is worth it when you use multiple threads for CPU-bound work.
  4. The speedup wasn't a perfect 4x because of threading overhead and OS scheduling, but 2.90x with 4 threads is a dramatic improvement over 1.05x.

  The benchmark file is at thread_benchmark.py in your project. To run Python 3.14t yourself, use:
  uv run --python 3.14t thread_benchmark.py

  Sources:
  - https://www.python.org/downloads/release/python-3140/
  - https://py-free-threading.github.io/running-gil-disabled/
  - https://towardsdatascience.com/python-3-14-and-the-end-of-the-gil/
"""

"""
Sin GIL es mejor cuando:                                                                                                                                                                                                                                                                                                                                                            
  - Trabajo CPU-bound con múltiples hilos — Pasamos de 1.05x a 2.90x de speedup. Es una mejora enorme. Si tu aplicación hace cálculos pesados en paralelo (procesamiento de datos, machine learning, criptografía, etc.), el free-threading es un game changer.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       
  Con GIL está bien cuando:

  - Trabajo I/O-bound (requests HTTP, lectura de archivos, bases de datos) — Ambas versiones dieron ~4x speedup. El GIL ya se libera durante I/O, así que no hay diferencia real.
  - Código single-threaded — Python 3.14t fue un poco más lento en secuencial (7.81s vs 7.19s), hay un ~8-10% de overhead por la maquinaria del free-threading.

  Resumen rápido:

  ┌──────────────────────────────┬───────────────────┬───────────────────────────────────┐
  │          Escenario           │        GIL        │              Sin GIL              │
  ├──────────────────────────────┼───────────────────┼───────────────────────────────────┤
  │ CPU-bound + hilos            │ Malo              │ Mucho mejor                       │
  ├──────────────────────────────┼───────────────────┼───────────────────────────────────┤
  │ I/O-bound + hilos            │ Bien              │ Igual                             │
  ├──────────────────────────────┼───────────────────┼───────────────────────────────────┤
  │ Single-threaded              │ Ligeramente mejor │ ~10% más lento                    │
  ├──────────────────────────────┼───────────────────┼───────────────────────────────────┤
  │ Compatibilidad con librerías │ Todo funciona     │ Algunas librerías aún no soportan │
  └──────────────────────────────┴───────────────────┴───────────────────────────────────┘

  En la práctica: La mayoría de aplicaciones web/API son I/O-bound, así que el GIL nunca fue un problema real para ellas. Donde el free-threading brilla es en procesamiento de datos, cómputo científico, y cualquier tarea CPU-intensiva que quieras paralelizar con hilos en lugar de usar multiprocessing (que es más pesado porque crea procesos separados con su propia      
  memoria).

  El futuro de Python va hacia free-threading — eventualmente será el default. Por ahora es una opción opt-in que vale la pena para workloads CPU-bound paralelos.
"""

"""
Recomendación

Quédate con Python 3.11 estándar para tu CRM. Python 3.14t sería útil si tu app hiciera cálculos pesados en paralelo (procesamiento de imágenes, ML, simulaciones), pero no es el caso.
"""
import sys
import time
import threading
import math
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- Config ---
NUM_WORKERS = 4
CPU_WORK_SIZE = 5_000_000  # iterations per worker
IO_SIMULATED_DELAY = 0.5   # seconds per worker

def print_header():
    print("=" * 60)
    print("        THREADING BENCHMARK")
    print("=" * 60)
    print(f"Python version : {sys.version}")
    if hasattr(sys, "_is_gil_enabled"):
        print(f"GIL enabled    : {sys._is_gil_enabled()}")
    else:
        print(f"GIL enabled    : Yes (no free-threading support)")
    print(f"Workers        : {NUM_WORKERS}")
    print(f"CPU work size  : {CPU_WORK_SIZE:,} iterations/worker")
    print("=" * 60)


# --- CPU-bound task (pure Python math) ---
def cpu_bound_work(n):
    """Heavy computation that holds the GIL in standard Python."""
    total = 0.0
    for i in range(1, n + 1):
        total += math.sqrt(i) * math.sin(i) / (i + 1)
    return total


# --- I/O-bound task (simulated with sleep) ---
def io_bound_work(delay):
    """Simulates I/O wait (network, disk, etc.)."""
    time.sleep(delay)
    return delay


def run_sequential_cpu():
    results = []
    for _ in range(NUM_WORKERS):
        results.append(cpu_bound_work(CPU_WORK_SIZE))
    return results


def run_threaded_cpu():
    results = []
    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        futures = [executor.submit(cpu_bound_work, CPU_WORK_SIZE) for _ in range(NUM_WORKERS)]
        for f in as_completed(futures):
            results.append(f.result())
    return results


def run_sequential_io():
    results = []
    for _ in range(NUM_WORKERS):
        results.append(io_bound_work(IO_SIMULATED_DELAY))
    return results


def run_threaded_io():
    results = []
    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        futures = [executor.submit(io_bound_work, IO_SIMULATED_DELAY) for _ in range(NUM_WORKERS)]
        for f in as_completed(futures):
            results.append(f.result())
    return results


def benchmark(label, func):
    start = time.perf_counter()
    func()
    elapsed = time.perf_counter() - start
    print(f"  {label:<35} {elapsed:.4f}s")
    return elapsed


def main():
    print_header()

    # --- CPU-bound benchmarks ---
    print("\n[1] CPU-BOUND WORK (pure Python math loop)")
    print("-" * 50)
    seq_cpu = benchmark("Sequential", run_sequential_cpu)
    thr_cpu = benchmark(f"Threaded ({NUM_WORKERS} threads)", run_threaded_cpu)
    speedup_cpu = seq_cpu / thr_cpu
    print(f"  {'Speedup:':<35} {speedup_cpu:.2f}x")
    if speedup_cpu < 1.2:
        print("  ^ GIL is preventing true parallelism!")
    else:
        print("  ^ Threads are running in TRUE parallel (no GIL)!")

    # --- I/O-bound benchmarks ---
    print(f"\n[2] I/O-BOUND WORK (sleep {IO_SIMULATED_DELAY}s x {NUM_WORKERS} workers)")
    print("-" * 50)
    seq_io = benchmark("Sequential", run_sequential_io)
    thr_io = benchmark(f"Threaded ({NUM_WORKERS} threads)", run_threaded_io)
    speedup_io = seq_io / thr_io
    print(f"  {'Speedup:':<35} {speedup_io:.2f}x")
    print("  ^ I/O-bound tasks benefit from threads even with the GIL.")

    # --- Summary ---
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  CPU-bound speedup: {speedup_cpu:.2f}x  ", end="")
    if speedup_cpu < 1.2:
        print("(GIL bottleneck)")
    else:
        print("(FREE-THREADED!)")
    print(f"  I/O-bound speedup: {speedup_io:.2f}x")
    print()
    if speedup_cpu < 1.2:
        print("  With the GIL, CPU-bound threads can't run in parallel.")
        print("  Try running this with Python 3.14t (free-threaded) to see")
        print("  real parallel speedup!")
    else:
        print("  Free-threaded Python is running threads in TRUE parallel!")
        print("  CPU-bound work scales across threads without the GIL.")
    print("=" * 60)


if __name__ == "__main__":
    main()

