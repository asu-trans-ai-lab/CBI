# -*- coding:utf-8 -*-
##############################################################
# Created Date: Thursday, December 1st 2022
# Contact Info: luoxiangyong01@gmail.com
# Author/Copyright: Mr. Xiangyong Luo
##############################################################

import os
import datetime
from pathlib import Path
from typing import Union  # Python version <= 3.9


# A decorator to measure the time of a function
def func_running_time(func):
    def inner(*args, **kwargs):
        print(f'INFO Begin to run function: {func.__name__} …')
        time_start = datetime.datetime.now()
        res = func(*args, **kwargs)
        time_diff = datetime.datetime.now() - time_start
        print(
            f'INFO Finished running function: {func.__name__}, total: {time_diff.seconds}s')
        print()
        return res
    return inner


# convert OS path to standard linux path
def path2linux(path: Union[str, Path]) -> str:
    """Convert a path to a linux path, linux path can run in windows, linux and mac"""
    try:
        return path.replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")


# get files from a folder by file type
def get_file_from_folder_by_type(dir_name: str, file_type: str = "txt", isTraverseSubdirectory: bool = False) -> list:
    if isTraverseSubdirectory:
        files_list = []
        for root, dirs, files in os.walk(dir_name):
            files_list.extend([os.path.join(root, file) for file in files])
        return [path2linux(file) for file in files_list if file.split(".")[-1] == file_type]

    # files in the first layer of the folder
    return [path2linux(os.path.join(dir_name, file)) for file in os.listdir(dir_name) if file.split(".")[-1] == file_type]


# check if the required files exist in the folder by giving required files list and files in the folder
def check_required_files_exist(required_files: list, dir_files: list) -> bool:
    # format the required file name to standard linux path
    required_files = [path2linux(os.path.abspath(filename))
                      for filename in required_files]

    required_files_short = [filename.split(
        "/")[-1] for filename in required_files]
    dir_files_short = [filename.split("/")[-1] for filename in dir_files]

    # mask have the same length as required_files
    mask = [file in dir_files_short for file in required_files_short]
    if all(mask):
        return True

    print(f"Error: Required files are not satisfied, \
          missing files are: {[required_files_short[i] for i in range(len(required_files_short)) if not mask[i]]}")

    return False


# check if the required columns exist in the loaded data columns
def check_required_column_names_exist(required_columns: list, loaded_columns: list) -> bool:
    if set(required_columns).issubset(set(loaded_columns)):
        return True

    print(f"Error: Required columns are not satisfied, missing columns are: {set(required_columns) - set(loaded_columns)}")
    return False


# check file name exist in path, if exist, then create new file name with _1, _1_1, ...
def validate_filename(path_filename: str, ) -> str:
    """if the file name exist in path,then create new file name with _1, _1_1, ..."""
    filename_abspath = path2linux(os.path.abspath(path_filename))

    file_suffix = filename_abspath.split(".")[-1]
    file_without_suffix = filename_abspath[:-len(file_suffix) - 1]

    if os.path.exists(filename_abspath):
        filename_update = f"{file_without_suffix}_1.{file_suffix}"
        return validate_filename(filename_update)
    return filename_abspath


# generate absolute path for saving file
def generate_absolute_path(file_name: str = "p4g_fig.png", folder_name: str = "cbi_results"):
    # create folder if not exist
    if not os.path.isdir(os.path.join(Path(__file__).parent, folder_name)):
        os.mkdir(os.path.join(Path(__file__).parent, folder_name))
    return path2linux(os.path.join(Path(__file__).parent, folder_name, file_name))
