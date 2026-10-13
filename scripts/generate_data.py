"""
CLI script to generate deterministic synthetic dataset.
Usage:
  python scripts/generate_data.py --count 3000 --seed 42
"""

import argparse
import json
import os
import sys

# Ensure backend is on python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.data.synthetic_generator import generate_synthetic_dataset, save_dataset_to_csv


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic IT service tickets for Workflow Mining Agent.")
    parser.add_argument("--count", type=int, default=3000, help="Number of tickets to generate (default: 3000)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility (default: 42)")
    parser.add_argument("--output-csv", type=str, default="data/synthetic_tickets_3000.csv", help="Path to output CSV")
    parser.add_argument("--output-json", type=str, default="data/ground_truth_manifest.json", help="Path to ground truth JSON")
    parser.add_argument("--include-devops", action="store_true", help="Include 4 DevOps/SRE workflows (total 10 workflows)")
    
    args = parser.parse_args()
    
    os.makedirs(os.path.dirname(args.output_csv), exist_ok=True)
    os.makedirs(os.path.dirname(args.output_json), exist_ok=True)
    
    print(f"Generating {args.count} synthetic tickets with random seed {args.seed} (include_devops={args.include_devops})...")
    tickets, manifest = generate_synthetic_dataset(num_tickets=args.count, seed=args.seed, include_devops=args.include_devops)
    
    save_dataset_to_csv(tickets, args.output_csv, include_ground_truth=True)
    print(f"Saved dataset with ground truth to {args.output_csv} ({len(tickets)} rows).")
    
    # Save a public CSV version without ground truth (simulating real enterprise import)
    clean_csv = args.output_csv.replace(".csv", "_no_ground_truth.csv")
    save_dataset_to_csv(tickets, clean_csv, include_ground_truth=False)
    print(f"Saved customer-facing version without ground truth to {clean_csv}.")
    
    with open(args.output_json, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"Saved evaluation ground truth manifest to {args.output_json}.")
    
    print("\nSummary of Planted Workflows:")
    for wf_key, meta in manifest["workflows"].items():
        print(f" - {meta['name']} ({wf_key}): {meta['count']} tickets, {meta['expected_hours_total']} total hours")
    print(f" - Unrelated one-off tickets: {manifest['one_off_total']} tickets")
    print("\nDataset generation completed successfully.")


if __name__ == "__main__":
    main()
