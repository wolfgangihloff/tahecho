#!/usr/bin/env python3
"""
Run Jira agent evaluation experiments using LangSmith.

This script runs evaluation experiments against the Jira agent
using datasets from tests/datasets/ directory.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any

# Add project root and src to path to import our modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))  # For config.py
sys.path.insert(0, str(project_root / "src"))  # For tahecho modules

from langsmith import Client, traceable
from langsmith.evaluation import evaluate
from dotenv import load_dotenv

from tahecho.agents.jira_mcp_agent import JiraMCPAgent
from tahecho.agents.state import AgentState
from create_jira_eval_dataset import load_dataset_from_file, get_available_datasets

load_dotenv()

# LangSmith configuration
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT", "tahecho-jira-eval")

if not LANGCHAIN_API_KEY:
    raise ValueError("LANGCHAIN_API_KEY environment variable is required")

# Initialize LangSmith client
client = Client(api_key=LANGCHAIN_API_KEY)

@traceable(name="jira_agent_evaluation")
def run_jira_agent(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Run the Jira agent with tracing enabled."""
    
    # Extract user input from inputs dict
    user_input = inputs.get("user_input", "")
    
    if not isinstance(user_input, str):
        return {"output": f"Error: Invalid input type. Expected string, got {type(user_input)}"}
    
    try:
        # Initialize agent
        agent = JiraMCPAgent()
        
        # Create initial state
        state = AgentState(user_input=user_input)
        
        # Execute agent
        result_state = agent.execute(state)
        
        # Extract the response
        if result_state.agent_results.get("jira_mcp_agent"):
            output = result_state.agent_results["jira_mcp_agent"]
        else:
            output = "No response generated"
        
        return {"output": output}
        
    except Exception as e:
        return {"output": f"Error executing Jira agent: {str(e)}"}

def create_evaluator(evaluation_criteria: Dict[str, Any]):
    """Create evaluation function based on dataset criteria."""
    
    def evaluate_jira_response(run, example):
        """Evaluate Jira agent response against expected output."""
        
        # Safe handling of response output
        response_raw = run.outputs.get("output", "") if run.outputs else ""
        response = response_raw.lower() if response_raw else ""
        
        expected = example.outputs.get("expected_output", {}) if example.outputs else {}
        
        results = {
            "score": 0.0,
            "feedback": [],
            "contains_check": True,
            "not_contains_check": True,
            "ticket_count_check": True
        }
        
        # Get weights from criteria
        contains_weight = evaluation_criteria.get("contains_weight", 0.4)
        not_contains_weight = evaluation_criteria.get("not_contains_weight", 0.3)
        ticket_count_weight = evaluation_criteria.get("ticket_count_weight", 0.3)
        
        # Check required content
        contains = expected.get("contains", [])
        contains_score = 0.0
        if contains:
            found_items = sum(1 for item in contains if item.lower() in response)
            contains_score = found_items / len(contains)
            if contains_score < 1.0:
                missing = [item for item in contains if item.lower() not in response]
                results["contains_check"] = False
                results["feedback"].append(f"Missing required content: {missing}")
        
        # Check forbidden content
        not_contains = expected.get("not_contains", [])
        not_contains_score = 1.0
        if not_contains:
            forbidden_found = [item for item in not_contains if item.lower() in response]
            if forbidden_found:
                not_contains_score = 0.0
                results["not_contains_check"] = False
                results["feedback"].append(f"Contains forbidden content: {forbidden_found}")
        
        # Check ticket count if specified
        ticket_count_score = 1.0
        ticket_count = expected.get("ticket_count")
        if ticket_count is not None:
            # Simple heuristic: count TT- patterns
            import re
            tt_tickets = len(re.findall(r'tt-\d+', response))
            if tt_tickets == ticket_count:
                ticket_count_score = 1.0
            else:
                ticket_count_score = 0.0
                results["ticket_count_check"] = False
                results["feedback"].append(f"Expected {ticket_count} tickets, found {tt_tickets}")
        
        # Calculate weighted score
        weighted_score = (
            contains_score * contains_weight +
            not_contains_score * not_contains_weight +
            ticket_count_score * ticket_count_weight
        )
        
        results["score"] = weighted_score
        results["contains_score"] = contains_score
        results["not_contains_score"] = not_contains_score
        results["ticket_count_score"] = ticket_count_score
        
        if not results["feedback"]:
            results["feedback"] = ["All checks passed"]
        
        return results
    
    return evaluate_jira_response

def run_evaluation(dataset_file: str, experiment_name: str = None):
    """Run evaluation experiment using a dataset file."""
    
    print(f"📊 Running evaluation with dataset: {dataset_file}")
    
    # Load dataset
    dataset_data = load_dataset_from_file(dataset_file)
    dataset_name = dataset_data.get("name", Path(dataset_file).stem)
    
    # Create experiment name
    if not experiment_name:
        experiment_name = f"{dataset_name}-experiment"
    
    print(f"🧪 Experiment name: {experiment_name}")
    
    # Get or create dataset in LangSmith
    try:
        dataset = client.read_dataset(dataset_name=dataset_name)
        print(f"✅ Using existing dataset: {dataset_name}")
    except:
        print(f"❌ Dataset '{dataset_name}' not found in LangSmith.")
        print(f"Please upload it first using: python scripts/create_jira_eval_dataset.py -d {Path(dataset_file).stem}")
        return
    
    # Create evaluator
    evaluation_criteria = dataset_data.get("evaluation_criteria", {})
    evaluator = create_evaluator(evaluation_criteria)
    
    # Run evaluation
    print(f"🚀 Starting evaluation...")
    
    try:
        results = evaluate(
            run_jira_agent,
            data=dataset,
            evaluators=[evaluator],
            experiment_prefix=experiment_name,
            metadata={
                "dataset_file": dataset_file,
                "dataset_version": dataset_data.get("version", "unknown"),
                "evaluation_criteria": evaluation_criteria
            }
        )
        
        print(f"✅ Evaluation completed!")
        print(f"📈 Results summary:")
        print(f"   - Total runs: {len(results)}")
        
        # Calculate average scores
        if results:
            # Handle both dict and object result formats
            scores = []
            for r in results:
                if hasattr(r, 'evaluation_results') and r.evaluation_results:
                    eval_result = r.evaluation_results.get("evaluate_jira_response", {})
                    if isinstance(eval_result, dict) and "score" in eval_result:
                        scores.append(eval_result["score"])
                elif isinstance(r, dict) and "evaluation_results" in r:
                    eval_result = r["evaluation_results"].get("evaluate_jira_response", {})
                    if isinstance(eval_result, dict) and "score" in eval_result:
                        scores.append(eval_result["score"])
            
            if scores:
                avg_score = sum(scores) / len(scores)
                print(f"   - Average score: {avg_score:.2f}")
                
                passing_score = evaluation_criteria.get("passing_score", 0.8)
                passed = sum(1 for s in scores if s >= passing_score)
                print(f"   - Passed (>= {passing_score}): {passed}/{len(scores)} ({passed/len(scores)*100:.1f}%)")
            else:
                print(f"   - Could not extract scores from results")
        
        print(f"🔗 View detailed results at: https://smith.langchain.com")
        
        return results
        
    except Exception as e:
        print(f"❌ Evaluation failed: {e}")
        raise

def main():
    """Main function to run evaluations."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Jira agent evaluation experiments")
    parser.add_argument("--dataset", "-d", help="Dataset file to use for evaluation")
    parser.add_argument("--experiment", "-e", help="Custom experiment name")
    parser.add_argument("--list", "-l", action="store_true", help="List available datasets")
    args = parser.parse_args()
    
    print("🧪 Jira Agent Evaluation Runner")
    print(f"📡 Using LangSmith project: {LANGCHAIN_PROJECT}")
    
    # List available datasets
    available_datasets = get_available_datasets()
    
    if args.list:
        print(f"\n📋 Available datasets:")
        for dataset in available_datasets:
            dataset_file = f"tests/datasets/{dataset}.json"
            try:
                data = load_dataset_from_file(dataset_file)
                description = data.get("description", "No description")
                test_count = len(data.get("test_cases", []))
                print(f"  - {dataset}: {test_count} test cases")
                print(f"    {description}")
            except Exception as e:
                print(f"  - {dataset}: Error loading ({e})")
        return
    
    if not available_datasets:
        print("❌ No datasets found in tests/datasets/")
        return
    
    # Determine which dataset to use
    if args.dataset:
        if args.dataset not in available_datasets:
            print(f"❌ Dataset '{args.dataset}' not found.")
            print(f"Available datasets: {', '.join(available_datasets)}")
            return
        dataset_to_use = args.dataset
    else:
        # Use the first available dataset
        dataset_to_use = available_datasets[0]
        print(f"📝 No dataset specified, using: {dataset_to_use}")
    
    # Run evaluation
    dataset_file = f"tests/datasets/{dataset_to_use}.json"
    
    try:
        results = run_evaluation(dataset_file, args.experiment)
        print(f"\n🎯 Evaluation completed successfully!")
        
    except Exception as e:
        print(f"❌ Evaluation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
