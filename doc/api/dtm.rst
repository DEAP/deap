.. _dtm-bases:

Distributed Task Manager Overview
=================================

.. deprecated:: 0.9
   DTM will be removed in version 1.0. Please consider using `SCOOP <http://scoop.googlecode.com>`_ instead for distributing your evolutionnary algorithms or other software.

DTM is a distributed task manager which works over many communication layers. Currently, all modern MPI implementations are supported through `mpi4py <http://code.google.com/p/mpi4py/>`_, and an experimental TCP backend is available.

.. warning::
    As on version 0.2, DTM is still in *alpha stage*, meaning that some specific bugs may appear; the communication and operation layers are quite stable, though. Feel free to report bugs and performance issues if you isolate a problematic situation.


DTM Main Features
-----------------

DTM has some very interesting features :

- Offers a similar interface to the Python's multiprocessing module
- Automatically balances the load between workers (and therefore supports heterogeneous networks and different task duration)
- Supports an arbitrary number of workers without changing a byte in the program
- Abstracts the user from the communication management (the same program can be run over MPI, TCP or multiprocessing just by changing the communication manager)
- Provides easy-to-use parallelization paradigms
- Offers a trace mode, which can be used to tune the performance of the running program (still experimental)

Introductory example
--------------------

First, lets take a look to a very simple distribution example. The sequential program we want to parallelize reads as follow : ::
    
    def op(x):
        return x + 1./x     # Or any operation
        
    if __name__ == "__main__":
        nbrs = range(1, 1000)
        results = map(op, nbrs)
    
This program simply applies an arbitrary operation to each item of a list. Although it is a very trivial program (and therefore would not benefit from a parallelization), lets assume we want to distribute the workload over a cluster.
We just import the task manager, and use the DTM parallel version of :func:`map` : ::
    
    from deap import dtm
    
    def op(x):
        return x + 1./x     # Or any operation
    
    def main():
        nbrs = range(1, 1000)
        results = dtm.map(op, nbrs)
    
    dtm.start(main)
    
And we are done! This program can now run over MPI, with an arbitrary number of processors, without changing anything. We just run it like a normal MPI program (here with OpenMPI) ::
    
    $ mpirun -n * python myProgram.py
    
The operation done in the op() function can be virtually any operation, including other DTM calls (which in turn may also spawn sub-tasks, and so on).

.. note::
    The encapsulation of the main execution code into a function is required by DTM, in order to be able to control which worker will start the execution.

Functions documentation
-----------------------
.. automodule:: deap.dtm

.. autoclass:: deap.dtm.manager.Control
    :members:

.. autoclass:: deap.dtm.manager.AsyncResult
    :members:
        
        
DTM launching
-------------

DTM can support many communication environment. The only real restriction on the choice of a communication backend is that is must provide an access from each worker to every other (that is, the worker 0 must be able to directly communicate with all other workers, and so for the worker 1, 2, etc.). Currently, two main backends are available : one using MPI through the `mpi4py <http://code.google.com/p/mpi4py/>`_ layer, and another using TCP (with SSH for the launch process).

If you already have a functionnal MPI installation, you should choose the mpi4py backend, as it can provide better performances in some cases and easier configuration. On the other side, MPI implementations may cause some strange errors when you use low-level system operations (such as fork). In any case, both backends should be ready for production use, and as the backend switch is as easy as changing only one line in your script, this choice should not be an issue.

Launch DTM with the mpi4py backend
++++++++++++++++++++++++++++++++++

When this backend is used, DTM delegates the start-up process to MPI. In this way, any MPI option can be used. For instance : ::
    
    mpirun -n 32 -hostfile myHosts -npernode 4 -bind-to-core python yourScript.py --yourScriptParams ...

Will launch your script on 32 workers, distributed over the hosts listed in 'myHosts', without exceeding 4 workers by host, and will bind DTM workers to a CPU core. The bind-to-core option can provide a good performance improvement in some environments, and does not affect the behavior of DTM at all.


Launch DTM with the pure-TCP backend
++++++++++++++++++++++++++++++++++++

The TCP backend includes a launcher which works with SSH in order to start remote DTM workers. Therefore, your execution environment must provide a SSH access to every host, and a shared file system such as NFS (or, at least, ensure that the script you want to execute and the DTM libraries are located in a common path for every worker). You also have to provide a host file which follows the same synthax as the MPI host files, for instance : ::
    
    firstComputer.myNetwork.com slots=4
    otherComputer.myNetwork.com slots=6
    221.32.118.3 slots=4

.. warning::
    The hostnames / addresses you write in this file must be accessible and translable on every machine used. For instance, putting 'localhost' in this file among other remote hosts **will fail** because each host will try to bind ports for 'localhost' (which will fail, as this is not a network-accessible address).
    
Then you can launch DTM with this file : ::
    
    python myScript.py --dtmTCPhosts=myHostFile
    
.. note::
    Do not forget to explicitly set the communication manager to **deap.dtm.commManagerTCP** : ::
        
        dtm.setOptions(communicationManager="deap.dtm.commManagerTCP")

This backend can also be useful if you want to launch local jobs. If your hostfile contains only 'localhost' or '127.0.0.1', DTM will start all the workers locally, without using SSH.


Troubleshooting and Pitfalls
----------------------------

Here are the most common errors or problems reported with DTM. Some of them are caused by a bad use of the task manager, others are limitations from the libraries and programs used by DTM.

Isolation per worker
++++++++++++++++++++

In DTM, the atomic independent working units are called workers. They are separate processes, and do not share any information other than those from the communications (explicitly called). Therefore, two variables cannot interfere if they are used in different workers, and your program should not rely on this.
Thus, one has to be extremely careful about which data is global, and which is local to a task. For instance, consider the following program : ::
    
    from deap import dtm

    foo = [0]

    def bar(n):
        foo[0] += n
        return foo[0]

    def main():
        listNbr = range(30)
        results = dtm.map(bar, listNbr)
        print("Results : " + str(results))
        
    dtm.start(main)

Although it is syntactically correct, it may not produce the result you are waiting for. On a serial evaluation (using the built-in :func:`map` function), it simply produces a list containing the sums of numbers from 0 to 30 (it is a quite odd approach, but it works) : ::

    Results : [0, 1, 3, 6, 10, 15, 21, 28, 36, 45, 55, 66, 78, 91, 105, 120, 136, 153, 171, 190, 210, 231, 253, 276, 300, 325, 351, 378, 406, 435]

But with DTM, as foo is not shared between workers, the program generate a completely unpredictable output, for instance : ::
    
    Results : [0, 1, 2, 5, 5, 10, 11, 17, 25, 20, 30, 36, 48, 43, 57, 72, 88, 65, 83, 107, 127, 104, 126, 150, 150, 175, 176, 203, 203, 232]
    
The reverse problem should also be taken into account. If an object keeps its state, it is generally not a good idea to make it global (accessible from all tasks). For instance, if you create a log like this : ::
    
    from deap import dtm
    
    logfile = open('myLogFile', 'w+')
    
    def task1(args):
        # [...]
        logfile.write("Log task 1")
        # [...]
    def task2(args):
        # [...]
        logfile.write("Log task 2")
        # [...]
    
    def main():
        listNbr = range(100)
        statusTask1 = dtm.map_async(task1, listNBr)
        statusTask2 = dtm.map_async(task2, listNBr)
        # [...]
    
    dtm.start()

You may experience some unusual outputs, as task1 and task2 writings will probably overlap (because they use the same resource if, by chance, they are executed on the same worker, which will probably happens).
In doubt, use local variables.


Exceptions
++++++++++

When an Python exception occurs during a task execution, DTM catchs it (and try to run another task on this worker). This exception is then raised in the *parent task*. If there is no such task (the task where the exception occurs is the root task), then it is thrown and DTM stops its execution.

The moment when the exception will be raised in the parent tasks depends on the child task type : if it is a synchronous call (like :func:`~deap.dtm.manager.Control.apply` or :func:`~deap.dtm.manager.Control.map`), it is raised when the parent awake (i.e. as if it has been raised by the DTM function itself). If it is an asynchronous call (like :func:`~deap.dtm.manager.Control.apply_async` or :func:`~deap.dtm.manager.Control.map_async`), the exception is raised when the parent task performs a :func:`~deap.dtm.manager.AsyncResult.get` on the :class:`~deap.dtm.manager.AsyncResult` object. Also, the :func:`~deap.dtm.manager.AsyncResult.successful` will return *False* if an exception occured, without raising it.

.. note::
    When DTM catches an exception, it outputs a warning on the standard error output stating the exception type and arguments. This warning does not mean that the exception has been raised in the parent task (actually, in some situations, it may take a lot of time if every workers are busy); it is logged only for information purpose.


MPI and threads
+++++++++++++++

Recent MPI implementations supports four levels of threading : single, funneled, serialized and multiple. However, many environments (like Infiniband backend) do not support other level than single. In that case, if you use the `mpi4py <http://code.google.com/p/mpi4py/>`_ backend, make sure that mpi4py does not initialize MPI environment in another mode than single (as DTM has been designed so that only the communication thread makes MPI calls, this mode works well even if there is more than one active thread in a DTM worker). This setting can be changed in the file "site-packages/mpi4py/rc.py", with the variable `thread_level`.


Cooperative multitasking
++++++++++++++++++++++++

DTM works on a cooperative philosophy. There is no preemption system to interrupt an executing thread (and eventually starts one with a higher priority). When a task begins its execution, the worker will execute it until the task returns or makes a DTM synchronous call, like map or apply. If the task enters an infinite loop or reaches a dead-lock state, then the worker will also be in dead-lock -- it will be able to transfer its other tasks to other workers though. DTM is not a fair scheduler, and thus cannot guarantee any execution delay or avoid any case of starvation; it just tries to reach the best execution time knowing some information about the tasks.


Pickling
++++++++

When dealing with non trivial programs, you may experience error messages like this : ::
    
    PicklingError: Can't pickle <class '__main__.****'>: attribute lookup __main__.**** failed

This is because DTM makes use of the Python :mod:`pickle` module in order to serialize data and function calls (so they can be transferred from one worker to another). Although the pickle module is very powerful (it handles recursive and shared objects, multiple references, etc.), it has some limitations. Most of the time, a pickling error can be easily solved by adding `__setstate__() <http://docs.python.org/library/pickle.html#object.__setstate__>`_ and `__getstate__() <http://docs.python.org/library/pickle.html#object.__getstate__>`_ methods to the problematic class (see the `Python documentation <http://docs.python.org/library/pickle.html#the-pickle-protocol>`_ for more details about the pickling protocol).

This may also be used to accelerate pickling : by defining your own pickling methods, you can speedup the pickling operation (the same way you can speedup the deepcopy operation by defining your own `__deepcopy__()` method. If your program use thousands of objects from the same class, it may be worthwhile.

Take also note of the following Python interpreter limitations :
    
* As on version 2.6, partial functions cannot be pickled. Python 2.7 works fine.
* Lambda functions cannot be pickled in every Python version (up to 3.2). User should use normal functions, or tools from functools, or ensure that its parallelization never need to explicitly transfer a lambda function (not its result, but the lambda object itself) from a worker to another.
* Functions are usually never pickled : they are just referenced, and should be importable in the unpickling environment, even if they are standard functions (defined with the keyword **def**). For instance, consider this (faulty) code : ::
    
    from deap import dtm
    def main():
        def bar(n):
            return n**2
            
        listNbr = range(30)
        results = dtm.map(bar, listNbr)
        
    dtm.start(main)
    
On the execution, this will produce an error like : ::
    
    TypeError: can't pickle function objects

Because the pickler will not be able to find a global reference to the function *bar()*. The same restriction applies on classes and modules.

Asynchronous tasks and active waiting
+++++++++++++++++++++++++++++++++++++

DTM supports both synchronous and asynchronous tasks (that do not stop the parent task). For the asynchronous tasks, DTM returns an object with an API similar to the Python :class:`multiprocessing.pool.AsyncResult`. This object offers some convenient functions to wait on a result, or test if the task is done. However, some issues may appear in DTM with a program like that : ::
    
    from deap import dtm
    def myTask(param):
        # [...] Long treatment
        return param+2
    
    def main():
        listTasks = range(100)
        asyncReturn = dtm.map_async(myTask, listTasks)
        
        while not asyncReturn.ready():
            continue
        
        # Other instructions...
    
    dtm.start(main)

This active waiting (by looping while the result is not available), although syntactically valid, might produce unexpected "half-deadlocks". Keep in mind that DTM is not a preemptive system : if you load a worker only for waiting on another, the load balancer may not work properly. For instance, it may consider that as the parent task is still working, the asynchronous child tasks can still wait, or that one of the child tasks should remain on the same worker than its parent to balance the load between workers. As the load balancer is not completely deterministic, the child tasks should eventually complete, but in an unpredictable time.

It is way better to do something like this : ::
    
    def main():
        listTasks = range(100)
        asyncReturn = dtm.map_async(myTask, listTasks)
        
        asyncReturn.wait()  # or dtm.waitForAll()
        # [...]

By calling one of these functions, you effectively notify DTM that you are now waiting for those asynchronous tasks, and willing to let the worker do another job. The call will then return to your parent function when all the results will be available.
