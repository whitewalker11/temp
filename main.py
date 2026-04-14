import argparse
import sys
from metrics import AIObservabilityCorrelator
from datetime import datetime

def print_summary(metrics):
    if not metrics:
        print("⚠️ No data found in the specified window. Check your DB timestamps.")
        return

    print("\n" + "█"*80)
    print(f"   AI OBSERVABILITY PEAK REPORT | {datetime.now().strftime('%H:%M:%S')}")
    print("█"*80)

    # Section 1: System Overview
    print(f"\n[1] SYSTEM OVERVIEW")
    print(f" • Total Requests: {metrics['total_requests']} | Active Nodes: {', '.join(metrics['active_nodes'])}")

    # Section 2: Model Density & Efficiency
    print(f"\n[2] MODEL EFFICIENCY & CONCURRENCY DENSITY")
    print("💡 IDEA: Measures 'Tokens per GPU Cycle'. High density means your kernels")
    print("   are saturated correctly. Low density suggests a memory bottleneck.")
    print(f"   {'Model Name':<18} | {'Tkn/sec':<10} | {'Peak GPU':<10} | {'Status'}")
    print(f"   {'-'*60}")
    for m in metrics['efficiency']:
        status = "⚠️ BOTTLENECK" if m['avg_peak_gpu'] > 90 else "✅ OPTIMAL"
        print(f" • {m['model_name']:<18} | {m['avg_tps']:>8.2f} | {m['avg_peak_gpu']:>8.1f}% | {status}")

    # Section 3: Saturation Insights
    print(f"\n[3] INFRASTRUCTURE SATURATION HINTS")
    print("💡 IDEA: If Avg Queue Time > 0.5s, your node is hitting the 'Breaking Point'.")
    for m in metrics['efficiency']:
        if m['avg_q_time'] > 0.5:
            print(f" 🔥 ALERT: {m['name']} is stalling. Avg Queue: {m['avg_q_time']:.4f}s")
        else:
            print(f" 🟢 STABLE: {m['model_name']} processing smoothly.")

    print("\n" + "█"*80 + "\n")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--window', type=int, default=30, help='Window in minutes')
    parser.add_argument('--uri', default='192.168.20.8:27018')
    args = parser.parse_args()

    try:
        correlator = AIObservabilityCorrelator(mongo_uri=args.uri)
        print(f"Analyzing last {args.window} minutes of data...")
        report = correlator.generate_all_correlations(args.window)
        print_summary(report)
    except Exception as e:
        print(f"❌ Error during execution: {e}")

if __name__ == "__main__":
    main()
