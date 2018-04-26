# coding: utf-8

import numpy as np
import datetime,dateutil.parser,pandas,math
from collections import Counter
from geopy.geocoders import Nominatim
from geopy.distance import great_circle
from geopy.exc import GeocoderTimedOut
from geopy.exc import GeocoderServiceError
from scipy.stats import entropy
# from mpl_toolkits.basemap import Basemap
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import matplotlib.cm as cm

def computeDwellingPoints(positions_log, n, typeRankST, typeRankDG, flags):

    ############### Get all set of positions from all users either original or rounded #################################
    if not flags["kmeans"]:
        rErrors = [[] for _ in range(4)]
        sfix = "{0:."+str(n)+"f}"; kmeans = []

    l = 0
    for p_user in positions_log['positions']:
        l += len(p_user['positions'])
    if not flags["kmeans"]:
        print("Rounding user positions ...")
        for i in range(len(rErrors)):
            rErrors[i] = [[] for _ in range(l)]
    rPos = [[] for _ in range(l)] if flags["allPos"] else [[] for _ in range(len(positions_log['positions']))]
    for i in range(len(positions_log['positions'])):
        p_user = positions_log['positions'][i]
        if not flags["allPos"]:
            rPos[i] = [[] for _ in range(len(p_user['positions']))]
        for p in range(len(p_user['positions'])):
            if not flags["kmeans"]:
                if flags["allPos"]:
                    rPos[i*1+p] = ([float(sfix.format(float(p_user['positions'][p]['point']['lat']))),
                                    float(sfix.format(float(p_user['positions'][p]['point']['lon'])))])
                else:
                    rPos[i][p] = ([float(sfix.format(float(p_user['positions'][p]['point']['lat']))),
                                   float(sfix.format(float(p_user['positions'][p]['point']['lon'])))])
                for j in range(len(rErrors)):
                    s = "{0:."+str(j+1)+"f}"
                    rErrors[j][i*1+p] = great_circle(
                        (float(p_user['positions'][p]['point']['lat']), float(p_user['positions'][p]['point']['lon'])),
                        (float(s.format(float(p_user['positions'][p]['point']['lat']))),
                         float(s.format(float(p_user['positions'][p]['point']['lon']))))).meters
            else:
                if flags["allPos"]:
                    rPos[i*1+p] = [float(p_user['positions'][p]['point']['lat']), float(p_user['positions'][p]['point']['lon'])]
                else:
                    rPos[i][p] = [float(p_user['positions'][p]['point']['lat']), float(p_user['positions'][p]['point']['lon'])]
    ####################################################################################################################

    ######################### This belongs to the thirld milestone #####################################################
    if flags["kmeans"]:
        print("Clustering user positions ...")
        if flags["allPos"]:
            try:
                kmeans = KMeans(n_clusters=6, random_state=0).fit(rPos)
            except ValueError as e:
                print str(e)+" Skipping grouping DP identification ..."
                return
            dwellPoints = [kmeans.cluster_centers_[i].tolist() for i in range(len(kmeans.cluster_centers_))]
            # print kmeans.labels_
        else:
            kmeans, dwellPoints = [[] for _ in range(len(rPos))], [[] for _ in range(len(rPos))]
            for i in range(len(rPos)):
                try:
                    kmeans[i] = KMeans(n_clusters=6, random_state=0).fit(rPos[i])
                except ValueError as e:
                    print str(e) + ".\nSkipping grouping DP identification ..."
                    return
                dwellPoints[i] = [kmeans[i].cluster_centers_[j].tolist() for j in range(len(kmeans[i].cluster_centers_))]
                # print kmeans[i].labels_
    else:
        if flags["allPos"]:
            dwellPoints = getRankedClusters(rPos, flags["verbose"])
        else:
            dwellPoints = [getRankedClusters(rPos[i], flags["verbose"]) for i in range(len(rPos))]
        # if flags["verbose"]: plotErrors(rErrors)
    ####################################################################################################################

    ######################### This belongs to the first milestone ######################################################
    staytimes = computeStayTimes(positions_log['positions'], dwellPoints, kmeans)
    rankedLocsSts = rankStayTimes(staytimes, typeRankST)
    ####################################################################################################################

    ######################### This belongs to the second milestone #####################################################
    deltaGroups = computeDeltaGroups(staytimes)
    rankedLocsDgs = rankDeltaGroups(deltaGroups, typeRankDG)
    u_entropies,u_dt = calcUserEntropies(staytimes)
    eRankedLocsDgs = predLocEntrDgs(deltaGroups)
    ####################################################################################################################

    return rPos, dwellPoints, kmeans, rankedLocsSts, rankedLocsDgs, u_entropies, u_dt, eRankedLocsDgs

######################### This belongs to the first milestone ##########################################################
######################### Given the stay times, rank locations #########################################################
def rankStayTimes(staytimes, type):

    rankedLocations = [[] for _ in range(len(staytimes))]

    for j in range(len(staytimes)):
        if type == 'sum':
            s = 'Accumulated'
            t = [pandas.Series(staytimes[j][1][i]).sum() for i in range(len(staytimes[j][1]))]
            for i in range(len(t)):
                t[i] = datetime.timedelta(-1) if not isinstance(t[i], datetime.timedelta) else t[i]
        elif type == 'mean':
            s = 'Averaged'
            t = [pandas.Series(staytimes[j][1][i]).mean() for i in range(len(staytimes[j][1]))]
            for i in range(len(t)):
                t[i] = datetime.timedelta(-1) if not isinstance(t[i], datetime.timedelta) else t[i]
        else:
            print "Unknown type"
            return -1

        p = sorted(range(len(t)), key=lambda i: t[i], reverse=True)
        rankedLocations[j] = [tuple([t[p[i]], p[i]]) for i in range(len(p))]

    # print "\nRanked Locations (dwelling point candidates) by "+s+" Stay Times:"
    # for j in range(len(rankedLocations)):
    #     print "For the User's Stay Times \"%s\":" % staytimes[j][0]
    #     for rl in rankedLocations[j]:
    #         print "\tLocation "+str(rl[1])+": "+str(rl[0])

    return rankedLocations

######################### This belongs to the first milestone ##########################################################
############ Given the positions_log and dwelling points, compute stay times ###########################################
def computeStayTimes(positions_log, dwellPoints, kmeans):

    staytimes = []; i = 0 if kmeans else []
    n = len(str(dwellPoints[0][0]).split('.')[-1]) if not isinstance(dwellPoints[0][0], list) else len(str(dwellPoints[0][0][0]).split('.')[-1])
    s = "{0:."+str(n)+"f}"

    print("Computing user stay times ...")
    for p_user in positions_log:
        deltas = [[] for _ in range(len(dwellPoints))] if not isinstance(dwellPoints[0][0], list) else [[] for _ in range(len(dwellPoints[positions_log.index(p_user)]))]
        tdp = [[] for _ in range(len(dwellPoints))] if not isinstance(dwellPoints[0][0], list) else [[] for _ in range(len(dwellPoints[positions_log.index(p_user)]))]
        p_dp = -1
        pos_user = p_user['positions']
        for p in pos_user:
            pos = [float(s.format(float(p['point']['lat']))), float(s.format(float(p['point']['lon'])))]
            # print str(pos)+" : "+ p['timestamp']

            if not kmeans:
                dps = dwellPoints if not isinstance(dwellPoints[0][0], list) else dwellPoints[positions_log.index(p_user)]
                if pos in dps:
                    p_dp = dps.index(pos)
                    tdp[p_dp].append(p['timestamp'])
                    next_tp = pos_user[pos_user.index(p)+1]['timestamp'] if pos_user.index(p)+1 < len(pos_user) else []
                    # print str(p_dp) + ": " + str(pos) + " , " + p['timestamp']
            else:
                kmns = kmeans if not isinstance(dwellPoints[0][0], list) else kmeans[positions_log.index(p_user)]
                p_dp = kmns.labels_[i]
                tdp[p_dp].append(p['timestamp'])
                next_tp = pos_user[pos_user.index(p)+1]['timestamp'] if pos_user.index(p)+1 < len(pos_user) else []
                # print str(p_dp) + ": " + str(pos) + " , " + p['timestamp']
            if p_dp >= 0:
                if pos_user.index(p)+1 < len(pos_user):
                    next_pos = [float(s.format(float(pos_user[pos_user.index(p)+1]['point']['lat']))),
                               float(s.format(float(pos_user[pos_user.index(p)+1]['point']['lon'])))]
                    if next_tp and (kmeans and p_dp == kmns.labels_[i+1] or not kmeans and next_pos == dps[p_dp]):
                        tdp[p_dp].append(next_tp)
                    else:
                        deltas[p_dp].append(dateutil.parser.parse(max(t for t in tdp[p_dp])) -
                                            dateutil.parser.parse(min(tdp[p_dp]))); tdp[p_dp] = []
                        # print deltas[p_dp]
                        p_dp = -1
                else:
                    deltas[p_dp].append(dateutil.parser.parse(max(t for t in tdp[p_dp])) -
                                        dateutil.parser.parse(min(tdp[p_dp]))); tdp[p_dp] = []
                    # print deltas[p_dp]
            i += 1 if kmeans else []
        # print deltas
        staytimes.append(tuple([p_user['user_id'], deltas]))

    return staytimes

########################################################################################################################




######################### This belongs to the second milestone #########################################################
########## Given the Delta Groups, rank predictability of locations by entropy #########################################
def predLocEntrDgs(deltaGroups):

    entropiesDgs = [[] for _ in range(len(deltaGroups))]

    print("Calculating user entropies ...")

    t_sec = [[] for _ in range(len(deltaGroups))]
    for j in range(len(deltaGroups)):
        t = [pandas.Series(deltaGroups[j][i]) for i in range(len(deltaGroups[j]))]
        t_sec[j] = [t[i][0].days*24*60*60+t[i][0].seconds for i in range(len(t))]
        try:
            t_norm = [float(x) / np.sum(t_sec[j]) for x in t_sec[j]]
        except ZeroDivisionError as e:
            print "Warning: "+ str(e) + " when calculating the entropy. Setting norm to 0"
            t_norm = 0
        entropiesDgs[j] = entropy(t_norm, base=2) / math.log(180, 2)
        # print "Group "+str(j)+", Seconds: "+str(t_sec[j])+"; Sec_Sum: "+str(np.sum(t_sec[j]))+"; Norm: "+str(
        #     t_norm)+"; Entropies: "+str(entropiesDgs[j])

    p = sorted(range(len(entropiesDgs)), key=lambda i: entropiesDgs[i] if isinstance(entropiesDgs[i], float) else [], reverse=True)
    rankedLocations = [tuple([entropiesDgs[p[i]], p[i]]) for i in range(len(p))]

    # print "\nRanked Locations (dwelling point candidates) by timedelta's entropies:"
    # for j in range(len(rankedLocations)):
    #     s = "\tLocation " + str(rankedLocations[j][1]) + ", Entropy = " + str(rankedLocations[j][0])
    #     if rankedLocations[j][0] == float('-Inf'): s += " --> All timedeltas are 0!"
    #     print s

    return rankedLocations

######################### This belongs to the second milestone #########################################################
########## Given the Stay Times, rank predictability of locations by entropy ###########################################
def calcUserEntropies(staytimes):

    rankedLocations, u_entropies, u_dt = [[] for _ in range(len(staytimes))], [[] for _ in range(len(staytimes))], [[] for _ in range(len(staytimes))]

    for j in range(len(staytimes)):
        t_sec = [[] for _ in range(len(staytimes[j][1]))]; u_dt[j] = []
        for i in range(len(staytimes[j][1])):
            t = pandas.Series(staytimes[j][1][i][k] for k in range(len(staytimes[j][1][i])))
            t_sec[i] = [t[k].days * 24 * 60 * 60 + t[k].seconds for k in range(len(t))]
            u_dt[j].append(np.sum(t_sec[i]))
        try:
            t_norm = [float(x) / np.sum(u_dt[j]) for x in u_dt[j]]
        except ZeroDivisionError as e:
            print "Warning: " + str(e) + " when calculating the entropy. Setting norm to 0"
            t_norm = 0
        u_entropies[j] = entropy(t_norm, base=2) / math.log(180, 2)
        # print "User " + str(j) + ", Seconds_Loc: " + str(np.sum(u_tsec[j])) + "; Norm: " + str(
        #     t_norm) + "; Entropies: " + str(u_entropies[j])

        p = sorted(range(len(u_dt[j])), key=lambda i: u_dt[j][i] if isinstance(u_dt[j][i], int) else [], reverse=True)
        rankedLocations[j] = [tuple([u_dt[j][p[i]], p[i]]) for i in range(len(p))]

    # print "\nRanked Locations (dwelling point candidates) by staytime's entropies:"
    # for j in range(len(udt_entropies)):
    #     print "For the given User's Stay Times \"%s\":" % staytimes[j][0]
    #     for rl in udt_entropies[j]:
    #         s = "\tLocation " + str(rl[1]) + ", Entropy = "+str(rl[0])
    #         if rl[0] == float('-Inf'): s += " --> All timedeltas are 0!"
    #         print s

    return u_entropies, rankedLocations

######################### This belongs to the second milestone #########################################################
######################## Given the Delta Groups, rank locations ########################################################
def rankDeltaGroups(deltaGroups, type):

    if type == 'sum':
        # print "\nRanked Locations (dwelling point candidates) by the Accumulated Delta Groups:"
        t = [pandas.Series(deltaGroups[j]).sum() for j in range(len(deltaGroups))]
        for i in range(len(t)):
            t[i] = datetime.timedelta(-1) if not isinstance(t[i], datetime.timedelta) else t[i]
    elif type == 'mean':
        # print "\nRanked Locations (dwelling point candidates) by the Averaged Delta Groups:"
        t = [pandas.Series(deltaGroups[j]).mean() for j in range(len(deltaGroups))]
        for i in range(len(t)):
            t[i] = datetime.timedelta(-1) if not isinstance(t[i], datetime.timedelta) else t[i]
    else:
        print "Error: Undefined metric type"
        return -1

    p = sorted(range(len(t)), key=lambda i: t[i], reverse=True)
    rankedLocations = [tuple([t[p[i]],p[i]]) for i in range(len(p))]

    # for j in range(len(rankedLocations)):
    #     print "\tLocation "+str(rankedLocations[j][1])+": "+str(rankedLocations[j][0])

    return rankedLocations

######################### This belongs to the second milestone #########################################################
###################### Given the staytimes, compute delta groups #######################################################
def computeDeltaGroups(staytimes):
    deltaGroups = [[] for _ in range(len(staytimes[0][1]))]

    for st in staytimes:
        for j in range(len(deltaGroups)):
            if st[1][j]:
                for delta in st[1][j]:
                    deltaGroups[j].append(delta)

    return deltaGroups

########################################################################################################################




######################### This belongs to the thirld milestone #########################################################
####### Given the rounded positions, get ranked clusters by occurrences ################################################
def getRankedClusters(rPos, verbose):
    ctr = Counter(tuple(rp) for rp in rPos)
    dps_ = ctr.most_common(6); dps = []
    # print dps_
    # print "Groups (Clusters) of Ranked Locations by rounded positions: \n"
    for dp in dps_:
        if verbose:
            geolocator = Nominatim()
            try:
                location = geolocator.reverse(str(dp[0][0]) + "," + str(dp[0][1]))
                print((location.latitude, location.longitude))
                print(u''.join(location.address).encode('utf-8').strip())
                # print(location.raw)
            except AttributeError as e:
                print "Geocoder: "+str(e)
            except GeocoderTimedOut as e:
                print "Geocoder: "+str(e)
            except GeocoderServiceError as e:
                print "Geocoder: "+str(e)
        dps.append([dp[0][0],dp[0][1]])

    # print len(ctr)

    return dps

######################### This belongs to the thirld milestone #########################################################
############# Given the mean distances (errors), compute plot errors ###################################################
def plotErrors(errors):
    x = np.array([i for i in range(len(errors))])
    y = [np.mean(errors[i]) for i in range(len(errors))]

    fig, ax = plt.subplots()

    # add some text for labels, title and axes ticks
    ax.set_ylabel('Mean Error (in meters)')
    ax.set_xlabel('Rounding from 1 to 4 floating point numbers')
    ax.set_title('Averaged Great Circle distances given by the rounding effect')
    plt.xticks(x, [".1f",".2f",".3f",".4f"])

    plt.bar(x, y, color="blue", align='center')

    plt.show()

########################## This belongs to the thirld milestone ########################################################
############# Given the positions and clusters, draw points into the map ###############################################
# def drawPositions(rPos, clusters, kmeans):
#
#     x,y = [], []
#     for p_user in rPos:
#         lat, lon = p_user[0:2]
#         y.append(float(lat))
#         x.append(float(lon))
#
#     try:
#         m = Basemap(llcrnrlon=np.min(x), llcrnrlat=np.min(y), urcrnrlon=np.max(x), urcrnrlat=np.max(y),projection='cyl')
#     except ZeroDivisionError as e:
#         print "Basemap: "+str(e)+". There are too few positions or they the same"
#         return
#
#     # m.drawcoastlines()
#     # m.drawcountries(linewidth=0.25)
#     # m.fillcontinents(color='coral', lake_color='aqua')
#     m.drawmapboundary(fill_color='aqua')
#     # m.drawmapboundary(fill_color='white')  # fill to edge
#     size = 20
#
#
#     if not kmeans:
#         x1, y1 = m(x, y)
#         m.scatter(x1, y1, s=size, c='k', marker="o", cmap=cm.jet, alpha=1.0)
#
#     x, y = [[] for _ in range(len(clusters))], [[] for _ in range(len(clusters))]
#     for i in range(len(rPos)):
#         if not kmeans and rPos[i] in clusters:
#             x[clusters.index(rPos[i])].append(rPos[i][1]); y[clusters.index(rPos[i])].append(rPos[i][0])
#         elif kmeans:
#             x[kmeans.labels_[i]].append(rPos[i][1]); y[kmeans.labels_[i]].append(rPos[i][0])
#     size = size*4 if not kmeans else size
#     centroids = [[[] for _ in range(len(clusters))] for _ in range(2)] if kmeans else []
#     for i in range(len(clusters)):
#         if i == 0: c = 'r'
#         elif i == 1: c = 'b'
#         elif i == 2: c = 'm'
#         elif i == 3: c = 'y'
#         elif i == 4: c = 'g'
#         elif i == 5: c = 'w'
#         if kmeans: centroids[0][i] = kmeans.cluster_centers_[i][1]; centroids[1][i] = kmeans.cluster_centers_[i][0]
#         x1, y1 = m(x[i], y[i])
#
#         m.scatter(x1, y1, s=size, color=c, marker="o", cmap=cm.jet, alpha=1.0)
#     if kmeans: m.scatter(centroids[0], centroids[1], s=size*6, color='k', marker="o", cmap=cm.jet, alpha=1.0);
#
#     plt.title("User positions on the map")  # might want to change this!
#     plt.show()
