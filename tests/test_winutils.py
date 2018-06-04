import pytest
import os
import tempfile

from datetime import datetime, timedelta
import windows.utils
import windows.generated_def as gdef
from tests.pfwtest import *

pytestmark = pytest.mark.usefixtures('check_for_gc_garbage')


ntqueryinformationfile_info_structs = {
    gdef.FileAccessInformation: gdef.FILE_ACCESS_INFORMATION,
    gdef.FileAlignmentInformation: gdef.FILE_ALIGNMENT_INFORMATION,
    gdef.FileAllInformation: gdef.FILE_ALL_INFORMATION,
    gdef.FileAttributeTagInformation: gdef.FILE_ATTRIBUTE_TAG_INFORMATION,
    gdef.FileBasicInformation: gdef.FILE_BASIC_INFORMATION,
    gdef.FileEaInformation: gdef.FILE_EA_INFORMATION ,
    gdef.FileInternalInformation: gdef.FILE_INTERNAL_INFORMATION,
    gdef.FileIoPriorityHintInformation: gdef.FILE_IO_PRIORITY_HINT_INFORMATION,
    gdef.FileModeInformation: gdef.FILE_MODE_INFORMATION,
    gdef.FileNetworkOpenInformation: gdef.FILE_NETWORK_OPEN_INFORMATION,
    gdef.FileNameInformation: gdef.FILE_NAME_INFORMATION,
    gdef.FilePositionInformation: gdef.FILE_POSITION_INFORMATION,
    gdef.FileStandardInformation: gdef.FILE_STANDARD_INFORMATION,
    gdef.FileIsRemoteDeviceInformation: gdef.FILE_IS_REMOTE_DEVICE_INFORMATION,
}

def test_query_file_information():
    f = open(r"C:\windows\system32\ntdll.dll")
    handle = windows.utils.get_handle_from_file(f)
    for info_class, info_struct in ntqueryinformationfile_info_structs.items():
        res = windows.utils.query_file_information(handle, info_class) # Fail should raise
        resf = windows.utils.query_file_information(f, info_class) # Try with the file directly
        # Check return type
        assert isinstance(res, info_struct)
        assert isinstance(resf, info_struct)


ntqueryvolumeinformationfile_info_structs = {
    gdef.FileFsAttributeInformation: gdef.FILE_FS_ATTRIBUTE_INFORMATION,
    gdef.FileFsControlInformation: gdef.FILE_FS_CONTROL_INFORMATION,
    gdef.FileFsDeviceInformation: gdef.FILE_FS_DEVICE_INFORMATION,
    # gdef.FileFsDriverPathInformation: gdef.FILE_FS_DRIVER_PATH_INFORMATION, # Not handled for now
    gdef.FileFsFullSizeInformation: gdef.FILE_FS_FULL_SIZE_INFORMATION,
    gdef.FileFsObjectIdInformation: gdef.FILE_FS_OBJECTID_INFORMATION,
    gdef.FileFsSizeInformation: gdef.FILE_FS_SIZE_INFORMATION,
    gdef.FileFsVolumeInformation: gdef.FILE_FS_VOLUME_INFORMATION,
    gdef.FileFsSectorSizeInformation: gdef.FILE_FS_SECTOR_SIZE_INFORMATION,
}

def test_query_volume_information():
    f = open(r"C:\windows\system32\ntdll.dll")
    handle = windows.utils.get_handle_from_file(f)

    for info_class, info_struct in ntqueryvolumeinformationfile_info_structs.items():
        res = windows.utils.query_volume_information(handle, info_class) # Fail should raise
        resf = windows.utils.query_volume_information(f, info_class) # Try with the file directly
        # Check return type
        assert isinstance(res, info_struct)
        assert isinstance(resf, info_struct)

def date_equals(d1, d2, acceptable_delta=timedelta(microseconds=1)):
    if d2 > d1:
        delta = d2 - d1
    else:
        delta = d1 - d2
    return delta <= acceptable_delta

def test_datetime_from_filetime():
    FILENAME = "C:\\windows\\system32\\ntdll.dll"
    f = open(FILENAME)

    datetime_from_filetime = windows.utils.datetime_from_filetime

    # Compare to os.stat
    stats = os.stat(FILENAME)
    utc_satime = datetime.utcfromtimestamp(stats.st_atime)
    utc_smtime = datetime.utcfromtimestamp(stats.st_mtime)
    utc_sctime = datetime.utcfromtimestamp(stats.st_ctime)

    # Compare to NtQueryInformationFile
    fileinfo = windows.utils.query_file_information(f, gdef.FileBasicInformation)

    utc_watime = datetime_from_filetime(fileinfo.LastAccessTime)
    utc_wmtime = datetime_from_filetime(fileinfo.LastWriteTime)
    utc_wctime = datetime_from_filetime(fileinfo.CreationTime)

    assert date_equals(utc_satime, utc_watime)
    assert date_equals(utc_smtime, utc_wmtime)
    assert date_equals(utc_sctime, utc_wctime)

    # Test rounding
    ## Round-down


    assert date_equals(datetime_from_filetime(131492395680727300), datetime(2017, 9, 7, 6, 32, 48, 72730))
    assert date_equals(datetime_from_filetime(131492395680727304), datetime(2017, 9, 7, 6, 32, 48, 72730))

    assert date_equals(datetime_from_filetime(131492395680727305), datetime(2017, 9, 7, 6, 32, 48, 72731))
    assert date_equals(datetime_from_filetime(131492395680727309), datetime(2017, 9, 7, 6, 32, 48, 72731))

    assert date_equals(datetime.utcfromtimestamp(1504764215.5896280), datetime_from_filetime(131492378155896280))
    assert date_equals(datetime.utcfromtimestamp(1504764215.5896284), datetime_from_filetime(131492378155896284))
    assert date_equals(datetime.utcfromtimestamp(1504764215.5896285), datetime_from_filetime(131492378155896285))
    assert date_equals(datetime.utcfromtimestamp(1504764215.5896289), datetime_from_filetime(131492378155896289))



def test_unix_timestamp_from_filetime():
    # Check date vs timestamps to be sure
    assert datetime.utcfromtimestamp(1504765968.072730) == datetime(2017, 9, 7, 6, 32, 48, 72730)
    assert windows.utils.unix_timestamp_from_filetime(131492395680727300) == 1504765968.072730
    assert windows.utils.unix_timestamp_from_filetime(131492395680727304) == 1504765968.072730

    assert datetime.utcfromtimestamp(1504765968.072731) == datetime(2017, 9, 7, 6, 32, 48, 72731)
    assert windows.utils.unix_timestamp_from_filetime(131492395680727309) == 1504765968.072731
    assert windows.utils.unix_timestamp_from_filetime(131492395680727305) == 1504765968.072731

@pytest.mark.parametrize("prefix,prefixtype", [
    ("long_ascii_prefix", str),
    (u'\u4e2d\u56fd\u94f6\u884c\u7f51\u94f6\u52a9\u624b', unicode),
    ])
def test_long_short_path_str_unicode(prefix, prefixtype):
    """Test that get_short_path/get_long_path works with str/unicode path and preserve path type"""
    assert isinstance(prefix, prefixtype)
    with tempfile.NamedTemporaryFile(prefix=prefix) as f:
        basename = f.name.lower()
        assert isinstance(basename, prefixtype)
        short_name = windows.utils.get_short_path(basename).lower()
        assert isinstance(short_name, prefixtype)
        assert short_name != basename
        full_name = windows.utils.get_long_path(short_name).lower()
        assert isinstance(full_name, prefixtype)
        assert full_name == basename