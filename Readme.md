# Parallel Buffer

Python package that provides utilities for programmable simultaneous (multicore) data acquisition and processing.

## Getting Started

These instructions will get you a copy of the project up and running on your
local machine for development and testing purposes. See deployment for notes on
how to deploy the project on a live system.

### Prerequisites

- [Python 3.8+](https://www.python.org/downloads/) (necessary for the SharedMemory standard module)
- Python packages :
  - [numpy](https://numpy.org/)
  - [psutil](https://github.com/giampaolo/psutil)

Run (`python --version` to check whether "python" in the PATH refers to your Python3.8+ install; replace by "python3" if you maintain instances of both Python2 and Python3)
```
python -m pip install psutil
python -m pip install numpy
```

### Testing

A test module `pb_test.py` is provided at the root level of the package.

Running the test (from either parallel_buffer/ or its parent directory):
```
python pb_test.py
```
Check the console for standard output, it should end with "Worker processes have all exited successfully"

## Usage and Modules

### General flow

Parallel Buffer manages the concurrent execution of data acquisition and processing tasks (via its `DataGetter` and `WorkerProcessesPool` objects). It also provides a managed shared buffer (`BufferPool`) to store said data and allow for efficient interprocess communication.

Practical use cases generally follow the pattern :
- Setup `BufferPool` buffer by providing format parameters such as :
  * Numerical type of the stored elements
  * 2D Dimensions of an atomic *chunk* of the buffer (i.e. one that can be exclusively borrowed by any single task)
  * Number of chunks
  * Format for a shared output region
- Setup `DataGetter` acquisition and `WorkerProcessesPool` processing tasks with :
  * storage backend provided by the previous `BufferPool` object
  * programmable behavior via setter methods accepting any `Callable` object
- Start non-blocking execution of both tasks with calls to `DataGetter.run` and `WorkerProcessesPool.initiateWorkers`
- ...
- When code flow asks for the output of processing, it can be waited for with a call to `WorkerProcessesPool.waitForAllProcesses`.

At the setup stage, a convention hint is that all required parameters `X` of `DataGetter` and `WorkerProcessesPool` can be adjusted via corresponding `setX` instance methods.

#### Buffer structure

A `BufferPool` main shared storage is defined by its parameters :

--- TODO ---



<!--### Break down into end to end tests

Explain what these tests test and why

```
Give an example
```

### And coding style tests

Explain what these tests test and why

```
Give an example
```

## Deployment

Add additional notes about how to deploy this on a live system

## Built With

* [Dropwizard](http://www.dropwizard.io/1.0.2/docs/) - The web framework used
* [Maven](https://maven.apache.org/) - Dependency Management
* [ROME](https://rometools.github.io/rome/) - Used to generate RSS Feeds

## Contributing

Please read
[CONTRIBUTING.md](https://gist.github.com/PurpleBooth/b24679402957c63ec426) for
details on our code of conduct, and the process for submitting pull requests to
us.

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available,
see the [tags on this repository](https://github.com/your/project/tags). 

## Authors

* **Billie Thompson** - *Initial work* -
* [PurpleBooth](https://github.com/PurpleBooth)

See also the list of
[contributors](https://github.com/your/project/contributors) who participated in
this project.

## License

This project is licensed under the MIT License - see the
[LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Hat tip to anyone whose code was used
* Inspiration
* etc


---> 