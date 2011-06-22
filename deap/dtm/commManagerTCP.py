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

from multiprocessing.connection import Client,Listener
import Queue
import time
import threading
import sys
import os
import socket
import subprocess

DTM_TCP_MIN_LATENCY = 0.005
DTM_TCP_MAX_LATENCY = 0.01
DTM_CONCURRENT_RECV_LIMIT = 1000
DTM_CONCURRENT_SEND_LIMIT = 1000

# Les communications par multiprocessing.connection ont le defaut
# de demander enormement de connexions (1 entre chaque paire de workers)
# soit au total n*(n-1)/2 connexions ouvertes pour n workers
# Les ports sont automatiquement attribues a partir du numero ci-dessous
BASE_COMM_PORT = 10011

class DtmCommThread(threading.Thread):
    
    def __init__(self, recvQ, sendQ, mainThreadEvent, exitEvent, commReadyEvent, randomGenerator, cmdlineArgs):
        threading.Thread.__init__(self)
        self.recvQ = recvQ
        self.sendQ = sendQ
        
        self.exitStatus = exitEvent
        self.wakeUpMainThread = mainThreadEvent
        self.random = randomGenerator
        self.commReadyEvent = commReadyEvent
        
        self.cmdArgs = cmdlineArgs
        
        self.traceMode = False
        self.traceTo = None

        self.props = dict(dtmTCPGlobalLaunch = True, 
                        dtmTCPLocalLaunch = False, 
                        dtmTCPLineNo = -1, 
                        dtmTCPhosts = '', 
                        dtmTCPstartPort = BASE_COMM_PORT, 
                        dtmTCPnPortsByHost = -1,
                        dtmTCPnbrWorkers = -1,
                        dtmTCPmaxWorkersByHost = -1,
                        dtmTCPisRootWorker = False)
                        
        self.userArgs = ""
        indexArg = 1
        while indexArg < len(cmdlineArgs):
            keyDataF = cmdlineArgs[indexArg][2:].split('=')
            if keyDataF[0] in self.props.keys():
                self.props[keyDataF[0]] = keyDataF[1]
            else:
                self.userArgs += cmdlineArgs[indexArg] + " "
            indexArg += 1
        if self.props['dtmTCPhosts'] == '':
            cmdlineArgs = cmdlineArgs[1].split(' ')
            self.userArgs = ""
            indexArg = 1
            while indexArg < len(cmdlineArgs):
                keyDataF = cmdlineArgs[indexArg][2:].split('=')
                if keyDataF[0] in self.props.keys():
                    self.props[keyDataF[0]] = keyDataF[1]
                else:
                    self.userArgs += cmdlineArgs[indexArg] + " "
                indexArg += 1
        
    @property
    def poolSize(self):
        return len(self.tabConn)+1      # +1 parce que nous n'avons pas de connexion avec nous-memes

    @property
    def workerId(self):
        return (self.workerHost, self.workerHostId)

    @property
    def isRootWorker(self):
        return bool(int(self.props['dtmTCPisRootWorker']))
        
    @property
    def isLaunchProcess(self):
        return bool(int(self.props['dtmTCPGlobalLaunch'])) or bool(int(self.props['dtmTCPLocalLaunch']))

    def iterOverIDs(self):
        return self.tabConn.keys() + [self.workerId]
    
    def setTraceModeOn(self, xmlLog):
        # Profiling is not currently enabled with TCP
        return
    
    def _createListener(self, remoteInfo):
        tmpListener = Listener(remoteInfo)
        return tmpListener.accept()
    
    def _createClient(self, remoteInfo):
        return Client(remoteInfo)
    
    def run(self):
        # On check si on execute vraiment DTM ou si on est seulement un lanceur
        if int(self.props['dtmTCPGlobalLaunch']):
            # Lanceur global. On cree une connexion SSH avec chaque host pour
            # executer un lanceur local, puis on se met en attente
            sshWait = []
            lineTab = []
            maxWorkersByHost = 1
            totalWorkers = 0
            #print(self.props['dtmTCPGlobalLaunch'], self.props['dtmTCPLocalLaunch'])
            #print('>>>>',self.props['dtmTCPhosts'])
            try:
                with open(self.props['dtmTCPhosts']) as hostFile:
                    for line in hostFile:
                        if line[0] == '#' or line[0] == '\n' or line[0] == '\r':
                            continue
                        lineTab.append(line.replace("\n", "").replace("\r", "").split(" "))
                        totalWorkers += int(lineTab[-1][1].split("=")[1])
                        if int(lineTab[-1][1].split("=")[1]) > maxWorkersByHost:
                            maxWorkersByHost = int(lineTab[-1][1].split("=")[1])
                        
                    # Pour le moment, si on utilise localhost, on va quand meme ouvrir une connexion locale
                    # Pas trop trop efficace, mais bon
                    for lineCount,hostH in enumerate(lineTab):
                        #print(hostH[0], self.props['dtmTCPhosts'], self.cmdArgs[0])
                        #print(["/usr/bin/ssh", "-x", hostH[0], "cd "+"" +";", "python"+\
                                    #str(sys.version_info[0])+"."+str(sys.version_info[1])+" " + self.cmdArgs[0] +\
                                    #" --dtmTCPGlobalLaunch=0 --dtmTCPLocalLaunch=1 --dtmTCPLineNo="+str(lineCount) +\
                                    #" --dtmTCPhosts=" + str(self.props['dtmTCPhosts']) + " --dtmTCPnPortsByHost=" + str(maxWorkersByHost*(totalWorkers-1)) +\
                                    #" --dtmTCPstartPort="+ str(self.props['dtmTCPstartPort']) + " --dtmTCPnbrWorkers="+str(hostH[1].split("=")[1])+\
                                    #" --dtmTCPmaxWorkersByHost="+ str(maxWorkersByHost)+" "+ self.userArgs])
                        sshWait.append(subprocess.Popen(["/usr/bin/ssh", "-x", hostH[0], "cd "+"/gel/usr/magar207/deap_workon/deap/dtm/tests" +";", "python"+\
                                    str(sys.version_info[0])+"."+str(sys.version_info[1])+" " + self.cmdArgs[0] +\
                                    " --dtmTCPGlobalLaunch=0 --dtmTCPLocalLaunch=1 --dtmTCPLineNo="+str(lineCount) +\
                                    " --dtmTCPhosts=" + str(self.props['dtmTCPhosts']) + " --dtmTCPnPortsByHost=" + str(maxWorkersByHost*(totalWorkers-1)) +\
                                    " --dtmTCPstartPort="+ str(self.props['dtmTCPstartPort']) + " --dtmTCPnbrWorkers="+str(hostH[1].split("=")[1])+\
                                    " --dtmTCPmaxWorkersByHost="+ str(maxWorkersByHost)+" "+ self.userArgs], stdout=sys.stdout, stderr=sys.stderr))
                        #sshWait.append(subprocess.Popen(["/usr/bin/ssh", "-x", hostH[0], "cd "+str(os.getcwd())+";", "python2.7 boumpaf.py"], stdout=sys.stdout, stderr=sys.stderr))
                        #sshWait.append(subprocess.Popen(["/usr/bin/ssh", "-x", hostH[0], "cd /gel/usr/magar207/deap_workon/examples; python2.7 gp_ant.py"], stdout=sys.stdout, stderr=sys.stderr))
            except IOError:
                raise AssertionError, str(sys.argv)
           
            for connJob in sshWait:
                connJob.wait()
            self.commReadyEvent.set()
            return
        elif int(self.props['dtmTCPLocalLaunch']):
            # Lanceur local. On utilise subprocess.popen pour lancer les
            # "vraies" instances de DTM, puis on se met en attente
            dtmLocalWorkersList = []
            
            #currentBasePort = int(self.props['dtmTCPstartPort'])
            for i in range(int(self.props['dtmTCPnbrWorkers'])):
                #sys.stdout.write(str(["apython"+str(sys.version_info[0])+"."+str(sys.version_info[1]), self.cmdArgs[0],
                        #" --dtmTCPGlobalLaunch=0 --dtmTCPLocalLaunch=0 --dtmTCPLineNo="+str(self.props['dtmTCPLineNo']) +\
                        #" --dtmTCPhosts=" + str(self.props['dtmTCPhosts']) + " --dtmTCPnPortsByHost=" + str(self.props['dtmTCPnPortsByHost']) +\
                        #" --dtmTCPstartPort="+ str(self.props['dtmTCPstartPort']) + " --dtmTCPnbrWorkers="+str(i)+\
                        #" --dtmTCPmaxWorkersByHost="+ str(self.props['dtmTCPmaxWorkersByHost']) +" --dtmTCPisRootWorker=1", self.userArgs]) + "\n\n")
                #sys.stdout.flush()
                #sys.stderr.flush()
                
                if i == 0 and int(self.props['dtmTCPLineNo']) == 0:
                    dtmLocalWorkersList.append(subprocess.Popen(["python"+str(sys.version_info[0])+"."+str(sys.version_info[1]), self.cmdArgs[0],
                        " --dtmTCPGlobalLaunch=0 --dtmTCPLocalLaunch=0 --dtmTCPLineNo="+str(self.props['dtmTCPLineNo']) +\
                        " --dtmTCPhosts=" + str(self.props['dtmTCPhosts']) + " --dtmTCPnPortsByHost=" + str(self.props['dtmTCPnPortsByHost']) +\
                        " --dtmTCPstartPort="+ str(self.props['dtmTCPstartPort']) + " --dtmTCPnbrWorkers="+str(i)+\
                        " --dtmTCPmaxWorkersByHost="+ str(self.props['dtmTCPmaxWorkersByHost']) +" --dtmTCPisRootWorker=1", self.userArgs]))
                else:
                    dtmLocalWorkersList.append(subprocess.Popen(["python"+str(sys.version_info[0])+"."+str(sys.version_info[1]), self.cmdArgs[0],
                        " --dtmTCPGlobalLaunch=0 --dtmTCPLocalLaunch=0 --dtmTCPLineNo="+str(self.props['dtmTCPLineNo']) +\
                        " --dtmTCPhosts=" + str(self.props['dtmTCPhosts']) + " --dtmTCPnPortsByHost=" + str(self.props['dtmTCPnPortsByHost']) +\
                        " --dtmTCPstartPort="+ str(self.props['dtmTCPstartPort']) + " --dtmTCPnbrWorkers="+str(i)+\
                        " --dtmTCPmaxWorkersByHost="+ str(self.props['dtmTCPmaxWorkersByHost']), self.userArgs]))
                        
                #currentBasePort += int(self.props['dtmTCPnPortsByHost']) / int(self.props['dtmTCPnbrWorkers'])
            
            for dtmW in dtmLocalWorkersList:
                dtmW.wait()
            
            self.commReadyEvent.set()
            return
        
        # Ici, on est rendu a executer DTM a proprement parler
        # Il faut d'abord ouvrir les bons ports, creer les Client/Listeners
        # Ensuite, on associe un id (host, numero) a chaque worker
        # Cet ID est associe a un tuple (IP, port)
        self.tabConn = {}
        listListeners = {}
        lineTab = []
        self.workerHostId = int(self.props['dtmTCPnbrWorkers'])
        maxWorkersByHost = int(self.props['dtmTCPmaxWorkersByHost'])
        fullyhost = "boumbadaboum"
        with open(self.props['dtmTCPhosts']) as hostFile:
            for hostline in hostFile:
                if hostline[0] == '#' or hostline[0] == '\n' or hostline[0] == '\r':
                    continue
                
                #hostInfos = hostline.replace("\n", "").replace("\r", "").split(" ")
                lineTab.append(hostline.replace("\n", "").replace("\r", "").split(" "))
                if len(lineTab)-1 == int(self.props['dtmTCPLineNo']):
                    fullyhost = lineTab[-1][0]
                # Si notre # de ligne est SUPERIEUR a celui de l'autre OU que
                # notre ID est SUPERIEUR a celui d'un autre worker sur le meme host que nous
                # alors c'est NOUS qui creons le CLIENT
                # Sinon, on cree l'objet Listener a qui un client va tenter de se connecter
                # On commence par creer nos Listeners, ensuite nos clients
            
            for lineC,hostInfos in enumerate(lineTab):
                remoteIp = socket.gethostbyname(hostInfos[0])
                
                if lineC > int(self.props['dtmTCPLineNo']):
                    for i in range(0, int(hostInfos[1].split("=")[1])):
                        #sys.stdout.write(str(("Listener", self.props['dtmTCPLineNo'], self.workerHostId, lineC, i, maxWorkersByHost, len(lineTab), " < ", remoteIp,
                                        #lineC*maxWorkersByHost + i + self.workerHostId*maxWorkersByHost*len(lineTab))) + "\n\n")
                        #sys.stdout.flush()
                        try:
                            listListeners[(hostInfos[0], i)] = Listener((fullyhost, int(self.props['dtmTCPstartPort']) +\
                                        lineC*maxWorkersByHost + i + self.workerHostId*maxWorkersByHost*len(lineTab)))
                            #self.tabConn[(hostInfos[0], i)] = self._createListener((socket.gethostname(), int(self.props['dtmTCPstartPort']) +\
                                        #lineC*maxWorkersByHost + i + self.workerHostId*maxWorkersByHost*len(lineTab)))
                        except Exception as ex:
                            sys.stderr.write(str(("><<<<<<<<<<<<<", "Listener", self.props['dtmTCPLineNo'], self.workerHostId, lineC, i, maxWorkersByHost, len(lineTab), " < ", remoteIp,
                                        lineC*maxWorkersByHost + i + self.workerHostId*maxWorkersByHost*len(lineTab))) + "\n\n")
                            raise ex
                elif lineC == int(self.props['dtmTCPLineNo']):
                    self.workerHost = hostInfos[0]
                    for i in range(0, int(hostInfos[1].split("=")[1])):
                        if i == self.workerHostId:
                            continue    # Pas de connexion avec nous-memes
                        
                        if i > self.workerHostId:
                            #sys.stdout.write(str(("Listener", self.props['dtmTCPLineNo'], self.workerHostId, lineC, i, maxWorkersByHost, len(lineTab), " => ", remoteIp,
                                        #int(self.props['dtmTCPLineNo'])*maxWorkersByHost + i + self.workerHostId*maxWorkersByHost*len(lineTab))) + "\n\n")
                            #sys.stdout.flush()
                            try:
                                #self.tabConn[(hostInfos[0], i)] = self._createListener((socket.gethostname(), int(self.props['dtmTCPstartPort']) + lineC*maxWorkersByHost + i + self.workerHostId*maxWorkersByHost*len(lineTab)))         
                                listListeners[(hostInfos[0], i)] = Listener(('127.0.0.1', int(self.props['dtmTCPstartPort']) + lineC*maxWorkersByHost + i + self.workerHostId*maxWorkersByHost*len(lineTab)))
                            except Exception as ex:
                                sys.stderr.write(str((">>>>>>>>>>>>>>>>", "Listener", self.props['dtmTCPLineNo'], self.workerHostId, lineC, i, maxWorkersByHost, len(lineTab), " => ", remoteIp,
                                        int(self.props['dtmTCPLineNo'])*maxWorkersByHost + i + self.workerHostId*maxWorkersByHost*len(lineTab))) +"\n\n\n")
                                raise ex
                        else:
                            #sys.stdout.write(str(("Client", self.props['dtmTCPLineNo'], self.workerHostId, lineC, i, maxWorkersByHost, len(lineTab), " <= ", remoteIp,
                                        #int(self.props['dtmTCPLineNo'])*maxWorkersByHost + self.workerHostId + i*maxWorkersByHost*len(lineTab))) + "\n\n")
                            #sys.stdout.flush()
                            # i < self.workerHostId
                            self.tabConn[(hostInfos[0], i)] = Client(('127.0.0.1', int(self.props['dtmTCPstartPort']) + lineC*maxWorkersByHost + self.workerHostId + i*maxWorkersByHost*len(lineTab)))
                            
                else:
                    # lineC < int(self.props['dtmTCPLineNo'])
                    for i in range(0, int(hostInfos[1].split("=")[1])):
                        #sys.stdout.write(str(("Client", self.props['dtmTCPLineNo'], self.workerHostId, lineC, i, maxWorkersByHost, len(lineTab), " > ", remoteIp,
                                        #int(self.props['dtmTCPLineNo'])*maxWorkersByHost + self.workerHostId + i*maxWorkersByHost*len(lineTab))) + "\n\n")
                        #sys.stdout.flush()
                        self.tabConn[(hostInfos[0], i)] = Client((remoteIp, int(self.props['dtmTCPstartPort']) +\
                                        int(self.props['dtmTCPLineNo'])*maxWorkersByHost + self.workerHostId + i*maxWorkersByHost*len(lineTab)))
        
        
        for le in listListeners.keys():
            #sys.stdout.write("WAIT FOR ACCEPT "+str(self.workerHostId) + " (" + str(len(self.tabConn))+","+str(len(listListeners))+")\n")
            #sys.stdout.write(str(socket.gethostbyname(le[0])) + " " + str(le[1]) +" \n")
            #sys.stdout.flush()
            conn = listListeners[le].accept()
            self.tabConn[le] = conn
            #sys.stdout.write("FINISH WAIT\n")
        
        #sys.stdout.write(str(self.workerId)+"\n" +"\t"+str(self.isRootWorker)+"\n")
        #sys.stdout.flush()
        self.commReadyEvent.set()
        
        working = True
        countRecvNotTransmit = 0
        countRecvTimeInit = time.time()

        while working:
            recvSomething = False
            sendSomething = False

            if self.exitStatus.is_set():    # On quitte
                # Note importante : le thread de communication DOIT vider la sendQ
                # AVANT de quitter (les ordres de quit doivent etre envoyes)
                working = False

            # On poll les connexions
            for conn in self.tabConn.values():
                #if conn is None:    # On ne recoit pas de messages de nous-memes
                    #continue
                if conn.poll():
                    # On a recu quelque chose
                    try:
                        self.recvQ.put(conn.recv())
                        countRecvNotTransmit += 1
                    except EOFError:
                        working = False
                    recvSomething = True
            
            if countRecvNotTransmit > 50 or (time.time() - countRecvTimeInit > 0.1 and countRecvNotTransmit > 0):
                countRecvNotTransmit = 0
                countRecvTimeInit = time.time()
                self.wakeUpMainThread.set()

            while True:
                # On envoie tous les messages
                try:
                    sendMsg = self.sendQ.get_nowait()
                    self.tabConn[sendMsg.receiverWid].send(sendMsg)
                    sendSomething = True
                except Queue.Empty:
                    break

            if not recvSomething:
                time.sleep(self.random.uniform(DTM_TCP_MIN_LATENCY, DTM_TCP_MAX_LATENCY))
                