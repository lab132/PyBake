

def sizeof(value):
    t = type(value)
    if t is bool:
        return 1
    if t is int:
        return 4
    if t is bytes:
        return len(t)
    if t is str:
        return len(t.encode("UTF-8"))
    if t.layout is not None: # Duck typing! If it has a `size` member we use that to determine the size
        return int(t.layout.size) # Raise a TypeError if `t.size` is not an int

    raise TypeError("Unknown type. Lists and dictionaries are not supported by this function.")
