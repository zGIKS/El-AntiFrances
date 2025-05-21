import csv
from collections import deque
from flask import Flask, render_template, request, redirect, url_for
import os
import matplotlib
matplotlib.use('Agg')  # Usar backend no interactivo para evitar errores con Flask
import matplotlib.pyplot as plt
import numpy as np

app = Flask(__name__)

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

# Utilidad para dibujar el Gantt como imagen
def draw_gantt(state_timeline, processes, filename):
    fig, ax = plt.subplots(figsize=(max(8, len(state_timeline)//2), 2+len(processes)*0.5))
    yticks = []
    ylabels = []
    colors = {'E': '#4caf50', 'L': '#ffc107', 'F': '#2196f3', '': '#f5f5f5'}
    for idx, p in enumerate(processes):
        yticks.append(idx)
        ylabels.append(f'P{p.pid}')
        last = None
        start = 0
        for t, state in enumerate(state_timeline):
            val = state[p.pid]
            if val != last:
                if last is not None and last != '':
                    ax.barh(idx, t-start, left=start, color=colors[last], edgecolor='k', height=0.5)
                start = t
                last = val
        if last and last != '':
            ax.barh(idx, len(state_timeline)-start, left=start, color=colors[last], edgecolor='k', height=0.5)
    ax.set_yticks(yticks)
    ax.set_yticklabels(ylabels)
    ax.set_xlabel('Tiempo')
    ax.set_title('Diagrama de Gantt')
    ax.grid(True, axis='x', linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

# Utilidad para leer el CSV generado
def read_csv_table(filename):
    with open(filename, newline='') as f:
        return list(csv.reader(f))

@app.route('/', methods=['GET', 'POST'])
def index():
    results = None
    if request.method == 'POST':
        n = int(request.form['num_processes'])
        quantum = int(request.form['quantum'])
        arrivals = [int(request.form[f'arrival_{i}']) for i in range(n)]
        bursts = [int(request.form[f'burst_{i}']) for i in range(n)]
        processes = [Process(i+1, 0, bursts[i], arrivals[i]) for i in range(n)]
        # Calcular para varios quantums
        quantums = list(range(1, 11))
        resultados_quantum = []
        for q in quantums:
            test_procs = [Process(p.pid, p.priority, p.burst_time, p.arrival_time) for p in processes]
            _, res = round_robin_scheduler(test_procs, q)
            awt = sum(r['espera'] for r in res) / len(res)
            resultados_quantum.append((q, round(awt,2)))
        quantum_optimo, awt_optimo = min(resultados_quantum, key=lambda x: x[1])
        # Calcular resultados para el quantum elegido
        processes.sort(key=lambda p: p.arrival_time)
        state_timeline, resultados = round_robin_scheduler(processes, quantum)
        act = round(sum(r['retorno'] for r in resultados)/len(resultados),2)
        awt = round(sum(r['espera'] for r in resultados)/len(resultados),2)
        # Guardar Gantt como imagen
        static_path = os.path.join(app.root_path, 'static')
        if not os.path.exists(static_path):
            os.makedirs(static_path)
        gantt_img = os.path.join(static_path, 'gantt.png')
        draw_gantt(state_timeline, processes, gantt_img)
        # Leer CSV para mostrarlo como tabla
        csv_file = os.path.join(app.root_path, 'gantt_chart.csv')
        generate_gantt_csv(state_timeline, processes, csv_file)
        csv_data = read_csv_table(csv_file)
        results = {
            'quantum_optimo': quantum_optimo,
            'awt_optimo': awt_optimo,
            'resultados_quantum': resultados_quantum,
            'resultados': resultados,
            'act': act,
            'awt': awt,
            'csv_data': csv_data
        }
    return render_template('index.html', results=results)

if __name__ == '__main__':
    app.run(debug=True)
