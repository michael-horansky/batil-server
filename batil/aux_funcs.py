# Auxilary functions for batil source code

import hashlib

def hash_number(n, length=16, salt="bitkavsluckach"):
    # Convert number to string
    input_string = (str(n) + salt).encode('utf-8')

    # Compute SHA-256 hash
    h = hashlib.sha256(input_string).hexdigest()

    # Take first 'length' characters
    return(h[:length])
