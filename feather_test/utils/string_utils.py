import re
import logging

logger = logging.getLogger("feather_test")


def to_snake_case(name):
    """
    Convert a string from CamelCase or PascalCase to snake_case.

    This function takes a string in CamelCase or PascalCase format and converts it
    to snake_case. It handles consecutive uppercase letters correctly by treating
    them as a single word (except for the last one if followed by a lowercase letter).

    Examples:
        >>> to_snake_case("HelloWorld")
        'hello_world'
        >>> to_snake_case("HTTPRequest")
        'http_request'
        >>> to_snake_case("APIClientConfig")
        'api_client_config'

    :param name: The string to convert to snake_case.
    :type name: str
    :return: The input string converted to snake_case.
    :rtype: str
    """
    # First, handle the case where we have consecutive uppercase letters
    # This regex looks for uppercase letters that are followed by lowercase letters
    # or are at the end of the string, and adds an underscore before them
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    
    # Then, handle the remaining uppercase letters
    # This regex looks for lowercase letters or numbers followed by uppercase letters
    # and adds an underscore between them
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

