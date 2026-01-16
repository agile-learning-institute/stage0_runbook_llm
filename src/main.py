"""Main CLI entry point."""
import os
import sys
import logging
import argparse

from .executor import Executor
from .patch_generator import parse_patch_response

logger = logging.getLogger(__name__)


def main():
    """Main CLI entry point."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="LLM-powered code transformation executor")
    parser.add_argument(
        "--task",
        required=True,
        help="Task name (without .md extension)"
    )
    parser.add_argument(
        "--repo-root",
        default=os.getenv("REPO_ROOT", "/workspace/repo"),
        help="Repository root path (default: REPO_ROOT env var or /workspace/repo)"
    )
    parser.add_argument(
        "--context-root",
        default=os.getenv("CONTEXT_ROOT", "/workspace/context"),
        help="Context root path (default: CONTEXT_ROOT env var or /workspace/context)"
    )
    parser.add_argument(
        "--log-level",
        default=os.getenv("LOG_LEVEL", "INFO"),
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: LOG_LEVEL env var or INFO)"
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Validate required environment variables
    tracking_breadcrumb = os.getenv("TRACKING_BREADCRUMB")
    if not tracking_breadcrumb:
        logger.warning("TRACKING_BREADCRUMB not set")

    # Validate paths
    if not os.path.exists(args.repo_root):
        logger.error(f"Repository root does not exist: {args.repo_root}")
        sys.exit(1)

    if not os.path.exists(args.context_root):
        logger.error(f"Context root does not exist: {args.context_root}")
        sys.exit(1)

    try:
        # Create executor and run task
        executor = Executor(args.repo_root, args.context_root)
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
