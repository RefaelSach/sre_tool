# SRE Tool

A command-line tool for managing Kubernetes deployments built with Python.

## Versions

There are two versions of the tool available:

- **sre_tool_v1:** The older version with unstructured code, no logging, and fewer best practices applied.
- **sre_tool_v2:** The newer version with improved structure, logging, and better adherence to best practices, making the code easier to read and maintain.

The way to run the tool remains the same for both versions, but for `sre_tool_v2`, use `main.py` instead of `sre_tool.py`.

## Prerequisites

Before using this tool, ensure you have:

- Python 3.x installed
- Access to a Kubernetes cluster
- A valid kubeconfig file

## Installation

Install required dependencies:

```bash
pip install -r requirements.txt
```

Configure Kubernetes access by setting the `KUBECONFIG` environment variable:

```bash
export KUBECONFIG=./kubeconfig
```

## Usage

The tool provides four main commands: `list`, `scale`, `info`, and `diagnostic`.

### Listing Deployments

List all deployments in the cluster:

```bash
python3 sre_tool.py list  # For v1
python3 main.py list      # For v2
```

List deployments in a specific namespace:

```bash
python3 sre_tool.py list --namespace default  # For v1
python3 main.py list --namespace default      # For v2
```

### Scaling Deployments

Scale a deployment to a specified number of replicas:

```bash
python3 sre_tool.py scale --replicas 5 --deployment test-deployment  # For v1
python3 main.py scale --replicas 5 --deployment test-deployment      # For v2
```

### Retrieving Deployment Info

Get detailed information about a specific deployment:

```bash
python3 sre_tool.py info --deployment failing-deployment --namespace default  # For v1
python3 main.py info --deployment failing-deployment --namespace default      # For v2
```

### Running Diagnostic on Deployments

Run diagnostics on a deployment:

```bash
python3 sre_tool.py diagnostic --deployment resource-deployment --namespace default  # For v1
python3 main.py diagnostic --deployment resource-deployment --namespace default      # For v2
```

### Help

To see all available options and commands:

```bash
python3 sre_tool.py --help  # For v1
python3 main.py --help      # For v2
```
