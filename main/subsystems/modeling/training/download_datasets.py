import gdown
from toolbox.globals import path_to
from toolbox.google_drive_downloader import download_from_drive
import file_system_py as FileSystem


# DJI ROCO.zip file from google drive
# https://drive.google.com/file/d/1DVoutipvYzRm77B4Mmk2bp7fRqLW8p1E
download_from_drive(
    file_id="1DVoutipvYzRm77B4Mmk2bp7fRqLW8p1E",
    to=path_to.datasets+"/dji_roco.zip",
)