#    This file is part of DEAP.
#
#    DEAP is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation, either version 3 of
#    the License, or (at your option) any later version.
#
#    DEAP is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with DEAP. If not, see <http://www.gnu.org/licenses/>.

import mpi
import Queue
import time
import threading

DTM_MPI_LATENCY = 0.1

class DtmCommThread(threading.Thread):

    def __init__(self, recvQ, sendQ, exitEvent, commReadyEvent):
        threading.Thread.__init__(self)
        self.recvQ = recvQ
        self.sendQ = sendQ
        self.pSize = mpi.size
        self.currentId = mpi.rank
        self.exitStatus = exitEvent
        self.countSend = 0
        self.countRecv = 0
        commReadyEvent.set()         # On doit notifier le thread principal qu'on est pret
        
    @property
    def poolSize(self):
        return self.pSize

    @property
    def workerId(self):
        return self.currentId

    @property
    def isRootWorker(self):
        return self.currentId == 0

    def iterOverIDs(self):
        return xrange(self.pSize)

    def run(self):
        recvAsync = mpi.irecv()
        working = True

        while working:
            recvSomething = False
            sendSomething = False

            if self.exitStatus.is_set():    # On quitte
                # Note importante : le thread de communication DOIT vider la sendQ
                # AVANT de quitter (les ordres de quit doivent etre envoyes)
                working = False
                time.sleep(2)
	    
            if recvAsync:
                # On a recu quelque chose
                self.recvQ.put(recvAsync.message)
                recvAsync = mpi.irecv()
                self.countRecv += 1
                recvSomething = True

            while True:
                # On envoie tous les messages
                try:		    
                    sendMsg = self.sendQ.get_nowait()
                    mpi.isend(sendMsg[1], sendMsg[0])
                    sendSomething = True
                    self.countSend += 1
                except Queue.Empty:
                    break

            if not recvSomething:
                time.sleep(DTM_MPI_LATENCY)
        
        print("/////////////////////", mpi.rank, self.countSend, self.countRecv)