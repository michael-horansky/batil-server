# Auxilary functions for batil source code

import hashlib
from werkzeug.utils import secure_filename
import os

from batil.engine.game_logic.command_properties import *

# -----------------------------------------------------------------------------
# --------------------------------- FUNCTIONS ---------------------------------
# -----------------------------------------------------------------------------

# ----------------------------- Text manipulation -----------------------------

# Hashes

def hash_number(n, length=16, salt="bitkavsluckach"):
    # Convert number to string
    input_string = (str(n) + salt).encode('utf-8')

    # Compute SHA-256 hash
    h = hashlib.sha256(input_string).hexdigest()

    # Take first 'length' characters
    return(h[:length])

# Compression

def compress_commands(list_of_commands):
    # list_of_commands is a list of dicts, each having a fixed number of keywords
    list_of_encoded_commands = []
    for cmd in list_of_commands:
        ordered_list_of_args = [str(allowed_command_string_vals["type"].index(cmd["type"]))] # first val is always command type
        for kw in command_keywords[cmd["type"]]:
            if kw not in cmd.keys():
                ordered_list_of_args.append("")
            elif cmd[kw] == None or cmd[kw] == "":
                ordered_list_of_args.append("")
            else:
                if kw in integer_command_keywords:
                    ordered_list_of_args.append(str(cmd[kw]))
                else:
                    # string command keyword, can be compressed further
                    ordered_list_of_args.append(str(allowed_command_string_vals[kw].index(cmd[kw])))
        # These command vals can contain alphanumeric characters or underscores _, so we will use two separators: + between command vals and ; between commands.
        list_of_encoded_commands.append("+".join(ordered_list_of_args))
    return(";".join(list_of_encoded_commands))

def decompress_commands(encoded_string):
    # undoes compress_commands()
    if encoded_string == "":
        return([])
    list_of_commands = []
    list_of_encoded_cmds = encoded_string.split(";")
    for encoded_cmd in list_of_encoded_cmds:
        cmd_dict = {}
        ordered_list_of_encoded_vals = encoded_cmd.split("+")

        cmd_type = allowed_command_string_vals["type"][int(ordered_list_of_encoded_vals[0])]

        cmd_dict["type"] = cmd_type

        for i in range(len(command_keywords[cmd_type])):
            kw = command_keywords[cmd_type][i]
            val = ordered_list_of_encoded_vals[i+1]
            if val == "":
                cmd_dict[kw] = None
            else:
                if kw in integer_command_keywords:
                    cmd_dict[kw] = int(val)
                else:
                    cmd_dict[kw] = allowed_command_string_vals[kw][int(val)]
        list_of_commands.append(cmd_dict)
    return(list_of_commands)

# Conversion

def seconds_to_str(seconds, val_on_none = "", val_on_neg = ""):
    if seconds is None:
        return(val_on_none)

    if seconds < 0:
        return(val_on_neg)

    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)

    return(f"{hours}:{minutes:02}:{secs:02}")

# ----------------------------- File manipulation -----------------------------

def get_file_extension(file_storage):
    # file_storage is the uploaded file from request.files["file"]
    filename = secure_filename(file_storage.filename)  # strips weird chars
    _, ext = os.path.splitext(filename)
    if ext.lower() in PFP_EXTENSIONS:
        return(PFP_EXTENSIONS.index(ext.lower()))
    return(None)

# ----------------------------- Type manipulation -----------------------------

def make_dict(imm_dict, cols):
    res = {}
    for col in cols:
        res[col] = imm_dict[col]
    return(res)

def make_tuple(my_dict, cols):
    return(tuple(my_dict[x] for x in cols))

# -----------------------------------------------------------------------------
# --------------------------------- CONSTANTS ---------------------------------
# -----------------------------------------------------------------------------

PFP_EXTENSIONS = ["_DEFAULT_USER_pfp", ".png", ".jpg", ".jpeg", ".webp", ".gif"]
