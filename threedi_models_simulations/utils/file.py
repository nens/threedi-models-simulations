import hashlib
import os
from uuid import uuid4
from zipfile import ZIP_DEFLATED, ZipFile


def is_writable(working_dir: str) -> bool:
    """Try to write and remove an empty text file into given location."""
    try:
        test_filename = f"{uuid4()}.txt"
        test_file_path = os.path.join(working_dir, test_filename)
        with open(test_file_path, "w") as test_file:
            test_file.write("")
        os.remove(test_file_path)
    except (PermissionError, OSError):
        return False
    else:
        return True


def unzip_archive(zip_filepath, location=None):
    """Unzip archive content."""
    if not location:
        location = os.path.dirname(zip_filepath)
    with ZipFile(zip_filepath, "r") as zf:
        content_list = zf.namelist()
        zf.extractall(location)
        return content_list


def zip_into_archive(file_path, compression=ZIP_DEFLATED):
    """Zip file."""
    zip_filename = os.path.basename(file_path)
    zip_filepath = file_path.rsplit(".", 1)[0] + ".zip"
    with ZipFile(zip_filepath, "w", compression=compression) as zf:
        zf.write(file_path, arcname=zip_filename)
    return zip_filepath


def is_file_checksum_equal(file_path, etag):
    """Checking if etag (MD5 checksum) matches checksum calculated for a given file."""
    with open(file_path, "rb") as file_to_check:
        data = file_to_check.read()
        md5_returned = hashlib.md5(data).hexdigest()
        return etag == md5_returned


def translate_illegal_chars(
    text, illegal_characters=r'\/:*?"<>|', replacement_character="-"
):
    """Remove illegal characters from the text."""
    sanitized_text = "".join(
        char if char not in illegal_characters else replacement_character
        for char in text
    )
    return sanitized_text
