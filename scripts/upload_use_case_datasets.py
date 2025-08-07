#!/usr/bin/env python3
"""
Upload use case evaluation datasets to LangSmith.

This script uploads the public sector use case datasets to LangSmith
for systematic evaluation tracking.
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
LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT", "tahecho-public-sector-eval")

if not LANGCHAIN_API_KEY:
    print("❌ LANGCHAIN_API_KEY environment variable is required")
    print("   Please set it in your .env file or environment")
    exit(1)

# Initialize LangSmith client
client = Client(api_key=LANGCHAIN_API_KEY)

def load_use_case_dataset(dataset_name: str) -> Optional[Dict[str, Any]]:
    """Load a use case dataset from the use_cases directory."""
    dataset_path = Path(f"tests/datasets/use_cases/{dataset_name}.json")
    
    if not dataset_path.exists():
        print(f"❌ Dataset file not found: {dataset_path}")
        return None
    
    try:
        with open(dataset_path, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
        return dataset
    except Exception as e:
        print(f"❌ Error loading dataset {dataset_path}: {e}")
        return None

def get_available_use_case_datasets() -> List[str]:
    """Get list of available use case datasets."""
    use_cases_dir = Path("tests/datasets/use_cases")
    if not use_cases_dir.exists():
        return []
    
    datasets = []
    for file_path in use_cases_dir.glob("*.json"):
        # Skip specific files: backups, use_case_summary, and checklists
        if (not file_path.name.startswith("backup") and 
            file_path.name != "use_case_summary.json" and
            "checklist" not in file_path.name and
            not file_path.name.endswith("_backup.json")):
            datasets.append(file_path.stem)
    
    return sorted(datasets)

def create_public_sector_evaluation_functions():
    """Create evaluation functions for public sector use cases."""
    
    def evaluate_public_sector_response(outputs: Dict[str, Any], reference_outputs: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate public sector chat response against expected criteria."""
        
        response = outputs.get("output", "").lower()
        expected = reference_outputs
        
        results = {
            "score": 0.0,
            "feedback": [],
            "factual_accuracy": True,
            "language_quality": True,
            "completeness": True,
            "bias_check": True,
            "hallucination_check": True
        }
        
        # Check required content (factual accuracy)
        contains = expected.get("contains", [])
        contains_score = 0
        for item in contains:
            if item.lower() in response:
                contains_score += 1
            else:
                results["factual_accuracy"] = False
                results["feedback"].append(f"Missing expected content: {item}")
        
        if contains:
            contains_ratio = contains_score / len(contains)
        else:
            contains_ratio = 1.0
        
        # Check forbidden content (bias/hallucination indicators)
        not_contains = expected.get("not_contains", [])
        for item in not_contains:
            if item.lower() in response:
                results["hallucination_check"] = False
                results["feedback"].append(f"Contains problematic content: {item}")
        
        # Basic language quality check (German administrative language)
        if len(response) < 10:
            results["language_quality"] = False
            results["feedback"].append("Response too short")
        
        # Completeness check
        if len(response) < 50:
            results["completeness"] = False
            results["feedback"].append("Response appears incomplete")
        
        # Calculate weighted score based on public sector evaluation framework
        factual_weight = 0.3
        hallucination_weight = 0.2
        language_weight = 0.2
        bias_weight = 0.15
        completeness_weight = 0.15
        
        # More strict scoring - factual accuracy heavily impacts score
        # If no required content is found, score should be very low
        factual_score = contains_ratio if contains_ratio > 0 else 0.0
        hallucination_score = 1.0 if results["hallucination_check"] else 0
        language_score = 0.7 if results["language_quality"] else 0.2  # Reduced language score
        bias_score = 1.0 if results["bias_check"] else 0
        completeness_score = 0.6 if results["completeness"] else 0.1  # Reduced completeness score
        
        results["score"] = (
            factual_score * factual_weight +
            hallucination_score * hallucination_weight +
            language_score * language_weight +
            bias_score * bias_weight +
            completeness_score * completeness_weight
        )
        
        # Critical failure conditions
        if not results["hallucination_check"]:
            results["score"] = 0.0  # Hallucinations are critical failures
            results["feedback"].append("CRITICAL: Hallucination detected - automatic failure")
        
        if not results["feedback"]:
            results["feedback"] = ["All checks passed"]
        
        return results
    
    return evaluate_public_sector_response

def upload_use_case_dataset(dataset_name: str, custom_name: Optional[str] = None):
    """Upload a use case dataset to LangSmith."""
    
    # Load dataset
    dataset_data = load_use_case_dataset(dataset_name)
    if not dataset_data:
        return None
    
    # Use custom name or generate from dataset info
    langsmith_name = custom_name or f"pga_{dataset_name}_evaluation"
    description = dataset_data.get("description", f"Public sector evaluation dataset: {dataset_name}")
    test_cases = dataset_data.get("test_cases", [])
    
    print(f"\n📤 Uploading {dataset_name} to LangSmith...")
    print(f"   Dataset name: {langsmith_name}")
    print(f"   Test cases: {len(test_cases)}")
    
    try:
        # Check if dataset exists
        try:
            existing_dataset = client.read_dataset(dataset_name=langsmith_name)
            print(f"   ⚠️  Dataset '{langsmith_name}' already exists. Updating...")
            dataset = existing_dataset
        except:
            # Create new dataset
            print(f"   ✨ Creating new dataset '{langsmith_name}'...")
            dataset = client.create_dataset(
                dataset_name=langsmith_name,
                description=description
            )
        
        # Add examples to dataset
        examples = []
        skipped = 0
        
        for i, case in enumerate(test_cases):
            # Skip test cases that need validation
            state = case.get("metadata", {}).get("state", "")
            if state == "draft":
                skipped += 1
                continue
            
            try:
                example = client.create_example(
                    dataset_id=dataset.id,
                    inputs={"user_input": case["input"]},
                    outputs=case["expected_output"],
                    metadata={
                        **case.get("metadata", {}),
                        "use_case": dataset_name,
                        "administrative_dimension": case.get("metadata", {}).get("use_case", {}).get("administrative_dimension"),
                        "document_availability": case.get("metadata", {}).get("use_case", {}).get("document_availability")
                    }
                )
                examples.append(example)
                
                if (len(examples) + 1) % 50 == 0:
                    print(f"   Added {len(examples)} examples...")
                    
            except Exception as e:
                print(f"   ⚠️  Error adding example {i}: {e}")
                continue
        
        print(f"\n✅ Successfully uploaded dataset '{langsmith_name}':")
        print(f"   📊 Dataset ID: {dataset.id}")
        print(f"   📋 Examples added: {len(examples)}")
        print(f"   ⏭️  Skipped (need validation): {skipped}")
        print(f"   🔗 View at: https://smith.langchain.com/datasets/{dataset.id}")
        
        return dataset
        
    except Exception as e:
        print(f"❌ Error uploading dataset: {e}")
        raise

def main():
    """Main function to upload use case datasets to LangSmith."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Upload public sector use case datasets to LangSmith")
    parser.add_argument("--dataset", "-d", help="Specific dataset to upload")
    parser.add_argument("--name", "-n", help="Custom dataset name in LangSmith")
    parser.add_argument("--list", "-l", action="store_true", help="List available datasets")
    parser.add_argument("--priority-1", "-p1", action="store_true", help="Upload only Priority 1 datasets")
    parser.add_argument("--ready-only", "-r", action="store_true", help="Upload only datasets ready for evaluation")
    
    args = parser.parse_args()
    
    print("🚀 Public Sector Dataset Uploader")
    print(f"📡 Using LangSmith project: {LANGCHAIN_PROJECT}")
    
    # Get available datasets
    available_datasets = get_available_use_case_datasets()
    
    if args.list:
        print(f"\n📋 Available use case datasets:")
        for dataset in available_datasets:
            # Load dataset to check status
            data = load_use_case_dataset(dataset)
            if data:
                total_cases = len(data.get("test_cases", []))
                priority = data.get("specifications", {}).get("priority", "unknown")
                print(f"   - {dataset}: {total_cases} cases (Priority {priority})")
        return
    
    if not available_datasets:
        print("❌ No use case datasets found in tests/datasets/use_cases/")
        return
    
    # Determine datasets to upload
    datasets_to_upload = []
    
    if args.dataset:
        if args.dataset not in available_datasets:
            print(f"❌ Dataset '{args.dataset}' not found.")
            print(f"Available datasets: {', '.join(available_datasets)}")
            return
        datasets_to_upload = [args.dataset]
    
    elif args.priority_1:
        # Upload Priority 1 datasets
        priority_1_datasets = ["factual_questions", "reasoning_questions", "summarization"]
        datasets_to_upload = [d for d in priority_1_datasets if d in available_datasets]
        print(f"\n🔥 Uploading Priority 1 datasets: {', '.join(datasets_to_upload)}")
    
    elif args.ready_only:
        # Upload only datasets ready for evaluation
        ready_datasets = ["factual_questions", "reasoning_questions"]  # Based on evaluation results
        datasets_to_upload = [d for d in ready_datasets if d in available_datasets]
        print(f"\n✅ Uploading evaluation-ready datasets: {', '.join(datasets_to_upload)}")
    
    else:
        # Ask user which datasets to upload
        print(f"\n📋 Available datasets: {', '.join(available_datasets)}")
        response = input("Upload all datasets? (y/n): ")
        if response.lower() == 'y':
            datasets_to_upload = available_datasets
        else:
            return
    
    # Upload datasets
    successful_uploads = []
    
    for dataset_name in datasets_to_upload:
        try:
            dataset = upload_use_case_dataset(dataset_name, args.name)
            if dataset:
                successful_uploads.append(dataset_name)
        except Exception as e:
            print(f"❌ Failed to upload dataset '{dataset_name}': {e}")
            continue
    
    print(f"\n🎯 Upload Summary:")
    print(f"   ✅ Successfully uploaded: {len(successful_uploads)} datasets")
    if successful_uploads:
        print(f"   📋 Datasets: {', '.join(successful_uploads)}")
    
    print(f"\n🔧 Next steps:")
    print(f"   1. View datasets at: https://smith.langchain.com")
    print(f"   2. Create evaluation runs using the uploaded datasets")
    print(f"   3. Monitor performance across administrative dimensions")

if __name__ == "__main__":
    main()
