import logging
from typing import Optional

logger = logging.getLogger("sre-tool")

class DiagnosticsManager:
    """Handles diagnostic operations for Kubernetes resources"""
    
    def __init__(self, k8s_client, deployment_manager, pod_manager):
        """Initialize with required manager instances
        
        Args:
            k8s_client: Kubernetes client instance
            deployment_manager: Deployment manager instance
            pod_manager: Pod manager instance
        """
        self.k8s_client = k8s_client
        self.apps_api = k8s_client.apps_api
        self.deployment_manager = deployment_manager
        self.pod_manager = pod_manager
        self.timeout = k8s_client.timeout
        
    def deployment_diagnostics(self, deployment_name: str, 
                              namespace: Optional[str] = None,
                              pod_name: Optional[str] = None) -> str:
        """Perform comprehensive diagnostics on a deployment
        
        Args:
            deployment_name: Name of the deployment
            namespace: Optional namespace of the deployment
            pod_name: Optional specific pod to diagnose
            
        Returns:
            str: Formatted diagnostic information
        """
        try:
            # Get deployment info first
            deployment_output = self.deployment_manager.retrieve_deployment_info(
                deployment_name, namespace
            )
            
            # Find namespace if not provided
            if not namespace:
                namespace = self.deployment_manager.locate_deployment_namespace(deployment_name)
                if "not found" in namespace or "Exception" in namespace:
                    return f"{deployment_output}\nError: {namespace}"
            
            # Find the ReplicaSet for this deployment
            try:
                replica_sets_list = self.apps_api.list_namespaced_replica_set(
                    namespace,
                    timeout_seconds=self.timeout
                )
                
                replica_set_name = None
                for rs in replica_sets_list.items:
                    if (rs.metadata.owner_references and
                        rs.metadata.owner_references[0].kind == 'Deployment' and 
                        rs.metadata.owner_references[0].name == deployment_name):
                        replica_set_name = rs.metadata.name
                        break
                        
                if not replica_set_name:
                    return f"{deployment_output}\nError: No ReplicaSet found for deployment {deployment_name}"
                    
            except Exception as e:
                logger.error(f"Error finding ReplicaSet: {e}")
                return f"{deployment_output}\nError finding ReplicaSet: {e}"
            
            # Get pod status for this ReplicaSet
            pod_status = self.pod_manager.get_pods_status(namespace, replica_set_name, pod_name)
            
            # Format pod information
            all_pod_outputs = []
            for pod in pod_status:
                if "error" in pod:
                    all_pod_outputs.append(f"Pod Info Error: {pod['error']}")
                    continue
                    
                # Format container information
                container_info = []
                for c in pod['containers']:
                    container_image = f"{c['name']}({c['image']})"
                    container_str = f"[CPU request: {c.get('cpu_request', 'N/A')}, "
                    container_str += f"CPU limit: {c.get('cpu_limit', 'N/A')}, "
                    
                    # Add CPU usage if available
                    if c.get('cpu_usage') != 'N/A':
                        container_str += f"CPU usage: {c.get('cpu_usage', 'N/A')}"
                        if c.get('cpu_usage_percentage') != 'N/A':
                            container_str += f" ({c.get('cpu_usage_percentage', 'N/A')}), "
                        else:
                            container_str += ", "
                    
                    container_str += f"Memory request: {c.get('memory_request', 'N/A')}, "
                    container_str += f"Memory limit: {c.get('memory_limit', 'N/A')}"
                    
                    # Add memory usage if available
                    if c.get('memory_usage') != 'N/A':
                        container_str += f", Memory usage: {c.get('memory_usage', 'N/A')}"
                        if c.get('memory_usage_percentage') != 'N/A':
                            container_str += f" ({c.get('memory_usage_percentage', 'N/A')})"
                    
                    container_str += "]"
                    container_info.append(container_str)
                
                # Format conditions
                conditions_str = ", ".join([
                    f"{cond['type']}:{cond['status']}" for cond in pod['conditions']
                ])
                
                # Build pod output
                pod_output = "Pod Info:\n"
                pod_output += f"Name: {pod['name']}, Namespace: {pod['namespace']}\n"
                pod_output += f"Node: {pod.get('node', 'N/A')}\n"
                pod_output += f"Phase: {pod['phase']}, Reason: {pod.get('reason', 'N/A')}\n"
                pod_output += f"Conditions: {conditions_str}\n"
                
                # Add any container reasons (errors)
                if pod.get('container_reasons'):
                    pod_output += f"Container Issues: {', '.join(pod['container_reasons'])}\n"
                
                # Add container details including resource usage
                for idx, c in enumerate(pod['containers']):
                    pod_output += f"Container {idx+1}: {c['name']} ({c['image']})\n"
                    pod_output += f"  Resource Requests: CPU={c.get('cpu_request', 'N/A')}, Memory={c.get('memory_request', 'N/A')}\n"
                    pod_output += f"  Resource Limits: CPU={c.get('cpu_limit', 'N/A')}, Memory={c.get('memory_limit', 'N/A')}\n"
                    
                    if c.get('cpu_usage') != 'N/A' or c.get('memory_usage') != 'N/A':
                        pod_output += f"  Current Usage: CPU={c.get('cpu_usage', 'N/A')}"
                        if c.get('cpu_usage_percentage') != 'N/A':
                            pod_output += f" ({c.get('cpu_usage_percentage', 'N/A')})"
                        pod_output += f", Memory={c.get('memory_usage', 'N/A')}"
                        if c.get('memory_usage_percentage') != 'N/A':
                            pod_output += f" ({c.get('memory_usage_percentage', 'N/A')})"
                        pod_output += "\n"
                
                pod_output += "-" * 50 + "\n"
                all_pod_outputs.append(pod_output)
            
            # Combine all outputs
            output = deployment_output
            for pod_output in all_pod_outputs:
                output += pod_output
                
            return output
            
        except Exception as e:
            error_msg = f"Error performing diagnostics: {e}"
            logger.error(error_msg)
            return error_msg