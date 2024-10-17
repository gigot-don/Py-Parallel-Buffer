import os
from .Buffers import BufferPool
from . import Constants

class DataGetter(object):
    def __init__(self, parBufferPool: BufferPool):
        self._bufferConnection = parBufferPool.borrowConnection()

    ### Helper methods for initial setup
    def setStreamDescriptor(self, parStreamDescriptor) -> None:
        self._streamDescriptor = parStreamDescriptor
    def setOpenStreamFunction(self, parOpenStreamFunc) -> None: # signature should be (streamDescriptor) -> streamType
        self._openStreamFunction = parOpenStreamFunc
    def setCloseStreamFunction(self, parCloseStreamFunc) -> None: # signature should be ([mutable] streamType) -> NoneType
        self._closeStreamFunction = parCloseStreamFunc
    def setChunkPopulater(self, parChunkPopulater) -> None: # signature should be ([mutable] streamType, [mutable] array) -> NoneType
        self._chunkPopulater = parChunkPopulater
    def setShouldStopFunction(self, parShouldStopFunction) -> None: # signature should be (streamType) -> bool
        self._shouldStopFunction = parShouldStopFunction
    #def setGetExemplarFunction(self, parGetExemplarFunc) -> None:
        #self._getExemplarFunc = parGetExemplarFunc

    #def performSetup(self) -> None:
        #self._dType = self._bufferConnection._dType
        #self._numberExemplarsInChunk = self._bufferConnection._chunkShape[0]
        #self._numberElemsInVector = self._bufferConnection._chunkShape[1]

        #self._dType = parDType
        #self._resultDType = parResultDType
        #self._numberElemsInVector = parNumberElemsInVector
        #self._numberExemplarsInChunk = parNumberExemplarsInChunk
        #self._resultShape = parResultShape

    def run(self) -> None:
        # Finish setup via attributes of possible Populater object if necessary
        if not hasattr(self, '_streamDescriptor'):
            self._streamDescriptor = self._chunkPopulater.streamDescriptor
        if not hasattr(self, '_openStreamFunction'):
            self._openStreamFunction = self._chunkPopulater.openStream
        if not hasattr(self, '_closeStreamFunction'):
            self._closeStreamFunction = self._chunkPopulater.closeStream
        if not hasattr(self, '_shouldStopFunction'):
            self._shouldStopFunction = self._chunkPopulater.shouldStop

        # Fork resources
        self._bufferConnection._openConnection()
        self._pID = os.getpid()
        self._stream = self._openStreamFunction(self._streamDescriptor)
        print(f'Processus (acquisition) {self._pID} : stream ouvert, connexions aux buffers etablie')

        while True:
            if self._shouldStopFunction(self._stream):
                self._closeStreamFunction(self._stream)
                print(f'Process acquisition {self._pID} : stream ferme, terminaison en cours. Envoi signal arret à la file...')
                self._bufferConnection._busyIndicesQueue.put(Constants.sentinelValue)
                return

            print(f'Process acquisition {self._pID} : en attente de Chunk à remplir')
            nextChunkIndex = self._bufferConnection._freeIndicesQueue.get()
            nextChunk = self._bufferConnection.getChunk(nextChunkIndex)

            print(f'Process acquisition {self._pID} : debut acquisition vers Chunk {nextChunkIndex}')
            self._chunkPopulater(self._stream, nextChunk)

            #print(f'DEBUG : Etat Chunk apres passage du Populater {nextChunk[:3,:10]}')

            print(f'Process acquisition {self._pID} : acquisition Chunk {nextChunkIndex} terminee, mise a disposition en cours')
            #self._bufferConnection._freeIndicesQueue.task_done()
            self._bufferConnection._busyIndicesQueue.put(nextChunkIndex)
        # Inaccessible branch