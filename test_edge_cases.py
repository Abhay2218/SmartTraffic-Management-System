import unittest
import os
from backend.services.c_engine_service import CEngineService
from backend.services.simulation_service import SimulationService
from backend.app import create_app

class TestEdgeCases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()

    def test_01_zero_vehicles(self):
        payload = {
            "algorithm": "ADAPTIVE",
            "quantum": 2,
            "junctions": [{"id": 1, "name": "Ghanta Ghar"}],
            "vehicles": []
        }
        res = CEngineService.run_scheduling(payload)
        self.assertEqual(res['metrics']['completed_vehicles'], 0)

    def test_02_one_vehicle(self):
        payload = {
            "algorithm": "FCFS",
            "quantum": 2,
            "junctions": [{"id": 1, "name": "Ghanta Ghar"}],
            "vehicles": [{"id": 1, "junction_id": 1, "type": "Car", "direction": "NORTH", "arrival_time": 0, "burst_time": 3, "priority": 3, "is_emergency": 0}]
        }
        res = CEngineService.run_scheduling(payload)
        self.assertEqual(res['metrics']['completed_vehicles'], 1)
        self.assertEqual(res['execution_order'], [1])

    def test_03_maximum_configured_vehicles(self):
        vehicles = []
        for i in range(50):
            vehicles.append({
                "id": i + 1, "junction_id": (i % 4) + 1, "type": "Car",
                "direction": ["NORTH", "SOUTH", "EAST", "WEST"][i % 4],
                "arrival_time": i // 3, "burst_time": 2, "priority": (i % 4) + 1, "is_emergency": 0
            })
        payload = {
            "algorithm": "ADAPTIVE", "quantum": 2,
            "junctions": [{"id": 1, "name": "J1"}, {"id": 2, "name": "J2"}],
            "vehicles": vehicles
        }
        res = CEngineService.run_scheduling(payload)
        self.assertEqual(res['metrics']['completed_vehicles'], 50)

    def test_04_multiple_vehicles_same_arrival_time(self):
        vehicles = [
            {"id": 1, "junction_id": 1, "type": "Car", "direction": "NORTH", "arrival_time": 0, "burst_time": 2, "priority": 2, "is_emergency": 0},
            {"id": 2, "junction_id": 1, "type": "Car", "direction": "SOUTH", "arrival_time": 0, "burst_time": 2, "priority": 2, "is_emergency": 0},
            {"id": 3, "junction_id": 1, "type": "Car", "direction": "EAST", "arrival_time": 0, "burst_time": 2, "priority": 2, "is_emergency": 0}
        ]
        payload = {"algorithm": "FCFS", "quantum": 2, "junctions": [{"id": 1, "name": "J1"}], "vehicles": vehicles}
        res = CEngineService.run_scheduling(payload)
        self.assertEqual(res['metrics']['completed_vehicles'], 3)

    def test_05_all_vehicles_emergency(self):
        vehicles = [
            {"id": 1, "junction_id": 1, "type": "Ambulance", "direction": "NORTH", "arrival_time": 0, "burst_time": 2, "priority": 1, "is_emergency": 1},
            {"id": 2, "junction_id": 1, "type": "Fire Truck", "direction": "SOUTH", "arrival_time": 0, "burst_time": 3, "priority": 1, "is_emergency": 1}
        ]
        payload = {"algorithm": "PRIORITY", "quantum": 2, "junctions": [{"id": 1, "name": "J1"}], "vehicles": vehicles}
        res = CEngineService.run_scheduling(payload)
        self.assertEqual(res['metrics']['emergency_vehicles'], 2)

    def test_06_no_emergency_vehicles(self):
        vehicles = [
            {"id": 1, "junction_id": 1, "type": "Car", "direction": "NORTH", "arrival_time": 0, "burst_time": 2, "priority": 3, "is_emergency": 0}
        ]
        payload = {"algorithm": "FCFS", "quantum": 2, "junctions": [{"id": 1, "name": "J1"}], "vehicles": vehicles}
        res = CEngineService.run_scheduling(payload)
        self.assertEqual(res['metrics']['emergency_vehicles'], 0)

    def test_07_empty_junction(self):
        # Junction 2 has no vehicles assigned
        vehicles = [
            {"id": 1, "junction_id": 1, "type": "Car", "direction": "NORTH", "arrival_time": 0, "burst_time": 2, "priority": 3, "is_emergency": 0}
        ]
        payload = {
            "algorithm": "ADAPTIVE", "quantum": 2,
            "junctions": [{"id": 1, "name": "J1"}, {"id": 2, "name": "J2 Empty"}],
            "vehicles": vehicles
        }
        res = CEngineService.run_scheduling(payload)
        self.assertEqual(res['metrics']['completed_vehicles'], 1)

    def test_08_extremely_congested_junction(self):
        # 30 vehicles all arriving at Junction 1
        vehicles = [{"id": i+1, "junction_id": 1, "type": "Car", "direction": "NORTH", "arrival_time": 0, "burst_time": 1, "priority": 3, "is_emergency": 0} for i in range(30)]
        payload = {"algorithm": "ADAPTIVE", "quantum": 2, "junctions": [{"id": 1, "name": "J1"}], "vehicles": vehicles}
        res = CEngineService.run_scheduling(payload)
        self.assertEqual(res['metrics']['completed_vehicles'], 30)

    def test_09_same_priority_vehicles(self):
        vehicles = [
            {"id": 1, "junction_id": 1, "type": "Car", "direction": "NORTH", "arrival_time": 1, "burst_time": 2, "priority": 2, "is_emergency": 0},
            {"id": 2, "junction_id": 1, "type": "Car", "direction": "SOUTH", "arrival_time": 0, "burst_time": 2, "priority": 2, "is_emergency": 0}
        ]
        payload = {"algorithm": "PRIORITY", "quantum": 2, "junctions": [{"id": 1, "name": "J1"}], "vehicles": vehicles}
        res = CEngineService.run_scheduling(payload)
        # Vehicle 2 arrived first, tie-breaker prioritizes Vehicle 2
        self.assertEqual(res['execution_order'], [2, 1])

    def test_10_very_large_round_robin_quantum(self):
        # If quantum >= max burst time, RR behaves like FCFS
        vehicles = [
            {"id": 1, "junction_id": 1, "type": "Car", "direction": "NORTH", "arrival_time": 0, "burst_time": 3, "priority": 3, "is_emergency": 0},
            {"id": 2, "junction_id": 1, "type": "Car", "direction": "SOUTH", "arrival_time": 0, "burst_time": 4, "priority": 3, "is_emergency": 0}
        ]
        payload = {"algorithm": "ROUND_ROBIN", "quantum": 500, "junctions": [{"id": 1, "name": "J1"}], "vehicles": vehicles}
        res = CEngineService.run_scheduling(payload)
        self.assertEqual(res['execution_order'], [1, 2])

    def test_11_quantum_zero(self):
        # Quantum = 0 should automatically default safely to 2
        payload = {
            "algorithm": "ROUND_ROBIN", "quantum": 0,
            "junctions": [{"id": 1, "name": "J1"}],
            "vehicles": [{"id": 1, "junction_id": 1, "type": "Car", "direction": "NORTH", "arrival_time": 0, "burst_time": 2, "priority": 3, "is_emergency": 0}]
        }
        res = CEngineService.run_scheduling(payload)
        self.assertEqual(res['metrics']['completed_vehicles'], 1)

    def test_12_invalid_junction_id_validation(self):
        res = self.client.post('/api/vehicles', json={
            "plate_number": "UK07-INV-1",
            "vehicle_type": "Car",
            "direction": "NORTH"
            # Missing junction_id
        })
        self.assertEqual(res.status_code, 400)

    def test_13_invalid_direction_validation(self):
        res = self.client.post('/api/vehicles', json={
            "plate_number": "UK07-INV-2",
            "vehicle_type": "Car",
            "junction_id": 1,
            "direction": "NORTHEAST" # Invalid direction
        })
        self.assertEqual(res.status_code, 400)

    def test_14_negative_arrival_time_validation(self):
        res = self.client.post('/api/vehicles', json={
            "plate_number": "UK07-INV-3",
            "junction_id": 1,
            "direction": "NORTH",
            "arrival_time": -5
        })
        self.assertEqual(res.status_code, 400)

    def test_15_zero_burst_time_validation(self):
        res = self.client.post('/api/vehicles', json={
            "plate_number": "UK07-INV-4",
            "junction_id": 1,
            "direction": "NORTH",
            "burst_time": 0
        })
        self.assertEqual(res.status_code, 400)

    def test_16_road_closure_incident(self):
        res = self.client.post('/api/incidents', json={
            "simulation_id": 1,
            "junction_id": 1,
            "road_id": 1,
            "incident_type": "ROAD_CLOSURE",
            "severity": "HIGH",
            "description": "Maintenance work on Rajpur Road"
        })
        self.assertEqual(res.status_code, 201)
        inc_id = res.get_json()['data']['id']
        # Resolve incident
        res_res = self.client.put(f'/api/incidents/{inc_id}/resolve')
        self.assertEqual(res_res.status_code, 200)

    def test_17_accident_incident(self):
        res = self.client.post('/api/incidents', json={
            "simulation_id": 1,
            "junction_id": 2,
            "road_id": 2,
            "incident_type": "ACCIDENT",
            "severity": "CRITICAL",
            "description": "Vehicle collision at Ballupur Chowk"
        })
        self.assertEqual(res.status_code, 201)
        inc_id = res.get_json()['data']['id']
        self.client.put(f'/api/incidents/{inc_id}/resolve')

    def test_18_vehicle_arriving_during_round_robin_execution(self):
        vehicles = [
            {"id": 1, "junction_id": 1, "type": "Car", "direction": "NORTH", "arrival_time": 0, "burst_time": 5, "priority": 3, "is_emergency": 0},
            {"id": 2, "junction_id": 1, "type": "Car", "direction": "SOUTH", "arrival_time": 1, "burst_time": 2, "priority": 3, "is_emergency": 0}
        ]
        payload = {"algorithm": "ROUND_ROBIN", "quantum": 2, "junctions": [{"id": 1, "name": "J1"}], "vehicles": vehicles}
        res = CEngineService.run_scheduling(payload)
        # V1 runs from 0-2 (preempted). During 0-2, V2 arrived at 1. Next V2 runs from 2-4 (completes). Then V1 finishes 4-7.
        self.assertEqual(res['execution_order'], [1, 2, 1, 1])

    def test_19_starvation_scenario_with_aging(self):
        # Low priority vehicle (prio 5) waiting behind multiple continuous priority 1 vehicles
        vehicles = [
            {"id": 1, "junction_id": 1, "type": "Car", "direction": "NORTH", "arrival_time": 0, "burst_time": 2, "priority": 1, "is_emergency": 0},
            {"id": 2, "junction_id": 1, "type": "Car", "direction": "SOUTH", "arrival_time": 0, "burst_time": 5, "priority": 5, "is_emergency": 0}
        ]
        payload = {"algorithm": "PRIORITY", "quantum": 2, "aging_threshold": 2, "junctions": [{"id": 1, "name": "J1"}], "vehicles": vehicles}
        res = CEngineService.run_scheduling(payload)
        # Vehicle 2 must eventually complete and have aging recorded
        v2 = next(v for v in res['vehicles'] if v['id'] == 2)
        self.assertEqual(v2['status'], 'COMPLETED')
        self.assertGreater(v2['completion_time'], 0)

    def test_20_simulation_reset(self):
        res = self.client.post('/api/simulations/1/reset')
        self.assertEqual(res.status_code, 200)

    def test_21_multiple_simulations(self):
        res1 = self.client.post('/api/simulations', json={"name": "Sim Multi 1", "algorithm": "FCFS"})
        self.assertEqual(res1.status_code, 201)
        res2 = self.client.post('/api/simulations', json={"name": "Sim Multi 2", "algorithm": "ROUND_ROBIN"})
        self.assertEqual(res2.status_code, 201)

    def test_22_database_failure_handling(self):
        # Non-existent simulation should return 404 gracefully
        res = self.client.get('/api/simulations/999999')
        self.assertEqual(res.status_code, 404)

    def test_23_c_engine_invalid_input_resilience(self):
        # Corrupted input JSON
        with self.assertRaises(Exception):
            CEngineService.run_scheduling({"algorithm": "INVALID_ALG", "vehicles": "not a list"})

    def test_24_invalid_api_request(self):
        # 404 for unknown route
        res = self.client.get('/api/unknown_route_404')
        self.assertEqual(res.status_code, 404)

if __name__ == '__main__':
    unittest.main()
