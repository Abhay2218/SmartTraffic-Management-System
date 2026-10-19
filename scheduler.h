#ifndef SCHEDULER_H
#define SCHEDULER_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_VEHICLES 250
#define MAX_JUNCTIONS 10
#define MAX_ROADS 20
#define MAX_EVENTS 1000

/* =========================================================
   ENUMS
   ========================================================= */

typedef enum {
    NORTH = 0,
    SOUTH = 1,
    EAST = 2,
    WEST = 3
} Direction;

typedef enum {
    SIGNAL_RED = 0,
    SIGNAL_YELLOW = 1,
    SIGNAL_GREEN = 2
} SignalState;

typedef enum {
    ALG_FCFS = 0,
    ALG_PRIORITY = 1,
    ALG_ROUND_ROBIN = 2,
    ALG_ADAPTIVE = 3
} SchedulingAlgorithm;

typedef enum {
    STATE_WAITING = 0,
    STATE_RUNNING = 1,
    STATE_COMPLETED = 2,
    STATE_BLOCKED = 3
} VehicleState;

/* =========================================================
   DATA STRUCTURES
   ========================================================= */

typedef struct {
    int id;
    int junction_id;
    char type[32];
    Direction direction;
    int arrival_time;
    int burst_time;
    int remaining_time;
    int initial_priority;
    int priority;          /* Current effective priority (1 = highest) */
    int is_emergency;
    
    /* Scheduling outcomes */
    int start_time;
    int completion_time;
    int waiting_time;
    int turnaround_time;
    int aging_boost;       /* Number of times priority was aged up */
    VehicleState state;
} Vehicle;

typedef struct {
    int junction_id;
    char name[64];
    int queue_count[4];    /* Count per direction: N, S, E, W */
    SignalState signals[4];
    int green_time[4];     /* In seconds */
    int road_blocked[4];   /* 1 if incident/road closure, 0 otherwise */
    int active_direction;
    int is_manual_override;
} Junction;

typedef struct {
    int time_tick;
    int vehicle_id;
    int junction_id;
    Direction direction;
    char action[64];       /* e.g., "ARRIVED", "STARTED", "PREEMPTED", "AGED", "COMPLETED" */
    char details[128];
} ScheduleEvent;

typedef struct {
    double avg_waiting_time;
    double avg_turnaround_time;
    double throughput;     /* vehicles / unit time */
    int total_time;
    int completed_vehicles;
    int emergency_vehicles;
    double avg_emergency_wait;
} PerformanceMetrics;

typedef struct {
    Vehicle vehicles[MAX_VEHICLES];
    int vehicle_count;
    Junction junctions[MAX_JUNCTIONS];
    int junction_count;
    SchedulingAlgorithm algorithm;
    int quantum;
    int aging_threshold;   /* Ticks of waiting before priority decrements by 1 (ages) */
    
    /* Output results */
    Vehicle scheduled_vehicles[MAX_VEHICLES];
    int execution_order[MAX_VEHICLES * 10];
    int execution_order_len;
    ScheduleEvent events[MAX_EVENTS];
    int event_count;
    PerformanceMetrics metrics;
} TrafficSimulation;

/* =========================================================
   FUNCTION PROTOTYPES
   ========================================================= */

const char* directionToString(Direction dir);
Direction stringToDirection(const char* str);
const char* signalStateToString(SignalState state);
const char* algorithmToString(SchedulingAlgorithm alg);
SchedulingAlgorithm stringToAlgorithm(const char* str);

void initJunction(Junction *j, int id, const char *name);
void resetSimulationState(TrafficSimulation *sim);
int calculateGreenTimeDynamic(int queue_length, int has_emergency);
int calculateAdaptiveDirectionScore(const Junction *j, Direction dir, const Vehicle vehicles[], int count);
Direction selectAdaptiveGreenDirection(Junction *j, const Vehicle vehicles[], int count);

/* Algorithms */
void runFCFS(TrafficSimulation *sim);
void runPriority(TrafficSimulation *sim, int enable_aging);
void runRoundRobin(TrafficSimulation *sim);
void runAdaptive(TrafficSimulation *sim);

void computePerformanceMetrics(TrafficSimulation *sim);
void logScheduleEvent(TrafficSimulation *sim, int time_tick, int v_id, int j_id, Direction dir, const char *action, const char *details);

/* JSON I/O */
int parseSimulationJSON(const char *json_str, TrafficSimulation *sim);
int loadSimulationFromFile(const char *filename, TrafficSimulation *sim);
char* generateSimulationJSON(const TrafficSimulation *sim);
int saveSimulationToFile(const TrafficSimulation *sim, const char *filename);

#endif /* SCHEDULER_H */
