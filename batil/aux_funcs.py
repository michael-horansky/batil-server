# Auxilary functions for batil source code

import hashlib
from werkzeug.utils import secure_filename
import os

def hash_number(n, length=16, salt="bitkavsluckach"):
    # Convert number to string
    input_string = (str(n) + salt).encode('utf-8')

    # Compute SHA-256 hash
    h = hashlib.sha256(input_string).hexdigest()

    # Take first 'length' characters
    return(h[:length])

def get_file_extension(file_storage):
    # file_storage is the uploaded file from request.files["file"]
    filename = secure_filename(file_storage.filename)  # strips weird chars
    _, ext = os.path.splitext(filename)
    if ext.lower() in PFP_EXTENSIONS:
        return(PFP_EXTENSIONS.index(ext.lower()))
    return(None)

def seconds_to_str(seconds, val_on_none = "", val_on_neg = ""):
    if seconds is None:
        return(val_on_none)

    if seconds < 0:
        return(val_on_neg)

    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)

    return(f"{hours}:{minutes:02}:{secs:02}")

def make_dict(imm_dict, cols):
    res = {}
    for col in cols:
        res[col] = imm_dict[col]
    return(res)

def make_tuple(my_dict, cols):
    return(tuple(my_dict[x] for x in cols))


# --------------------------------- CONSTANTS ---------------------------------

PFP_EXTENSIONS = ["_DEFAULT_USER_pfp", ".png", ".jpg", ".jpeg", ".webp", ".gif"]
