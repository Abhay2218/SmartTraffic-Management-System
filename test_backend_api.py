import unittest
import json
from backend.app import create_app

class TestBackendAPI(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_health_check(self):
        resp = self.client.get('/api/system/health')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data.get('status'), 'HEALTHY')
        self.assertTrue(data['database']['connected'])
        self.assertTrue(data['c_engine']['available'])

    def test_sync_test_endpoint(self):
        resp = self.client.get('/api/system/sync-test')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data.get('status'), 'SUCCESS')
        self.assertTrue(data['data']['test_passed'])

    def test_junctions_list(self):
        resp = self.client.get('/api/junctions')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data.get('status'), 'SUCCESS')
        self.assertGreaterEqual(len(data.get('data', [])), 4)

    def test_roads_list(self):
        resp = self.client.get('/api/roads')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data.get('status'), 'SUCCESS')
        self.assertGreaterEqual(len(data.get('data', [])), 8)

    def test_vehicles_crud(self):
        # 1. Create Vehicle
        new_v = {
            "simulation_id": 1,
            "plate_number": "UK07-TEST-1234",
            "vehicle_type": "Ambulance",
            "junction_id": 1,
            "direction": "EAST",
            "arrival_time": 0,
            "burst_time": 2,
            "priority": 1,
            "is_emergency": 1
        }
        res_post = self.client.post('/api/vehicles', json=new_v)
        self.assertEqual(res_post.status_code, 201)
        created = res_post.get_json().get('data', {})
        v_id = created['id']

        # 2. Get Vehicle
        res_get = self.client.get(f'/api/vehicles/{v_id}')
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(res_get.get_json()['data']['plate_number'], "UK07-TEST-1234")

        # 3. Update Vehicle
        res_put = self.client.put(f'/api/vehicles/{v_id}', json={"status": "RUNNING"})
        self.assertEqual(res_put.status_code, 200)
        self.assertEqual(res_put.get_json()['data']['status'], "RUNNING")

        # 4. Delete Vehicle
        res_del = self.client.delete(f'/api/vehicles/{v_id}')
        self.assertEqual(res_del.status_code, 200)

    def test_vehicles_batch_and_clear(self):
        # 1. Batch Create
        batch_payload = {
            "simulation_id": 1,
            "vehicles": [
                {"vehicle_type": "Car", "junction_id": 1, "direction": "NORTH", "burst_time": 3, "priority": 3},
                {"vehicle_type": "Ambulance", "junction_id": 2, "direction": "SOUTH", "burst_time": 2, "priority": 1, "is_emergency": 1},
                {"vehicle_type": "Bus", "junction_id": 3, "direction": "EAST", "burst_time": 5, "priority": 2}
            ]
        }
        res_batch = self.client.post('/api/vehicles/batch', json=batch_payload)
        self.assertEqual(res_batch.status_code, 201)
        data = res_batch.get_json()
        self.assertEqual(data.get('status'), 'SUCCESS')
        self.assertEqual(data.get('count'), 3)

        # 2. Clear vehicles by status
        res_clear_comp = self.client.delete('/api/vehicles/clear?simulation_id=1&status=COMPLETED')
        self.assertEqual(res_clear_comp.status_code, 200)

    def test_manual_signal_control(self):

        # Apply manual override: Set EAST to GREEN
        payload = {
            "junction_id": 1,
            "direction": "EAST",
            "green_time": 25
        }
        res = self.client.post('/api/signals/manual', json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get('status'), 'SUCCESS')
        self.assertEqual(data.get('active_direction'), 'EAST')

        # Check junction state: Only EAST should be GREEN, others RED
        j_res = self.client.get('/api/junctions/1')
        signals = j_res.get_json()['data']['signals']
        self.assertEqual(signals['EAST']['state'], 'GREEN')
        self.assertEqual(signals['NORTH']['state'], 'RED')
        self.assertEqual(signals['SOUTH']['state'], 'RED')
        self.assertEqual(signals['WEST']['state'], 'RED')

        # Restore automatic mode
        res_auto = self.client.post('/api/signals/automatic', json={"junction_id": 1})
        self.assertEqual(res_auto.status_code, 200)

    def test_simulation_lifecycle_and_state(self):
        # Start simulation 1 with Adaptive algorithm
        res_start = self.client.post('/api/simulations/1/start', json={
            "algorithm": "ADAPTIVE",
            "quantum": 2
        })
        self.assertEqual(res_start.status_code, 200)
        data = res_start.get_json()
        self.assertEqual(data.get('status'), 'SUCCESS')
        self.assertIn('metrics', data.get('data', {}))

        # Check real-time state poll
        res_state = self.client.get('/api/simulations/1/state')
        self.assertEqual(res_state.status_code, 200)
        s_data = res_state.get_json().get('data', {})
        self.assertIn('summary', s_data)
        self.assertIn('junctions', s_data)

        # Reset simulation 1
        res_reset = self.client.post('/api/simulations/1/reset')
        self.assertEqual(res_reset.status_code, 200)

    def test_analytics_compare_benchmark(self):
        res = self.client.get('/api/analytics/compare?simulation_id=1&quantum=2')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get('status'), 'SUCCESS')
        comp = data.get('comparison', {})
        self.assertIn('FCFS', comp)
        self.assertIn('PRIORITY', comp)
        self.assertIn('ROUND_ROBIN', comp)
        self.assertIn('ADAPTIVE', comp)

if __name__ == '__main__':
    unittest.main()
