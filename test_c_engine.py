import unittest
import os
import json
from backend.services.c_engine_service import CEngineService

class TestCEngine(unittest.TestCase):
    def test_engine_binary_exists(self):
        path = CEngineService.get_engine_path()
        self.assertTrue(os.path.exists(path), f"Engine path should exist: {path}")

    def test_synchronization_demonstration(self):
        res = CEngineService.run_sync_test()
        self.assertTrue(res.get('test_passed'), "Sync demonstration must pass")
        self.assertGreater(res.get('mutex_locks_acquired', 0), 0)
        self.assertGreater(res.get('semaphore_waits_completed', 0), 0)
        self.assertGreater(res.get('race_conditions_prevented', 0), 0)

    def test_fcfs_scheduling(self):
        payload = {
            "algorithm": "FCFS",
            "quantum": 2,
            "aging_threshold": 5,
            "junctions": [{"id": 1, "name": "Ghanta Ghar"}],
            "vehicles": [
                {"id": 10, "junction_id": 1, "type": "Car", "direction": "NORTH", "arrival_time": 2, "burst_time": 2, "priority": 3, "is_emergency": 0},
                {"id": 20, "junction_id": 1, "type": "Car", "direction": "SOUTH", "arrival_time": 0, "burst_time": 3, "priority": 1, "is_emergency": 0}
            ]
        }
        res = CEngineService.run_scheduling(payload)
        self.assertEqual(res.get('status'), 'SUCCESS')
        # Vehicle 20 arrived at 0, Vehicle 10 arrived at 2: Vehicle 20 must execute before 10 in FCFS
        order = res.get('execution_order', [])
        self.assertEqual(order, [20, 10])
        metrics = res.get('metrics', {})
        self.assertEqual(metrics.get('completed_vehicles'), 2)

    def test_priority_scheduling_with_aging(self):
        payload = {
            "algorithm": "PRIORITY",
            "quantum": 2,
            "aging_threshold": 3,
            "junctions": [{"id": 1, "name": "Ghanta Ghar"}],
            "vehicles": [
                {"id": 1, "junction_id": 1, "type": "Ambulance", "direction": "NORTH", "arrival_time": 1, "burst_time": 2, "priority": 1, "is_emergency": 1},
                {"id": 2, "junction_id": 1, "type": "Car", "direction": "EAST", "arrival_time": 0, "burst_time": 4, "priority": 4, "is_emergency": 0}
            ]
        }
        res = CEngineService.run_scheduling(payload)
        self.assertEqual(res.get('status'), 'SUCCESS')
        # Car 2 starts at 0. Ambulance arrives at 1. Once Car 2 finishes at 4, Ambulance has priority 1 and finishes at 6.
        metrics = res.get('metrics', {})
        self.assertEqual(metrics.get('completed_vehicles'), 2)
        self.assertEqual(metrics.get('emergency_vehicles'), 1)

    def test_round_robin_with_quantum(self):
        payload = {
            "algorithm": "ROUND_ROBIN",
            "quantum": 2,
            "aging_threshold": 5,
            "junctions": [{"id": 1, "name": "Ghanta Ghar"}],
            "vehicles": [
                {"id": 1, "junction_id": 1, "type": "Car", "direction": "NORTH", "arrival_time": 0, "burst_time": 4, "priority": 3, "is_emergency": 0},
                {"id": 2, "junction_id": 1, "type": "Car", "direction": "SOUTH", "arrival_time": 0, "burst_time": 2, "priority": 3, "is_emergency": 0}
            ]
        }
        res = CEngineService.run_scheduling(payload)
        order = res.get('execution_order', [])
        # V1 runs 2 units -> preempted. V2 runs 2 units -> completes. V1 runs remaining 2 units -> completes.
        self.assertEqual(order, [1, 2, 1])

    def test_adaptive_scheduling_emergency_bonus(self):
        payload = {
            "algorithm": "ADAPTIVE",
            "quantum": 2,
            "aging_threshold": 3,
            "junctions": [{"id": 1, "name": "Ghanta Ghar"}],
            "vehicles": [
                {"id": 1, "junction_id": 1, "type": "Car", "direction": "NORTH", "arrival_time": 0, "burst_time": 2, "priority": 3, "is_emergency": 0},
                {"id": 2, "junction_id": 1, "type": "Ambulance", "direction": "EAST", "arrival_time": 0, "burst_time": 2, "priority": 1, "is_emergency": 1}
            ]
        }
        res = CEngineService.run_scheduling(payload)
        self.assertEqual(res.get('status'), 'SUCCESS')
        # East has emergency vehicle, should receive green signal and schedule first
        order = res.get('execution_order', [])
        self.assertEqual(order[0], 2)

if __name__ == '__main__':
    unittest.main()
