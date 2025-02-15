from kubernetes import client, config
import argparse
import json

def check_kubernetes_connection():
    try:
        api_instance = client.CoreV1Api()
        api_instance.list_namespace()
        print("Kubernetes cluster is reachable.")
        print(" ")
        return True  
    
    except config.ConfigException as e:  
        print(f"Kubernetes configuration error: {e}")
        return False
    
    except client.ApiException as e:  
        print(f"Kubernetes API error: {e}")
        print(f"Response body: {e.body}")  
        print(f"Response headers: {e.headers}") 
        return False  
    
    except Exception as e:  
        print(f"An unexpected error occurred: {e}")
        return False

# list pod status
def get_pods_status(namespace,replicaset_name,pod_name):
    try:
        core_api = client.CoreV1Api()
        pods_list = core_api.list_namespaced_pod(namespace)
        pods_data = []
        for pod in pods_list.items:
            if (pod.metadata.owner_references[0].kind == 'ReplicaSet' and pod.metadata.owner_references[0].name == replicaset_name):
                #print(pod.metadata.name)
                container_statuses = pod.status.container_statuses or []
                conditions = pod.status.conditions or [] 
                container_reasons = []
                for container_status in container_statuses:
                    if container_status.state.waiting:
                        container_reasons.append(container_status.state.waiting.reason)
                    elif container_status.state.terminated:
                        container_reasons.append(container_status.state.terminated.reason)

                container_resources = []
                for container in pod.spec.containers:
                    requests = container.resources.requests or {}
                    limits = container.resources.limits or {}
                    container_resources.append({
                        "name": container.name,
                        "image": container.image,
                        "cpu_request": requests.get("cpu", "N/A"),
                        "memory_request": requests.get("memory", "N/A"),
                        "cpu_limit": limits.get("cpu", "N/A"),
                        "memory_limit": limits.get("memory", "N/A"),
                    })

                pod_data = {
                    "name": pod.metadata.name,
                    "namespace": pod.metadata.namespace,
                    "phase": pod.status.phase,
                    "reason": pod.status.reason,
                    "conditions": [{"type": c.type, "status": c.status, "reason": c.reason, "message": c.message} for c in conditions],
                    "container_reasons": container_reasons,
                    "containers": container_resources,
                    "start_time": pod.metadata.creation_timestamp.isoformat() if pod.metadata.creation_timestamp else None
                }
                pods_data.append(pod_data)  
        return pods_data  

    except Exception as e: 
        return f"Error: {e}"
    
#  Locate a deployment's namespace function
def locate_deployment_namespace(api_instance,deployment_name):
    try:
        deployments = api_instance.list_deployment_for_all_namespaces()
        for deployment in deployments.items:
            if deployment.metadata.name == deployment_name:
                print(f'Found deployment {deployment.metadata.name}, in namespace: {deployment.metadata.namespace}')
                return deployment.metadata.namespace
        return(f"Requested deployment: {deployment_name}, not found.")
    except Exception as e:
        return(f"Exepction when retriving deployments: {e}")
    
#sre list
#List all deployments function
def list_deployments(api_instance, namespace):
    # List Deployments  
    try:
        output = "Deployments list: \n"
        if namespace != None:
            deployments = api_instance.list_namespaced_deployment(namespace)
        else:
            deployments = api_instance.list_deployment_for_all_namespaces()
        for deployment in deployments.items:
            output += "Namespace: %s, Name: %s, Replicas: %s \n" % (deployment.metadata.namespace,deployment.metadata.name, deployment.spec.replicas)
        return output
    except Exception as e:
        return(f"Error when retriving deployments: {e}")

#sre scale
#Scae deployments function
def scale_deployment(api_instance,deployment_name,namespace,scale_number):
    try:
        scale_body = {
            'spec':{
                'replicas': scale_number
            }
        }
        if namespace != None:
            api_instance.patch_namespaced_deployment_scale(deployment_name,namespace,scale_body)
        else:
            namespace = locate_deployment_namespace(api_instance,deployment_name)
            api_instance.patch_namespaced_deployment_scale(deployment_name,namespace,scale_body)
        #Retrievie current replicas from deployment
        read_scale_request = api_instance.read_namespaced_deployment_scale(deployment_name,namespace)
        current_replicas = read_scale_request.status.replicas
   
        #Sample deployment replicas number.
        while current_replicas != scale_number:
            read_scale_request = api_instance.read_namespaced_deployment_scale(deployment_name,namespace)
            current_replicas = read_scale_request.status.replicas
        print (f"Deployment Replicas: {current_replicas}")
        return (f"Succesfully scaled {read_scale_request.metadata.name}, to {current_replicas} replicas")


    except Exception as e:
        return(f"Error when scaling deployment: {e}")
    
#sre info
def retrieve_deployment_info(api_instance,deployment_name,namespace):
    try:
        if namespace != None:
            deployment = api_instance.read_namespaced_deployment_status(deployment_name,namespace)
        else:
            result = api_instance.list_deployment_for_all_namespaces()
            deployment = result.items[0]

        output = "Deployment Info: \n"
        output += f"Name: {deployment.metadata.name}, Namespace: {deployment.metadata.namespace}, \n"
        output += f"Replicas: Desired={deployment.spec.replicas}, Ready={deployment.status.ready_replicas if deployment.status.ready_replicas is not None else 0}, "  
        output += f"Available={deployment.status.available_replicas if deployment.status.available_replicas is not None else 0},\n"
        output += f"Containers: "
        for container in deployment.spec.template.spec.containers:
            output += f"{container.name}({container.image}) \n"
        
        output += "-" * 50 + "\n" 
        return output
    except Exception as e: 
        return f"Error: {e}"
    
#sre diagnostic - 
def deployment_diagnostics(api_instance,deployment_name,namespace, pod_name):
    try:
        #Retrieive deployment output from 'info' command function.
        deployment_output = retrieve_deployment_info(api_instance,deployment_name,namespace)
        #Retrieive deployment's namespace if not inputed
        if namespace != None:
            replica_sets_list = api_instance.list_namespaced_replica_set(namespace)
        else:
            namespace = locate_deployment_namespace(api_instance,deployment_name)
            replica_sets_list = api_instance.list_namespaced_replica_set(namespace)

        for rs in replica_sets_list.items:
            if (rs.metadata.owner_references[0].kind == 'Deployment' and rs.metadata.owner_references[0].name == deployment_name):
                replica_set_name = rs.metadata.name
                
        pod_status = get_pods_status(namespace,replica_set_name, pod_name)
        all_pod_outputs = []
        for pod in pod_status:
            container_info = []
            for c in pod['containers']:
                container_image = f"{c['name']}({c['image']})"
                if c.get('cpu_request') != 'N/A' or c.get('memory_request') != 'N/A':
                    container_str = f"[CPU: {c.get('cpu_request', 'N/A')}, Memory: {c.get('memory_request', 'N/A')}]"
                    print(container_str)
                container_info.append(container_str)
            container_info_str = ", ".join(container_info)
            conditions_str = ", ".join([f"{cond['type']}:{cond['status']}" for cond in pod['conditions']])
            
            pod_output = f"Pod Info:\n"  
            pod_output += f"Name: {pod['name']}, Namespace: {pod['namespace']}\n"
            pod_output += f"Phase: {pod['phase']}, Reason: {pod.get('reason', 'N/A')}\n"
            pod_output += f"Conditions: {conditions_str}\n"
            pod_output += f"Image: {container_image}, Containers: {container_info_str}\n"  
            pod_output += "-" * 50 + "\n" 
            all_pod_outputs.append(pod_output)

        output = deployment_output
        for i in all_pod_outputs:
            output += i
        return output

    except Exception as e: 
        return f"Error: {e}"


def main():
    parser = argparse.ArgumentParser(prog='sre',description="a simple cli tool, helps to manage k8s resources without using k8s commands")
    subparser = parser.add_subparsers(dest="command", help="Available commands")

    #list command
    list_parser = subparser.add_parser("list", help="List deployments in a cluster")
    list_parser.add_argument("--namespace" ,help="Required namespace")

    #scale command
    scale_parser = subparser.add_parser("scale" ,help="scale deployments in a cluster")
    scale_parser.add_argument('--replicas',required=True, type=int, help="Number of replicas to scale to")
    scale_parser.add_argument('--deployment',required=True ,type=str, help='Name of deployment to scale')
    scale_parser.add_argument('--namespace', type=str, help='Scale the deployment in the specified namespace')

    #info command
    scale_parser = subparser.add_parser("info" ,help="Shows information regarding a deployment in the cluster")
    scale_parser.add_argument('--deployment',required=True, type=str, help="Name of deployment")
    scale_parser.add_argument('--namespace',type=str, help='Namespace of the deployment')
    
    #diagnostic command
    scale_parser = subparser.add_parser("diagnostic" ,help="Show diagnose of a deployments and its corresponding resources (rs,pods)in a cluster")
    scale_parser.add_argument('--deployment',required=True, type=str, help="Name of deployment")
    scale_parser.add_argument('--namespace',type=str, help='Namespace of the deployment')
    scale_parser.add_argument('--pod',type=str, help='Name of a pod to Include pod-level diagnostics, such as pending, failed, or crash-looping pods.')

    args = parser.parse_args()
    config.load_kube_config()
    apps_v1 = client.AppsV1Api()
    check_kubernetes_connection()
    if args.command == "list":
        result = list_deployments(apps_v1, args.namespace)
    elif args.command == 'scale':
        result = scale_deployment(apps_v1,args.deployment,args.namespace,args.replicas)
    elif args.command == 'info':
        result = retrieve_deployment_info(apps_v1,args.deployment,args.namespace)
    elif args.command == 'diagnostic':
        result = deployment_diagnostics(apps_v1,args.deployment,args.namespace,args.pod)
    if 'Error' in result:
        print(f"Failed to run command: {args.command} deployment")
        print("-" * 50)
        print(f"Error for devs: {result}")
    else:
        print(result)

if __name__ == '__main__':
    main()