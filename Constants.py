import numpy as np
import psutil

# Ordre par défaut d'énumération np.array : ligne par ligne

#extractedDataType = np.dtype(np.float)
#resultDataType = np.dtype(np.int16)
dataLogging = True # NotImplemented
sentinelValue = None

_nbWorkerProcesses = len(psutil.Process().cpu_affinity()) # 1 (main) process for data acquisition + logging:w
