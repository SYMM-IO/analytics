class StringBuilder:
    def __init__(self):
        self._strings = []

    def append(self, value):
        self._strings.append(value)
        return self

    def append_line(self, value=""):
        self._strings.append(value + "\n")
        return self

    def clear(self):
        self._strings = []

    def length(self):
        return len(''.join(self._strings))

    def __str__(self):
        return ''.join(self._strings)
