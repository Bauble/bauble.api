
import os

default_date_format = "%m/%d/%Y"

def get(key, default=None):
    value = os.environ.get(key, default)
    if isinstance(value, str):
        if value.lower() == 'true':
            return True
        elif value.lower() == 'false':
            return False
    return value


def set(key, value):
    os.environ[key] = value
