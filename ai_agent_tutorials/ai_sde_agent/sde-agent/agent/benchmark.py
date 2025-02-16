import argparse

from agent import composio_toolset, crew

from swekit.benchmark.run_evaluation import evaluate
from swekit.config.store import IssueConfig


def bench(workspace_id: str, issue_config: IssueConfig) -> str:
    """Run benchmark on the agent."""

    # Set the workspace for the tools to run.
    composio_toolset.set_workspace_id(workspace_id)

    # kick off the crew on the issue.
    return crew.kickoff(
        inputs={
            "repo": issue_config.repo_name,
            "issue": issue_config.issue_desc,
        }
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run benchmark on the agent.",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--test-split",
        type=str,
        default="1:2",
        help="Test split ratio (e.g. 1:2, 1:500) Maximum 500 tests per project.",
    )
    group.add_argument(
        "--test-instance-ids",
        type=str,
        default="",
        help="Test instance ids (comma-separated)",
    )
    args = parser.parse_args()

    if args.test_instance_ids:
        test_instance_ids_list = [
            id.strip() for id in args.test_instance_ids.split(",")
        ]
        test_range = "1:500"
    else:
        test_instance_ids_list = []
        test_range = args.test_split

    evaluate(
        bench,
        dry_run=False,
        test_range=test_range,
        test_instance_ids=test_instance_ids_list,
        # image_name="composio/composio:latest", # if you are doing local dev
    )
