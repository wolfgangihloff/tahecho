#!/usr/bin/env python3
"""
Fix source tracking in datasets to properly reference actual source documents
instead of Excel files.

This script corrects the source_file references to point to the actual content
documents in tests/test_content/ directories.
"""

import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import os


# Mapping of file_set to actual source documents
SOURCE_DOCUMENT_MAPPING = {
    "EU AI Act": {
        "directory": "/Users/wolfgang.ihloff/workspace/tahecho/tests/test_content/EU AI Act",
        "primary_document": "OJ_L_202401689_DE_TXT.pdf",
        "description": "EU AI Act - Official Journal of the European Union"
    },
    "BayHIG": {
        "directory": "/Users/wolfgang.ihloff/workspace/tahecho/tests/test_content/BayHIG",
        "documents": [
            "AVBayHIG.pdf",
            "Bayerisches_Hochschulinnovationsgesetz__Vollzugshinweise.pdf",
            "BayHIG (1).pdf",
            "Begründung_HIG_im_Rahmen_der_Landtagsbehandlung.pdf"
        ],
        "description": "Bayerisches Hochschulinnovationsgesetz documents"
    },
    "Deutschlandstipendium": {
        "directory": "/Users/wolfgang.ihloff/workspace/tahecho/tests/test_content/Deutschlandstipendium",
        "documents": [
            "Bericht 2021.pdf",
            "Bericht 2022.pdf", 
            "Bericht 2023.pdf"
        ],
        "description": "Deutschland-Stipendium annual reports"
    },
    "Dokumente": {
        "directory": "/Users/wolfgang.ihloff/workspace/tahecho/tests/test_content/Dokumente",
        "description": "Various government documents",
        "note": "Multiple documents - generic reference"
    },
    "Hochschulverträge": {
        "directory": "/Users/wolfgang.ihloff/workspace/tahecho/tests/test_content/Hochschulverträge",
        "description": "University contracts and agreements",
        "note": "Multiple contract documents"
    },
    "IT-Planungsrat": {
        "directory": "/Users/wolfgang.ihloff/workspace/tahecho/tests/test_content/IT-Planungsrat",
        "description": "IT Planning Council documents and decisions",
        "note": "Multiple Beschluss documents"
    },
    "Kabinettsprotokolle": {
        "directory": "/Users/wolfgang.ihloff/workspace/tahecho/tests/test_content/Kabinettsprotokolle",
        "description": "Cabinet meeting protocols",
        "note": "Multiple protocol documents"
    },
    "Personalstrategie": {
        "directory": "/Users/wolfgang.ihloff/workspace/tahecho/tests/test_content/Personalstrategie",
        "documents": [
            "Personalmasterplan Hannover.pdf",
            "Personalstrategie Bülach.pdf",
            "Personalstrategie_Stadt Ulm.pdf",
            "personalstrategie-stuttgart.pdf"
        ],
        "description": "Personnel strategy documents from various cities"
    },
    "Startups": {
        "directory": "/Users/wolfgang.ihloff/workspace/tahecho/tests/test_content/Startups",
        "documents": [
            "66a Gruendungsradar_2022.pdf",
            "66b Dt. Startup Monitor_2023.pdf"
        ],
        "description": "German startup ecosystem reports"
    },
    "Nordstream": {
        "directory": "/Users/wolfgang.ihloff/workspace/tahecho/tests/test_content/Nordstream",
        "description": "Nordstream related documents",
        "note": "Multiple documents and email attachments"
    }
}


def get_actual_source_documents(file_set: str) -> Dict[str, Any]:
    """
    Get the actual source documents for a given file_set.
    
    Args:
        file_set: The file_set identifier
        
    Returns:
        Dictionary with source document information
    """
    mapping = SOURCE_DOCUMENT_MAPPING.get(file_set)
    if not mapping:
        return {
            "source_documents": [f"Unknown - {file_set}"],
            "source_directory": None,
            "document_count": 0,
            "note": f"No mapping found for file_set: {file_set}"
        }
    
    directory = mapping.get("directory")
    if not directory or not os.path.exists(directory):
        return {
            "source_documents": [f"Directory not found - {file_set}"],
            "source_directory": directory,
            "document_count": 0,
            "note": f"Directory does not exist: {directory}"
        }
    
    # Get actual files in the directory
    try:
        actual_files = [f for f in os.listdir(directory) if not f.startswith('.')]
        
        # Use specified documents if available, otherwise use all files
        if "documents" in mapping:
            source_documents = mapping["documents"]
        elif "primary_document" in mapping:
            source_documents = [mapping["primary_document"]]
        else:
            source_documents = actual_files
        
        return {
            "source_documents": source_documents,
            "source_directory": directory,
            "document_count": len(source_documents),
            "description": mapping.get("description", ""),
            "all_files_in_directory": actual_files,
            "note": mapping.get("note", "")
        }
        
    except Exception as e:
        return {
            "source_documents": [f"Error reading directory - {file_set}"],
            "source_directory": directory,
            "document_count": 0,
            "note": f"Error reading directory: {e}"
        }


def fix_test_case_source_tracking(test_case: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fix the source tracking for a single test case.
    
    Args:
        test_case: The test case to fix
        
    Returns:
        Updated test case with corrected source tracking
    """
    file_set = test_case.get("expected_output", {}).get("file_set", "")
    if not file_set:
        file_set = test_case.get("metadata", {}).get("file_set", "")
    
    if not file_set:
        return test_case  # No file_set to fix
    
    # Get actual source documents
    source_info = get_actual_source_documents(file_set)
    
    # Update the origin information
    origin = test_case.get("metadata", {}).get("origin", {})
    
    # Keep track of the original Excel source for traceability
    original_source_file = origin.get("source_file", "")
    
    updated_origin = {
        **origin,
        "content_source_documents": source_info["source_documents"],
        "content_source_directory": source_info["source_directory"],
        "content_document_count": source_info["document_count"],
        "content_description": source_info.get("description", ""),
        "excel_source_file": original_source_file,  # Preserve original Excel reference
        "source_type": "content_documents",
        "source_tracking_fixed": datetime.now().isoformat()
    }
    
    # Add note if there are issues
    if source_info.get("note"):
        updated_origin["source_note"] = source_info["note"]
    
    # Update the test case
    updated_test_case = {
        **test_case,
        "metadata": {
            **test_case.get("metadata", {}),
            "origin": updated_origin
        }
    }
    
    return updated_test_case


def fix_dataset_source_tracking(dataset_path: str) -> None:
    """
    Fix source tracking for an entire dataset.
    
    Args:
        dataset_path: Path to the dataset file
    """
    print(f"🔧 Fixing source tracking for: {Path(dataset_path).name}")
    
    # Load dataset
    try:
        with open(dataset_path, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
    except Exception as e:
        print(f"❌ Error loading dataset: {e}")
        return
    
    test_cases = dataset.get("test_cases", [])
    print(f"   📊 Processing {len(test_cases)} test cases")
    
    # Fix each test case
    updated_test_cases = []
    file_set_counts = {}
    fixed_count = 0
    
    for test_case in test_cases:
        updated_test_case = fix_test_case_source_tracking(test_case)
        updated_test_cases.append(updated_test_case)
        
        # Track if we actually fixed something
        if updated_test_case.get("metadata", {}).get("origin", {}).get("source_tracking_fixed"):
            fixed_count += 1
        
        # Count file sets
        file_set = test_case.get("expected_output", {}).get("file_set", "")
        if file_set:
            file_set_counts[file_set] = file_set_counts.get(file_set, 0) + 1
    
    # Update dataset
    updated_dataset = {
        **dataset,
        "test_cases": updated_test_cases,
        "version": dataset.get("version", "1.0.0") + "_source_fixed",
        "last_updated": datetime.now().isoformat(),
        "source_tracking_fix": {
            "fixed_date": datetime.now().isoformat(),
            "test_cases_fixed": fixed_count,
            "file_set_distribution": file_set_counts,
            "source_document_mapping": {fs: get_actual_source_documents(fs) 
                                       for fs in file_set_counts.keys()}
        }
    }
    
    # Create backup
    backup_path = str(dataset_path).replace('.json', f'_backup_before_source_fix_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    print(f"   💾 Creating backup: {Path(backup_path).name}")
    
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
    
    # Save updated dataset
    print(f"   💾 Saving updated dataset")
    
    with open(dataset_path, 'w', encoding='utf-8') as f:
        json.dump(updated_dataset, f, indent=2, ensure_ascii=False)
    
    print(f"   ✅ Fixed {fixed_count} test cases")
    print(f"   📊 File set distribution:")
    for file_set, count in file_set_counts.items():
        source_info = get_actual_source_documents(file_set)
        doc_count = source_info["document_count"]
        print(f"      - {file_set}: {count} questions → {doc_count} source documents")


def main():
    """Main function to fix source tracking across datasets."""
    print("🔍 Source Tracking Fix")
    print("=" * 50)
    
    # Datasets to fix
    datasets_to_fix = [
        "/Users/wolfgang.ihloff/workspace/tahecho/tests/datasets/use_cases/factual_questions.json",
        "/Users/wolfgang.ihloff/workspace/tahecho/tests/datasets/use_cases/summarization.json",
        "/Users/wolfgang.ihloff/workspace/tahecho/tests/datasets/use_cases/reasoning_questions.json",
        "/Users/wolfgang.ihloff/workspace/tahecho/tests/datasets/use_cases/comparison.json",
        "/Users/wolfgang.ihloff/workspace/tahecho/tests/datasets/use_cases/creative_writing.json",
        "/Users/wolfgang.ihloff/workspace/tahecho/tests/datasets/use_cases/rewriting.json"
    ]
    
    for dataset_path in datasets_to_fix:
        if os.path.exists(dataset_path):
            fix_dataset_source_tracking(dataset_path)
        else:
            print(f"⚠️  Dataset not found: {Path(dataset_path).name}")
    
    print(f"\n✅ Source tracking fix completed!")
    print(f"\n📊 Source Document Summary:")
    
    for file_set, mapping in SOURCE_DOCUMENT_MAPPING.items():
        source_info = get_actual_source_documents(file_set)
        print(f"   🏛️ {file_set}:")
        print(f"      📁 Directory: {source_info['source_directory']}")
        print(f"      📄 Documents: {source_info['document_count']}")
        if source_info.get("note"):
            print(f"      ℹ️  Note: {source_info['note']}")
    
    print(f"\n🔧 Benefits of Fixed Source Tracking:")
    print(f"   ✅ Accurate source document references")
    print(f"   ✅ Traceability to actual content files")
    print(f"   ✅ Preserved Excel source for metadata tracking")
    print(f"   ✅ Document count and directory information")
    print(f"   ✅ Better understanding of content scope per file_set")


if __name__ == "__main__":
    main()
