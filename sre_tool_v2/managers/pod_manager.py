import logging
from typing import List, Dict, Any, Optional
from kubernetes import client

from utils.resource_converter import convert_cpu_to_cores, convert_memory_to_bytes

logger = logging.getLogger("sre-tool")

class PodManager:
    """Manages Kubernetes pod operations"""
    
    def __init__(self, k8s_client):
        """Initialize with a Kubernetes client
        
        Args:
            k8s_client: Kubernetes client instance
        """
        self.k8s_client = k8s_client
        self.core_api = k8s_client.core_api
        self.timeout = k8s_client.timeout
        
    def get_pods_status(self, namespace: str, replicaset_name: str, 
                       pod_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get detailed status of pods belonging to a ReplicaSet
        
        Args:
            namespace: Namespace of the pods
            replicaset_name: Name of the parent ReplicaSet
            pod_name: Optional specific pod name to filter
            
        Returns:
            List[Dict]: Detailed pod information
        """
        try:
            pods_list = self.core_api.list_namespaced_pod(
                namespace,
                timeout_seconds=self.timeout
            )
            pods_data = []
            
            # Get node metrics for resource usage calculation
            try:
                metrics_api = client.CustomObjectsApi()
                node_metrics = metrics_api.list_cluster_custom_object(
                    "metrics.k8s.io", "v1beta1", "nodes", 
                    timeout_seconds=self.timeout
                )
                pod_metrics = metrics_api.list_namespaced_custom_object(
                    "metrics.k8s.io", "v1beta1", namespace, "pods",
                    timeout_seconds=self.timeout
                )
                metrics_available = True
            except Exception as e:
                logger.warning(f"Unable to get metrics: {e}")
                metrics_available = False
                
            for pod in pods_list.items:
                # Skip if pod doesn't have owner references
                if not pod.metadata.owner_references:
                    continue
                    
                # Filter by replicaset name if provided
                if (pod.metadata.owner_references[0].kind == 'ReplicaSet' and 
                    pod.metadata.owner_references[0].name == replicaset_name):
                    
                    # Filter by pod name if provided
                    if pod_name and pod_name != pod.metadata.name:
                        continue
                    
                    # Process container statuses
                    container_statuses = pod.status.container_statuses or []
                    conditions = pod.status.conditions or []
                    
                    # Get container reasons
                    container_reasons = []
                    for container_status in container_statuses:
                        if container_status.state.waiting:
                            container_reasons.append(container_status.state.waiting.reason)
                        elif container_status.state.terminated:
                            container_reasons.append(container_status.state.terminated.reason)
                    
                    # Get container resources
                    container_resources = []
                    for container in pod.spec.containers:
                        requests = container.resources.requests or {}
                        limits = container.resources.limits or {}
                        
                        # Initialize resource data
                        resource_data = {
                            "name": container.name,
                            "image": container.image,
                            "cpu_request": requests.get("cpu", "N/A"),
                            "memory_request": requests.get("memory", "N/A"),
                            "cpu_limit": limits.get("cpu", "N/A"),
                            "memory_limit": limits.get("memory", "N/A"),
                            "cpu_usage": "N/A",
                            "memory_usage": "N/A",
                            "cpu_usage_percentage": "N/A",
                            "memory_usage_percentage": "N/A"
                        }
                        
                        # Add usage metrics if available
                        if metrics_available:
                            try:
                                for item in pod_metrics.get('items', []):
                                    if item['metadata']['name'] == pod.metadata.name:
                                        for container_metric in item['containers']:
                                            if container_metric['name'] == container.name:
                                                cpu_usage = container_metric['usage']['cpu']
                                                memory_usage = container_metric['usage']['memory']
                                                
                                                # Calculate percentages if requests are available
                                                if 'cpu' in requests and requests['cpu'] != "N/A":
                                                    try:
                                                        request_cpu = convert_cpu_to_cores(requests['cpu'])
                                                        usage_cpu = convert_cpu_to_cores(cpu_usage)
                                                        cpu_percentage = (usage_cpu / request_cpu) * 100
                                                        resource_data["cpu_usage_percentage"] = f"{cpu_percentage:.1f}%"
                                                    except:
                                                        pass
                                                
                                                if 'memory' in requests and requests['memory'] != "N/A":
                                                    try:
                                                        request_mem = convert_memory_to_bytes(requests['memory'])
                                                        usage_mem = convert_memory_to_bytes(memory_usage)
                                                        mem_percentage = (usage_mem / request_mem) * 100
                                                        resource_data["memory_usage_percentage"] = f"{mem_percentage:.1f}%"
                                                    except:
                                                        pass
                                                        
                                                resource_data["cpu_usage"] = cpu_usage
                                                resource_data["memory_usage"] = memory_usage
                            except Exception as e:
                                logger.debug(f"Error calculating resource usage: {e}")
                        
                        container_resources.append(resource_data)
                    
                    # Create pod data entry
                    pod_data = {
                        "name": pod.metadata.name,
                        "namespace": pod.metadata.namespace,
                        "phase": pod.status.phase,
                        "reason": pod.status.reason,
                        "conditions": [
                            {
                                "type": c.type, 
                                "status": c.status, 
                                "reason": c.reason, 
                                "message": c.message
                            } for c in conditions
                        ],
                        "container_reasons": container_reasons,
                        "containers": container_resources,
                        "start_time": pod.metadata.creation_timestamp.isoformat() 
                                     if pod.metadata.creation_timestamp else None,
                        "node": pod.spec.node_name
                    }
                    
                    pods_data.append(pod_data)
                    
            return pods_data
            
        except Exception as e:
            logger.error(f"Error getting pod status: {e}")
            return [{"error": f"Error: {e}"}]