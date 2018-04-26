# coding: utf-8

import numpy as np
import requests, sys, json, datetime
from requests.auth import HTTPBasicAuth

# GET positions_log and destinations_log from the server
def generateLogs(urlpos, urldest, auth):

    # retrieve and generate destinations log
    data = getLog(urldest, auth)
    destinations_log = []
    for d_user in data['destinations']:
        destinations = []
        for d in d_user['destinations']:
            ts = datetime.datetime.fromtimestamp(d['last_update']).isoformat()
            point = {'lat': d['point']['lat'], 'lon': d['point']['lon']}
            type = u''.join(d['type']).encode('utf-8').strip()
            destinations.append({'last_update': ts, 'point': point, 'type': type})
        destinations_log.append({'_id': d_user['_id'], 'user_id': d_user['user_id'], 'destinations': destinations})
    destinations_log = {'destinations': destinations_log}

    # retrieve and generate positions log
    data = getLog(urlpos, auth)
    positions_log = []
    for p_user in data['positions']:
        positions = []
        for p in p_user['items']:
            ts = datetime.datetime.fromtimestamp(p['timestamp']).isoformat()
            point = {'lat': p['point']['lat'], 'lon': p['point']['lon']}
            positions.append({'timestamp': ts, 'point': point})
        positions_log.append({'user_id': p_user['user_id'], 'positions': positions})
    positions_log = {'positions': positions_log}

    print positions_log
    print destinations_log

    return positions_log, destinations_log

# GET data from JSON files through HTTP
def getLog(url, auth):

    print("Attempting to get logs from "+str(url))
    try:
        r = requests.get(url, auth=HTTPBasicAuth(auth['username'], auth['password']))
        data = r.json()
    except requests.exceptions.RequestException as e:
        print e
        sys.exit(1)
    except ValueError:
        print 'Decoding JSON has failed'
        sys.exit(1)

    assert r.status_code == 200

    return data
