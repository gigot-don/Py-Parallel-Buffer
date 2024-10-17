
import numpy as np
import sys
sys.path.append('..') # provides path if test is run from WD parallel_buffer/
sys.path.append('.') # provides path if test from outside parallel_buffer/
import parallel_buffer as pb
import examples_chunk_populater as pop
import examples_processing_functions as proc
import cv2

if __name__=="__main__":
    # Experimental constants
    dataPath = 'videos/colors.mp4'
    numberOfFramesToAnalyze = 1000
    noiseVariance = 100

    dummyCap = cv2.VideoCapture(dataPath)
    numPixelsInFrame = int(dummyCap.get(cv2.CAP_PROP_FRAME_WIDTH)*dummyCap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    del dummyCap

    s = pb.BufferSetupParams()

    # Mandatory setup params
    s.setDataDType(pop.dTypeForProjectionStorage)
    s.setResultDType(np.min_scalar_type(numberOfFramesToAnalyze* numPixelsInFrame))
    s.setResultShape((pop.maxProjectedValue+1, pop.maxProjectedValue+1))
    s.setNumberElemsInVector(numPixelsInFrame)

    # One of the two last params must be set ; other can be determined to best fit available resources
    s.setNumberChunks() # set to an upper sensible bound from the number of processors available to the Python interpreter (see "Constants" module)
    s.calcNumberExemplarsToFit(20) # auto sets last param, with upper bound supplied (see docs)

    bufferPool = s.generateBufferPool() # all configured via data supplied to s (helper)

    # Create the tasks (both acquisition and processing) backed by the memory buffer
    dataGetter = pb.DataGetter(bufferPool)
    processingPool = pb.WorkerProcessesPool(bufferPool)

    populaterInstance = pop.FrameReaderFromFile(numberOfFramesToAnalyze)
    populaterInstance._stdDev = noiseVariance

    # Assign these behavior parameters to the tasks
    dataGetter.setStreamDescriptor(dataPath)
    dataGetter.setChunkPopulater(populaterInstance)

    processingPool.setPartialResultArrayShape((pop.maxProjectedValue+1, pop.maxProjectedValue+1))
    processingPool.setPartialResultDType(pop.dTypeForProjectionStorage)
    processingPool.setProcessFunction(proc.processChunkFunctionBetter)
    processingPool.setContributeResultsFunction(proc.contributeResult)
    processingPool.setCleanUpFunction(proc.cleanUpFunction)

    # Launch tasks (asynchroneously)
    # To change : dataGetter being sync means it blocks all other launches
    processingPool.initiateWorkers()
    dataGetter.run()

    # Wait for end of tasks (which will necessarily be that of processing)
    processingPool.waitForAllProcesses()

    np.save('resultat-'+str(noiseVariance), np.ndarray(bufferPool._resultShape, bufferPool._resultDType, bufferPool._resultSharedMemory.buf))

