#!/usr/bin/env python3
"""
Create public sector evaluation datasets from converted Excel data.

This script processes the converted JSON files from Excel and creates
structured evaluation datasets for testing chat performance in public sector contexts.
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from collections import defaultdict


def load_json_data(json_path: str) -> Dict[str, Any]:
    """Load JSON data from file."""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {json_path}: {e}")
        raise


def clean_and_deduplicate_data(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean and deduplicate the dataset.
    
    Args:
        json_data: The raw JSON data from Excel conversion
        
    Returns:
        Cleaned JSON data with duplicates removed
    """
    cleaned_data = {
        "source_file": json_data["source_file"],
        "sheets": {},
        "metadata": json_data.get("metadata", {})
    }
    
    for sheet_name, sheet_data in json_data["sheets"].items():
        print(f"Cleaning sheet: {sheet_name}")
        
        # Track unique entries by content hash
        seen_hashes: Set[str] = set()
        cleaned_rows = []
        
        for row in sheet_data["data"]:
            # Skip empty rows
            if not any(row.values()) or all(v is None or str(v).strip() == "" for v in row.values()):
                continue
            
            # Create hash for deduplication
            row_content = f"{row.get('prompt', '')}{row.get('file_set', '')}{row.get('category', '')}"
            row_hash = hashlib.md5(row_content.encode()).hexdigest()
            
            if row_hash not in seen_hashes:
                seen_hashes.add(row_hash)
                cleaned_rows.append(row)
        
        print(f"  - Original rows: {len(sheet_data['data'])}")
        print(f"  - Cleaned rows: {len(cleaned_rows)}")
        print(f"  - Removed: {len(sheet_data['data']) - len(cleaned_rows)}")
        
        cleaned_data["sheets"][sheet_name] = {
            **sheet_data,
            "data": cleaned_rows,
            "shape": [len(cleaned_rows), len(sheet_data["columns"])]
        }
    
    return cleaned_data


def create_public_sector_eval_dataset(json_data: Dict[str, Any], dataset_name: str) -> Dict[str, Any]:
    """
    Create evaluation dataset from cleaned JSON data.
    
    Args:
        json_data: Cleaned JSON data
        dataset_name: Name for the evaluation dataset
        
    Returns:
        Evaluation dataset structure
    """
    print(f"\nCreating evaluation dataset: {dataset_name}")
    
    # Group test cases by category and file_set
    test_cases_by_category = defaultdict(list)
    file_sets = set()
    
    for sheet_name, sheet_data in json_data["sheets"].items():
        for row in sheet_data["data"]:
            prompt = str(row.get("prompt", "") or "").strip()
            file_set = str(row.get("file_set", "") or "").strip()
            category = str(row.get("category", "Unknown") or "Unknown").strip()
            baseline_response = str(row.get("baseline_model_response", "") or "").strip()
            
            # Skip if essential fields are missing
            if not prompt or not baseline_response:
                continue
            
            file_sets.add(file_set)
            
            # Create test case
            test_case = {
                "id": f"{dataset_name}_{len(test_cases_by_category[category])}",
                "input": prompt,
                "expected_output": {
                    "contains": [],  # To be filled based on baseline response analysis
                    "category": category,
                    "file_set": file_set,
                    "baseline_response": baseline_response[:500] + "..." if len(baseline_response) > 500 else baseline_response
                },
                "metadata": {
                    "test_type": "public_sector_query",
                    "category": category,
                    "file_set": file_set,
                    "domain": "public_sector",
                    "language": "de" if any(german_word in prompt.lower() for german_word in ["ist", "das", "wie", "was", "wo", "wann", "warum"]) else "en"
                }
            }
            
            # Try to extract key terms that should be in responses
            if baseline_response:
                # Simple heuristic: extract important terms from baseline response
                key_terms = []
                
                # Look for specific numbers, dates, proper nouns
                import re
                
                # Extract numbers with context
                numbers = re.findall(r'\*\*(\d+(?:[.,]\d+)*)\*\*|\b(\d+(?:[.,]\d+)*)\s*(?:Euro|%|Prozent|Jahre?|Semester|Studierende)', baseline_response)
                for match in numbers:
                    num = match[0] or match[1]
                    if num:
                        key_terms.append(num)
                
                # Extract bold terms (likely important)
                bold_terms = re.findall(r'\*\*(.*?)\*\*', baseline_response)
                key_terms.extend([term for term in bold_terms if len(term) > 2 and len(term) < 50])
                
                # Take first few key terms
                test_case["expected_output"]["contains"] = key_terms[:5]
            
            test_cases_by_category[category].append(test_case)
    
    # Create final dataset structure
    all_test_cases = []
    for category, cases in test_cases_by_category.items():
        all_test_cases.extend(cases)
    
    dataset = {
        "name": dataset_name,
        "description": f"Public sector evaluation dataset from {json_data['source_file']}",
        "version": "1.0.0",
        "created_date": "2024-01-11",
        "source": json_data["source_file"],
        "domain": "public_sector",
        "language": "de",
        "test_cases": all_test_cases,
        "metadata": {
            "total_test_cases": len(all_test_cases),
            "categories": list(test_cases_by_category.keys()),
            "file_sets": sorted(list(file_sets)),
            "category_counts": {cat: len(cases) for cat, cases in test_cases_by_category.items()}
        },
        "evaluation_criteria": {
            "relevance_weight": 0.3,
            "accuracy_weight": 0.3,
            "completeness_weight": 0.2,
            "language_quality_weight": 0.2,
            "passing_score": 0.75
        }
    }
    
    print(f"✅ Created dataset with {len(all_test_cases)} test cases")
    print(f"📊 Categories: {list(test_cases_by_category.keys())}")
    print(f"📁 File sets: {sorted(list(file_sets))}")
    
    return dataset


def main():
    """Main function to process Excel-converted JSON files and create evaluation datasets."""
    
    print("🏛️  Public Sector Evaluation Dataset Creator")
    print("=" * 60)
    
    # Define input files
    input_files = [
        {
            "path": "/Users/wolfgang.ihloff/workspace/tahecho/tests/test_content/PGA_Eval_Small_v20250409.json",
            "dataset_name": "pga_eval_small"
        },
        {
            "path": "/Users/wolfgang.ihloff/workspace/tahecho/tests/test_content/PGA_Eval_Document_Collections_v20250411.json",
            "dataset_name": "pga_eval_collections"
        }
    ]
    
    datasets_dir = Path("/Users/wolfgang.ihloff/workspace/tahecho/tests/datasets")
    datasets_dir.mkdir(exist_ok=True)
    
    for file_info in input_files:
        file_path = file_info["path"]
        dataset_name = file_info["dataset_name"]
        
        if not Path(file_path).exists():
            print(f"❌ File not found: {file_path}")
            continue
        
        print(f"\n📊 Processing: {Path(file_path).name}")
        
        try:
            # Load and clean data
            raw_data = load_json_data(file_path)
            
            # For large files, limit processing to avoid memory issues
            if dataset_name == "pga_eval_collections":
                print("⚠️  Large file detected - limiting to first 1000 rows per sheet")
                for sheet_name, sheet_data in raw_data["sheets"].items():
                    if len(sheet_data["data"]) > 1000:
                        sheet_data["data"] = sheet_data["data"][:1000]
                        sheet_data["shape"] = [1000, sheet_data["shape"][1]]
            
            cleaned_data = clean_and_deduplicate_data(raw_data)
            
            # Create evaluation dataset
            eval_dataset = create_public_sector_eval_dataset(cleaned_data, dataset_name)
            
            # Save cleaned data
            cleaned_path = datasets_dir / f"{dataset_name}_cleaned.json"
            with open(cleaned_path, 'w', encoding='utf-8') as f:
                json.dump(cleaned_data, f, indent=2, ensure_ascii=False)
            print(f"💾 Saved cleaned data: {cleaned_path}")
            
            # Save evaluation dataset
            dataset_path = datasets_dir / f"{dataset_name}_public_sector.json"
            with open(dataset_path, 'w', encoding='utf-8') as f:
                json.dump(eval_dataset, f, indent=2, ensure_ascii=False)
            print(f"📋 Saved evaluation dataset: {dataset_path}")
            
        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")
            continue
    
    print(f"\n🎯 Dataset creation completed!")
    print(f"\n📁 Output directory: {datasets_dir}")
    print(f"🔧 Next steps:")
    print(f"  1. Review the created datasets in tests/datasets/")
    print(f"  2. Upload to LangSmith using scripts/create_jira_eval_dataset.py")
    print(f"  3. Run evaluations against your chat system")


if __name__ == "__main__":
    main()
