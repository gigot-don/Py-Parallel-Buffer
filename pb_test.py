import numpy as np
import sys
sys.path.append('..') # provides path if test is run from WD parallel_buffer/
sys.path.append('.') # provides path if test from outside parallel_buffer/
import parallel_buffer as pb

if __name__=="__main__":
    s = pb.BufferSetupParams()

    # Mandatory setup params
    s.setDataDType(np.dtype(np.uint8))
    s.setResultDType(np.dtype(np.float64))
    s.setResultShape((3,3))
    s.setNumberElemsInVector(100)

    # One of the two last params must be set ; other can be determined to best fit available resources
    s.setNumberChunks() # set to an upper sensible bound from the number of processors available to the Python interpreter (see "Constants" module)
    s.calcNumberExemplarsToFit(1000) # auto sets last param, with upper bound supplied (see docs)

    bufferPool = s.generateBufferPool() # all configured via data supplied to s (helper)

    # Create the tasks (both acquisition and processing) backed by the memory buffer
    dataGetter = pb.DataGetter(bufferPool)
    processingPool = pb.WorkerProcessesPool(bufferPool)

# Define their operation functions (should be put in separate file)
# These functions characterize their properties (e.g. what modality (video, audio...) and what
# type of input stream (disk file, live device...) DataGetter will deal with)
class dummyPopulater(object):
    # Does not actually gets data, but only operates for 10 chunks before requesting shutdown
    def __init__(self):
        self._countdown = 30
        self._x = 1
    def openStream(self, parStreamDescriptor) -> None:
        print('Stream ouvert... haha non je t ai eu !')
        return None
    def closeStream(self, parStream) -> None:
        print('Stream ferme, c etait pas trop complique.')
    def __call__(self, parStream, parChunkArray) -> None:
        self._countdown = self._countdown - 1
        for i in range(1000):
            self._x += 1
        print(f'Feu d artifice dans {self._countdown}')
    def shouldStop(self, parStream):
        return self._countdown==0
oyThatIsSomeIntricateMachinery = dummyPopulater()

def theMostImpactfulFunction(iDontCare, whyDoYou): pass # all argument functions of WorkerProcessesPool take exactly 2 arguments
# what these arguments are (and their order) differ however, see docs
def butWontYouWaitSomeTime(whatThis, whoThat):
    x = 1
    for i in range(10000000):
        x += 1

if __name__=='__main__':
    # Assign these behavior parameters to the tasks
    dataGetter.setStreamDescriptor('idk')
    dataGetter.setChunkPopulater(oyThatIsSomeIntricateMachinery)

    processingPool.setPartialResultArrayShape((2,1))
    processingPool.setPartialResultDType(np.dtype(np.int16))
    processingPool.setProcessFunction(butWontYouWaitSomeTime)
    processingPool.setContributeResultsFunction(theMostImpactfulFunction)
    processingPool.setCleanUpFunction(theMostImpactfulFunction)

    # Launch tasks (asynchroneously)
    # To change : dataGetter being sync means it blocks all other launches
    processingPool.initiateWorkers()
    dataGetter.run()

    # Wait for end of tasks (which will necessarily be that of processing)
    processingPool.waitForAllProcesses()

