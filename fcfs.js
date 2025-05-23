// fcfs.js - Lógica principal de la calculadora FCFS
// Inspirado en la estructura de script.js (Round Robin)

// Si Proceso ya está definido, no lo redefinir
if (typeof Proceso === 'undefined') {
class Proceso {
    constructor(pid, arrival, burst) {
        this.pid = pid;
        this.arrival = arrival;
        this.burst = burst;
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
}

class FCFSScheduler {
    constructor(processes) {
        // Clonar procesos para evitar efectos colaterales
        this.processes = processes.map(p => new Proceso(p.pid, p.arrival, p.burst));
        this.stateTimeline = [];
        this.finishTimes = {};
    }

    ejecutar() {
        let n = this.processes.length;
        let procs = this.processes.map(p => Object.assign(Object.create(Object.getPrototypeOf(p)), p));
        let time = 0, completed = 0;
        let ready = [];
        let stateTimeline = [];
        let finishTimes = {};
        let waiting = procs.slice().sort((a, b) => a.arrival - b.arrival);

        while (completed < n) {
            while (waiting.length && waiting[0].arrival <= time) {
                ready.push(waiting.shift());
            }
            if (ready.length === 0) {
                stateTimeline.push({});
                time++;
                continue;
            }
            let p = ready.shift();
            if (p.firstExec === null) p.firstExec = time;
            for (let i = 0; i < p.burst; i++) {
                let state = {};
                procs.forEach(proc => {
                    if (proc.pid === p.pid) state[proc.pid] = 'E';
                    else if (proc.arrival > time) state[proc.pid] = '';
                    else if (proc.remaining > 0) state[proc.pid] = 'L';
                    else state[proc.pid] = '';
                });
                stateTimeline.push(state);
                p.remaining--;
                time++;
                while (waiting.length && waiting[0].arrival <= time) {
                    ready.push(waiting.shift());
                }
            }
            p.finished = true;
            finishTimes[p.pid] = time;
            completed++;
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
            let tComienzo = p.firstExec !== null ? p.firstExec : (finishTimes[p.pid] - p.burst); // CO
            return {pid: p.pid, retorno: tRetorno, espera: tEspera, comienzo: tComienzo};
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

// Módulo principal (IIFE para evitar contaminación global)
const FCFSApp = (function() {
    function updateTable() {
        let n = parseInt(document.getElementById('num_processes').value);
        let tbody = document.getElementById('tableBody');
        tbody.innerHTML = '';
        for (let i = 0; i < n; i++) {
            let row = `<tr>\n                <td>P${i+1}</td>\n                <td><input type="number" name="arrival_${i}" value="${i}" min="0" required></td>\n                <td><input type="number" name="burst_${i}" value="3" min="1" required></td>\n            </tr>`;
            tbody.innerHTML += row;
        }
    }

    function calcular() {
        let n = parseInt(document.getElementById('num_processes').value);
        let arrivals = [], bursts = [];
        for (let i = 0; i < n; i++) {
            arrivals.push(parseInt(document.getElementsByName('arrival_' + i)[0].value));
            bursts.push(parseInt(document.getElementsByName('burst_' + i)[0].value));
        }
        let processes = [];
        for (let i = 0; i < n; i++) {
            processes.push(new Proceso(i+1, arrivals[i], bursts[i]));
        }
        let scheduler = new FCFSScheduler(processes);
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
        mostrarCSV(ganttCSV, processes, resultados, act, awt, arrivals, bursts, fiPorPid);
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

    function mostrarCSV(csv, processes, resultados, act, awt, arrivals, bursts, fiPorPid) {
        // Construir cabecera de datos para CSV/Excel
        let entrada = [['Datos de entrada:']];
        entrada.push(['PID', 'Llegada', 'Ejecución']);
        processes.forEach((p, i) => {
            entrada.push([`P${p.pid}`, arrivals[i], bursts[i]]);
        });
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
            a.download = 'gantt_chart_fcfs.csv';
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
                        else if (cell === 'F') style += 'background:#e53935;color:#fff;';
                        else style += 'background:#f5f5f5;';
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
            a.download = 'gantt_chart_fcfs.xls';
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

document.addEventListener('DOMContentLoaded', FCFSApp.updateTable);
window.updateTable = FCFSApp.updateTable;
window.calcular = FCFSApp.calcular;