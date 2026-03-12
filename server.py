from fastmcp import FastMCP

mcp = FastMCP("kubeflow-mcp")


def create_trainer_client(namespace: str = "default"):
    # returns a namespace-scoped TrainingClient
    from kubeflow.training import TrainingClient
    return TrainingClient(namespace=namespace)


@mcp.tool()
def list_training_jobs(namespace: str = "default") -> str:
    # list all TrainJobs and their status
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


@mcp.tool()
def get_training_logs(name: str, namespace: str = "default") -> str:
    # fetch logs for a given TrainJob
    try:
        client = create_trainer_client(namespace)
        logs = client.get_job_logs(name=name, namespace=namespace)
        return logs if logs else f"No logs found for job '{name}'"
    except Exception as e:
        return f"Error fetching logs for '{name}': {str(e)}"


@mcp.tool()
def get_training_job(name: str, namespace: str = "default") -> str:
    # get detailed status of a single TrainJob
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
            f"Completed: {end or 'N/A'}\n"
            f"Conditions:\n{conditions_str}"
        )
    except Exception as e:
        return f"Error fetching job '{name}': {str(e)}"


@mcp.tool()
def check_prerequisites(namespace: str = "default") -> str:
    # run basic pre-flight checks before submitting jobs
    results = []

    try:
        import kubeflow.training as kt
        version = getattr(kt, "__version__", "unknown")
        results.append(f"[PASS] kubeflow-training importable (version: {version})")
    except ImportError as e:
        results.append(f"[FAIL] kubeflow-training SDK not found: {e}")
        return "\n".join(results)

    try:
        client = create_trainer_client(namespace)
        results.append(f"[PASS] TrainingClient ok for namespace '{namespace}'")
    except Exception as e:
        results.append(f"[FAIL] TrainingClient could not be created: {e}")
        return "\n".join(results)

    try:
        jobs = client.list_training_jobs(namespace=namespace)
        count = len(jobs) if jobs else 0
        results.append(f"[PASS] API reachable — {count} TrainJob(s) in '{namespace}'")
    except Exception as e:
        results.append(f"[WARN] API connectivity probe failed: {e}")

    try:
        from kubeflow.training import TrainingClient as TC
        supported = getattr(TC, "job_kind", None) or "TrainJob (default)"
        results.append(f"[INFO] Default job kind: {supported}")
    except Exception:
        results.append("[INFO] Could not determine supported job kinds")

    results.append("\nPre-flight check complete.")
    return "\n".join(results)
