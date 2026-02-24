# Kubeflow MCP Server — Proof of Concept

A proof-of-concept MCP server that lets LLM tools like Claude 
interact with Kubeflow TrainJobs.

## Problem it solves
Currently there is no way for an LLM to:
- See status of a Kubeflow TrainJob
- Debug a crash loop by reading logs
- List running/failed jobs in a namespace

## Tools implemented
| Tool | Description |
|---|---|
| `list_training_jobs(namespace)` | Lists all TrainJobs with their status |
| `get_training_logs(name, namespace)` | Fetches logs to debug failures |

## Related
- Tracking issue: https://github.com/kubeflow/sdk/issues/238
- KEP-936: https://github.com/kubeflow/community/issues/936

## How to run
pip install -r requirements.txt
python server.py
