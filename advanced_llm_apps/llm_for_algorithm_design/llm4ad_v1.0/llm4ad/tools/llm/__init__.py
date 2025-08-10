import os
import inspect
import importlib


def import_all_llm_classes_from_subfolders(root_directory):
    """Dynamically imports all classes from Python files that share the same name as their parent folder.
    Args:
        root_directory (str): The root directory (e.g., 'method') to start the search.
    """
    # Iterate through the subdirectories
    for subdir in os.listdir(root_directory):
        module_path = os.path.join(root_directory, subdir)

        if os.path.exists(module_path):
            # Build the module name for importing (e.g., method.eoh.eoh)
            module_name = f'{__name__}.{subdir}'.rstrip('.py')

            # Dynamically import the module
            if os.path.basename(module_path) != '__init__.py':
                module = importlib.import_module(module_name)
            else:
                continue

            # Import all classes from the module
            for attribute_name in dir(module):
                attribute = getattr(module, attribute_name)
                if isinstance(attribute, type):  # Only import class objects
                    # Use inspect to check if the class is defined in the current module
                    if inspect.getmodule(attribute).__file__ == module.__file__:
                        globals()[attribute_name] = attribute  # Add the class to the global namespace
                        # print(f'Imported class {attribute_name} from {module_name}')
