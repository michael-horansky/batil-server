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


# --------------------------------- CONSTANTS ---------------------------------

PFP_EXTENSIONS = [".png", ".jpg", ".jpeg", ".webp", ".gif"]
