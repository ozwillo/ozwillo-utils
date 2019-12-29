from tinydb import TinyDB, Query
import os
import time

real_path = os.path.dirname(os.path.realpath(__file__))
path = real_path + '/db.json'

db = TinyDB(path)

tokens_table = db.table('tokens_table')

def clear_tokens_table():
    tokens_table.purge()

def get_valid_token():
    '''
    returns a valid token record from the database
    valid means it's going to expire in more than 20 minutes
    '''
    Token = Query()
    token_data = tokens_table.search(Token.expiry_date > (time.time() + 1200))
    return token_data

def store_token(token_data):
    clear_tokens_table()

    access_token = token_data.get('access_token', False)
    expires_in = token_data.get('expires_in', 0)
    expiry_date = time.time() + expires_in

    tokens_table.insert({
        'token_value' : access_token,
        'expiry_date' : expiry_date,
        'refresh_token' : token_data.get('refresh_token', False),
        'id_token' : token_data.get('id_token', False),
    })
