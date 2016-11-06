class Record(object):
    def __init__(self, source, length):
        self._source = source
        self._content = None
        target = source.cursor + length

        _                  = source.unpack('B')       # TODO: extended attributes length
        self.location      = source.unpack_both('I')
        self.length        = source.unpack_both('I')
        self.datetime      = source.unpack_dir_datetime()
        flags              = source.unpack('B')
        self.is_hidden     = flags & 1
        self.is_directory  = flags & 2
        # TODO: other flags
        _                  = source.unpack('B')       # TODO: interleave unit size
        _                  = source.unpack('B')       # TODO: interleave gap size
        _                  = source.unpack_both('h')  # TODO: volume sequence
        name_length        = source.unpack('B')
        self.name          = source.unpack_string(name_length).split(';')[0]
        if self.name == "\x00":
            self.name = ""

        # TODO: extended attributes
        source.unpack_raw(target - source.cursor)

    def __repr__(self):
        return "<Record (%s) name=%r>" % (
            "directory" if self.is_directory else "file",
            self.name)

    @property
    def children_unsafe(self):
        """
        Assuming this is a directory record, this generator yields a record for each child. Use
        with caution: at each iteration, the generator assumes that the source cursor has not moved
        since the previous child was yielded. For safer behaviour, use :func:`children`.
        """
        assert self.is_directory
        self._source.seek(self.location, self.length)
        _ = self._source.unpack_record()  # current directory
        _ = self._source.unpack_record()  # parent directory
        while len(self._source) > 0:
            record = self._source.unpack_record()

            if record is None:
                self._source.unpack_boundary()
                continue

            yield record

    @property
    def children(self):
        """
        Assuming this is a directory record, this property contains records for its children.
        """
        return list(self.children_unsafe)

    @property
    def content(self):
        """
        Assuming this is a file record, this property contains the file's contents
        """
        assert not self.is_directory
        if self._content is None:
            self._source.seek(self.location, self.length, is_content=True)
            self._content = self._source.unpack_all()
        return self._content



