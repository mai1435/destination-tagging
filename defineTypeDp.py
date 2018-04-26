# coding: utf-8

from computeDwellingPoints import computeDwellingPoints
from geopy.distance import great_circle
from matplotlib import pyplot as plt
import matplotlib.cm as cm
import datetime,dateutil.parser
import numpy as np

def defineTypeDp(positions_log, dps, dpst, kmeans, verbose):

    ############################# This belongs to the second milestone #################################################
    S, se_locs, ts = getSeqDests(positions_log['positions'])
    userTrips, nodes = getUserTrips(S, dps, dpst, kmeans, ts)
    # M,N = computeMotifNetwork(nodes, verbose)
    ###################################################################################################################

    return nodes

def getSeqDests(positions_log):

    S, se_locs, ts = [[] for _ in positions_log], [[] for _ in positions_log], [[] for _ in positions_log]
    print("Obtaining user sequence destinations ...")
    for i in range(len(positions_log)):
        S[i], se_locs[i], ts[i] = [], [], []
        for p in positions_log[i]['positions']:
            j = positions_log[i]['positions'].index(p)
            S[i].append([float(p['point']['lat']), float(p['point']['lon'])])
            se_locs[i].append(S[i][j]) if j == 0 or j == len(positions_log[i]['positions'])-1 else []
            ts[i].append(p['timestamp'])

    return S, se_locs, ts

def getUserTrips(S, dps, dpst, kmeans, ts):

    userTrips = [[] for _ in range(len(S))]
    nodes = [[] for _ in range(len(S))]
    n = len(str(dps[0][0]).split('.')[-1]) if not isinstance(dps[0][0], list) else len(str(dps[0][0][0]).split('.')[-1])
    s = "{0:." + str(n) + "f}" if not kmeans else []
    print("Obtaining user trips and assigning type of destinations ...")
    for i in range(len(S)):
        nodes[i] = [[] for _ in range(len(S[i]))]
        userTrips[i] = [[] for _ in range(len(S[i])-1)]
        # for j in range(len(kmeans.labels_)): print kmeans.labels_[j]
        for j in range(len(S[i])):
            if not kmeans:
                seq1 = [float(s.format(float(S[i][j][0]))), float(s.format(float(S[i][j][1])))]
                if j < len(S[i])-1: seq2 = [float(s.format(float(S[i][j+1][0]))), float(s.format(float(S[i][j+1][1])))]
            else:
                seq1 = S[i][j]; seq2 = S[i][j+1] if j < len(S[i])-1 else []

            if j < len(S[i])-1:
                dist = great_circle((float(seq1[0]), float(seq1[1])), (float(seq2[0]), float(seq2[1]))).meters
                userTrips[i][j] = tuple([seq1, seq2, dist])

            # Here, we do not assume starting and end positions to be necessarily type "home", but we assume "home"
            # as the most frequent positions during the weekdays, then "work", and then "others". During the week-end
            # time, we assume there is no "work" type, and hence we assume "home" during the night from 0:00 to 6:00
            # (independently of their position), and the type "other" for the remainder of the weekend, which is a
            # strong assumption but it would work for most European people.
            if not kmeans:
                if not isinstance(dps[0][0], list):
                    idx = dps.index(seq1) if seq1 in dps else -1
                else:
                    idx = dps[i].index(seq1) if seq1 in dps[i] else -1
            else:
                if not isinstance(dps[0][0], list):
                    idx = kmeans.labels_[j]
                else:
                    idx = kmeans[i].labels_[j]
            # Check if timeday ts[i] is weekend.
            weekend = getTimeDay(dateutil.parser.parse(ts[i][j]))
            # print ts[i][j]+" Weekend: "+str(weekend)
            if idx == dpst[i][0][1] or weekend["night"]: nodes[i][j if j < len(S[i]) else j+1] = 'home'
            elif idx == dpst[i][1][1] and not weekend["time"]: nodes[i][j if j < len(S[i]) else j+1] = 'work'
            else: nodes[i][j if j < len(S[i]) else j+1] = 'other'

    print userTrips
    print nodes
    return userTrips, nodes

def getTimeDay(date):

    weekend = dict.fromkeys(["night", "time"], False)
    if date.weekday() >= 5 or (date.weekday() == 4 and date.hour >= 15) or (date.weekday() == 0 and date.hour < 6):
        weekend["time"] = True
        if date.hour >= 0 and date.hour < 6:
            weekend["night"] = True

    return weekend

def computeMotifNetwork(nodes, verbose):

    # Get Distinct Nodes
    N = [[] for _ in range(len(nodes))]
    for i in range(len(nodes)):
        N[i] = dict({'home': nodes[i].count('home'), 'work': nodes[i].count('work'), 'other': nodes[i].count('other')})

    # Create Motif Network Matrices for each User
    M = [[] for _ in range(len(nodes))]
    for i in range(len(nodes)):
        M[i] = np.zeros((len(N[i].keys()),len(N[i].keys())))
        for j in range(len(nodes[i])-1):
            if nodes[i][j] == 'home':
                if nodes[i][j+1] == 'home':    M[i][0][0] = 1
                elif nodes[i][j+1] == 'work':  M[i][1][0] = 1
                elif nodes[i][j+1] == 'other': M[i][2][0] = 1
            elif nodes[i][j] == 'work':
                if nodes[i][j+1] == 'home':    M[i][0][1] = 1
                elif nodes[i][j+1] == 'work':  M[i][1][1] = 1
                elif nodes[i][j+1] == 'other': M[i][2][1] = 1
            elif nodes[i][j] == 'other':
                if nodes[i][j+1] == 'home':    M[i][0][2] = 1
                elif nodes[i][j+1] == 'work':  M[i][1][2] = 1
                elif nodes[i][j+1] == 'other': M[i][2][2] = 1
        print M[i]
        if verbose:
            plt.pcolor(M[i], cmap=cm.seismic)
            plt.pcolor([M[i][2], M[i][1], M[i][0]],cmap=cm.seismic)
            plt.show()
    print N
    return M, N
