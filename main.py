import argparse
from metrics import AIObservabilityCorrelator
from datetime import datetime

def print_summary(metrics_list):
    print("\n" + "█"*80)
    print(f"   AI OBSERVABILITY DASHBOARD | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("█"*80)

    # Section 1: Model Performance & Efficiency Idea
    print(f"\n[1] MODEL EFFICIENCY & CONCURRENCY DENSITY")
    print("IDEA: Measures 'Tokens per GPU Cycle'. High Density means the model is ")
    print("      generating text efficiently without wasting hardware compute.")
    print(f"   {'Model Name':<18} | {'Tkn/sec':<10} | {'Peak GPU':<10} | {'Density'}")
    print(f"   {'-'*65}")
    for m in metrics_list:
        print(f" • {m['name']:<18} | {m['tps']:>8.2f} | {m['peak_gpu']:>8.1f}% | {m['density']:>8.2f}")

    # Section 2: Infrastructure Saturation Idea
    print(f"\n[2] SYSTEM SATURATION ANALYSIS")
    print("IDEA: Compares Queue Wait Time vs. Hardware Load. If Peak GPU is 100% ")
    print("      and Density is low, the node is saturated and requires scaling.")
    
    for m in metrics_list:
        if m['peak_gpu'] > 85:
            print(f" ⚠️ ALERT: {m['name']} is hitting Hardware Ceiling ({m['peak_gpu']:.1f}%).")
        if m['queue_impact'] > 0.5:
            print(f" ⏳ DELAY: High Queue impact detected for {m['name']} ({m['queue_impact']:.2f}s).")

    # Section 3: Cost & Resource Alignment
    print(f"\n[3] RESOURCE ALIGNMENT (UNIT ECONOMICS)")
    print("IDEA: Correlates user requests to physical node IDs to find 'Noisy Neighbors'.")
    print("      Helps identify which node is causing bottlenecks in your Linux cluster.")

    print("\n" + "█"*80 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--window', type=int, default=30)
    args = parser.parse_args()

    correlator = AIObservabilityCorrelator()
    report = correlator.generate_detailed_report(args.window)
    if report:
        print_summary(report)
    else:
        print("No workload data found in the specified window.")
