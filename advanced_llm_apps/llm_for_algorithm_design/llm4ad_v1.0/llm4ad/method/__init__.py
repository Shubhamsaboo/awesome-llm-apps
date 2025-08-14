from . import (
    funsearch,
    hillclimb,
    randsample,
    eoh,
    meoh,
    moead,
    nsga2
)

# try to import reevo
try:
    from . import reevo
except ImportError:
    pass

import os
import inspect
import importlib


def import_all_method_classes_from_subfolders(root_directory: str):
    """Dynamically imports all classes from Python files that share the same name as their parent folder.
    Args:
        root_directory: The root directory (e.g., 'method') to start the search.
    """
    # Iterate through the subdirectories
    for subdir in os.listdir(root_directory):
        subdir_path = os.path.join(root_directory, subdir)
        profiler_name = 'profiler'

        # Check if it's a directory and contains a .py file with the same name
        if os.path.isdir(subdir_path):
            module_file = f'{subdir}.py'
            profiler_file = f'{profiler_name}.py'
            module_path = os.path.join(subdir_path, module_file)
            profiler_path = os.path.join(subdir_path, profiler_file)

            # import the method
            if os.path.exists(module_path):
                # Build the module name for importing (e.g., method.eoh.eoh)
                module_name = f'{__name__}.{subdir}.{subdir}'

                # Dynamically import the module
                module = importlib.import_module(module_name)

                # Import all classes from the module
                for attribute_name in dir(module):
                    attribute = getattr(module, attribute_name)
                    if isinstance(attribute, type):  # Only import class objects
                        # Use inspect to check if the class is defined in the current module
                        if inspect.getmodule(attribute).__file__ == module.__file__:
                            globals()[attribute_name] = attribute  # Add the class to the global namespace
                            # print(f'Imported class {attribute_name} from {module_name}')

            # import the profiler
            if os.path.exists(profiler_path):
                # Build the module name for importing (e.g., method.eoh.eoh)
                module_name = f'{__name__}.{subdir}.{profiler_name}'

                # Dynamically import the module
                module = importlib.import_module(module_name)

                # Import all classes from the module
                for attribute_name in dir(module):
                    attribute = getattr(module, attribute_name)
                    if isinstance(attribute, type):  # Only import class objects
                        # Use inspect to check if the class is defined in the current module
                        if inspect.getmodule(attribute).__file__ == module.__file__:
                            globals()[attribute_name] = attribute  # Add the class to the global namespace
                            # print(f'Imported class {attribute_name} from {module_name}')
