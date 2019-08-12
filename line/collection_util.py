
class RestrictDict:
    """ A dict-like structure only allows modification
        with keys existed and same data type.

        is_valid() may be overrided to check data validity.
    """
    
    def __init__(self, init_data:dict):
        self.data = init_data

    def __getitem__(self, name):
        return self.data[name]

    def __setitem__(self, name, value):
        if name not in self.data:
            raise KeyError

        if not self.is_valid(name, value):
            raise ValueError

        self.data[name] = value

    def is_valid(self, name, value):
        #return isinstance(value, type(self.data[name]))
        return True

    def export(self):
        return self.data.copy()

    def update(self, data_dict, raise_error):
        for key, value in data_dict.items():
            try:
                self[key] = value
            except KeyError:
                if raise_error:
                    raise
                else:
                    pass

    def copy(self):
        return RestrictDict(self.data.copy())

    def items(self):
        return self.data.items()