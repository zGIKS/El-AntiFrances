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
    # Manual input for processes
    try:
        process_count = int(input("Ingrese la cantidad de procesos: "))
        time_quantum = int(input("Ingrese el quantum de tiempo: "))
        
        if process_count <= 0 or time_quantum <= 0:
            raise ValueError("La cantidad de procesos y el quantum deben ser mayores que cero")
            
        processes = []
        
        print("\n--- Ingrese los datos para cada proceso ---")
        for i in range(1, process_count + 1):
            print(f"\nProceso P{i}:")
            arrival_time = int(input(f"Tiempo de llegada para P{i}: "))
            burst_time = int(input(f"Tiempo de ejecución para P{i}: "))
            
            if burst_time <= 0 or arrival_time < 0:
                raise ValueError("El tiempo de ejecución debe ser mayor que cero y el tiempo de llegada debe ser mayor o igual a cero")
                
            # Usando un valor predeterminado para la prioridad ya que no se requiere
            priority = 0
            processes.append(Process(i, priority, burst_time, arrival_time))
        
        print("\nQuantum:", time_quantum)
        print("\nProcesos registrados:")
        print("PID | Tiempo Llegada | Tiempo Ejecución")
        print("----|----------------|----------------")
        for p in processes:
            print(f"P{p.pid} | {p.arrival_time:14} | {p.burst_time:16}")
        
        # El ordenamiento por tiempo de llegada se mantiene
        processes.sort(key=lambda p: p.arrival_time)
        state_timeline = round_robin_scheduler(processes, time_quantum)
        output_file = generate_gantt_csv(state_timeline, processes)
        
        print(f"\nGantt chart generado como '{output_file}'")
        print("E: Ejecutando | L: Esperando | F: Finalizado")
    
    except ValueError as e:
        print(f"Error: {e}")
        print("Por favor, ingrese valores numéricos válidos.")
    except Exception as e:
        print(f"Error inesperado: {e}")

def calcular_tiempos_desde_gantt(gantt_csv, tiempos_llegada, tiempos_ejecucion):
    with open(gantt_csv, newline='') as csvfile:
        reader = list(csv.reader(csvfile))
        procesos = reader[1:]
        resultados = []
        for idx, row in enumerate(procesos):
            llegada = tiempos_llegada[idx]
            ejecucion = tiempos_ejecucion[idx]
            # Buscar la última columna con 'E' o 'F'
            fin = 0
            for i in range(1, len(row)):
                if row[i] in ('E', 'F'):
                    fin = i
            t_retorno = fin - llegada
            t_espera = t_retorno - ejecucion
            resultados.append({'retorno': t_retorno, 'espera': t_espera})
        return resultados

def mostrar_resultados_excel():
    tiempos_llegada = [0, 1, 2, 4, 5]
    tiempos_ejecucion = [7, 3, 4, 2, 4]
    
    # Calculando manualmente según el Gantt
    # P1: termina en t=19, llegó en t=0 → retorno = 19
    # P2: termina en t=6, llegó en t=1 → retorno = 5
    # P3: termina en t=18, llegó en t=2 → retorno = 16
    # P4: termina en t=14, llegó en t=4 → retorno = 10
    # P5: termina en t=20, llegó en t=5 → retorno = 15
    # Total: 19 + 5 + 16 + 10 + 15 = 65
    # Promedio: 65/5 = 13.0
    
    resultados = calcular_tiempos_desde_gantt('gantt_chart.csv', tiempos_llegada, tiempos_ejecucion)
    tiempos_retorno = [r['retorno'] for r in resultados]
    tiempos_espera = [r['espera'] for r in resultados]
    
    print("\nCálculo detallado:")
    print("PID | T. Llegada | T. Finalización | T. Retorno | T. Espera")
    print("----|------------|-----------------|------------|----------")
    
    # Calcula manualmente los valores esperados
    fin_p1 = 19  # Posición donde está 'F' para P1
    fin_p2 = 6   # Posición donde está 'F' para P2
    fin_p3 = 18  # Posición donde está 'F' para P3
    fin_p4 = 14  # Posición donde está 'F' para P4
    fin_p5 = 20  # Posición donde está 'F' para P5
    
    t_retorno_p1 = fin_p1 - tiempos_llegada[0]
    t_retorno_p2 = fin_p2 - tiempos_llegada[1]
    t_retorno_p3 = fin_p3 - tiempos_llegada[2]
    t_retorno_p4 = fin_p4 - tiempos_llegada[3]
    t_retorno_p5 = fin_p5 - tiempos_llegada[4]
    
    t_espera_p1 = t_retorno_p1 - tiempos_ejecucion[0]
    t_espera_p2 = t_retorno_p2 - tiempos_ejecucion[1]
    t_espera_p3 = t_retorno_p3 - tiempos_ejecucion[2]
    t_espera_p4 = t_retorno_p4 - tiempos_ejecucion[3]
    t_espera_p5 = t_retorno_p5 - tiempos_ejecucion[4]
    
    print(f"P1  | {tiempos_llegada[0]:10} | {fin_p1:15} | {t_retorno_p1:10} | {t_espera_p1:8}")
    print(f"P2  | {tiempos_llegada[1]:10} | {fin_p2:15} | {t_retorno_p2:10} | {t_espera_p2:8}")
    print(f"P3  | {tiempos_llegada[2]:10} | {fin_p3:15} | {t_retorno_p3:10} | {t_espera_p3:8}")
    print(f"P4  | {tiempos_llegada[3]:10} | {fin_p4:15} | {t_retorno_p4:10} | {t_espera_p4:8}")
    print(f"P5  | {tiempos_llegada[4]:10} | {fin_p5:15} | {t_retorno_p5:10} | {t_espera_p5:8}")
    
    # Calcular y mostrar los promedios manuales
    tiempos_retorno_manual = [t_retorno_p1, t_retorno_p2, t_retorno_p3, t_retorno_p4, t_retorno_p5]
    tiempos_espera_manual = [t_espera_p1, t_espera_p2, t_espera_p3, t_espera_p4, t_espera_p5]
    
    suma_retorno_manual = sum(tiempos_retorno_manual)
    suma_espera_manual = sum(tiempos_espera_manual)
    n = len(tiempos_retorno_manual)
    
    print(f"\nTiempos de retorno calculados manualmente: {tiempos_retorno_manual}")
    print(f"Suma de tiempos de retorno: {suma_retorno_manual}")
    print(f"T. medio de Retorno (manual): {suma_retorno_manual/n}")
    print(f"T. medio de Espera (manual): {suma_espera_manual/n}")
    
    # Verificar si los tiempos del algoritmo coinciden
    print(f"\nTiempos de retorno desde Gantt CSV: {tiempos_retorno}")
    suma_retorno = sum(tiempos_retorno)
    suma_espera = sum(tiempos_espera)
    print(f"Suma de tiempos de retorno: {suma_retorno}")
    print(f"T. medio de Retorno (CSV): {suma_retorno/n}")
    print(f"T. medio de Espera (CSV): {suma_espera/n}")

if __name__ == "__main__":
    mostrar_resultados_excel()
