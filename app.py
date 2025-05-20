import csv
from collections import deque

class Process:
    def __init__(self, pid, priority, burst_time):
        self.pid = pid                        # Process ID
        self.priority = priority              # Priority (lower value = higher priority)
        self.burst_time = burst_time          # Total execution time needed
        self.remaining_time = burst_time      # Remaining execution time
        self.finished = False                 # Flag to indicate if process is finished
        self.first_execution = None           # Time when process first started executing

def round_robin_scheduler(processes, time_quantum):
    """
    Simulates Round Robin scheduling algorithm and tracks process states.
    
    Args:
        processes: List of Process objects
        time_quantum: Time quantum for each process
        
    Returns:
        state_timeline: List of dictionaries with process states at each time unit
    """
    # Create a copy of processes to avoid modifying the original
    process_copies = [Process(p.pid, p.priority, p.burst_time) for p in processes]
    
    # Keep track of process states at each time unit
    state_timeline = []
    current_time = 0
    ready_queue = deque(process_copies)
    
    # Dictionary to map process ID to its object for quick lookup
    process_map = {p.pid: p for p in process_copies}
    
    # Track which processes have arrived in the system
    arrived_processes = set()
    
    # Track if we need to add an F for a process in the next state
    mark_finished = {}
    
    while ready_queue:
        current_process = ready_queue.popleft()
        arrived_processes.add(current_process.pid)
        
        # If this is the first time this process is executing, record the start time
        if current_process.first_execution is None:
            current_process.first_execution = current_time
        
        # Process executes for time_quantum or until completion
        execution_time = min(time_quantum, current_process.remaining_time)
        
        for t in range(execution_time):
            # Create state snapshot for this time unit
            state = {}
            
            # First, handle any process that needs to be marked as finished
            for pid, should_mark in list(mark_finished.items()):
                if should_mark:
                    state[pid] = 'F'
                    mark_finished[pid] = False  # Only mark once
                    process_map[pid].finished = True
                elif process_map[pid].finished:
                    state[pid] = ''  # Process already finished
            
            # Now handle the current process and other processes
            for p in process_copies:
                if p.pid in state:
                    continue  # Already handled
                
                if p.pid == current_process.pid:
                    state[p.pid] = 'E'  # Process is executing
                    
                    # Check if this execution will finish the process
                    if current_process.remaining_time == 1:  # This is the last execution unit
                        # Mark to add an F in the next state
                        mark_finished[p.pid] = True
                elif p.finished:
                    state[p.pid] = ''  # Process already finished
                elif p.pid in arrived_processes:
                    state[p.pid] = 'L'  # Process is waiting in queue
                else:
                    state[p.pid] = ''   # Process hasn't arrived yet
            
            state_timeline.append(state)
            
            # Decrease remaining time of current process
            current_process.remaining_time -= 1
        
        current_time += execution_time
        
        # If process is not marked for finishing, add it back to the queue
        if current_process.remaining_time > 0:
            ready_queue.append(current_process)
    
    # Add one final state if any process needs to be marked as finished
    if any(mark_finished.values()):
        final_state = {}
        for pid, should_mark in mark_finished.items():
            if should_mark:
                final_state[pid] = 'F'
            elif process_map[pid].finished:
                final_state[pid] = ''
            else:
                final_state[pid] = 'L'
        
        for p in process_copies:
            if p.pid not in final_state:
                if p.finished:
                    final_state[p.pid] = ''
                else:
                    final_state[p.pid] = 'L'
        
        state_timeline.append(final_state)
    
    return state_timeline

def generate_gantt_csv(state_timeline, processes, filename="gantt_chart.csv"):
    """
    Generates a CSV file representing the Gantt chart in horizontal format.
    
    States:
    - 'E' for executing
    - 'L' for waiting
    - '' for not started
    - 'F' for finished
    """
    # Create header row with time units
    header = ['Process'] + [str(t) for t in range(len(state_timeline))]
    
    # Create the data matrix for CSV
    csv_data = [header]
    
    for p in processes:
        row = [f'P{p.pid}']
        for t in range(len(state_timeline)):
            row.append(state_timeline[t][p.pid])
        csv_data.append(row)
    
    # Write to CSV
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        for row in csv_data:
            writer.writerow(row)
    
    return filename

def main():
    # Predefined dataset
    processes = [
        Process(1, 0, 7),  # P1: priority 0, burst time 7
        Process(2, 1, 3),  # P2: priority 1, burst time 3
        Process(3, 2, 4),  # P3: priority 2, burst time 4
        Process(4, 4, 2),  # P4: priority 4, burst time 2
        Process(5, 5, 4)   # P5: priority 5, burst time 4
    ]
    
    time_quantum = 3
    print("Quantum:", time_quantum)
    
    # Sort processes by priority (optional)
    processes.sort(key=lambda p: p.priority)
    
    # Run the Round Robin algorithm
    state_timeline = round_robin_scheduler(processes, time_quantum)
    
    # Generate CSV file
    output_file = generate_gantt_csv(state_timeline, processes)
    
    print(f"\nGantt chart has been generated as '{output_file}'")
    print("\nEstados en el diagrama:")
    print("E: Proceso en ejecución")
    print("L: Proceso en espera")
    print("F: Proceso terminado")
    print("(vacío): Proceso no iniciado")

if __name__ == "__main__":
    main()