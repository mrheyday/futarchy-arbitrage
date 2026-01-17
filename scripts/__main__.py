#!/usr/bin/env python3
"""
Entry point for running scripts as a module.

Usage:
    python -m scripts                    # Show available commands
    python -m scripts index_artifacts    # Run artifact indexing
    python -m scripts compile_all        # Run contract compilation
"""
import sys


def main():
    """Main entry point for scripts module."""
    available_commands = {
        "index_artifacts": "Index all Solidity artifacts (bytecode, ABI, ASM, opcodes)",
        "compile_all": "Compile Solidity contracts with all outputs",
        "deploy_executor_v5": "Deploy FutarchyArbExecutorV5 contract",
        "deploy_prediction_arb_v1": "Deploy PredictionArbExecutorV1 contract",
        "deploy_institutional_solver": "Deploy InstitutionalSolverSystem contract",
        "verify_contract": "Verify contract on block explorer",
    }

    if len(sys.argv) < 2:
        print("Usage: python -m scripts <command>")
        print("\nAvailable commands:")
        for cmd, desc in available_commands.items():
            print(f"  {cmd:30} - {desc}")
        print("\nExample: python -m scripts index_artifacts")
        sys.exit(0)

    command = sys.argv[1]
    
    # Remove the command from argv so submodules see correct args
    sys.argv = [f"scripts.{command}"] + sys.argv[2:]

    if command == "index_artifacts":
        from scripts.index_artifacts import main as run
        run()
    elif command == "compile_all":
        from scripts.compile_all import main as run
        run()
    elif command == "deploy_executor_v5":
        from scripts.deploy_executor_v5 import main as run
        run()
    elif command == "deploy_prediction_arb_v1":
        from scripts.deploy_prediction_arb_v1 import main as run
        run()
    elif command == "deploy_institutional_solver":
        from scripts.deploy_institutional_solver import main as run
        run()
    elif command == "verify_contract":
        from scripts.verify_contract import main as run
        run()
    else:
        print(f"Unknown command: {command}")
        print("Run 'python -m scripts' to see available commands.")
        sys.exit(1)


if __name__ == "__main__":
    main()

