// colas.js - Planificador de Colas de Prioridad con Round Robin interno

class ProcesoCola {
    constructor(pid, arrival, burst, priority) {
        this.pid = pid;
        this.arrival = arrival;
        this.burst = burst;
        this.priority = priority;
        this.remaining = burst;
        this.finished = false;
        this.firstExec = null;
    }
    reset() {
        this.remaining = this.burst;
        this.finished = false;
        this.firstExec = null;
    }
}

class ColasScheduler {
    constructor(processes, quantum) {
        // Clonar procesos para evitar efectos colaterales
        this.processes = processes.map(p => new ProcesoCola(p.pid, p.arrival, p.burst, p.priority));
        this.quantum = quantum;
        this.stateTimeline = [];
        this.finishTimes = {};
    }

    ejecutar() {
        let n = this.processes.length;
        let procs = this.processes.map(p => Object.assign(Object.create(Object.getPrototypeOf(p)), p));
        let time = 0, completed = 0;
        let ready = {}; // prioridad -> cola (array)
        let waiting = procs.slice().sort((a, b) => a.arrival - b.arrival);
        let stateTimeline = [];
        let finishTimes = {};
        let current = null;
        let sliceCount = 0;
        let priorities = [...new Set(procs.map(p => p.priority))].sort((a, b) => b - a); // mayor primero

        function enqueue(p) {
            if (!ready[p.priority]) ready[p.priority] = [];
            ready[p.priority].push(p);
        }
        function dequeue() {
            for (let prio of priorities) {
                if (ready[prio] && ready[prio].length > 0) {
                    return ready[prio].shift();
                }
            }
            return null;
        }

        while (completed < n) {
            // Llegadas
            while (waiting.length && waiting[0].arrival <= time) {
                let p = waiting.shift();
                enqueue(p);
                // Preempción estricta
                if (current && p.priority > current.priority) {
                    enqueue(current);
                    current = null;
                    sliceCount = 0;
                }
            }
            // Seleccionar proceso actual si está vacío
            if (!current) {
                current = dequeue();
                if (current && current.firstExec === null) current.firstExec = time;
                sliceCount = 0;
            }
            // Timeline
            let state = {};
            procs.forEach(proc => {
                if (current && proc.pid === current.pid) state[proc.pid] = 'E';
                else if (proc.remaining > 0 && proc.arrival <= time) state[proc.pid] = 'L';
                else state[proc.pid] = '';
            });
            stateTimeline.push(state);
            // Ejecutar un tick
            if (current) {
                current.remaining--;
                sliceCount++;
                // Completado
                if (current.remaining === 0) {
                    finishTimes[current.pid] = time + 1;
                    current.finished = true;
                    completed++;
                    current = null;
                } else if (sliceCount === this.quantum) {
                    enqueue(current);
                    current = null;
                }
            }
            time++;
        }
        // Marcar F en el timeline
        Object.entries(finishTimes).forEach(([pid, ft]) => {
            if (ft < stateTimeline.length) stateTimeline[ft][parseInt(pid)] = 'F';
            else {
                let state = {};
                procs.forEach(proc => state[proc.pid] = '');
                state[pid] = 'F';
                stateTimeline.push(state);
            }
        });
        // Calcular resultados
        let resultados = procs.map(p => {
            let tRetorno = finishTimes[p.pid] - p.arrival;
            let tEspera = tRetorno - p.burst;
            let tComienzo = p.firstExec !== null ? p.firstExec : (finishTimes[p.pid] - p.burst);
            return {pid: p.pid, retorno: tRetorno, espera: tEspera, comienzo: tComienzo, prioridad: p.priority};
        });
        // Generar CSV
        let header = ['Process'];
        for (let t = 0; t < stateTimeline.length; t++) header.push(t);
        let ganttCSV = [header];
        procs.forEach(p => {
            let row = [`P${p.pid}`];
            for (let t = 0; t < stateTimeline.length; t++) {
                row.push(stateTimeline[t][p.pid] || '');
            }
            ganttCSV.push(row);
        });
        return {resultados, stateTimeline, ganttCSV};
    }
}

// Módulo principal para la app de Colas
const ColasApp = (function() {
    function updateTable() {
        let n = parseInt(document.getElementById('num_processes').value);
        let tbody = document.getElementById('tableBody');
        tbody.innerHTML = '';
        for (let i = 0; i < n; i++) {
            let row = `<tr>
                <td>P${i+1}</td>
                <td><input type="number" name="arrival_${i}" value="${i}" min="0" required></td>
                <td><input type="number" name="burst_${i}" value="3" min="1" required></td>
                <td><input type="number" name="priority_${i}" value="1" min="1" max="10" required></td>
            </tr>`;
            tbody.innerHTML += row;
        }
        // Agregar cabecera de prioridad si no existe
        let thead = document.querySelector('#processTable thead tr');
        if (thead && thead.children.length < 4) {
            let th = document.createElement('th');
            th.textContent = 'Prioridad';
            thead.appendChild(th);
        }
    }

    function calcular() {
        let n = parseInt(document.getElementById('num_processes').value);
        let arrivals = [], bursts = [], priorities = [];
        for (let i = 0; i < n; i++) {
            arrivals.push(parseInt(document.getElementsByName('arrival_' + i)[0].value));
            bursts.push(parseInt(document.getElementsByName('burst_' + i)[0].value));
            priorities.push(parseInt(document.getElementsByName('priority_' + i)[0].value));
        }
        let processes = [];
        for (let i = 0; i < n; i++) {
            processes.push(new ProcesoCola(i+1, arrivals[i], bursts[i], priorities[i]));
        }
        // Tomar quantum del input del usuario
        let quantumInput = document.getElementById('quantum');
        let quantum = quantumInput ? parseInt(quantumInput.value) : 3;
        if (isNaN(quantum) || quantum < 1) quantum = 3;
        let scheduler = new ColasScheduler(processes, quantum);
        let {resultados, stateTimeline, ganttCSV} = scheduler.ejecutar();
        // Calcular FI real por la celda 'F'
        let fiPorPid = {};
        processes.forEach(p => {
            for (let t = 0; t < stateTimeline.length; t++) {
                if (stateTimeline[t][p.pid] === 'F') {
                    fiPorPid[p.pid] = t;
                    break;
                }
            }
        });
        // Mostrar tabla de resultados
        let tbodyRes = document.querySelector('#tablaResultados tbody');
        tbodyRes.innerHTML = '';
        resultados.forEach(r => {
            let fi = fiPorPid[r.pid] !== undefined ? (fiPorPid[r.pid] - 1) : (r.retorno + arrivals[r.pid-1]);
            tbodyRes.innerHTML += `<tr><td>P${r.pid}</td><td>${r.retorno}</td><td>${r.espera}</td><td>${r.comienzo}</td><td>${fi}</td>`;
        });
        let act = resultados.reduce((acc, r) => acc + r.retorno, 0) / resultados.length;
        let awt = resultados.reduce((acc, r) => acc + r.espera, 0) / resultados.length;
        document.getElementById('act').textContent = act.toFixed(2);
        document.getElementById('awt').textContent = awt.toFixed(2);
        // Mostrar Gantt como tabla coloreada
        mostrarGantt(stateTimeline, processes);
        // Mostrar CSV como tabla
        mostrarCSV(ganttCSV, processes, quantum, resultados, act, awt, arrivals, bursts, fiPorPid);
        document.getElementById('resultados').style.display = '';
    }

    function mostrarGantt(stateTimeline, processes) {
        let div = document.getElementById('ganttChart');
        let html = '<table class="table table-bordered gantt-table"><thead><tr><th>Proceso</th>';
        for (let t = 0; t < stateTimeline.length; t++) html += `<th>${t}</th>`;
        html += '</tr></thead><tbody>';
        processes.forEach(p => {
            html += `<tr><td>P${p.pid}</td>`;
            for (let t = 0; t < stateTimeline.length; t++) {
                let val = stateTimeline[t][p.pid] || '';
                let cls = val ? 'gantt-' + val : 'gantt-empty';
                html += `<td class="${cls}">${val}</td>`;
            }
            html += '</tr>';
        });
        html += '</tbody></table>';
        div.innerHTML = html;
    }

    function mostrarCSV(csv, processes, quantum, resultados, act, awt, arrivals, bursts, fiPorPid) {
        // Construir cabecera de datos para CSV/Excel
        let entrada = [['Datos de entrada:']];
        entrada.push(['PID', 'Llegada', 'Ejecución', 'Prioridad']);
        processes.forEach((p, i) => {
            entrada.push([`P${p.pid}`, arrivals[i], bursts[i], p.priority]);
        });
        entrada.push(['Quantum usado:', quantum]);
        entrada.push(['']);
        entrada.push(['Tabla de resultados:']);
        entrada.push(['PID', 'CT', 'WT', 'CO', 'FI']);
        resultados.forEach(r => {
            let fi = fiPorPid && fiPorPid[r.pid] !== undefined ? (fiPorPid[r.pid] - 1) : (r.retorno + arrivals[r.pid-1]);
            entrada.push([`P${r.pid}`, r.retorno, r.espera, r.comienzo, fi]);
        });
        entrada.push(['']);
        entrada.push(['T. medio de CT (ACT):', act]);
        entrada.push(['T. medio de WT (AWT):', awt]);
        entrada.push(['']);
        // Unir con el Gantt
        let csvFull = entrada.concat([['Gantt Chart:']]).concat(csv);
        let csvString = csvFull.map(row => row.map(cell => '"'+cell+'"').join(",")).join("\n");
        let downloadBtn = document.getElementById('downloadCSV');
        downloadBtn.onclick = function() {
            let blob = new Blob([csvString], {type: 'text/csv'});
            let url = URL.createObjectURL(blob);
            let a = document.createElement('a');
            a.href = url;
            a.download = 'gantt_chart_colas.csv';
            document.body.appendChild(a);
            a.click();
            setTimeout(() => { document.body.removeChild(a); URL.revokeObjectURL(url); }, 100);
        };
        let downloadExcelBtn = document.getElementById('downloadExcel');
        downloadExcelBtn.onclick = function() {
            let html = '<table border="1" style="border-collapse:collapse;">';
            // Entrada
            entrada.forEach(row => {
                html += '<tr>';
                row.forEach(cell => {
                    html += `<td style="border:1px solid #222;">${cell}</td>`;
                });
                html += '</tr>';
            });
            // Separador visual
            html += '<tr><td colspan="100" style="border:1px solid #222;"><b>Gantt Chart:</b></td></tr>';
            // Gantt
            csv.forEach((row, i) => {
                html += '<tr>';
                row.forEach((cell, j) => {
                    let style = 'border:1px solid #222;';
                    if (i > 0 && j > 0) {
                        if (cell === 'E') style += 'background:#4caf50;color:#fff;';
                        else if (cell === 'L') style += 'background:#ffc107;color:#000;';
                    }
                    html += `<td style="${style}">${cell}</td>`;
                });
                html += '</tr>';
            });
            html += '</table>';
            let blob = new Blob([`<html><head><meta charset='UTF-8'></head><body>${html}</body></html>`], {type: 'application/vnd.ms-excel'});
            let url = URL.createObjectURL(blob);
            let a = document.createElement('a');
            a.href = url;
            a.download = 'gantt_chart_colas.xls';
            document.body.appendChild(a);
            a.click();
            setTimeout(() => { document.body.removeChild(a); URL.revokeObjectURL(url); }, 100);
        };
        document.getElementById('csvTable').innerHTML = '';
    }

    // Exponer funciones globales para el HTML
    return {
        updateTable,
        calcular
    };
})();

// Para integración con el HTML principal
window.ColasApp = ColasApp;
