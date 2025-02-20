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

The tool provides four main commands: `list`, `scale`, `info`, and `diagnostic`.

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

### Retrieving Deployment Info

Get detailed information about a specific deployment:

```bash
python3 sre_tool.py info --deployment failing-deployment --namespace default
```

### Running Diagnostic on Deployments

Run diagnostics on a deployment:

```bash
python3 sre_tool.py diagnostic --deployment resource-deployment --namespace default
```

### Help

To see all available options and commands:

```bash
python3 sre_tool.py --help
```

