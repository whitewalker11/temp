from pymongo import MongoClient
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from scipy.stats import pearsonr
from collections import defaultdict
import json

class AIObservabilityCorrelator:
    def __init__(self, mongo_uri="192.168.20.8:27018", db_name="AI-observability"):
        # Formatting URI for admin authentication if needed
        full_uri = f"mongodb://admin:admin@{mongo_uri}/ot_database?authSource=ot_database"
        self.client = MongoClient(full_uri)
        self.db = self.client[db_name]

    def get_time_aligned_data(self, time_window_minutes=60):
        """Fetch and align data with intelligent timestamp matching"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=time_window_minutes)
        
        # Determine if your DB uses Strings or BSON Dates
        sample = self.db['AI-workloads-real'].find_one()
        if not sample: return None
        
        is_string = isinstance(sample['timestamp'], str)
        t_start = start_time.isoformat() if is_string else start_time
        t_end = end_time.isoformat() if is_string else end_time
        
        query = {'timestamp': {'$gte': t_start, '$lte': t_end}}
        
        data = {
            'workloads': list(self.db['AI-workloads-real'].find(query)),
            'gpu': list(self.db['Hardware-gpu'].find(query)),
            'cpu': list(self.db['Hardware-cpu'].find(query)),
            'memory': list(self.db['Hardware-memory'].find(query))
        }
        
        if not data['workloads']: return None
        return self._build_node_index(data)

    def _build_node_index(self, data):
        indices = {f"{k}_by_node": defaultdict(list) for k in ['gpu', 'cpu', 'memory', 'workloads']}
        for key in ['gpu', 'cpu', 'memory', 'workloads']:
            for item in data[key]:
                indices[f"{key}_by_node"][item.get('node_id', 'unknown')].append(item)
        
        indices.update(data)
        indices['all_nodes'] = set(indices['workloads_by_node'].keys())
        return indices

    def _find_peak_gpu(self, workload, data):
        """Finds the peak GPU utilization during the request's specific lifecycle"""
        node_id = workload.get('node_id')
        start_ts = datetime.fromisoformat(workload['timestamp'])
        # Window based on total time (Queue + Processing)
        end_ts = start_ts + timedelta(seconds=workload.get('total_time_seconds', 0))
        
        gpu_snaps = data.get('gpu_by_node', {}).get(node_id, [])
        peaks = [0]
        
        for snap in gpu_snaps:
            snap_ts = datetime.fromisoformat(snap['timestamp'])
            if start_ts <= snap_ts <= end_ts:
                for g in snap.get('gpus', []):
                    peaks.append(g['utilization']['gpu_pct'])
        return max(peaks)

    def generate_all_correlations(self, window):
        data = self.get_time_aligned_data(window)
        if not data: return None
        
        # Calculation for Model Efficiency
        model_results = defaultdict(lambda: {'tps': [], 'peaks': [], 'q_time': [], 'cost': 0, 'reqs': 0})
        for w in data['workloads']:
            m = w['model_name']
            peak = self._find_peak_gpu(w, data)
            model_results[m]['tps'].append(w['tokens_per_second'])
            model_results[m]['peaks'].append(peak)
            model_results[m]['q_time'].append(w['queue_time_seconds'])
            model_results[m]['cost'] += w['cost_usd']
            model_results[m]['reqs'] += 1

        efficiency = []
        for model, s in model_results.items():
            avg_tps = np.mean(s['tps'])
            avg_peak = np.mean(s['peaks'])
            efficiency.append({
                'model_name': model,
                'efficiency_score': (avg_tps * 100) / (avg_peak + 1),
                'avg_tps': avg_tps,
                'avg_peak_gpu': avg_peak,
                'avg_q_time': np.mean(s['q_time'])
            })

        return {
            'efficiency': sorted(efficiency, key=lambda x: x['efficiency_score'], reverse=True),
            'active_nodes': list(data['all_nodes']),
            'total_requests': len(data['workloads'])
        }
