def decode_string(string):
    _string = string
    if isinstance(_string, bytes):
        _string = _string.decode()
    return _string


def str_to_bool(value):
    if isinstance(value, str):
        v = value.strip().lower()
        if v == "true":
            return True
        elif v == "false":
            return False
    return value
