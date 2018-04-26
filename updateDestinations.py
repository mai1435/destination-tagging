# coding: utf-8

import datetime, requests, sys, json, calendar
from requests.auth import HTTPBasicAuth

def updateDestinations(nodes, positions_log, destinations_log, urldest, AUTH):

    HEADERS = {'Content-Type': 'application/json'}

    dest_users = [dest['user_id'] for dest in destinations_log['destinations']]

    for p_user in positions_log['positions']:
        if p_user['user_id'] in dest_users:
            found_dest = False; i = 0; patch = False
            while not found_dest and i < destinations_log['destinations']:
                d_user = destinations_log['destinations'][i]
                found_dest = True if p_user['user_id'] == d_user['user_id'] else False
                i += 1 if not found_dest else i
            today = datetime.date.today()
            lastMonth = today.replace(day=1) - datetime.timedelta(days=1)

            # Check whether a destination exists for this user from the positions:
            points_dest = [dict(dest['point']) for dest in d_user['destinations']]
            remainderDests = []
            for p in p_user['positions']:
                if p['point'] not in points_dest:
                    patch = True
                    # the point is not in the list of destination points, then append a new destination.
                    try:
                        new_dest = {
                            'type': nodes[positions_log['positions'].index(p_user)][p_user['positions'].index(p)],
                            'last_update': calendar.timegm(datetime.datetime.strptime(  # assign the current time
                                datetime.datetime.now().isoformat(), "%Y-%m-%dT%H:%M:%S.%f").timetuple()),
                            'point': {'lat': p['point']['lat'], 'lon': p['point']['lon']}}
                    except ValueError as e:
                        # print(e.message)
                        # print("New attempt to set last_update field without floating points")
                        new_dest = {
                            'type': nodes[positions_log['positions'].index(p_user)][p_user['positions'].index(p)],
                            'last_update': calendar.timegm(datetime.datetime.strptime(  # assign the current time
                                datetime.datetime.now().isoformat(), "%Y-%m-%dT%H:%M:%S").timetuple()),
                            'point': {'lat': p['point']['lat'], 'lon': p['point']['lon']}}

                    d_user['destinations'].append(new_dest)
                else:  # the point exists in the list of destination points, create its new destination in a list.
                    try:
                        remainderDests.append({
                            'type': nodes[positions_log['positions'].index(p_user)][p_user['positions'].index(p)],
                            'last_update': calendar.timegm(datetime.datetime.strptime(  # assign the current time
                                datetime.datetime.now().isoformat(), "%Y-%m-%dT%H:%M:%S.%f").timetuple()),
                            'point': {'lat': p['point']['lat'], 'lon': p['point']['lon']}})
                    except ValueError as e:
                        # print(e.message)
                        # print("New attempt to set last_update field without floating points")
                        remainderDests.append({
                            'type': nodes[positions_log['positions'].index(p_user)][p_user['positions'].index(p)],
                            'last_update': calendar.timegm(datetime.datetime.strptime(  # assign the current time
                                datetime.datetime.now().isoformat(), "%Y-%m-%dT%H:%M:%S").timetuple()),
                            'point': {'lat': p['point']['lat'], 'lon': p['point']['lon']}})

            # append the remainder destinations to the list of user's destinations until #destinations == #positions.
            while len(d_user['destinations']) < len(p_user['positions']) and r_dest in remainderDests:
                d_user['destinations'].append(r_dest)

            for p in p_user['positions']:
                for d in d_user['destinations']:
                    if d['type'] == 'none' or d['last_update'] < lastMonth.isoformat():
                        patch = True
                        # update type and current time for deprecated/none type destinations
                        d['type'] = nodes[positions_log['positions'].index(p_user)][p_user['positions'].index(p)]
                        try:
                            d['last_update'] = calendar.timegm(datetime.datetime.strptime(  # assign the current time
                                datetime.datetime.now().isoformat(), "%Y-%m-%dT%H:%M:%S.%f").timetuple())
                        except ValueError as e:
                            # print(e.message)
                            # print("New attempt to set last_update field without floating points")
                            d['last_update'] = calendar.timegm(datetime.datetime.strptime(  # assign the current time
                                datetime.datetime.now().isoformat(), "%Y-%m-%dT%H:%M:%S").timetuple())
                    # else:     # do not modify destinations' last_update if patch is not needed
                    #     try:
                    #         d['last_update'] = calendar.timegm(datetime.datetime.strptime(
                    #             d['last_update'],"%Y-%m-%dT%H:%M:%S.%f").timetuple())
                    #     except ValueError as e:
                    #         # print(e.message)
                    #         # print("New attempt to set last_update field without floating points")
                    #         d['last_update'] = calendar.timegm(datetime.datetime.strptime(
                    #             d['last_update'], "%Y-%m-%dT%H:%M:%S").timetuple())
            if patch: patchDestination(urldest+d_user['_id'], d_user['destinations'], AUTH, HEADERS)
        else:
            # create and POST the new users' destinations
            d_user = {'user_id': p_user['user_id'], 'destinations': []}
            for p in p_user['positions']:
                try:
                    ts = calendar.timegm(datetime.datetime.strptime(  # assign the current time
                        datetime.datetime.now().isoformat(), "%Y-%m-%dT%H:%M:%S.%f").timetuple())
                except ValueError as e:
                    # print(e.message)
                    # print("New attempt to set last_update field without floating points")
                    ts = calendar.timegm(datetime.datetime.strptime(  # assign the current time
                        datetime.datetime.now().isoformat(), "%Y-%m-%dT%H:%M:%S").timetuple())
                point = {'lat': p['point']['lat'], 'lon': p['point']['lon']}
                d_user['destinations'].append({
                    'last_update': ts, 'point': point,
                    'type': nodes[positions_log['positions'].index(p_user)][p_user['positions'].index(p)]})
            postDestination(urldest, d_user, AUTH, HEADERS)

    return

# POST user in the destinations_log through JSON files
def postDestination(url, d_user, auth, HEADERS):

    json_data = json.dumps(d_user)

    try:
        r = requests.post(url, data=json_data, headers=HEADERS, auth=HTTPBasicAuth(auth['username'], auth['password']))
    except requests.exceptions.RequestException as e:
        print e
        sys.exit(1)

    print('Attempting to POST New user ' + d_user['user_id'] + ' with HTTP code ' + str(r.status_code))
    assert r.status_code == 201
    # print(json.dumps(r.json(), indent=4))

    return

# PATCH user destination in the destinations_log through JSON files
def patchDestination(url, new_dests, auth, HEADERS):

    json_data = json.dumps({'destinations': new_dests})
    try:
        r = requests.patch(url, data=json_data, headers=HEADERS,
                           auth=HTTPBasicAuth(auth['username'], auth['password']))
    except requests.exceptions.RequestException as e:
        print e
        sys.exit(1)

    print('Attempting to PATCH destination with HTTP code ' + str(r.status_code))
    assert r.status_code == 200
    # print(json.dumps(r.json(), indent=4))

    return
