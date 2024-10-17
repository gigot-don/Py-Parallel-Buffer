from multiprocessing import shared_memory, Lock, Queue
from numpy import ndarray, dtype, prod
from . import Constants

#class LockGuard(object):
#    def __init__(self, parLock: Lock):
#        parLock.acquire()
#        self._lock = parLock
#    
#    def __del__(self):
#        self._lock.release()

def _computeSizeOfChunk(parDType: dtype, parNumberElemsInVector: int, parNumberExemplarsInChunk: int) -> int:
    return parDType.itemsize*parNumberElemsInVector*parNumberExemplarsInChunk

def _computeSizeOfAllocInBytes(parDType: dtype, parNumberElemsInVector: int, parNumberExemplarsInChunk: int, parNumberChunks: int) -> int:
    return _computeSizeOfChunk(parDType, parNumberElemsInVector, parNumberExemplarsInChunk)*parNumberChunks

# DEPRECATED : see BufferPool._BufferConnection.getChunk(...)
#def borrowChunk(parChunkShape: tuple, parDType: dtype, parSharedMemoryBuffer: memoryview, parSizeOfChunk: int, parChunkIndex: int):
#    return ndarray(parChunkShape, dtype=parDType, buffer=parSharedMemoryBuffer[parChunkIndex*parSizeOfChunk:(parChunkIndex+1)*parSizeOfChunk])


class BufferPool(object):
    
    def _getDataSharedMemoryID(self):
        return self._dataSharedMemory.name

    def _getResultSharedMemoryID(self):
        return self._resultSharedMemory.name

    def __init__(self, parDType: dtype, parNumberElemsInVector: int, parNumberExemplarsInChunk: int, parNumberChunks: int, parResultShape : tuple, parResultDType: dtype):
        self._dataSharedMemory = shared_memory.SharedMemory(create=True, size=_computeSizeOfAllocInBytes(parDType, parNumberElemsInVector, parNumberExemplarsInChunk, parNumberChunks))
        self._resultSharedMemory = shared_memory.SharedMemory(create=True, size=int(prod(parResultShape)*parResultDType.itemsize)) 
        self._dType = parDType
        self._resultDType = parResultDType
        self._numberElemsInVector = parNumberElemsInVector
        self._numberExemplarsInChunk = parNumberExemplarsInChunk
        self._numberChunks = parNumberChunks
        self._resultShape = parResultShape

        self._freeIndicesQueue = Queue()
        self._busyIndicesQueue = Queue()

        for chunkIndex in range(parNumberChunks):
            self._freeIndicesQueue.put(chunkIndex) # All chunks are free to receive incoming data at start

        self._resultLock = Lock()

        #self._connectionLock = Lock()
        #self._connectionLock.acquire()
        #self._connectionCounter = 1
        #self._connectionLock.release()
        
    def __del__(self):
        self._dataSharedMemory.close()
        self._resultSharedMemory.close()
        #self._connectionLock.acquire()
        #self._connectionCounter
        #self._connectionLock.release()

        #if self._connectionCounter != 0:
        #    print('Erreur : destruction du pool de memoire partagee alors que des connexions restaient ouvertes !')
        #    raise Exception
        self._dataSharedMemory.unlink()
        self._resultSharedMemory.unlink()

    class _BufferConnection(object):
        def _openConnection(self):
            self._dataSharedMemory = shared_memory.SharedMemory(create=False, name=self._dataSharedMemoryName)
            self._resultSharedMemory = shared_memory.SharedMemory(create=False, name=self._resultSharedMemoryName)
            self._isOpen = True
            del self._dataSharedMemoryName
            del self._resultSharedMemoryName
        
        def __init__(self, parDataSharedMemoryName, parResultSharedMemoryName, parDType: dtype, parResultDType: dtype, parResultShape, parNumberElemsInVector: int, parNumberExemplarsInChunk: int, parFreeQueue: Queue, parBusyQueue: Queue, parResultLock: Lock):
            self._dataSharedMemoryName = parDataSharedMemoryName
            self._resultSharedMemoryName = parResultSharedMemoryName
            self._isOpen = False
            self._dType = parDType
            self._resultDType = parResultDType
            self._resultShape = parResultShape
            self._chunkShape = (parNumberExemplarsInChunk, parNumberElemsInVector)
            self._chunkSize = _computeSizeOfChunk(parDType, parNumberElemsInVector, parNumberExemplarsInChunk)
            self._freeIndicesQueue = parFreeQueue
            self._busyIndicesQueue = parBusyQueue
            self._resultLock = parResultLock
        
        def getChunk(self, parChunkIndex: int) -> ndarray:
            startIndex = self._chunkSize*parChunkIndex
            return ndarray(shape=self._chunkShape, dtype=self._dType, buffer=self._dataSharedMemory.buf[startIndex:startIndex+self._chunkSize])

        def __del__(self):
            if self._isOpen:
               self._dataSharedMemory.close()
               self._resultSharedMemory.close()
               # TODO décrémenter _connectionCounter du BufferPool, mais interprocess ??

    def borrowConnection(self) -> _BufferConnection:
        return self._BufferConnection(self._getDataSharedMemoryID(), self._getResultSharedMemoryID(), self._dType, self._resultDType, self._resultShape, self._numberElemsInVector, self._numberExemplarsInChunk, self._freeIndicesQueue, self._busyIndicesQueue, self._resultLock)

    