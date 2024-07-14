

import base64
from urllib.parse import urlparse, parse_qs


def get_parameter_by_name(url, name):
    """
    Extracts a query parameter from a URL.
    """
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    return query_params.get(name, [None])[0]  # Returns the first value of the parameter or None

def base64_decode(url):
    """
    Decodes a base64 encoded string.
    """
    try:
        encoded_str=get_parameter_by_name(url, 'url')
        base64_bytes = base64.b64decode(encoded_str)
        t=base64_bytes.decode('utf-8')
        print(t)
        return t  # Assumes the original text was UTF-8 encoded
    except Exception as e:
        print(f"Invalid base64 string: {e}")
        return None
