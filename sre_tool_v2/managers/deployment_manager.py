import logging
import time
from typing import Optional

from kubernetes.client.exceptions import ApiException

logger = logging.getLogger("sre-tool")

class DeploymentManager:
    """Manages Kubernetes deployment operations"""
    
    def __init__(self, k8s_client):
        """Initialize with a Kubernetes client
        
        Args:
            k8s_client: Kubernetes client instance
        """
        self.k8s_client = k8s_client
        self.apps_api = k8s_client.apps_api
        self.core_api = k8s_client.core_api
        self.timeout = k8s_client.timeout

    def locate_deployment_namespace(self, deployment_name: str) -> str:
        """Find the namespace for a given deployment
        
        Args:
            deployment_name: Name of the deployment
            
        Returns:
            str: Namespace of the deployment or error message
        """
        try:
            deployments = self.apps_api.list_deployment_for_all_namespaces(
                timeout_seconds=self.timeout
            )
            for deployment in deployments.items:
                if deployment.metadata.name == deployment_name:
                    logger.info(f"Found deployment {deployment_name} in namespace: {deployment.metadata.namespace}")
                    return deployment.metadata.namespace
            error_msg = f"Requested deployment: {deployment_name} not found"
            logger.warning(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"Exception when retrieving deployments: {e}"
            logger.error(error_msg)
            return error_msg

    def list_deployments(self, namespace: Optional[str] = None) -> str:
        """List all deployments, optionally filtered by namespace
        
        Args:
            namespace: Optional namespace to filter deployments
            
        Returns:
            str: Formatted list of deployments
        """
        try:
            output = "Deployments list:\n"
            if namespace:
                deployments = self.apps_api.list_namespaced_deployment(
                    namespace, 
                    timeout_seconds=self.timeout
                )
                logger.info(f"Listing deployments in namespace: {namespace}")
            else:
                deployments = self.apps_api.list_deployment_for_all_namespaces(
                    timeout_seconds=self.timeout
                )
                logger.info("Listing deployments across all namespaces")
                
            for deployment in deployments.items:
                output += f"Namespace: {deployment.metadata.namespace}, Name: {deployment.metadata.name}, Replicas: {deployment.spec.replicas}\n"
            return output
        except Exception as e:
            error_msg = f"Error when retrieving deployments: {e}"
            logger.error(error_msg)
            return error_msg

    def scale_deployment(self, deployment_name: str, scale_number: int, 
                         namespace: Optional[str] = None) -> str:
        """Scale a deployment to specified number of replicas
        
        Args:
            deployment_name: Name of the deployment to scale
            scale_number: Target number of replicas
            namespace: Optional namespace of the deployment
            
        Returns:
            str: Result message
        """
        try:
            # Find namespace if not provided
            if not namespace:
                namespace = self.locate_deployment_namespace(deployment_name)
                if "not found" in namespace or "Exception" in namespace:
                    return namespace
            
            # Prepare scale body
            scale_body = {'spec': {'replicas': scale_number}}
            
            # Apply scale operation
            self.apps_api.patch_namespaced_deployment_scale(
                deployment_name, 
                namespace, 
                scale_body,
                timeout_seconds=self.timeout
            )
            logger.info(f"Scaling {deployment_name} in namespace {namespace} to {scale_number} replicas")
            
            # Monitor scaling progress with timeout
            max_wait_time = 120  # 2 minutes timeout
            start_time = time.time()
            
            while True:
                # Check if we've exceeded the timeout
                if time.time() - start_time > max_wait_time:
                    warning_msg = f"Scaling operation timed out after {max_wait_time} seconds"
                    logger.warning(warning_msg)
                    return f"Partially scaled {deployment_name}. {warning_msg}"
                
                # Get current status
                read_scale_request = self.apps_api.read_namespaced_deployment_scale(
                    deployment_name,
                    namespace,
                    timeout_seconds=self.timeout
                )
                current_replicas = read_scale_request.status.replicas
                
                if current_replicas == scale_number:
                    logger.info(f"Successfully scaled {deployment_name} to {current_replicas} replicas")
                    break
                    
                logger.debug(f"Current replicas: {current_replicas}, target: {scale_number}")
                time.sleep(2)  # Wait before checking again
            
            return f"Successfully scaled {deployment_name} to {scale_number} replicas"
            
        except Exception as e:
            error_msg = f"Error when scaling deployment: {e}"
            logger.error(error_msg)
            return error_msg

    def retrieve_deployment_info(self, deployment_name: str, namespace: Optional[str] = None) -> str:
        """Get detailed information about a deployment
        
        Args:
            deployment_name: Name of the deployment
            namespace: Optional namespace of the deployment
            
        Returns:
            str: Formatted deployment information
        """
        try:
            if namespace:
                deployment = self.apps_api.read_namespaced_deployment(
                    deployment_name,
                    namespace,
        
                )
                logger.info(f"Retrieving info for deployment {deployment_name} in namespace {namespace}")
            else:
                # Display the first deployment if namespace and name not provided
                # This behavior is as specified in the requirements comment
                result = self.apps_api.list_deployment_for_all_namespaces(
                    limit=1,
                    timeout_seconds=self.timeout
                )
                if not result.items:
                    return "No deployments found in the cluster"
                deployment = result.items[0]
                logger.info(f"No specific deployment requested, showing first found: {deployment.metadata.name}")
            
            # Format the output
            output = "Deployment Info:\n"
            output += f"Name: {deployment.metadata.name}, Namespace: {deployment.metadata.namespace}\n"
            output += f"Replicas: Desired={deployment.spec.replicas}, "
            output += f"Ready={deployment.status.ready_replicas if deployment.status.ready_replicas is not None else 0}, "
            output += f"Available={deployment.status.available_replicas if deployment.status.available_replicas is not None else 0}\n"
            
            # Container details
            output += "Containers:\n"
            for container in deployment.spec.template.spec.containers:
                output += f"  {container.name} ({container.image})\n"
                
                # Resource requests and limits
                requests = container.resources.requests or {}
                limits = container.resources.limits or {}
                
                output += f"    Requests: CPU={requests.get('cpu', 'N/A')}, Memory={requests.get('memory', 'N/A')}\n"
                output += f"    Limits: CPU={limits.get('cpu', 'N/A')}, Memory={limits.get('memory', 'N/A')}\n"
                
            output += "-" * 50 + "\n"
            return output
            
        except Exception as e:
            error_msg = f"Error retrieving deployment info: {e}"
            logger.error(error_msg)
            return error_msg