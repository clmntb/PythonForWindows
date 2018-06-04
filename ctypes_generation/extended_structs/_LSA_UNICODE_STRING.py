INITIAL_LSA_UNICODE_STRING = _LSA_UNICODE_STRING

class _LSA_UNICODE_STRING(INITIAL_LSA_UNICODE_STRING):
    @property
    def str(self):
        """The python string of the LSA_UNICODE_STRING object

        :type: :class:`unicode`
        """
        if not self.Length:
            return ""
        if getattr(self, "_target", None) is not None: #remote ctypes :D -> TRICKS OF THE YEAR
            raw_data = self._target.read_memory(self.Buffer, self.Length)
            return raw_data.decode("utf16")
        size = int(self.Length / 2)
        return (ctypes.c_wchar * size).from_address(self.Buffer)[:]

    @classmethod
    def from_string(cls, s):
        utf16_len = len(s) * 2
        return cls(utf16_len, utf16_len, ctypes.cast(PWSTR(s), PVOID))

    def __repr__(self):
        return """<{0} "{1}" at {2}>""".format(type(self).__name__, self.str, hex(id(self)))