import os
from parserix import parse as _parse
import pandas as _pd


def create_loaddata(img_list):
    """
    create a dataframe suitable for cellprofilers LoadData module
    """
    df_long = create_long_loaddata(img_list)
    return cast_dataframe(df_long)


def create_long_loaddata(img_list):
    """
    create a dataframe of image paths with metadata columns
    """
    just_filenames = [_parse.img_filename(i) for i in img_list]
    df_img = _pd.DataFrame({
        "URL" : just_filenames,
        "path" : [_parse.path(i) for i in img_list],
        "Metadata_platename" : [_parse.plate_name(i) for i in img_list],
        "Metadata_well" : [_parse.img_well(i) for i in just_filenames],
        "Metadata_site" : [_parse.img_site(i) for i in just_filenames],
        "Metadata_channel" : [_parse.img_channel(i) for i in just_filenames],
        "Metadata_platenum" : [_parse.plate_num(i) for i in img_list]
    })
    return df_img


def cast_dataframe(dataframe):
    """reshape a create_loaddata dataframe from long to wide format"""
    n_channels = len(set(dataframe.Metadata_channel))
    wide_df = dataframe.pivot_table(
        index=["Metadata_site", "Metadata_well", "Metadata_platenum",
               "Metadata_platename", "path"],
        columns="Metadata_channel",
        values="URL",
        aggfunc="first").reset_index()
    # rename FileName columns from 1, 2... to FileName_W1, FileName_W2 ...
    columns = dict()
    for i in range(1, n_channels+1):
        columns[i] = "FileName_W" + str(i)
    wide_df.rename(columns=columns, inplace=True)
    # duplicate PathName for each channel
    for i in range(1, n_channels+1):
        wide_df["PathName_W" + str(i)] = wide_df.path
    wide_df.drop(["path"], axis=1, inplace=True)
    return wide_df


def update_file_paths(dataframe, cols, original, replacement):
    """
    change file paths (could just use sed)

    Parameters:
    ------------
    dataframe : pandas dataframe
    cols : list
        columns in which to replace the paths.
    original : string
        original text to be replaced
    replacement : string
        string with with original is replaced by
    """
    df_sub = dataframe[cols]
    return df_sub.applymap(lambda x: x.replace(original, replacement))


def rsync_string(filelist, source, destination):
    """
    Create rsync string pointing to a file-list and a destination
    If the file-list is truncated, then source has to be the location of the
    file-list so it forms a complete path.
    Destination will include the entire path located in the file-list, therefore
    truncation is recommended,
    Desination can also begin with a directory that has not yet been created,
    the directory will be created by the rsync command.
    """
    return "rsync --files-from={} {} {}".format(filelist, source, destination)


def rm_string(directory):
    """
    create string to remove job's data after successful run
    NOTE DANGER ZONE!!!
    """
    return "rm -rf {}".format(directory)


def cp_command(pipeline, load_data, output_location):
    """create cellprofiler command"""
    cmnd = "cellprofiler -r -c -p {} --data-file={} -o {}".format(
        pipeline, load_data, output_location)
    return cmnd
