#!/usr/bin/env python3
"""
LangChain evaluation utilities for Jira integration testing.

This script loads datasets from JSON files and uploads them to LangSmith
for systematic evaluation of Jira agent performance.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

from langsmith import Client
from dotenv import load_dotenv

load_dotenv()

# LangSmith configuration
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT", "tahecho-jira-eval")

if not LANGCHAIN_API_KEY:
    raise ValueError("LANGCHAIN_API_KEY environment variable is required")

# Initialize LangSmith client
client = Client(api_key=LANGCHAIN_API_KEY)

def load_dataset_from_file(dataset_path: str) -> Dict[str, Any]:
    """Load dataset from JSON file."""
    try:
        with open(dataset_path, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
        return dataset
    except FileNotFoundError:
        raise FileNotFoundError(f"Dataset file not found: {dataset_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in dataset file {dataset_path}: {e}")

def get_available_datasets(datasets_dir: str = "tests/datasets") -> List[str]:
    """Get list of available dataset files."""
    datasets_path = Path(datasets_dir)
    if not datasets_path.exists():
        return []
    
    return [f.stem for f in datasets_path.glob("*.json")]

def create_evaluation_functions():
    """Create evaluation functions for the dataset."""
    
    def evaluate_jira_response(outputs: Dict[str, Any], reference_outputs: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate if Jira agent response matches expected criteria."""
        
        response = outputs.get("output", "").lower()
        expected = reference_outputs.get("expected_output", {})
        
        results = {
            "score": 0.0,
            "feedback": [],
            "contains_check": True,
            "not_contains_check": True,
            "ticket_count_check": True
        }
        
        # Check required content
        contains = expected.get("contains", [])
        for item in contains:
            if item.lower() not in response:
                results["contains_check"] = False
                results["feedback"].append(f"Missing required content: {item}")
        
        # Check forbidden content
        not_contains = expected.get("not_contains", [])
        for item in not_contains:
            if item.lower() in response:
                results["not_contains_check"] = False
                results["feedback"].append(f"Contains forbidden content: {item}")
        
        # Check ticket count if specified
        ticket_count = expected.get("ticket_count")
        if ticket_count is not None:
            # Simple heuristic: count TT- patterns
            import re
            tt_tickets = len(re.findall(r'tt-\d+', response))
            if tt_tickets != ticket_count:
                results["ticket_count_check"] = False
                results["feedback"].append(f"Expected {ticket_count} tickets, found {tt_tickets}")
        
        # Calculate overall score
        checks_passed = sum([
            results["contains_check"],
            results["not_contains_check"], 
            results["ticket_count_check"]
        ])
        results["score"] = checks_passed / 3.0
        
        if not results["feedback"]:
            results["feedback"] = ["All checks passed"]
            
        return results
    
    return evaluate_jira_response

def upload_dataset(dataset_file: str, dataset_name: Optional[str] = None):
    """Upload a dataset from file to LangSmith."""
    
    # Load dataset from file
    dataset_data = load_dataset_from_file(dataset_file)
    
    # Use provided name or default from file
    name = dataset_name or dataset_data.get("name", Path(dataset_file).stem)
    description = dataset_data.get("description", f"Dataset loaded from {dataset_file}")
    test_cases = dataset_data.get("test_cases", [])
    
    try:
        # Check if dataset exists
        try:
            existing_dataset = client.read_dataset(dataset_name=name)
            print(f"Dataset '{name}' already exists. Updating...")
            dataset = existing_dataset
        except:
            # Create new dataset
            print(f"Creating new dataset '{name}'...")
            dataset = client.create_dataset(
                dataset_name=name,
                description=description
            )
        
        # Add examples to dataset
        examples = []
        for i, case in enumerate(test_cases):
            example = client.create_example(
                dataset_id=dataset.id,
                inputs={"user_input": case["input"]},
                outputs=case["expected_output"],
                metadata=case["metadata"]
            )
            examples.append(example)
            print(f"Added example {i+1}: {case['input'][:50]}...")
        
        print(f"\n✅ Successfully created dataset '{name}' with {len(examples)} examples")
        print(f"📊 Dataset ID: {dataset.id}")
        print(f"🔗 View at: https://smith.langchain.com/datasets/{dataset.id}")
        
        return dataset
        
    except Exception as e:
        print(f"❌ Error creating dataset: {e}")
        raise

def main():
    """Main function to create and upload evaluation datasets."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Upload Jira evaluation datasets to LangSmith")
    parser.add_argument("--dataset", "-d", help="Dataset file to upload (default: all available)")
    parser.add_argument("--name", "-n", help="Custom dataset name in LangSmith")
    parser.add_argument("--list", "-l", action="store_true", help="List available datasets")
    args = parser.parse_args()
    
    print("🚀 Jira Evaluation Dataset Manager")
    print(f"📡 Using LangSmith project: {LANGCHAIN_PROJECT}")
    
    # List available datasets
    available_datasets = get_available_datasets()
    
    if args.list:
        print(f"\n📋 Available datasets:")
        for dataset in available_datasets:
            print(f"  - {dataset}")
        return
    
    if not available_datasets:
        print("❌ No datasets found in tests/datasets/")
        return
    
    # Determine which datasets to upload
    if args.dataset:
        if args.dataset not in available_datasets:
            print(f"❌ Dataset '{args.dataset}' not found.")
            print(f"Available datasets: {', '.join(available_datasets)}")
            return
        datasets_to_upload = [args.dataset]
    else:
        datasets_to_upload = available_datasets
    
    # Upload datasets
    for dataset_name in datasets_to_upload:
        dataset_file = f"tests/datasets/{dataset_name}.json"
        print(f"\n📤 Uploading dataset: {dataset_name}")
        
        try:
            dataset = upload_dataset(dataset_file, args.name)
            
            # Show dataset contents
            dataset_data = load_dataset_from_file(dataset_file)
            test_cases = dataset_data.get("test_cases", [])
            
            print(f"\n📋 Dataset '{dataset_name}' Contents:")
            for i, case in enumerate(test_cases, 1):
                test_type = case.get("metadata", {}).get("test_type", "unknown")
                print(f"{i}. {test_type}: {case['input'][:60]}...")
            
        except Exception as e:
            print(f"❌ Failed to upload dataset '{dataset_name}': {e}")
            continue
    
    print(f"\n🎯 Next steps:")
    print(f"1. Run experiments using these datasets")
    print(f"2. View results at: https://smith.langchain.com")
    print(f"3. Create new datasets by adding JSON files to tests/datasets/")

if __name__ == "__main__":
    main()
