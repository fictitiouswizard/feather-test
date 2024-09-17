import importlib
import inspect
from feather_test.utils import to_snake_case
import logging

logger = logging.getLogger("feather_test")

def load_reporter(reporter_name_or_instance, **kwargs):
    """
    Load a reporter by name and initialize it with the given kwargs,
    or return the reporter instance if already configured.
    
    :param reporter_name_or_instance: Name of the reporter to load or an already configured reporter instance
    :param kwargs: Keyword arguments to pass to the reporter's constructor
    :return: Initialized reporter instance
    """
    # If reporter_name_or_instance is already a configured reporter, return it
    if not isinstance(reporter_name_or_instance, str):
        return reporter_name_or_instance

    reporter_name = reporter_name_or_instance
    try:
        # Try to load from feather_test.reporters first
        module = importlib.import_module('feather_test.reporters')
        reporter_class = getattr(module, reporter_name)
        return reporter_class(**kwargs)
    except (AttributeError, ImportError, TypeError):
        # If not found, try to import as a fully qualified name
        try:
            module_name, class_name = reporter_name.rsplit('.', 1)
            module = importlib.import_module(module_name)
            reporter_class = getattr(module, class_name)
            return reporter_class(**kwargs)
        except (ValueError, ImportError, AttributeError):
            # If still not found, try to import from any installed package
            try:
                snake_case_name = to_snake_case(reporter_name)
                module = importlib.import_module(f'feather_test_reporter_{snake_case_name}')
                reporter_class = getattr(module, reporter_name)
            except (ImportError, AttributeError):
                raise ValueError(f"Reporter '{reporter_name}' not found or invalid")

    
