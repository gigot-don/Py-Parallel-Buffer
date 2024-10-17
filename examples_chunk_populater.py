import numpy as np
import cv2 as cv

class FrameGrayerFromFile(object):
    streamType = cv.VideoCapture
    def __init__(self, parRemainingNumberOfFrames: int = 480):
        self._remainingNumberOfFrames = parRemainingNumberOfFrames
        self._shouldStop = False
    def setPixelIndices(self, parPixelIndices) -> None: # should allow to index a 2D numpy array into a slice with correct number of elements
        self._pixelIndices = parPixelIndices
    def openStream(self, parVideoName) -> streamType:
        stream = FrameReaderFromFile.streamType(parVideoName)
        dummyBool, self._frameBuffer = stream.read() # TODO : initialize framebuffer state without requiring lengthy reinit ? (docs lacking)
        self._grayBuffer = cv.cvtColor(self._frameBuffer, cv.COLOR_BGR2GRAY)
        stream.release()
        return FrameReaderFromFile.streamType(parVideoName)
    def closeStream(self, parStream: streamType):
        parStream.release()
    def shouldStop(self, parStream: streamType) -> bool:
        return self._shouldStop
    def __call__(self, parStream: streamType, parChunk: np.array):
        numberExemplars = parChunk.shape[1] # TODO : redundant after first time

        for relativeFrameIndex in range(min(self._remainingNumberOfFrames, numberExemplars)):
            checkValue, self._frameBuffer = parStream.read(self._frameBuffer)
            if not checkValue:
                print('Acquisition Error : could not receive frame (end of stream ?). Interrupting acquisition...')
                self._shouldStop = True
                break
            parChunk[relativeFrameIndex,:] =  cv.cvtColor(self._frameBuffer, cv.COLOR_BGR2GRAY, self._grayBuffer)
        self._remainingNumberOfFrames -= (relativeFrameIndex-1)
        self._shouldStop = self.shouldStop or self._remainingNumberOfFrames==0

maxOriginalTypeValue = np.uint16(256)
numChannels = 3
dTypeForProjectionStorage: np.dtype = np.min_scalar_type(maxOriginalTypeValue**numChannels) # probably uint32
maxOriginalTypeValue = dTypeForProjectionStorage.type(maxOriginalTypeValue) # Recast in this chosen type for overflows
quantifierBase = dTypeForProjectionStorage.type(8)
quantifierPowers = np.fromiter((quantifierBase**i for i in range(numChannels)), dtype=dTypeForProjectionStorage)
def _projectOriginalPixelToCompressedValue(parPixel: np.array) -> dTypeForProjectionStorage.type:
    return ((quantifierBase*parPixel)//maxOriginalTypeValue)@quantifierPowers
_vectorizedProjection: np.ufunc = np.frompyfunc(_projectOriginalPixelToCompressedValue, 1, 1, identity=0)
maxProjectedValue = quantifierBase**numChannels - 1

class FrameReaderFromFile(object):
    streamType = cv.VideoCapture
    def __init__(self, parRemainingNumberOfFrames: int = 480):
        self._remainingNumberOfFrames = parRemainingNumberOfFrames
        self._shouldStop = False
        self._rng = np.random.default_rng(np.random.SFC64())
    def setPixelIndices(self, parPixelIndices) -> None: # should allow to index a 2D numpy array into a slice with correct number of elements
        self._pixelIndices = parPixelIndices
    def openStream(self, parVideoName) -> streamType:
        stream = FrameReaderFromFile.streamType(parVideoName)
        dummyBool, self._frameBuffer = stream.read() # TODO : initialize framebuffer state without requiring lengthy reinit ? (docs lacking)
        recastBuffer = self._frameBuffer.astype(dTypeForProjectionStorage)
        recastBuffer = recastBuffer
        self._projectionBuffer = np.dot(recastBuffer, quantifierPowers)
        self._flatProjectionView = self._projectionBuffer[:] # is a VIEW on _projectionBuffer, not another name
        self._flatProjectionView.shape = -1
        self._nbFramesRead = 0
        self._totalFramesAvailable = int(stream.get(cv.CAP_PROP_FRAME_COUNT))
        stream.release()
        return FrameReaderFromFile.streamType(parVideoName)
    def closeStream(self, parStream: streamType):
        parStream.release()
    def shouldStop(self, parStream: streamType) -> bool:
        #print(f'From populater : should i stop ? {self._shouldStop}')
        return self._shouldStop
    def __call__(self, parStream: streamType, parChunk: np.array):
        numberExemplars = parChunk.shape[0] # TODO : redundant after first time

        for relativeFrameIndex in range(min(self._remainingNumberOfFrames, numberExemplars)):
            checkValue, self._frameBuffer = parStream.read(self._frameBuffer)
            #print(f'DEBUG : Debut de frame en sortie de cv2 {self._frameBuffer[0, :10, :]}')
            self._nbFramesRead += 1
            if not checkValue:
                print('Acquisition Error : could not receive frame (end of stream ?). Interrupting acquisition...')
                self._shouldStop = True
                break
            #### DEBUG
            #print(f'projection dims {self._flatProjectionView.shape} dtype {self._flatProjectionView.dtype}')
            #print(f'frame dims {self._frameBuffer.shape} dtype {self._flatProjectionView.dtype} / quantif {quantifierPowers.shape} {quantifierPowers.dtype}')
            #print(f'dot dims {np.dot(self._frameBuffer, quantifierPowers).shape} type {np.dot(self._frameBuffer, quantifierPowers).dtype}')
            #print(f'DEBUG : avant multiplication quantifierBase {quantifierBase};{quantifierBase.dtype} - debut frame {self._frameBuffer[:, :10, :]};{self._frameBuffer.dtype}')
            recastBuffer = self._frameBuffer.astype(dTypeForProjectionStorage) * quantifierBase
            #print(f'DEBUG : Debut de frame post-multiplication par quantifieur {recastBuffer[0, :10, :]}')
            noiseArray = np.round(self._rng.normal(scale=self._stdDev, size=self._frameBuffer.shape)).astype(dTypeForProjectionStorage)
            recastBuffer = recastBuffer + quantifierBase*noiseArray
            recastBuffer[recastBuffer >10000] = 0
            np.minimum(recastBuffer, dTypeForProjectionStorage.type((quantifierBase-1)*maxOriginalTypeValue), out=recastBuffer)
            assert maxOriginalTypeValue==256
            recastBuffer >>= 8 # correct for integer division as long as the previous assert holds
            #print(f'DEBUG : Debut de frame post-decalage {recastBuffer[0, :10, :]}')
            #print(f'DEBUG : quantifierPowers {quantifierPowers}')
            np.dot(recastBuffer, quantifierPowers, self._projectionBuffer)
            #print(f'DEBUG : Debut de frame post-quantification {self._projectionBuffer[0, :10]}')
            #print(f'DEBUG : Debut de frame quantifiee en vue aplatie {self._flatProjectionView[:10]}')
            #outView = parChunk[relativeFrameIndex,:]
            #print(f'outChunk dims {outView.shape} dtype {outView.dtype}')
            #print(f'projection dims {self._flatProjectionView.shape} dtype {self._flatProjectionView.dtype}')
            ####
            parChunk[relativeFrameIndex,:] = self._flatProjectionView
        self._remainingNumberOfFrames -= (relativeFrameIndex+1)
        #print(f'Acquisition task : Should stop because of error {self._shouldStop}')
        #print(f'Acquisition task : {self._remainingNumberOfFrames} frames remaining')
        #print(f'Acquisition task : Should stop because data gathered {self._remainingNumberOfFrames==0}')
        print(f'[Frame Counter] Read/Total : {self._nbFramesRead}/{self._totalFramesAvailable} -- Remaining : {self._remainingNumberOfFrames} ')
        self._shouldStop = self._shouldStop or (self._remainingNumberOfFrames<=0)