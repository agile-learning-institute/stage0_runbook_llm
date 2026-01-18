"""CLI command entry point."""
import os
import sys
import logging

try:
    from .config import Config
    from .executor import Executor
except ImportError:
    # Handle direct import (when PYTHONPATH=./src and running as module)
    from config import Config
    from executor import Executor

logger = logging.getLogger(__name__)


def main():
    """CLI command entry point."""
    # Initialize config (configures logging)
    config = Config()
    
    # Validate that required paths exist
    if not os.path.exists(config.REPO_ROOT):
        logger.error(f"Repository root does not exist: {config.REPO_ROOT}")
        sys.exit(1)

    # Context root is optional - only validate if set
    context_root = config.CONTEXT_ROOT if config.CONTEXT_ROOT else None
    if context_root and not os.path.exists(context_root):
        logger.error(f"Context root does not exist: {context_root}")
        sys.exit(1)

    try:
        # Execute task (context_root is optional)
        commit_message, patch = Executor.execute_task(
            config.REPO_ROOT,
            config.TASK_NAME,
            context_root=context_root
        )

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
