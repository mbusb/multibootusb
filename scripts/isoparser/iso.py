class ISO(object):
    def __init__(self, source):
        self._source = source

        # Unpack volume descriptors
        self.volume_descriptors = {}
        sector = 16
        while True:
            self._source.seek(sector)
            sector += 1

            vd = self._source.unpack_volume_descriptor()
            self.volume_descriptors[vd.name] = vd

            if vd.name == "terminator":
                break

        # Unpack the path table
        self._source.seek(
            self.volume_descriptors['primary'].path_table_l_loc,
            self.volume_descriptors['primary'].path_table_size)
        self.path_table = self._source.unpack_path_table()

        # Save a reference to the root record
        self.root = self.volume_descriptors['primary'].root_record

    def record(self, *path):
        """
        Retrieves a record for the given path.
        """
        path = [part.upper() for part in path]
        record = None
        pivot = len(path)

        # Resolve as much of the path as possible via the path table
        while pivot > 0:
            try:
                record = self.path_table.record(*path[:pivot])
            except KeyError:
                pivot -= 1
            else:
                break

        if record is None:
            record = self.root

        # Resolve the remainder of the path by walking record children
        for part in path[pivot:]:
            for child in record.children_unsafe:
                if child.name == part:
                    record = child
                    break
            else:
                raise KeyError(part)

        return record