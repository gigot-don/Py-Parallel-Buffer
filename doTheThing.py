import numpy as np
import matplotlib.pyplot as plt
from scipy.sparse.csgraph import shortest_path
from sklearn.manifold import MDS, Isomap

stdVals = []

def buildNames(parRadicalStr, parSuffixStr, parStdVals=stdVals):
    res = []
    for val in parStdVals:
        res.append(parRadicalStr + '-' + str(val) + '_' + parSuffixStr)
    return res

def normalizeThis(parOccurrenceArrays):
    res = []
    for val in parOccurrenceArrays:
        res.append(val / np.maximum(1, np.sum(val, -1))[:,np.newaxis])
    return res

def logifyThis(parNormalizedArrays):
    res = []
    for val in parNormalizedArrays:
        myMinVal = np.min(val[val!=0])
        res.append(-np.log(np.maximum(myMinVal/10000000, val)))
    return res

def dijkstraThis(parLogifiedArrays):
    res = []
    for val in parLogifiedArrays:
        res.append(shortest_path(val))
    return res

def plotMatrices(parMatrixList):
    for mat in parMatrixList:
        plt.figure()
        plt.imshow(mat)
    plt.show()

nCoords = 3
isoObj = Isomap(n_components=nCoords, metric='precomputed')
mdsObj = MDS(n_components=nCoords, dissimilarity='precomputed')

def isoThis(parDijkstraArrays, parIsoObj = isoObj):
    res = []
    for val in parDijkstraArrays:
        out = parIsoObj.fit_transform(val)
        res.append(out)
    return res

def mdsThis(parDijkstraArrays, parMdsObj = mdsObj):
    res = []
    for val in parDijkstraArrays:
        out = parMdsObj.fit_transform(val)
        res.append(out)
    return res

def plotScatters(parScatterList, parNCoords=nCoords):
    for scat in parScatterList:
        fig = plt.figure()
        if parNCoords==3:
            ax = fig.add_subplot(111, projection='3d')
        else:
            ax = fig.add_subplot(111)
        ax.scatter(scat[:,0], scat[:,1], scat[:,2])
    plt.show()

