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
                # Procesar la marca F para los procesos que terminaron exactamente en este momento
                if p.pid in process_completion and process_completion[p.pid] == current_time:
                    state[p.pid] = 'F'
                elif p.finished:
                    state[p.pid] = ''  # Ya ha terminado
                elif p.pid == process.pid:
                    # Último tick de ejecución del proceso actual
                    if i == execution_time - 1 and process.remaining_time == 1:
                        # Marcar este momento para mostrar F después
                        process_completion[p.pid] = current_time + 1
                        state[p.pid] = 'E'  # Aún ejecutando en este tick
                    else:
                        state[p.pid] = 'E'  # Ejecutando normalmente
                elif p.arrival_time <= current_time and not p.finished:
                    state[p.pid] = 'L'  # Esperando
                else:
                    state[p.pid] = ''  # No ha llegado todavía
            
            state_timeline.append(state)
            process.remaining_time -= 1
            current_time += 1
            
            # Verificar si el proceso ha terminado
            if process.remaining_time == 0:
                process.finished = True
                break

        # Añadir proceso de vuelta a la cola si no ha terminado
        if process.remaining_time > 0:
            ready_queue.append(process)

    # Asegurarse de que todos los procesos tengan su marca F
    for pid, finish_time in process_completion.items():
        # Si el tiempo de finalización está fuera del timeline actual
        if finish_time >= len(state_timeline):
            # Añadir un estado más con la marca F
            final_state = {p.pid: '' for p in process_copies}
            final_state[pid] = 'F'
            state_timeline.append(final_state)
        else:
            # Marcar F en el momento correspondiente
            state_timeline[finish_time][pid] = 'F'

    return state_timeline

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
            [0,    1,   2,   3,   4],    # Tiempos de llegada
            [5,    3,   8,   2,   4]     # Tiempos de ejecución
        ]
        
        time_quantum = 2  # Quantum definido
        
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
        state_timeline = round_robin_scheduler(processes, time_quantum)
        output_file = generate_gantt_csv(state_timeline, processes)
        
        print(f"\nGantt chart generado como '{output_file}'")
        print("E: Ejecutando | L: Esperando | F: Finalizado")
    
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Error inesperado: {e}")

if __name__ == "__main__":
    main()
