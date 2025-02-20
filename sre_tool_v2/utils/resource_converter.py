def convert_cpu_to_cores(cpu_str: str) -> float:
    """Convert Kubernetes CPU notation to core value
    
    Args:
        cpu_str: CPU string (e.g., "100m", "0.5")
        
    Returns:
        float: CPU value in cores
    """
    if cpu_str.endswith('m'):
        return float(cpu_str[:-1]) / 1000
    return float(cpu_str)
        
def convert_memory_to_bytes(mem_str: str) -> int:
    """Convert Kubernetes memory notation to bytes
    
    Args:
        mem_str: Memory string (e.g., "100Mi", "2Gi")
        
    Returns:
        int: Memory value in bytes
    """
    units = {'Ki': 2**10, 'Mi': 2**20, 'Gi': 2**30, 'Ti': 2**40}
    if mem_str[-2:] in units:
        return int(float(mem_str[:-2]) * units[mem_str[-2:]])
    elif mem_str[-1] == 'K':
        return int(float(mem_str[:-1]) * 1000)
    elif mem_str[-1] == 'M':
        return int(float(mem_str[:-1]) * 1000000)
    elif mem_str[-1] == 'G':
        return int(float(mem_str[:-1]) * 1000000000)
    return int(mem_str)