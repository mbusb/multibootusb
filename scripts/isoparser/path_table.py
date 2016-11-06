import record


class PathTable(object):
    def __init__(self, source):
        self._source = source
        self.paths = {}

        paths_list = []

        while len(source) > 0:
            name_length = source.unpack('B')
            _           = source.unpack('B')
            location    = source.unpack('<I')
            parent_idx  = source.unpack('<H') - 1
            name        = source.unpack_string(name_length)
            _           = source.unpack_raw(name_length % 2)

            path = []
            if len(paths_list) > 0:
                path.extend(paths_list[parent_idx])
            if name != "\x00":
                path.append(name)

            paths_list.append(path)
            self.paths[tuple(path)] = location

    def record(self, *path):
        location = self.paths[path]
        self._source.seek(location)
        return self._source.unpack_record()