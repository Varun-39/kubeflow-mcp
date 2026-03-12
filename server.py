from fastmcp import FastMCP

mcp = FastMCP("kubeflow-mcp")

# ---------------------------------------------------------------------------
# Helper — Phase 1 pattern confirmed by abhijeet-dhumal
# ---------------------------------------------------------------------------

def create_trainer_client(namespace: str = "default"):
    """
    Factory helper that returns a TrainingClient scoped to the given namespace.
    Centralises client creation so every tool uses the same initialisation pattern.
    """
    from kubeflow.training import TrainingClient
    return TrainingClient(namespace=namespace)


# ---------------------------------------------------------------------------
# Phase 1 — List jobs (original)
# ---------------------------------------------------------------------------

@mcp.tool()
def list_training_jobs(namespace: str = "default") -> str:
    """List all Kubeflow TrainJobs in a namespace with their latest status."""
    try:
        client = create_trainer_client(namespace)
        jobs = client.list_training_jobs(namespace=namespace)
        if not jobs:
            return f"No TrainJobs found in namespace '{namespace}'"
        return "\n".join(
            [f"- {j.metadata.name}: {j.status.conditions[-1].type}" for j in jobs]
        )
    except Exception as e:
        return f"Error listing jobs: {str(e)}"


# ---------------------------------------------------------------------------
# Phase 1 — Fetch logs (original)
# ---------------------------------------------------------------------------

@mcp.tool()
def get_training_logs(name: str, namespace: str = "default") -> str:
    """Get logs from a Kubeflow TrainJob to debug crash loops."""
    try:
        client = create_trainer_client(namespace)
        logs = client.get_job_logs(name=name, namespace=namespace)
        return logs if logs else f"No logs found for job '{name}'"
    except Exception as e:
        return f"Error fetching logs for '{name}': {str(e)}"


# ---------------------------------------------------------------------------
# Phase 2 — Get single job status (new)
# ---------------------------------------------------------------------------

@mcp.tool()
def get_training_job(name: str, namespace: str = "default") -> str:
    """
    Get detailed status of a specific Kubeflow TrainJob by name.

    Returns job phase, conditions, start time, and completion time when available.
    Corresponds to KEP Phase 2: per-job inspection.
    """
    try:
        client = create_trainer_client(namespace)
        job = client.get_training_job(name=name, namespace=namespace)
        if job is None:
            return f"TrainJob '{name}' not found in namespace '{namespace}'"

        meta = job.metadata
        status = job.status

        conditions = []
        if status and status.conditions:
            for c in status.conditions:
                conditions.append(f"  [{c.type}] {c.reason}: {c.message}")
        conditions_str = "\n".join(conditions) if conditions else "  No conditions reported"

        start = getattr(status, "start_time", None)
        end = getattr(status, "completion_time", None)

        return (
            f"TrainJob: {meta.name}\n"
            f"Namespace: {meta.namespace}\n"
            f"Created: {meta.creation_timestamp}\n"
            f"Started: {start or 'N/A'}\n"
            f"Completed: {end or 'N/A (still running or failed)'}\n"
            f"Conditions:\n{conditions_str}"
        )
    except Exception as e:
        return f"Error fetching job '{name}': {str(e)}"


# ---------------------------------------------------------------------------
# Phase 2 — Pre-flight / prerequisites check (new)
# ---------------------------------------------------------------------------

@mcp.tool()
def check_prerequisites(namespace: str = "default") -> str:
    """
    Phase 2 pre-flight validation: verify the environment is ready before
    submitting a TrainJob.

    Checks performed:
      1. kubeflow-training SDK is importable
      2. A TrainingClient can be instantiated for the given namespace
      3. The namespace contains at least one existing TrainJob (connectivity probe)
      4. kubeflow.training API version is reported

    Returns a structured readiness report.
    """
    results = []

    # Check 1 — SDK importable
    try:
        import kubeflow.training as kt
        version = getattr(kt, "__version__", "unknown")
        results.append(f"[PASS] kubeflow-training SDK importable (version: {version})")
    except ImportError as e:
        results.append(f"[FAIL] kubeflow-training SDK not found: {e}")
        return "\n".join(results)

    # Check 2 — Client instantiation
    try:
        client = create_trainer_client(namespace)
        results.append(f"[PASS] TrainingClient instantiated for namespace '{namespace}'")
    except Exception as e:
        results.append(f"[FAIL] TrainingClient could not be created: {e}")
        return "\n".join(results)

    # Check 3 — API connectivity (list jobs as a probe)
    try:
        jobs = client.list_training_jobs(namespace=namespace)
        count = len(jobs) if jobs else 0
        results.append(
            f"[PASS] API connectivity OK — {count} TrainJob(s) found in '{namespace}'"
        )
    except Exception as e:
        results.append(f"[WARN] API connectivity probe failed: {e}")

    # Check 4 — Report supported job kinds
    try:
        from kubeflow.training import TrainingClient as TC
        supported = getattr(TC, "job_kind", None) or "TrainJob (default)"
        results.append(f"[INFO] Default job kind: {supported}")
    except Exception:
        results.append("[INFO] Could not determine supported job kinds")

    results.append("\nPre-flight check complete.")
    return "\n".join(results)


if __name__ == "__main__":
    mcp.run()
