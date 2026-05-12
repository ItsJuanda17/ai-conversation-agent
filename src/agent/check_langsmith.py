from __future__ import annotations

import os
import time
from typing import Any

from dotenv import load_dotenv
from langsmith import Client, traceable
from langsmith.run_helpers import get_current_run_tree

from src.agent.agent import configure_observability
from src.agent.tools import consultar_propagacion


@traceable(name="validacion_langsmith_propagacion", tags=["validation", "mcp", "propagation"])
def traced_propagation_check(root_id: str, max_depth: int = 5) -> dict[str, Any]:
    run_tree = get_current_run_tree()
    result = consultar_propagacion(root_id=root_id, max_depth=max_depth)
    return {
        "run_id": str(run_tree.id) if run_tree is not None else None,
        "root_id": root_id,
        "direct_replies": result["direct_replies"],
        "total_descendants": result["total_descendants"],
        "metrics": result["metrics"],
    }


def main() -> None:
    load_dotenv()
    configure_observability()

    if os.getenv("LANGSMITH_TRACING", "false").lower() != "true":
        raise RuntimeError("LANGSMITH_TRACING is disabled. Enable it in the environment first.")

    if not os.getenv("LANGSMITH_API_KEY"):
        raise RuntimeError("Missing LANGSMITH_API_KEY in the environment.")

    project_name = os.getenv("LANGSMITH_PROJECT", "default")
    root_id = os.getenv("LANGSMITH_VALIDATION_ROOT_ID", "106064209472141_767905085584441")

    result = traced_propagation_check(root_id=root_id)
    run_id = result["run_id"]

    client = Client()
    trace_found = False

    for _ in range(5):
        runs = list(
            client.list_runs(
                project_name=project_name,
                run_ids=[run_id] if run_id else None,
                limit=1,
            )
        )
        trace_found = any(str(run.id) == run_id for run in runs)
        if trace_found:
            break
        time.sleep(1)

    print(f"LangSmith project: {project_name}")
    print(f"Run id: {run_id}")
    print(f"Trace visible: {trace_found}")
    print(f"Direct replies: {result['direct_replies']}")
    print(f"Total descendants: {result['total_descendants']}")


if __name__ == "__main__":
    main()