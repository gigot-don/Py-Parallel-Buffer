import psutil
from .Buffers import BufferPool, _computeSizeOfChunk
from . import Constants
from numpy import dtype, prod

def getNumberAvailableCores() -> int:
    return len(psutil.Process().cpu_affinity())
def getAvailableRAMInBytes() -> int:
    return psutil.virtual_memory().available

class BufferSetupParams(object):
    def setNumberElemsInVector(self, parNb: int) -> None:
        self._numberElemsInVector = parNb
    def setDataDType(self, parDType: dtype) -> None:
        self._dataDType = parDType
    def setResultShape(self, parShape: tuple) -> None:
        self._resultShape = parShape
    def setResultDType(self, parDType: dtype) -> None:
        self._resultDType = parDType
    def setNumberExemplarsInChunk(self, parNb: int) -> None:
        self._numberExemplarsInChunk = parNb
    def setNumberChunks(self, parNb: int = 2*Constants._nbWorkerProcesses) -> None:
        self._numberChunks = parNb

    def calcNumberChunksToFit(self) -> None:
        if hasattr(self, '_numberChunks'):
            print('Number of Chunks was already supplied, overwriting...')
        if not hasattr(self, '_dataDType'):
            print('Cannot compute suitable number of chunks for buffer: missing data type.')
            return
        if not hasattr(self, '_numberExemplarsInChunk'):
            print('Cannot compute suitable number of chunks for buffer: missing number of exemplars.')
            return
        if not hasattr(self, '_numberElemsInVector'):
            print('Cannot compute suitable number of chunks for buffer: missing number of elements in vector.')
            return

        memAvailable = getAvailableRAMInBytes()
        sizeOfChunk = _computeSizeOfChunk(self._dataDType, self._numberElemsInVector, self._numberExemplarsInChunk)
        nbMaxProcesses = Constants._nbWorkerProcesses
        sizeHintOfResult = 0
        if hasattr(self, '_resultShape') and hasattr(self, '_resultDType'):
            sizeHintOfResult = self._resultDType.itemsize*prod(self._resultShape)
        else:
            print('Missing information about results memory footprint to adjust chunk allocation: risks of overloading memory capacity during processing...')

        maxNumChunksInRam = memAvailable//(sizeOfChunk+sizeHintOfResult)
        if maxNumChunksInRam>2*nbMaxProcesses:
            print('Memory Allocation Info : could allocate maximum number of Chunks')
            self._numberChunks = 2*nbMaxProcesses
        else:
            self._numberChunks = maxNumChunksInRam
            if maxNumChunksInRam<nbMaxProcesses:
                print('Memory Allocation Warning (Critical) : cannot allocate 1 desired chunk per available core, insufficient memory.\nRestricting number of chunks to fit available RAM...')
        if memAvailable-(maxNumChunksInRam*(sizeOfChunk+sizeHintOfResult))<sizeHintOfResult:
            print('Memory Allocation Info : reduced number of Chunks by 1 to preserve space for results processing')
            self._numberChunks = self._numberChunks-1
        print(f'Final number of Chunks : {self._numberChunks}')

    def calcNumberExemplarsToFit(self, parMaxNumExemplars: int = 0) -> None: # TODO : could do with some refactoring, see similarity of calcNumberChunksToFit
        if hasattr(self, '_numberExemplarsInChunk'):
            print('Number of exemplars in Chunk was already supplied, overwriting...')
        if not hasattr(self, '_dataDType'):
            print('Cannot compute suitable number of exemplars for buffer: missing type data.')
            return
        if not hasattr(self, '_numberChunks'):
            print('Cannot compute suitable number of exemplars for buffer: missing number of chunks.')
            return
        if not hasattr(self, '_numberElemsInVector'):
            print('Cannot compute suitable number of exemplars for buffer: missing number of elements in vector.')
            return

        memAvailable = getAvailableRAMInBytes()
        sizePerExemplar = self._numberChunks*self._numberElemsInVector*self._dataDType.itemsize
        sizeHintOfResult = 0
        if hasattr(self, '_resultShape') and hasattr(self, '_resultDType'):
            sizeHintOfResult = self._resultDType.itemsize*prod(self._resultShape)
        else:
            print('Missing information about results memory footprint to adjust chunk allocation: risks of overloading memory capacity during processing...')

        maxNumExemplars = (memAvailable - (self._numberChunks+1)*sizeHintOfResult)//sizePerExemplar
        if maxNumExemplars<parMaxNumExemplars:
            print('Memory Allocation Info : could not allocate supplied number of exemplars, insufficient memory.')
            self._numberExemplarsInChunk = maxNumExemplars
        else:
            print('Memory Allocation Info : setting number of exemplars to supplied value (some overhead may be available).')
            self._numberExemplarsInChunk = parMaxNumExemplars
        
        print(f'Final number of Exemplars : {self._numberExemplarsInChunk}')
    
    def _checkForSetup(self) -> bool:
        res = True
        attribs = (('_numberElemsInVector', 'number of elements in vector'), ('_dataDType', 'data type'), ('_resultShape', 'shape of result array'), ('_resultDType', 'result type'), ('_numberExemplarsInChunk', 'number of exemplars'), ('_numberChunks', 'number of chunks'))
        for att in attribs:
            if not hasattr(self, att[0]):
                print('Memory Allocation Warning (Critical) : setup params incomplete, lacking information for ' + att[1])
                res = False
        return res
    
    def generateBufferPool(self) -> BufferPool:
        if not self._checkForSetup:
            raise ValueError
        print(f'Buffer setup parameters : Data type {self._dataDType} - num Elems in Vector {self._numberElemsInVector} - num Exemplars in Chunk {self._numberExemplarsInChunk} - num Chunks {self._numberChunks} - result shape {self._resultShape} - result type {self._resultDType}')
        return BufferPool(self._dataDType, self._numberElemsInVector, self._numberExemplarsInChunk, self._numberChunks, self._resultShape, self._resultDType)