from mcp.server.fastmcp import FastMCP

mcp = FastMCP("kubeflow-mcp")

@mcp.tool()
def get_training_logs(name: str, namespace: str = "default") -> str:
    """Get logs from a Kubeflow TrainJob to debug crash loops."""
    try:
        from kubeflow.training import TrainingClient
        client = TrainingClient()
        logs = client.get_job_logs(name=name, namespace=namespace)
        return logs if logs else f"No logs found for job '{name}'"
    except Exception as e:
        return f"Error fetching logs for '{name}': {str(e)}"

@mcp.tool()
def list_training_jobs(namespace: str = "default") -> str:
    """List all Kubeflow TrainJobs in a namespace."""
    try:
        from kubeflow.training import TrainingClient
        client = TrainingClient()
        jobs = client.list_training_jobs(namespace=namespace)
        if not jobs:
            return f"No TrainJobs found in namespace '{namespace}'"
        return "\n".join([f"- {j.metadata.name}: {j.status.conditions[-1].type}" for j in jobs])
    except Exception as e:
        return f"Error listing jobs: {str(e)}"

if __name__ == "__main__":
    mcp.run()
