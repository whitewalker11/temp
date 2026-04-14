import pandas as pd
import numpy as np
from pymongo import MongoClient
from datetime import datetime, timedelta
from scipy.stats import pearsonr
from collections import defaultdict
import json

class AIObservabilityCorrelator:
    def __init__(self, mongo_uri="192.168.20.8:27018", db_name="AI-observability"):
        self.client = MongoClient(f"mongodb://admin:admin@{mongo_uri}/ot_database?authSource=ot_database")
        self.db = self.client[db_name]

    def get_time_aligned_data(self, window_min):
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=window_min)
        query = {'timestamp': {'$gte': start_time.isoformat(), '$lte': end_time.isoformat()}}
        
        raw = {
            'workloads': list(self.db['AI-workloads-real'].find(query)),
            'gpu': list(self.db['Hardware-gpu'].find(query))
        }
        
        indexed = {'gpu_by_node': defaultdict(list), 'workloads_by_node': defaultdict(list), 'all_nodes': set()}
        for g in raw['gpu']:
            indexed['gpu_by_node'][g.get('node_id')].append(g)
            indexed['all_nodes'].add(g.get('node_id'))
        for w in raw['workloads']:
            indexed['workloads_by_node'][w.get('node_id')].append(w)
            indexed['all_nodes'].add(w.get('node_id'))
        
        return indexed

    def _get_peak_gpu(self, workload, indexed_data):
        node_id = workload.get('node_id')
        start_ts = datetime.fromisoformat(workload['timestamp'])
        end_ts = start_ts + timedelta(seconds=workload.get('total_time_seconds', 0))
        
        snaps = indexed_data['gpu_by_node'].get(node_id, [])
        peaks = [0]
        for s in snaps:
            ts = datetime.fromisoformat(s['timestamp'])
            if start_ts <= ts <= end_ts:
                for g in s.get('gpus', []):
                    peaks.append(g['utilization']['gpu_pct'])
        return max(peaks)

    def generate_detailed_report(self, window):
        data = self.get_time_aligned_data(window)
        if not data['workloads_by_node']: return None

        model_summary = defaultdict(lambda: {'tps': [], 'peaks': [], 'q_time': []})
        for w in data['workloads_by_node'].get('all_nodes', data['workloads_by_node']): # Handle indexing fallback
            for req in (data['workloads_by_node'][w] if isinstance(data['workloads_by_node'], dict) else []):
                m = req['model_name']
                peak = self._get_peak_gpu(req, data)
                model_summary[m]['tps'].append(req['tokens_per_second'])
                model_summary[m]['peaks'].append(peak)
                model_summary[m]['q_time'].append(req['queue_time_seconds'])

        results = []
        for model, stats in model_summary.items():
            avg_tps = np.mean(stats['tps'])
            avg_peak = np.mean(stats['peaks'])
            results.append({
                'name': model,
                'tps': avg_tps,
                'peak_gpu': avg_peak,
                'density': avg_tps / (avg_peak + 1),
                'queue_impact': np.mean(stats['q_time'])
            })
        return results
