import hashlib
from datetime import datetime 
import jwt

from mongoDB import token as token_entity

SECRET = "7DbIZSLoIlGgSDEfBGs1"
ALGORITHM = "HS256"

def get_token_value(user_id):
    value = user_id + str(datetime.now().timestamp())
    # encoding then sending to SHA512()
    result = hashlib.sha512(value.encode())
    result_hexadecimal = result.hexdigest()
    return result_hexadecimal

def encode_token_value(token_value):
    encoded_jwt = jwt.encode({"value": token_value}, SECRET, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token):
    try:
        decoded_token = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
        return decoded_token
    except Exception as e:
        print("An exception occurred ::", e)
    
def store_token_value(token_value):
    try:
        token_entity.insert_one(
            {
                "value": token_value
            }
        )
        return True
    except Exception as e:
        print("An exception occurred ::", e)
        return False


def token_value_is_valid(token_value):
    token_found = token_entity.find_one({'value': token_value})
    if token_found is None:
        return False
    else:
        return True 


def delete_token_value(token_value):
    result = token_entity.delete_one({'value': token_value})
    return result
