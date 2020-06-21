#!/usr/bin/python2.7
#-*- coding:utf-8 -*-

import requests
import json
import re

import sys
import pprint
pp = pprint.PrettyPrinter(indent=2)

import argparse
import logging
_log = logging.getLogger(__name__)

import time

import db

# kernel adresses
ozwillo_base_url = 'https://accounts.ozwillo-preprod.eu'
auth_url = ozwillo_base_url + '/a/auth'
login_url = ozwillo_base_url + '/a/login'
token_url = ozwillo_base_url + '/a/token'

# user credentials for ozwillo
username = 'your.email@somewhere.com'
password = 'your.password'

# app credentials and settings
client_id = "your.client.id"
client_secret = "your.client.secret.generated.at.provisioning"
scope = ["openid", "offline_access", "datacore", "profile", "email"]
# it needs to be valid otherwise the kernel will deny the request
redirect_uri = "https://your.app.domain.name/registered.callback.url"


def get_cookied_session():
    """
    login to ozwillo with our username and password
    returns a new requests session that is logged in to ozwillo
    """
    _log.debug("getting cookied session...")

    s = requests.Session()
    payload = {
        'u': username,
        'pwd': password,
        'continue': ozwillo_base_url,
    }

    headers = {'referer': login_url}

    r = s.post(login_url, data=payload, headers=headers)
    return s

def get_auth_page(s):
    ''' give our client_id to the auth_page '''
    _log.debug("getting auth page of oauth ...")

    payload = {
        'response_type': 'code',
        'client_id': client_id,
        'scope': scope,
        'redirect_uri': redirect_uri,
    }

    r = s.post(auth_url, data=payload, allow_redirects=False)

def get_code(s):
    ''' get the code '''
    _log.debug("giving approval of our user to our application... (to get the code)")
    payload = {
            'response_type' : 'code',
            'client_id' : client_id,
            'scope' : scope,
            'redirect_uri' : redirect_uri,
            }

    headers = {'referer': auth_url}

    r = s.post(auth_url+"/approve", data=payload, headers=headers, allow_redirects=False)
    location = r.headers['Location']
    code = ""

    try :
        code = re.search("code=[a-zA-Z0-9_-]*", location).group(0)
        code = code.split('=')[1].strip(' ')
        _log.debug("code is :")
        _log.debug(code)
    except AttributeError:
        _log.error("Code not found in location header of response")
        code = ''

    return code

class GetTokenRequestFailed(Exception):
    pass

def _get_token(s, code):
    ''' now that we have to code, we can get the token '''
    _log.debug("getting the token...")
    payload = {
            'grant_type' : 'authorization_code',
            'redirect_uri': redirect_uri,
            'code' : code,
            }

    headers = {'referer': redirect_uri}

    r = s.post(token_url, data=payload, headers=headers, auth=(client_id, client_secret))
    access_token = None

    if not r.ok :
        raise GetTokenRequestFailed(r);

    _log.debug("token full response : {}".format(json.loads(r.content)))

    access_token = json.loads(r.content)

    return access_token


def get_userinfo(access_token):
    ''' request our userinfo to Ozwillo '''
    _log.debug("getting the userinfo...")

    s = requests.Session()
    headers = {'Authorization' : 'Bearer '+access_token }
    userinfo = s.post(ozwillo_base_url+'/a/userinfo', headers=headers)

    return userinfo


def get_stored_valid_token():

    # check if we don't already have a valid token for ozwillo

    token_data = db.get_valid_token()

    valid_token = None
    if token_data:
        try:
            valid_token = token_data[0].get('token_value', False)
        except IndexError:
            return False;

    if valid_token:
        #_log.info("We had a valid access_token in store, using it...")
        #_log.info(access_token)
        return valid_token

    #if not access_token :
        #_log.info('No valid ozwillo token in store, re-authing to Ozwillo')
        # ozwillo auth
    return False


def login():
    """
    returns the access token and a "cookied" requests Session
    """

    stored = get_stored_valid_token()

    if stored:
        _log.info('Stored access token still valid, returning it')
        s = get_cookied_session()
        return stored, s

    _log.info('No valid ozwillo access token in store, re-authing to Ozwillo')

    access_token, s = get_token_via_auth()

    if not access_token:
        _log.critical('Could not retrieve token through authentication process')
        return False

    return access_token, s


def get_token_via_auth():
    """
    auths to ozwillo, returns a new valid token and cookied session
    """

    s = get_cookied_session()
    get_auth_page(s)
    code = get_code(s)

    token_data = None
    try:
        token_data = _get_token(s, code)
    except GetTokenRequestFailed as e:
        _log.critical('Request to get the Access Token failed')
        r = e.args[0]
        _log.debug("REQ URL : {}".format(r.request.url))
        _log.debug("REQ HEADERS : {}".format(pprint.pformat(r.request.headers)))
        _log.debug("REQ BODY : {}".format(pprint.pformat(r.request.body)))
        _log.debug("REQ RESULT : {} , reason : {}".format(r, r.reason))
        return False

    # We've gotten a valid token now, store it
    access_token = token_data.get('access_token', False)

    db.store_token(token_data)

    return access_token, s


if __name__ == "__main__":

    # parse args
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-d', '--debug',
        help="Print lots of debugging statements",
        action="store_const", dest="loglevel", const=logging.DEBUG,
        default=logging.DEBUG,
    )

    args = parser.parse_args()

    # logger stuff
    COLOR_SEQ = "\033[1;%dm" % 33
    RESET_SEQ = "\033[0m"

    _log.setLevel(args.loglevel)

    ch = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(COLOR_SEQ+'%(name)s %(asctime)s %(levelname)s :'+RESET_SEQ+' %(message)s')
    ch.setFormatter(formatter)

    _log.addHandler(ch)

    access_token, s = login()

    _log.debug('access_token :')
    _log.debug(access_token)

    userinfo = get_userinfo(access_token)
    _log.debug("userinfo response : %s", userinfo)
    _log.debug(userinfo.content)
