#!/usr/bin/env python3
"""Test script for optimize-evaluate workflow"""

import asyncio
import json
from runtime.executor import WorkflowExecutor

async def main():
    # Load input data
    with open('/tmp/optimize_input.json', 'r') as f:
        input_data = json.load(f)
    
    print(f"[test] Input: {input_data}")
    print()
    
    # Create executor
    executor = WorkflowExecutor(environment="experiment", verbose=True)
    
    # Execute workflow
    result = await executor.aexecute(
        'workflows/optimize_evaluate_workflow.py',
        input_data
    )
    
    print()
    print(f"[test] Final result:")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
