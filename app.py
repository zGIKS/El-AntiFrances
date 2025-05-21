import csv
from collections import deque

class Process:
    def __init__(self, pid, priority, burst_time, arrival_time=0):
        self.pid = pid
        self.priority = priority
        self.burst_time = burst_time
        self.remaining_time = burst_time
        self.finished = False
        self.first_execution = None
        self.arrival_time = arrival_time

def round_robin_scheduler(processes, time_quantum):
    process_copies = [Process(p.pid, p.priority, p.burst_time, p.arrival_time) for p in processes]
    state_timeline = []
    current_time = 0
    ready_queue = deque()
    waiting = sorted(process_copies, key=lambda p: p.arrival_time)  # procesos por llegar
    process_completion = {}  # Almacena cuándo termina cada proceso para mostrar F
    finish_times = {}  # Nuevo: almacena el tiempo de finalización real de cada proceso

    while ready_queue or waiting:
        # Añadir procesos que han llegado
        while waiting and waiting[0].arrival_time <= current_time:
            ready_queue.append(waiting.pop(0))

        if not ready_queue:
            # No hay procesos listos, avanzar tiempo
            state = {}
            for p in process_copies:
                if p.pid in process_completion and process_completion[p.pid] == current_time:
                    state[p.pid] = 'F'  # Mostrar F en el momento exacto de finalización
                elif p.finished:
                    state[p.pid] = ''  # Ya ha terminado
                else:
                    state[p.pid] = ''  # Aún no ha llegado
            state_timeline.append(state)
            current_time += 1
            continue

        process = ready_queue.popleft()

        if process.first_execution is None:
            process.first_execution = current_time

        execution_time = min(time_quantum, process.remaining_time)

        for i in range(execution_time):
            # Añadir procesos que llegaron en este tick
            while waiting and waiting[0].arrival_time <= current_time:
                ready_queue.append(waiting.pop(0))

            # Preparar el estado para este tick
            state = {}
            for p in process_copies:
                if p.pid in process_completion and process_completion[p.pid] == current_time:
                    state[p.pid] = 'F'
                elif p.finished:
                    state[p.pid] = ''
                elif p.pid == process.pid:
                    if i == execution_time - 1 and process.remaining_time == 1:
                        process_completion[p.pid] = current_time + 1
                        state[p.pid] = 'E'
                    else:
                        state[p.pid] = 'E'
                elif p.arrival_time <= current_time and not p.finished:
                    state[p.pid] = 'L'
                else:
                    state[p.pid] = ''
            state_timeline.append(state)
            process.remaining_time -= 1
            current_time += 1
            if process.remaining_time == 0:
                process.finished = True
                finish_times[process.pid] = current_time  # Guardar tiempo de finalización
                break
        if process.remaining_time > 0:
            ready_queue.append(process)

    for pid, finish_time in process_completion.items():
        if finish_time >= len(state_timeline):
            final_state = {p.pid: '' for p in process_copies}
            final_state[pid] = 'F'
            state_timeline.append(final_state)
        else:
            state_timeline[finish_time][pid] = 'F'

    # Calcular tiempos de retorno y espera
    resultados = []
    for p in process_copies:
        t_retorno = finish_times[p.pid] - p.arrival_time
        t_espera = t_retorno - p.burst_time
        resultados.append({'pid': p.pid, 'retorno': t_retorno, 'espera': t_espera})
    return state_timeline, resultados

def generate_gantt_csv(state_timeline, processes, filename="gantt_chart.csv"):
    header = ['Process'] + [str(t) for t in range(len(state_timeline))]
    csv_data = [header]

    for p in processes:
        row = [f'P{p.pid}']
        for t in range(len(state_timeline)):
            row.append(state_timeline[t][p.pid])
        csv_data.append(row)

    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        for row in csv_data:
            writer.writerow(row)

    return filename

def main():
    try:
        # Define the matrix with process data
        # Each column represents a process: [arrival_time, execution_time]
        process_matrix = [
            # P1   P2   P3   P4   P5
            [0,    1,   2,   4,   5],    # Tiempos de llegada
            [7,    3,   4,   2,   4]     # Tiempos de ejecución
        ]
        
        time_quantum = 3  # Quantum definido
        
        # Extraer datos de la matriz
        num_processes = len(process_matrix[0])
        processes = []
        
        print("\nProcesos registrados desde la matriz:")
        print("PID | Tiempo Llegada | Tiempo Ejecución")
        print("----|----------------|----------------")
        
        for i in range(num_processes):
            arrival_time = process_matrix[0][i]
            burst_time = process_matrix[1][i]
            
            if burst_time <= 0 or arrival_time < 0:
                raise ValueError(f"Error en datos del proceso P{i+1}: El tiempo de ejecución debe ser mayor que cero y el tiempo de llegada debe ser mayor o igual a cero")
                
            # Usando un valor predeterminado para la prioridad ya que no se requiere
            priority = 0
            processes.append(Process(i+1, priority, burst_time, arrival_time))
            print(f"P{i+1} | {arrival_time:14} | {burst_time:16}")
        
        print(f"\nQuantum: {time_quantum}")
        
        # El ordenamiento por tiempo de llegada se mantiene
        processes.sort(key=lambda p: p.arrival_time)
        state_timeline, resultados = round_robin_scheduler(processes, time_quantum)
        output_file = generate_gantt_csv(state_timeline, processes)
        
        print(f"\nGantt chart generado como '{output_file}'")
        print("E: Ejecutando | L: Esperando | F: Finalizado")

        # Mostrar tiempos de completitud y espera
        print("\nPID | CT (Tiempo de Completitud / Complete Time) | WT (Tiempo de Espera / Waiting Time)")
        print("----|------------------------------------------|-------------------------------")
        suma_retorno = 0
        suma_espera = 0
        for r in resultados:
            print(f"P{r['pid']}  | {r['retorno']!r}                                   | {r['espera']!r}")
            suma_retorno += r['retorno']
            suma_espera += r['espera']
        n = len(resultados)
        awt = suma_espera / n
        act = suma_retorno / n
        print(f"\nT. medio de CT (ACT): {act:.2f} (Promedio de Completitud / Average Completion Time)")
        print(f"T. medio de WT (AWT): {awt:.2f} (Promedio de Espera / Average Waiting Time)")

        # Calcular y mostrar el WT en FCFS (no óptimo global, solo secuencial)
        n_fcfs = len(processes)  # Claridad: n es el número de procesos
        procesos_ordenados = sorted(processes, key=lambda p: (p.arrival_time, p.pid))  # Desempate por PID
        wt_fcfs = []
        tiempo_actual = 0
        for i, p in enumerate(procesos_ordenados):
            if tiempo_actual < p.arrival_time:
                tiempo_actual = p.arrival_time
            if i == 0:
                wt_fcfs.append(0)
            else:
                wt_fcfs.append(tiempo_actual - p.arrival_time)
            tiempo_actual += p.burst_time  # burst_time es inmutable
        awt_fcfs = sum(wt_fcfs) / n_fcfs
        print(f"\nWT en FCFS: {awt_fcfs:.2f} (Tiempo de Espera en FCFS / Waiting Time in FCFS)")
    
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Error inesperado: {e}")

if __name__ == "__main__":
    main()
