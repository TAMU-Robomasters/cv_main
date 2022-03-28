import gdown
from toolbox.globals import path_to
import file_system_py as FileSystem

def download_from_drive(*, file_id, to, force=False, quiet=False):
    """
    # DJI ROCO.zip file from google drive
    # https://drive.google.com/file/d/1DVoutipvYzRm77B4Mmk2bp7fRqLW8p1E
    download_from_drive(
        file_id="1DVoutipvYzRm77B4Mmk2bp7fRqLW8p1E",
        force=False,
    )
    """
    FileSystem.ensure_is_folder(FileSystem.parent_folder(path_to.datasets))
    if force:
        FileSystem.remove(path_to.datasets)
    try:
        gdown.cached_download(f"https://drive.google.com/uc?id={file_id}", path_to.datasets, postprocess=gdown.extractall, quiet=quiet)
    except Exception as error:
        # cleanup
        FileSystem.remove(path_to.datasets)
        raise error


