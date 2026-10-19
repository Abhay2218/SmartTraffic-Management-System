import os
import json
import subprocess
import tempfile
from backend.config import Config

class CEngineService:
    @staticmethod
    def get_engine_path():
        exe_path = Config.C_ENGINE_PATH
        if os.path.exists(exe_path):
            return exe_path
        # Alternative search in common directories
        candidate = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'c_engine', 'bin', 'traffic_engine.exe')
        if os.path.exists(candidate):
            return candidate
        raise FileNotFoundError(f"C Scheduling Engine executable not found at: {exe_path}")

    @classmethod
    def run_scheduling(cls, payload):
        """
        Executes the compiled C engine with the given simulation configuration and vehicles.
        Returns the parsed JSON output from the C engine.
        """
        if not isinstance(payload, dict):
            raise ValueError("Payload must be a dictionary")
        if not isinstance(payload.get('vehicles'), list):
            raise ValueError("Vehicles must be a list")
        if payload.get('algorithm') not in ['FCFS', 'PRIORITY', 'ROUND_ROBIN', 'ADAPTIVE']:
            raise ValueError(f"Invalid algorithm: {payload.get('algorithm')}")

        exe = cls.get_engine_path()
        with tempfile.NamedTemporaryFile('w', suffix='_in.json', delete=False, encoding='utf-8') as fin:
            json.dump(payload, fin, indent=2)
            in_path = fin.name

        out_path = in_path.replace('_in.json', '_out.json')

        try:
            cmd = [exe, '--file', in_path, '--out', out_path]
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            if proc.returncode != 0:
                raise RuntimeError(
                    f"C Engine failed with exit code {proc.returncode}.\nStderr: {proc.stderr}\nStdout: {proc.stdout}"
                )

            if not os.path.exists(out_path):
                raise FileNotFoundError(f"C Engine output file not generated at {out_path}")

            with open(out_path, 'r', encoding='utf-8') as fout:
                result = json.load(fout)

            return result

        finally:
            # Clean up temporary files
            if os.path.exists(in_path):
                try: os.remove(in_path)
                except OSError: pass
            if os.path.exists(out_path):
                try: os.remove(out_path)
                except OSError: pass

    @classmethod
    def run_sync_test(cls):
        """
        Executes the C engine synchronization demonstration (--test-sync)
        verifying OS Mutex, Semaphore, and Critical Section invariants.
        """
        exe = cls.get_engine_path()
        proc = subprocess.run(
            [exe, '--test-sync'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if proc.returncode != 0:
            raise RuntimeError(f"Sync test failed.\nStderr: {proc.stderr}")

        return json.loads(proc.stdout)
