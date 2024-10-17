from .Buffers import BufferPool
from . import Constants
import os
from multiprocessing import Process, Queue
from numpy import ndarray, array, dtype, zeros


#def processChunkFunction(parChunkBuffer: memoryview, parChunkShape: tuple, parDataDType: dtype, parResultBuffer: memoryview, parResultShape: tuple, parResultDType: dtype):
#    dataChunk = ndarray(parChunkShape, dtype=parDataDType, buffer=parChunkBuffer)
#    resArray = ndarray(parResultShape, dtype=parResultDType, buffer=parResultBuffer)
#
#    iteratorHelper = iter(dataChunk)
#    prevLine = next(iteratorHelper) # REQUIRES : a line corresponds to a point in sensory experience (see matrix ordering)
#    nbElemsInLine = prevLine.size
#    for nextLine in iteratorHelper: # TODO : profile this block (keep constant buffer for Lines via rotating 2xnbElems array modified in place ?)
#        for iterIndex in range(nbElemsInLine):
#            resArray[prevLine[iterIndex], nextLine[iterIndex]] += 1
#        prevLine = nextLine
#    
#    # resArray now is the transition occurrence matrix of the processed chunk
#    return resArray # no copy involved here, unless the caller makes an unfortunate assignment

class WorkerProcessesPool(object):
    class _WorkerProcess(Process):
        def __init__(self, parBufferPoolConnection: BufferPool._BufferConnection, parPartialResultArrayShape: tuple, parPartialResultDType: dtype, parProcessChunkFunc, parCleanUpFunc, parContributeResultFunc):
            Process.__init__(self)
            self._bufferConnection = parBufferPoolConnection
            self._tmpResultArrayShape = parPartialResultArrayShape
            self._tmpResultDType = parPartialResultDType
            self._processChunkFunction = parProcessChunkFunc
            self._cleanUpFunction = parCleanUpFunc
            self._contributeResultFunction = parContributeResultFunc
            #self._freeIndicesQueue = parBufferPoolConnection._freeIndicesQueue
            #self._busyIndicesQueue = parBufferPoolConnection._busyIndicesQueue
            #self._sharedMemory = parBufferPoolConnection._sharedMemory

        def run(self):
            # Setup forked resources
            self._bufferConnection._openConnection()
            self._partialResultArray = zeros(self._tmpResultArrayShape, self._tmpResultDType)
            self._totalResultArray = ndarray(self._bufferConnection._resultShape, dtype= self._bufferConnection._resultDType, buffer=self._bufferConnection._resultSharedMemory.buf)
            self._pID = os.getpid()
            del self._tmpResultArrayShape
            print(f'Processus (traitement) {self._pID} : fork termine, connexion aux buffers etablie')

            # Listening and processing loop
            while True:
                print(f'Process traitement {self._pID} : en attente de Chunk pret')
                nextChunkIndex = self._bufferConnection._busyIndicesQueue.get()

                if nextChunkIndex == Constants.sentinelValue:
                    #self._bufferConnection._busyIndicesQueue.task_done()
                    print(f'Processus traitement {self._pID} : terminaison en cours. Rediffusion valeur arret...')
                    self._bufferConnection._busyIndicesQueue.put(Constants.sentinelValue)
                    return # Processing is done, terminate the worker process

                #nextChunk = buffer_pool.borrowChunk(self._bufferConnection._chunkShape, self._bufferConnection._dType, self._bufferConnection._sharedMemory, self._bufferConnection._chunkSize, nextChunkIndex)
                nextChunk = self._bufferConnection.getChunk(nextChunkIndex)

                #print(f'DEBUG : Etat chunk a la recuperation par Processing {nextChunk[:3,:10]}')

                print(f'Process traitement {self._pID} : debut du traitement de Chunk {nextChunkIndex}')

                self._processChunkFunction(nextChunk, self._partialResultArray)
                
                #self._bufferConnection._busyIndicesQueue.task_done()
                self._bufferConnection._freeIndicesQueue.put(nextChunkIndex)

                self._bufferConnection._resultLock.acquire()
                print(f'Process traitement {self._pID} : pooling des resultats intermediaires de Chunk {nextChunkIndex}')
                self._contributeResultFunction(self._partialResultArray, self._totalResultArray)
                self._bufferConnection._resultLock.release()
                self._cleanUpFunction(nextChunk, self._partialResultArray)
            ######## Inaccessible branch

    def _spawnProcess(self) -> Process:
        return self._WorkerProcess(self._bufferPool.borrowConnection(), self._partialResultArrayShape, self._partialResultDType, self._processChunkFunction, self._cleanUpFunction, self._contributeResultFunction)

    def __init__(self, parBufferPool: BufferPool):
        self._bufferPool = parBufferPool
        self._processes = []

    #### Helper methods for shared setup between processes :
    ## !! Signature requirements !!
    # processFunction should be (incomingChunkArray, [mutable] partialResultArray) -> void
    # cleanUpFunction should be the same, except incomingChunkArray can be mutable (adjust run method accordingly)
    # contributeResult should be (partialResultArray, [mutable] totalResultArray) -> void. Exclusive ownership is ensured by class boilerplate
    def setProcessFunction(self, parFunc) -> None:
        self._processChunkFunction = parFunc
    def setCleanUpFunction(self, parFunc) -> None:
        self._cleanUpFunction = parFunc
    def setContributeResultsFunction(self, parFunc) -> None:
        self._contributeResultFunction = parFunc
    def setPartialResultArrayShape(self, parShape: tuple) -> None:
        self._partialResultArrayShape = parShape
    def setPartialResultDType(self, parDType: dtype) -> None:
        self._partialResultDType = parDType


    def initiateWorkers(self, parNumberProcesses=Constants._nbWorkerProcesses):
        print(f'Initialisation de {parNumberProcesses} processus de traitement...')
        assert not self._processes, 'WorkerPool was reused with no guarantee that previous threads were joined' # evaluates to True iff _processes is empty
        self._processes = [self._spawnProcess() for i in range(parNumberProcesses)]
        for workerProcess in self._processes:
            workerProcess.start()

    def waitForAllProcesses(self):
        print('En attente de la terminaison des processus de traitement')
        for workerProcess in self._processes:
            workerProcess.join()
        print('Processus de traitement tous termines. Verification et maintenance memoire...')
        while not self._bufferPool._busyIndicesQueue.empty():
            queueTop = self._bufferPool._busyIndicesQueue.get()
            if queueTop!=Constants.sentinelValue:
                print('Warning (Critical) : non sentinel value was found in processing queue during closing maintenance !')
            #self._bufferPool._busyIndicesQueue.task_done()
        self._bufferPool._busyIndicesQueue.close()
        while not self._bufferPool._freeIndicesQueue.empty():
            queueTop = self._bufferPool._freeIndicesQueue.get()
            #self._bufferPool._freeIndicesQueue.task_done()
        self._bufferPool._freeIndicesQueue.close()
        print('Worker processes have all exited successfully.')

