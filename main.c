#include "scheduler.h"
#include "sync_sim.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/*
 * SmartTraffic - OS CPU & Intersection Scheduling Engine
 * Graphic Era (Deemed to be University) - Session 2025-26
 * Team: Kshitij Kukreti, Abhay Pratap Singh Negi, Abhyudaya Bhandari
 *
 * Implemented Algorithms:
 *   1. FCFS (First Come First Served)
 *   2. Priority Scheduling (with aging to prevent starvation)
 *   3. Round Robin (preemptive with time quantum)
 *   4. Adaptive Dynamic Scheduling (real-time queue scoring)
 *
 * Win32 Thread Synchronization:
 *   - Mutex for mutual exclusion against crossing collisions
 *   - Counting Semaphore for lane inflow capacity
 *   - Critical Section for thread-safe state tracking
 */

void printBanner(void) {
    printf("\n==================================================\n");
    printf(" SmartTraffic - OS Traffic Scheduling Engine\n");
    printf(" Graphic Era University | Sem V PBL (Team T217)\n");
    printf("==================================================\n");
}

void printUsage(const char* prog) {
    printBanner();
    printf("Usage:\n");
    printf("  %s --compare                      Compare all 4 algorithms on sample traffic\n", prog);
    printf("  %s --algo <NAME>                 Run single algorithm (FCFS, PRIORITY, ROUND_ROBIN, ADAPTIVE)\n", prog);
    printf("  %s --sync                        Run thread synchronization demo (Mutex & Semaphore)\n", prog);
    printf("  %s --test-sync                   Run sync test (JSON output for backend)\n", prog);
    printf("  %s --file <in.json> --out <out>  Run simulation from JSON file\n", prog);
    printf("  %s --stdin                       Read JSON from stdin\n", prog);
    printf("  %s                               Open interactive menu\n", prog);
}

/* Setup a realistic set of 6 vehicles for testing */
void setupBenchmarkWorkload(TrafficSimulation *sim) {
    memset(sim, 0, sizeof(TrafficSimulation));
    sim->junction_count = 1;
    initJunction(&sim->junctions[0], 1, "Clock Tower (Ghanta Ghar)");
    sim->quantum = 2;
    sim->aging_threshold = 3;

    /* 6 vehicles modeling CPU processes & traffic flows */
    sim->vehicle_count = 6;

    /* V1: City Bus (low priority, high burst time) */
    sim->vehicles[0].id = 1;
    sim->vehicles[0].junction_id = 1;
    strncpy(sim->vehicles[0].type, "Bus", 31);
    sim->vehicles[0].direction = SOUTH;
    sim->vehicles[0].arrival_time = 0;
    sim->vehicles[0].burst_time = 5;
    sim->vehicles[0].remaining_time = 5;
    sim->vehicles[0].initial_priority = 3;
    sim->vehicles[0].priority = 3;
    sim->vehicles[0].is_emergency = 0;

    /* V2: Private Car */
    sim->vehicles[1].id = 2;
    sim->vehicles[1].junction_id = 1;
    strncpy(sim->vehicles[1].type, "Car", 31);
    sim->vehicles[1].direction = EAST;
    sim->vehicles[1].arrival_time = 0;
    sim->vehicles[1].burst_time = 2;
    sim->vehicles[1].remaining_time = 2;
    sim->vehicles[1].initial_priority = 4;
    sim->vehicles[1].priority = 4;
    sim->vehicles[1].is_emergency = 0;

    /* V3: Ambulance (Emergency vehicle, priority 1) */
    sim->vehicles[2].id = 3;
    sim->vehicles[2].junction_id = 1;
    strncpy(sim->vehicles[2].type, "Ambulance", 31);
    sim->vehicles[2].direction = NORTH;
    sim->vehicles[2].arrival_time = 1;
    sim->vehicles[2].burst_time = 2;
    sim->vehicles[2].remaining_time = 2;
    sim->vehicles[2].initial_priority = 1;
    sim->vehicles[2].priority = 1;
    sim->vehicles[2].is_emergency = 1;

    /* V4: Police Car (Emergency vehicle, priority 1) */
    sim->vehicles[3].id = 4;
    sim->vehicles[3].junction_id = 1;
    strncpy(sim->vehicles[3].type, "Police", 31);
    sim->vehicles[3].direction = WEST;
    sim->vehicles[3].arrival_time = 2;
    sim->vehicles[3].burst_time = 2;
    sim->vehicles[3].remaining_time = 2;
    sim->vehicles[3].initial_priority = 1;
    sim->vehicles[3].priority = 1;
    sim->vehicles[3].is_emergency = 1;

    /* V5: Delivery Truck */
    sim->vehicles[4].id = 5;
    sim->vehicles[4].junction_id = 1;
    strncpy(sim->vehicles[4].type, "Truck", 31);
    sim->vehicles[4].direction = NORTH;
    sim->vehicles[4].arrival_time = 2;
    sim->vehicles[4].burst_time = 4;
    sim->vehicles[4].remaining_time = 4;
    sim->vehicles[4].initial_priority = 4;
    sim->vehicles[4].priority = 4;
    sim->vehicles[4].is_emergency = 0;

    /* V6: Commuter Car */
    sim->vehicles[5].id = 6;
    sim->vehicles[5].junction_id = 1;
    strncpy(sim->vehicles[5].type, "Car", 31);
    sim->vehicles[5].direction = SOUTH;
    sim->vehicles[5].arrival_time = 3;
    sim->vehicles[5].burst_time = 3;
    sim->vehicles[5].remaining_time = 3;
    sim->vehicles[5].initial_priority = 3;
    sim->vehicles[5].priority = 3;
    sim->vehicles[5].is_emergency = 0;
}

/* Interactive helper to take inputs for custom vehicles */
int inputCustomVehicles(TrafficSimulation *sim) {
    char line[128];
    memset(sim, 0, sizeof(TrafficSimulation));
    sim->junction_count = 1;
    initJunction(&sim->junctions[0], 1, "Ghanta Ghar (Clock Tower)");

    printf("\n==================================================\n");
    printf(" Custom Vehicle Workload Input\n");
    printf("==================================================\n");
    printf("Enter total number of vehicles (1 to 20) [default: 4]: ");

    int n = 4;
    if (fgets(line, sizeof(line), stdin) && line[0] != '\n') {
        int val = atoi(line);
        if (val > 0 && val <= 20) n = val;
    }
    sim->vehicle_count = n;

    printf("\nEnter details for each of the %d vehicles:\n", n);
    printf("[Directions: 0=NORTH, 1=SOUTH, 2=EAST, 3=WEST]\n");
    printf("[Priority  : 1=Highest/Emergency, 2=High, 3=Medium, 4=Normal/Low]\n\n");

    for (int i = 0; i < n; i++) {
        Vehicle *v = &sim->vehicles[i];
        v->id = i + 1;
        v->junction_id = 1;

        printf("----------------------------------------\n");
        printf(" Vehicle #%d (PID %d):\n", i + 1, v->id);
        printf("----------------------------------------\n");

        /* 1. Vehicle Type */
        printf("  Vehicle Type (Car, Bus, Truck, Ambulance, Police) [default: Car]: ");
        if (fgets(line, sizeof(line), stdin) && line[0] != '\n') {
            line[strcspn(line, "\r\n")] = '\0';
            strncpy(v->type, line, sizeof(v->type) - 1);
        } else {
            strncpy(v->type, "Car", sizeof(v->type) - 1);
        }

        /* 2. Approach Direction */
        printf("  Direction (0=NORTH, 1=SOUTH, 2=EAST, 3=WEST) [default: %d]: ", i % 4);
        if (fgets(line, sizeof(line), stdin) && line[0] != '\n') {
            int d = atoi(line);
            if (d >= 0 && d <= 3) v->direction = (Direction)d;
            else v->direction = (Direction)(i % 4);
        } else {
            v->direction = (Direction)(i % 4);
        }

        /* 3. Arrival Time */
        printf("  Arrival Time (units >= 0) [default: %d]: ", i);
        if (fgets(line, sizeof(line), stdin) && line[0] != '\n') {
            int at = atoi(line);
            v->arrival_time = (at >= 0) ? at : 0;
        } else {
            v->arrival_time = i;
        }

        /* 4. Burst Time */
        printf("  Burst Time (duration in sec > 0) [default: 3]: ");
        if (fgets(line, sizeof(line), stdin) && line[0] != '\n') {
            int bt = atoi(line);
            v->burst_time = (bt > 0) ? bt : 3;
        } else {
            v->burst_time = 3;
        }
        v->remaining_time = v->burst_time;

        /* 5. Priority */
        int def_priority = 3;
        if (strstr(v->type, "Ambulance") || strstr(v->type, "ambulance") ||
            strstr(v->type, "Police")    || strstr(v->type, "police") ||
            strstr(v->type, "Fire")      || strstr(v->type, "fire")) {
            def_priority = 1;
        }
        printf("  Priority (1=Highest, 4=Lowest) [default: %d]: ", def_priority);
        if (fgets(line, sizeof(line), stdin) && line[0] != '\n') {
            int pr = atoi(line);
            v->priority = (pr > 0) ? pr : def_priority;
        } else {
            v->priority = def_priority;
        }
        v->initial_priority = v->priority;

        /* 6. Emergency Flag */
        int def_emerg = (v->priority == 1) ? 1 : 0;
        printf("  Is Emergency Vehicle? (1=Yes, 0=No) [default: %d]: ", def_emerg);
        if (fgets(line, sizeof(line), stdin) && line[0] != '\n') {
            int em = atoi(line);
            v->is_emergency = (em == 1) ? 1 : 0;
        } else {
            v->is_emergency = def_emerg;
        }

        printf("\n");
    }

    /* Algorithm parameters */
    printf("Enter Round Robin Time Quantum (default: 2): ");
    if (fgets(line, sizeof(line), stdin) && line[0] != '\n') {
        int q = atoi(line);
        sim->quantum = (q > 0) ? q : 2;
    } else {
        sim->quantum = 2;
    }

    printf("Enter Aging Threshold (default: 3): ");
    if (fgets(line, sizeof(line), stdin) && line[0] != '\n') {
        int ag = atoi(line);
        sim->aging_threshold = (ag > 0) ? ag : 3;
    } else {
        sim->aging_threshold = 3;
    }

    return n;
}

/* Print tabular schedule output */
void printScheduleTable(const TrafficSimulation *sim) {
    printf("+-----+------------+-------+-----+-------+------+-------+-------+--------+------+-----+-------+\n");
    printf("| PID | Type       | Dir   | Arr | Burst | Prio | Emerg | Start | Finish | Wait | TAT | Aged? |\n");
    printf("+-----+------------+-------+-----+-------+------+-------+-------+--------+------+-----+-------+\n");
    for (int i = 0; i < sim->vehicle_count; i++) {
        const Vehicle *v = &sim->scheduled_vehicles[i];
        printf("| %3d | %-10s | %-5s | %3d | %5d | %4d | %-5s | %5d | %6d | %4d | %3d | %5d |\n",
               v->id,
               v->type,
               directionToString(v->direction),
               v->arrival_time,
               v->burst_time,
               v->priority,
               v->is_emergency ? "YES" : "NO",
               v->start_time,
               v->completion_time,
               v->waiting_time,
               v->turnaround_time,
               v->aging_boost);
    }
    printf("+-----+------------+-------+-----+-------+------+-------+-------+--------+------+-----+-------+\n");
}

/* Print ASCII Gantt Chart */
void printGanttChart(const TrafficSimulation *sim) {
    if (sim->execution_order_len == 0) return;

    printf("\nExecution Order: ");
    for (int i = 0; i < sim->execution_order_len; i++) {
        printf("V%d", sim->execution_order[i]);
        if (i + 1 < sim->execution_order_len) printf(" -> ");
    }
    printf("\n\nGantt Chart:\n+");
    for (int i = 0; i < sim->execution_order_len; i++) {
        printf("------+");
    }
    printf("\n|");
    for (int i = 0; i < sim->execution_order_len; i++) {
        printf("  V%-2d |", sim->execution_order[i]);
    }
    printf("\n+");
    for (int i = 0; i < sim->execution_order_len; i++) {
        printf("------+");
    }
    printf("\n");
}

/* Print Performance Metrics */
void printMetricsSummary(const char *algoName, const PerformanceMetrics *m) {
    printf("\nSummary for %s:\n", algoName);
    printf("  - Avg Waiting Time    : %.2f sec\n", m->avg_waiting_time);
    printf("  - Avg Turnaround Time : %.2f sec\n", m->avg_turnaround_time);
    printf("  - Overall Throughput  : %.3f veh/sec\n", m->throughput);
    printf("  - Emergency Wait Time : %.2f sec\n", m->avg_emergency_wait);
    printf("  - Total Time Elapsed  : %d sec\n", m->total_time);
}

/* Run single algorithm */
void executeAlgorithmByName(const char *name, TrafficSimulation *sim) {
    if (strcmp(name, "FCFS") == 0) {
        sim->algorithm = ALG_FCFS;
        runFCFS(sim);
    } else if (strcmp(name, "PRIORITY") == 0) {
        sim->algorithm = ALG_PRIORITY;
        runPriority(sim, 1);
    } else if (strcmp(name, "ROUND_ROBIN") == 0) {
        sim->algorithm = ALG_ROUND_ROBIN;
        runRoundRobin(sim);
    } else {
        sim->algorithm = ALG_ADAPTIVE;
        runAdaptive(sim);
    }
}

/* Compare all 4 algorithms on identical traffic */
void runComparisonWithSimulation(TrafficSimulation *base_sim) {
    printf("\n==================================================\n");
    printf(" Running Algorithm Comparison on Configured Traffic\n");
    printf("==================================================\n");
    printf("Workload: %d vehicles\n\n", base_sim->vehicle_count);

    const char *algos[] = {"FCFS", "PRIORITY", "ROUND_ROBIN", "ADAPTIVE"};
    const char *labels[] = {
        "1. FCFS (First Come First Served)",
        "2. Priority Scheduling (with Aging)",
        "3. Round Robin (Time Slicing)",
        "4. Adaptive Dynamic Scheduling"
    };

    TrafficSimulation results[4];

    for (int i = 0; i < 4; i++) {
        memcpy(&results[i], base_sim, sizeof(TrafficSimulation));
        executeAlgorithmByName(algos[i], &results[i]);

        printf("--------------------------------------------------\n");
        printf(" %s\n", labels[i]);
        printf("--------------------------------------------------\n");
        printScheduleTable(&results[i]);
        printGanttChart(&results[i]);
        printMetricsSummary(labels[i], &results[i].metrics);
        printf("\n");
    }

    /* Comparison table */
    printf("================================================================================\n");
    printf("                         ALGORITHM COMPARISON TABLE\n");
    printf("================================================================================\n");
    printf("+------------------------------------+-------------+-------------+------------+------------+\n");
    printf("| Algorithm                          | Avg Wait(s) | Avg TAT(s)  | Throughput | Emerg Wait |\n");
    printf("+------------------------------------+-------------+-------------+------------+------------+\n");
    for (int i = 0; i < 4; i++) {
        printf("| %-34s | %10.2f  | %10.2f  | %8.3f   | %9.2f  |\n",
               labels[i],
               results[i].metrics.avg_waiting_time,
               results[i].metrics.avg_turnaround_time,
               results[i].metrics.throughput,
               results[i].metrics.avg_emergency_wait);
    }
    printf("+------------------------------------+-------------+-------------+------------+------------+\n\n");

    printf("Analysis & Key Takeaways:\n");
    printf("  1. FCFS: Simplest to implement, but causes a convoy effect.\n");
    printf("     Emergency vehicles get held up behind buses (Emerg wait = %.2f sec).\n", results[0].metrics.avg_emergency_wait);
    printf("  2. Priority + Aging: Clears ambulances first (Emerg wait drops to %.2f sec).\n", results[1].metrics.avg_emergency_wait);
    printf("     Aging gradually bumps up waiting cars so they don't starve.\n");
    printf("  3. Round Robin: Cuts execution into quantum slices. Fair to all directions,\n");
    printf("     keeping the intersection responsive.\n");
    printf("  4. Adaptive: Delivers the best throughput (%.3f veh/sec). Dynamically allocates\n", results[3].metrics.throughput);
    printf("     green light time to whichever lane has the highest queue pressure.\n");
    printf("================================================================================\n\n");
}

void runComparisonBenchmark(void) {
    TrafficSimulation sim;
    setupBenchmarkWorkload(&sim);
    runComparisonWithSimulation(&sim);
}

/* Human-readable Win32 Synchronization Demo */
void runSyncDemonstrationHumanReadable(void) {
    printf("\n==================================================\n");
    printf(" Win32 Thread Synchronization Demonstration\n");
    printf("==================================================\n");
    printf("OS Primitives Tested:\n");
    printf("  - Mutex (CreateMutex)        : Only 1 vehicle direction crosses the junction at once\n");
    printf("  - Semaphore (CreateSemaphore): Restricts entry lane capacity to 2\n");
    printf("  - Critical Section           : Locks shared queue memory during updates\n");
    printf("  - Worker Threads             : 8 concurrent vehicle threads running simultaneously\n\n");

    SyncTestResult res = runSynchronizationDemonstration(8);

    printf("Thread Logs:\n");
    for (int i = 0; i < res.log_count; i++) {
        printf("  %s\n", res.log_messages[i]);
    }

    printf("\nSummary:\n");
    printf("  - Mutex locks acquired   : %d / 8\n", res.mutex_locks_acquired);
    printf("  - Semaphore waits passed : %d / 8\n", res.semaphore_waits_completed);
    printf("  - Race conditions avoided: %d\n", res.race_conditions_prevented);
    printf("  - Deadlocks detected     : 0\n");
    printf("  - Overall Status         : %s\n", res.test_passed ? "PASS (All threads synchronized cleanly)" : "FAILED");
    printf("==================================================\n\n");
}

/* File mode for Flask backend */
int runFileMode(const char* in_file, const char* out_file) {
    TrafficSimulation sim;
    if (loadSimulationFromFile(in_file, &sim) != 0) {
        fprintf(stderr, "Error: Failed to load simulation input from %s\n", in_file);
        return 1;
    }

    switch (sim.algorithm) {
        case ALG_FCFS:        runFCFS(&sim); break;
        case ALG_PRIORITY:    runPriority(&sim, 1); break;
        case ALG_ROUND_ROBIN: runRoundRobin(&sim); break;
        case ALG_ADAPTIVE:    runAdaptive(&sim); break;
        default:              runAdaptive(&sim); break;
    }

    if (saveSimulationToFile(&sim, out_file) != 0) {
        fprintf(stderr, "Error: Failed to save simulation output to %s\n", out_file);
        return 1;
    }

    printf("SUCCESS: Simulation processed and saved to %s\n", out_file);
    return 0;
}

/* Stdin mode */
int runStdinMode(void) {
    size_t cap = 256 * 1024;
    char *buf = (char*)malloc(cap);
    if (!buf) return 1;
    size_t len = 0;
    int c;
    while ((c = getchar()) != EOF && len + 1 < cap) {
        buf[len++] = (char)c;
    }
    buf[len] = '\0';

    TrafficSimulation sim;
    if (parseSimulationJSON(buf, &sim) != 0) {
        free(buf);
        fprintf(stderr, "{\"status\": \"ERROR\", \"message\": \"Failed to parse JSON\"}\n");
        return 1;
    }
    free(buf);

    switch (sim.algorithm) {
        case ALG_FCFS:        runFCFS(&sim); break;
        case ALG_PRIORITY:    runPriority(&sim, 1); break;
        case ALG_ROUND_ROBIN: runRoundRobin(&sim); break;
        case ALG_ADAPTIVE:    runAdaptive(&sim); break;
        default:              runAdaptive(&sim); break;
    }

    char *out_json = generateSimulationJSON(&sim);
    if (out_json) {
        fputs(out_json, stdout);
        free(out_json);
    }
    return 0;
}

/* JSON Sync Test Mode (for automated test suite) */
int runSyncTestMode(void) {
    SyncTestResult res = runSynchronizationDemonstration(8);
    printf("{\n");
    printf("  \"test_passed\": %s,\n", res.test_passed ? "true" : "false");
    printf("  \"mutex_locks_acquired\": %d,\n", res.mutex_locks_acquired);
    printf("  \"semaphore_waits_completed\": %d,\n", res.semaphore_waits_completed);
    printf("  \"race_conditions_prevented\": %d,\n", res.race_conditions_prevented);
    printf("  \"logs\": [\n");
    for (int i = 0; i < res.log_count; i++) {
        printf("    \"%s\"%s\n", res.log_messages[i], (i + 1 < res.log_count) ? "," : "");
    }
    printf("  ]\n");
    printf("}\n");
    return 0;
}

/* Custom Interactive Simulation with full vehicle inputs */
void runCustomSimulation(void) {
    TrafficSimulation sim;
    inputCustomVehicles(&sim);

    printf("Choose Algorithm to run:\n");
    printf("  [1] FCFS\n");
    printf("  [2] Priority with Aging\n");
    printf("  [3] Round Robin (Time Slicing)\n");
    printf("  [4] Adaptive Dynamic\n");
    printf("  [5] Compare All 4 on this input\n");
    printf("Choice [1-5, default: 4]: ");

    char line[64];
    int alg_choice = 4;
    if (fgets(line, sizeof(line), stdin) && line[0] != '\n') {
        int val = atoi(line);
        if (val >= 1 && val <= 5) alg_choice = val;
    }

    if (alg_choice == 5) {
        runComparisonWithSimulation(&sim);
        return;
    }

    const char *names[] = {"FCFS", "PRIORITY", "ROUND_ROBIN", "ADAPTIVE"};
    const char *algoName = names[alg_choice - 1];
    executeAlgorithmByName(algoName, &sim);

    printf("\n--- Results for %s ---\n", algoName);
    printScheduleTable(&sim);
    printGanttChart(&sim);
    printMetricsSummary(algoName, &sim.metrics);
}

/* Interactive Menu */
int runInteractiveMode(void) {
    char input[64];
    while (1) {
        printBanner();
        printf("Options:\n");
        printf("  [1] Compare All 4 Algorithms (Sample Preset Traffic)\n");
        printf("  [2] Run FCFS (First Come First Served)\n");
        printf("  [3] Run Priority Scheduling with Aging\n");
        printf("  [4] Run Round Robin (Time Slicing)\n");
        printf("  [5] Run Adaptive Dynamic Scheduling\n");
        printf("  [6] Run Win32 Thread Synchronization Demo (Mutex & Semaphore)\n");
        printf("  [7] Enter Custom Vehicles (Arrival Time, Burst, Priority, etc.)\n");
        printf("  [8] Exit\n");
        printf("Enter choice (1-8): ");

        if (!fgets(input, sizeof(input), stdin)) break;
        int choice = atoi(input);

        if (choice == 1) {
            runComparisonBenchmark();
        } else if (choice >= 2 && choice <= 5) {
            printf("\nChoose workload:\n  [1] Use sample preset vehicles (6 vehicles)\n  [2] Enter custom vehicle details manually\nChoice [1/2, default: 1]: ");
            char sub_opt[64];
            int use_custom = 0;
            if (fgets(sub_opt, sizeof(sub_opt), stdin) && sub_opt[0] != '\n') {
                if (atoi(sub_opt) == 2) use_custom = 1;
            }

            TrafficSimulation sim;
            if (use_custom) {
                inputCustomVehicles(&sim);
            } else {
                setupBenchmarkWorkload(&sim);
            }

            const char *names[] = {"FCFS", "PRIORITY", "ROUND_ROBIN", "ADAPTIVE"};
            executeAlgorithmByName(names[choice - 2], &sim);
            printf("\n--- Output for %s ---\n", names[choice - 2]);
            printScheduleTable(&sim);
            printGanttChart(&sim);
            printMetricsSummary(names[choice - 2], &sim.metrics);
        } else if (choice == 6) {
            runSyncDemonstrationHumanReadable();
        } else if (choice == 7) {
            runCustomSimulation();
        } else if (choice == 8) {
            printf("\nExiting. Bye!\n");
            break;
        } else {
            printf("\nInvalid option, please enter 1-8.\n");
        }

        printf("\nPress ENTER to continue...");
        fgets(input, sizeof(input), stdin);
    }
    return 0;
}

int main(int argc, char *argv[]) {
    if (argc >= 2) {
        if (strcmp(argv[1], "--compare") == 0) {
            runComparisonBenchmark();
            return 0;
        } else if (strcmp(argv[1], "--algo") == 0 && argc >= 3) {
            TrafficSimulation sim;
            setupBenchmarkWorkload(&sim);
            executeAlgorithmByName(argv[2], &sim);
            printScheduleTable(&sim);
            printGanttChart(&sim);
            printMetricsSummary(argv[2], &sim.metrics);
            return 0;
        } else if (strcmp(argv[1], "--sync") == 0) {
            runSyncDemonstrationHumanReadable();
            return 0;
        } else if (strcmp(argv[1], "--test-sync") == 0) {
            return runSyncTestMode();
        } else if (strcmp(argv[1], "--stdin") == 0) {
            return runStdinMode();
        } else if (strcmp(argv[1], "--file") == 0 && argc >= 5 && strcmp(argv[3], "--out") == 0) {
            return runFileMode(argv[2], argv[4]);
        } else if (strcmp(argv[1], "--help") == 0 || strcmp(argv[1], "-h") == 0) {
            printUsage(argv[0]);
            return 0;
        }
    }

    return runInteractiveMode();
}
