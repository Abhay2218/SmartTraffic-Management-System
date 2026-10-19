#ifndef SYNC_SIM_H
#define SYNC_SIM_H

#include <stdio.h>
#include <stdlib.h>

#ifdef _WIN32
#include <windows.h>
#endif

typedef struct {
    int junction_id;
    int active_vehicles_in_critical_section;
    int current_direction_crossing;
    int total_collisions_prevented;
    int max_lane_capacity;
    
#ifdef _WIN32
    HANDLE intersection_mutex;
    HANDLE lane_semaphore;
    CRITICAL_SECTION queue_lock;
#endif
} SynchronizedJunction;

typedef struct {
    int test_passed;
    int mutex_locks_acquired;
    int semaphore_waits_completed;
    int race_conditions_prevented;
    char log_messages[20][128];
    int log_count;
} SyncTestResult;

void initSynchronizedJunction(SynchronizedJunction *sj, int junction_id, int max_capacity);
void cleanupSynchronizedJunction(SynchronizedJunction *sj);

/* Thread/Vehicle operations on shared resource */
int acquireIntersectionAccess(SynchronizedJunction *sj, int vehicle_id, int direction, int burst_time);
void releaseIntersectionAccess(SynchronizedJunction *sj, int vehicle_id, int direction);

/* Demonstration test runner */
SyncTestResult runSynchronizationDemonstration(int vehicle_count);

#endif /* SYNC_SIM_H */
