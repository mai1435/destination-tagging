import requests, json, sys, time
from requests.auth import HTTPBasicAuth
from pprint import pprint
import numpy as np

last_timestamp = 14567409
# AUTH = HTTPBasicAuth('a@a.a0', '12345678')
AUTH = HTTPBasicAuth('admin', 'password')
BASEURL = 'http://46.101.238.243:5000/rest/v2'
HEADERS = {'content-type': 'application/json'}

UPDATE_METHOD = 'PUT'  # 'PUT' or 'PATCH'

res = requests.get(BASEURL + '/positions?group_by_user&timestamp_$gt=' + str(last_timestamp), headers=HEADERS, auth=AUTH)
positions = res.json()['positions']

# new user must be created before adding their positions
if not positions:
    res = requests.get(BASEURL + '/users', headers=HEADERS, auth=AUTH)
    users = res.json()['users']  # Add random positions if they do not exist
    if res.status_code not in range(200, 203):
        print(json.dumps(res.json(), indent=4))
        sys.exit(1)

    if len(users) < 5:
        for u in range(np.random.randint(5, 10)):
            new_user = {
               "email": str(np.random.randint(10000,99999))+"@doe.com",
               "password": "12345678",
               "name": "John Doe",
               "phone": "3274589556",
               "dob": "1970-12-31",
               "gender": "FEMALE",
               "fcm_token": "engPNkGUVl0:APA91bF3iVPpY6uC..."
            }
            data = json.dumps(new_user)
            url = BASEURL + '/users'
            res = requests.post(url, data=data, headers=HEADERS, auth=AUTH)
            print res
            if res.status_code != 201:
                print(json.dumps(res.json(), indent=4))
        # curl -H "Authorization: Basic YUBhLmEwOjEyMzQ1Njc4" -X DELETE http://46.101.238.243:5001/rest/v2/users/583c23e4c2543f3bc396ebee
        # curl -H "Authorization: Basic ZGVzdF90YWc6c29jaWFsQ0BSLiQ=" -X DELETE http://46.101.238.243:5001/rest/v2/users/58944a31e04bd523c0ca8eab
        print("Users generated successfully!")
    res = requests.get(BASEURL + '/users', headers=HEADERS, auth=AUTH)
    users = res.json()['users']  # Add random positions if they do not exist
    if res.status_code not in range(200,203):
        print(json.dumps(res.json(), indent=4))
        sys.exit(1)

    for u in users:
        print('New user ' + u['_id'])
        for j in range(np.random.randint(10, 20)):
            new_pos = {'user_id': u['_id'], 'timestamp': 14567410, 'point': {'lat': 41.5486, 'lon': 2.9546}}
            url = BASEURL + '/positions'
            data = json.dumps(new_pos)
            print data
            res = requests.post(url, data=data, headers=HEADERS, auth=AUTH)
            print res.status_code
            if res.status_code not in range(200, 203):
                print(json.dumps(res.json(), indent=4))

    print("Dummy User positions generated successfully!")

#-------------------------------------------------------------------------------
# Calculate new destinations based on positions
#-------------------------------------------------------------------------------

res = requests.get(BASEURL + '/positions?group_by_user_id&timestamp_$gt=' + str(last_timestamp), headers=HEADERS, auth=AUTH)
positions = res.json()['positions']

print("Attempting to create new user (dummy) destinations...")
new_destinations = []
for position in positions:
    new_dest = {
        'user_id': position['user_id'],
        'destinations': []
    }

    # <do your computations here...>
    # current_timestamp = int(time.time())
    # for i in range(3):
    #     new_dest['destinations'].append({
    #         'last_update': current_timestamp,
    #         'type': 'none',
    #         'point': {
    #             'lat': 1,
    #             'lon': 2
    #         }
    #     })
    #
    new_destinations.append(new_dest)

#-------------------------------------------------------------------------------
# Create/Update destinations on server
#-------------------------------------------------------------------------------
res = requests.get(BASEURL + '/destinations', headers=HEADERS, auth=AUTH)
destinations = res.json()['destinations']

# Create a dict for users with existing destinations:
#   user_id -> objectId of existing destination on server
existing_users = dict([ (dest['user_id'], dest['_id']) for dest in destinations ])

for new_destination in new_destinations:

    user_id = new_destination['user_id']

    #---------------------------------------------------------------------------
    # If we have an existing destination for this user, update it (PUT)
    #---------------------------------------------------------------------------
    if user_id in existing_users:
        print('Existing user ' + user_id)
        destination_id = existing_users[user_id]
        url = BASEURL + '/destinations/' + destination_id

        # Use PUT to update object (send the whole updated object)
        if UPDATE_METHOD == 'PUT':
            data = json.dumps(new_destination)
            res = requests.put(url, data=data, headers=HEADERS, auth=AUTH)
        # Use PATCH to update object (send only the field to update, with the new value)
        else:
            data = json.dumps({'destinations': new_destination['destinations']})
            res = requests.patch(url, data=data, headers=HEADERS, auth=AUTH)

        if res.status_code != 200:
            print(json.dumps(res.json(), indent=4))

    # Else create a new destination (POST)
    else:
        print('New user ' + user_id)
        url = BASEURL + '/destinations'
        data = json.dumps(new_destination)
        print res.status_code
        res = requests.post(url, data=data, headers=HEADERS, auth=AUTH)
        if res.status_code != 201:
            print(json.dumps(res.json(), indent=4))

# -------------------------------------------------------------------------------
# Remove specific destination on server from shell
# -------------------------------------------------------------------------------
# curl -H "Authorization: Basic YUBhLmEwOjEyMzQ1Njc4" -X DELETE http://46.101.238.243:5001/rest/v2/destinations/583c23e4c2543f3bc396ebee