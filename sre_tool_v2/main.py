#!/usr/bin/env python3
import argparse
import time
import logging
from typing import Optional

from clients.kubernetes_client import KubernetesClient
from managers.deployment_manager import DeploymentManager
from managers.pod_manager import PodManager
from managers.diagnostics_manager import DiagnosticsManager


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("sre-tool")

def main():
    """Main entry point for the CLI tool"""
    
    parser = argparse.ArgumentParser(
        prog='sre_tool',
        description="A simple CLI tool that helps manage Kubernetes resources without direct kubectl usage"
    )
    subparser = parser.add_subparsers(dest="command", help="Available commands")
    
    # List command
    list_parser = subparser.add_parser("list", help="List deployments in a cluster")
    list_parser.add_argument("--namespace", help="Optional namespace to filter results")
    
    # Scale command
    scale_parser = subparser.add_parser("scale", help="Scale deployments in a cluster")
    scale_parser.add_argument('--replicas', required=True, type=int, help="Number of replicas to scale to")
    scale_parser.add_argument('--deployment', required=True, type=str, help='Name of deployment to scale')
    scale_parser.add_argument('--namespace', type=str, help='Scale the deployment in the specified namespace')
    
    # Info command
    info_parser = subparser.add_parser("info", help="Shows information regarding a deployment in the cluster")
    info_parser.add_argument('--deployment', required=True, type=str, help="Name of deployment")
    info_parser.add_argument('--namespace', type=str, 
                             help='Display deployment info in the specified namespace. If omitted, show info for the first deployment found.')
    
    # Diagnostic command
    diag_parser = subparser.add_parser("diagnostic", help="Show diagnose of a deployment and its resources (rs, pods)")
    diag_parser.add_argument('--deployment', required=True, type=str, help="Name of deployment")
    diag_parser.add_argument('--namespace', type=str, help='Namespace of the deployment')
    diag_parser.add_argument('--pod', type=str, help='Name of a pod to include pod-level diagnostics')
    
    # Debug command
    debug_parser = subparser.add_parser("debug", help="Set log level for debugging")
    debug_parser.add_argument('--level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                             default='INFO', help='Set logging level')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Handle debug command first
    if args.command == "debug":
        logging.getLogger().setLevel(getattr(logging, args.level))
        print(f"Log level set to {args.level}")
        return
    
    # Initialize Kubernetes client
    try:
        k8s_client = KubernetesClient(timeout=30)
        if not k8s_client.check_connection():
            logger.error("Failed to connect to Kubernetes cluster")
            return
        
        # Initialize managers
        deployment_manager = DeploymentManager(k8s_client)
        pod_manager = PodManager(k8s_client)
        diagnostics_manager = DiagnosticsManager(k8s_client, deployment_manager, pod_manager)
        
        # Execute requested command
        if args.command == "list":
            result = deployment_manager.list_deployments(args.namespace)
        elif args.command == 'scale':
            result = deployment_manager.scale_deployment(args.deployment, args.replicas, args.namespace)
        elif args.command == 'info':
            result = deployment_manager.retrieve_deployment_info(args.deployment, args.namespace)
        elif args.command == 'diagnostic':
            result = diagnostics_manager.deployment_diagnostics(args.deployment, args.namespace, args.pod)
        else:
            logger.error(f"Unknown command: {args.command}")
            parser.print_help()
            return
        
        if 'Error' in result:
            logger.error(f"Failed to run command: {args.command}")
            print("-" * 50)
            print(f"Error: {result}")
        else:
            print(result)
            
    except Exception as e:
        logger.error(f"Failed running tool: {e}")
        print(f"Failed running tool: {e}")


if __name__ == '__main__':
    main()