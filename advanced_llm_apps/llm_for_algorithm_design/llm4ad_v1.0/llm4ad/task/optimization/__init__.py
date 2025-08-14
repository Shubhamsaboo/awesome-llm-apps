# import os
# import importlib
#
#
# def import_all_evaluation_classes(root_directory):
#     """
#     Recursively imports all classes from 'evaluation.py' files found in the directory structure.
#
#     Args:
#         root_directory (str): The root directory to start the search for 'evaluation.py' files.
#     """
#     for dirpath, _, filenames in os.walk(root_directory):
#         # Check if 'evaluation.py' exists in the current directory
#         if 'evaluation.py' in filenames:
#             # Build the module path relative to the root directory
#             module_name = '.'.join(os.path.relpath(dirpath, root_directory).split(os.sep)) + '.evaluation'
#
#             # Dynamically import the 'evaluation.py' module
#             module = importlib.import_module(module_name)
#
#             # Iterate over the module's attributes and check if they are classes
#             for attribute_name in dir(module):
#                 attribute = getattr(module, attribute_name)
#                 if isinstance(attribute, type):  # Only import class objects
#                     globals()[attribute_name] = attribute
#                     print(f"Imported class {attribute_name} from {module_name}")
#
#
# # Example usage, assuming 'problem' is the root directory:
# import_all_evaluation_classes('problem')
