class VolumeDescriptor(object):
    name = None

    def __init__(self, source):
        pass

    def __repr__(self):
        return "<VolumeDescriptor name=%r>" % self.name


class BootVD(VolumeDescriptor):
    name = "boot"


class PrimaryVD(VolumeDescriptor):
    name = "primary"

    def __init__(self, source):
        super(PrimaryVD, self).__init__(source)

        _                                  = source.unpack_raw(1)     # unused
        self.system_identifier             = source.unpack_string(32)
        self.volume_identifier             = source.unpack_string(32)
        _                                  = source.unpack_raw(8)     # unused
        self.volume_space_size             = source.unpack_both('i')
        _                                  = source.unpack_raw(32)    # unused
        self.volume_set_size               = source.unpack_both('h')
        self.volume_seq_num                = source.unpack_both('h')
        self.logical_block_size            = source.unpack_both('h')
        self.path_table_size               = source.unpack_both('i')
        self.path_table_l_loc              = source.unpack('<i')
        self.path_table_opt_l_loc          = source.unpack('<i')
        self.path_table_m_loc              = source.unpack('>i')
        self.path_table_opt_m_loc          = source.unpack('>i')
        self.root_record                   = source.unpack_record()
        self.volume_set_identifier         = source.unpack_string(128)
        self.publisher_identifier          = source.unpack_string(128)
        self.data_preparer_identifier      = source.unpack_string(128)
        self.application_identifier        = source.unpack_string(128)
        self.copyright_file_identifier     = source.unpack_string(38)
        self.abstract_file_identifier      = source.unpack_string(36)
        self.bibliographic_file_identifier = source.unpack_string(37)
        self.volume_datetime_created       = source.unpack_vd_datetime()
        self.volume_datetime_modified      = source.unpack_vd_datetime()
        self.volume_datetime_expires       = source.unpack_vd_datetime()
        self.volume_datetime_effective     = source.unpack_vd_datetime()
        self.file_structure_version        = source.unpack('B')


class SupplementaryVD(VolumeDescriptor):
    name = "supplementary"


class PartitionVD(VolumeDescriptor):
    name = "partition"


class TerminatorVD(VolumeDescriptor):
    name = "terminator"