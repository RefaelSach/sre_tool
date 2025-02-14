# SRE Tool

A command-line tool for managing Kubernetes deployments built with Python.

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

The tool provides two main commands: `list` and `scale`.

### Listing Deployments

List all deployments in the cluster:

```bash
python3 sre_tool.py list
```

List deployments in a specific namespace:

```bash
python3 sre_tool.py list --namespace default
```

### Scaling Deployments

Scale a deployment to a specified number of replicas:

```bash
python3 sre_tool.py scale --replicas 5 --deployment test-deployment
```

## Help

To see all available options and commands:

```bash
python3 sre_tool.py --help
```

## Implementation Notes

### `--namespace` Argument Functionality

- When specified, the tool will display deployment info in the specified namespace.
- If omitted, the tool will show info for the first deployment found in the cluster.

This implementation choice was made based on initial requirements interpretation. Future versions may modify this behavior based on user feedback.

