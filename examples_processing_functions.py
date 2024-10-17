from numpy import array, add

##### MODIFY THESE FUNCTIONS TO SET THE PROCESSING BEHAVIOR
def processChunkFunction(parChunkArray: array, parResultArray: array):

    iteratorHelper = iter(parChunkArray)
    prevLine = next(iteratorHelper) # REQUIRES : a line corresponds to a point in sensory experience (see matrix ordering)
    nbElemsInLine = prevLine.size
    for nextLine in iteratorHelper: # TODO : profile this block (keep constant buffer for Lines via rotating 2xnbElems array modified in place ? numpy doc : slices are borrowing mem)
        for iterIndex in range(nbElemsInLine):
            parResultArray[prevLine[iterIndex], nextLine[iterIndex]] += 1
        prevLine = nextLine
    # resArray now is the transition occurrence matrix of the processed chunk

def processChunkFunctionBetter(parChunkArray: array, parResultArray: array):
    endValues = parChunkArray[1:, :]
    startValues = parChunkArray[:-1,:] # All transitions are now of the form (startValues[k], endValues[k])
    startValues.shape = -1
    endValues.shape = -1
    print(f'StartValues (first 10): {startValues[:10]} - EndValues (first 10): {endValues[:10]}')
    add.at(parResultArray, (startValues, endValues), 1) # see https://numpy.org/doc/stable/reference/generated/numpy.ufunc.at.html
    

def cleanUpFunction(parChunkArray: array, parResultArray: array):
    # Si la fonction cleanUp agit sur le chunk (partagé), modifier WorkerProcessesPool._WorkerProcess.run() et intervertir le queue.put et le cleanUp !
    parResultArray.fill(0)

def  contributeResult(parPartialResultArray: array, parTotalResultArray: array):
    parTotalResultArray += parPartialResultArray
###########################################################
