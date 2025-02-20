import logging
from kubernetes import client, config
from kubernetes.client.exceptions import ApiException

logger = logging.getLogger("sre-tool")

class KubernetesClient:
    """Centralized class for Kubernetes API clients"""
    
    def __init__(self, timeout: int = 30):
        """Initialize Kubernetes API clients
        
        Args:
            timeout: API request timeout in seconds
        """
        try:
            config.load_kube_config()
            self.core_api = client.CoreV1Api()
            self.apps_api = client.AppsV1Api()
            self.timeout = timeout
            logger.debug("Kubernetes client initialized successfully")
        except config.ConfigException as e:
            logger.error(f"Failed to load kubeconfig: {e}")
            raise

    def check_connection(self) -> bool:
        """Verify connection to Kubernetes cluster
        
        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            self.core_api.list_namespace(timeout_seconds=self.timeout)
            logger.info("Kubernetes cluster is reachable")
            return True
        except config.ConfigException as e:
            logger.error(f"Kubernetes configuration error: {e}")
            return False
        except ApiException as e:
            logger.error(f"Kubernetes API error: {e}")
            logger.debug(f"Response body: {e.body}")
            logger.debug(f"Response headers: {e.headers}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error occurred: {e}")
            return False