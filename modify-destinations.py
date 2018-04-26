import requests, json, sys, time, random
from requests.auth import HTTPBasicAuth
from subprocess import call

# AUTH = HTTPBasicAuth('a@a.a0', '12345678')
AUTH = HTTPBasicAuth('admin', 'password')
BASEURL = 'http://46.101.238.243:5000/rest/v2'
HEADERS = {'content-type': 'application/json'}

res = requests.get(BASEURL + '/destinations', auth=AUTH)
destinations = res.json()['destinations']
for new_destination in destinations:
    new_dests = []
    for i in range(random.randint(0, 3)):
        new_dests.append({
            'type': 'none',
            'last_update': 1,
            'point': {'lat': 1, 'lon': 1}
        })

    url = BASEURL + '/destinations/' + new_destination['_id']
    method = 'NONE' #'PUT' #PATCH'
    if method == 'PUT':
        data = json.dumps(new_destination)
        res = requests.put(url, data=data, headers=HEADERS, auth=AUTH)
    elif method == 'PATCH':
        data = json.dumps({'destinations': new_dests})
        res = requests.patch(url, data=data, headers=HEADERS, auth=AUTH)

    assert res.status_code == 200

    res = requests.get(url, auth=AUTH)
    print("%s\n-----------------" % json.dumps(res.json(), indent=4))

    # cmd = "curl -H \"Authorization: Basic YUBhLmEwOjEyMzQ1Njc4\" -X DELETE http://46.101.238.243:5001/rest/v2/destinations/" +new_destination['_id']
    # cmd = "curl -H \"Authorization: Basic ZGVzdF90YWc6c29jaWFsQ0BSLiQ=\" -X DELETE http://46.101.238.243:5001/rest/v2/destinations/" + new_destination['_id']
    # print cmd
    # call(cmd, shell=True)
