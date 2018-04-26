# coding: utf-8

#################### Main function for the Destination Tagging module ###########################

from computeDwellingPoints import computeDwellingPoints
# from computeDwellingPoints import drawPositions
from generateLogs import generateLogs
from defineTypeDp import defineTypeDp
from updateDestinations import updateDestinations

def main():

    BASEURL = 'http://46.101.238.243:5000/rest/v2/'
    AUTH = {'username': 'admin', 'password': 'password'}

    # here we assume a starting datetime and always get the positions grouped by the same timestamp, i.e. positions
    # grow over time
    urlpos = BASEURL + "positions?group_by_user_id&timestamp_$gt=14567409"
    urldest = BASEURL + "destinations/"

    positions_log, destinations_log = generateLogs(urlpos, urldest, AUTH)

    if not positions_log['positions']:
        print("There are no positions in the logs. Exiting service...")
        return

    flags = dict.fromkeys(["kmeans", "allPos", "verbose"], False)
    # flags["kmeans"] = True; flags["allPos"] = True
    n_floatPoints, typeRankST, typeRankDG = 3, 'sum', 'mean'

    r = computeDwellingPoints(positions_log, n_floatPoints, typeRankST, typeRankDG, flags)

    if flags["verbose"]:
        kmns = r[2] if flags["kmeans"] else [0 for _ in range(len(r[0]))]
        # drawPositions(r[0], r[1], r[2]) if flags["allPos"] else [drawPositions(r[0][i], r[1][i], kmns[i]) for i in range(len(r[0]))]

    nodes = defineTypeDp(positions_log, r[1], r[3], r[2], flags["verbose"])

    updateDestinations(nodes, positions_log, destinations_log, urldest, AUTH)

    return

if __name__ == "__main__":
    main()
