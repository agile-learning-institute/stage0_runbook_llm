"""CLI command entry point."""
import os
import sys
import argparse
import logging

from .config import Config
from .executor import Executor

logger = logging.getLogger(__name__)


def main():
    """CLI command entry point."""
    # Initialize config (configures logging)
    config = Config()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="LLM-powered code transformation executor")
    parser.add_argument(
        "--task",
        required=True,
        help="Task name (without .md extension)"
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Repository root path (default: from config/REPO_ROOT env var)"
    )
    parser.add_argument(
        "--context-root",
        default=None,
        help="Context root path (default: from config/CONTEXT_ROOT env var)"
    )

    args = parser.parse_args()

    # Use config values with command-line overrides
    repo_root = args.repo_root or config.REPO_ROOT
    context_root = args.context_root or config.CONTEXT_ROOT

    # Validate required environment variables
    if not config.TRACKING_BREADCRUMB:
        logger.warning("TRACKING_BREADCRUMB not set")

    # Validate paths
    if not os.path.exists(repo_root):
        logger.error(f"Repository root does not exist: {repo_root}")
        sys.exit(1)

    if not os.path.exists(context_root):
        logger.error(f"Context root does not exist: {context_root}")
        sys.exit(1)

    try:
        # Create executor and run task
        executor = Executor(repo_root, context_root)
        commit_message, patch = executor.execute_task(args.task)

        # Output to stdout in the required format
        print("---COMMIT_MSG---")
        print(commit_message)
        print("---PATCH---")
        print(patch)

        sys.exit(0)
    except Exception as e:
        logger.error(f"Task execution failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
