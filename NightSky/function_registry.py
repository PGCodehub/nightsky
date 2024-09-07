# file: function_registry.py
from typing import Callable, Dict, List

function_registry: Dict[str, Dict[str, Callable]] = {}

def register_function(func: Callable) -> Callable:
    module_name = func.__module__
    func_name = func.__name__
    if func_name not in function_registry:
        function_registry[func_name] = {}
    function_registry[func_name][module_name] = func
    return func

def load_registered_function(function_name: str, module_name: str = None) -> Callable:
    if function_name not in function_registry:
        raise ValueError(f"No function named '{function_name}' has been registered")
    
    if module_name:
        if module_name not in function_registry[function_name]:
            raise ValueError(f"No function named '{function_name}' from module '{module_name}' has been registered")
        return function_registry[function_name][module_name]
    
    if len(function_registry[function_name]) > 1:
        raise ValueError(f"Multiple functions named '{function_name}' have been registered. Please specify a module name.")
    
    return next(iter(function_registry[function_name].values()))

def list_registered_functions() -> Dict[str, List[str]]:
    return {func_name: list(modules.keys()) for func_name, modules in function_registry.items()}