
from pysvg.filter import *
from pysvg.gradient import *
from pysvg.linking import *
from pysvg.script import *
from pysvg.shape import *
from pysvg.structure import *
from pysvg.style import *
from pysvg.text import *
from pysvg.builders import *

from lxml import etree

import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import os
import os.path

PIX_BY_SEC = 220
HEIGHT_BY_WORKER = 110
RESOLUTION_TASK_DISCOVER = 0.005
OFFSET_LEFT = 40


colorsList = ['#ee0000', '#00bb00', '#0000ff', '#aaaa00', '#00aaaa', '#000077', '#cc00cc']
funcAssignDict = {}
workersTimeDelta = []

taskDict = {}

class badDispatchFinder(object):

    def __init__(self, maxTime, tasksDict):
        self.timeBlocks = [0 for i in xrange(int(maxTime / RESOLUTION_TASK_DISCOVER))]
        for task in tasksDict.values():
            self.addTask(task)
        return

    def addTask(self, taskInfo):
        for i in xrange(int(taskInfo[0] / RESOLUTION_TASK_DISCOVER), int(taskInfo[1][0] / RESOLUTION_TASK_DISCOVER)):
            self.timeBlocks[i] += 1

    def drawParts(self, svgObj, nbrWorkers):
        i = 0
        oh = ShapeBuilder()
        myStyle = StyleBuilder()
        myStyle.setFontFamily(fontfamily="Verdana")
        myStyle.setFontWeight('bold')
        myStyle.setFontSize('14pt')
        txt = text("Parallelisable?", 5, 20)
        txt.set_style(myStyle.getStyle())
        svgObj.addElement(txt)

        while i < len(self.timeBlocks):
            if self.timeBlocks[i] > nbrWorkers:
                beginRect = i
                while i < len(self.timeBlocks) and self.timeBlocks[i] > nbrWorkers:
                    i += 1
                endRect = i
                svgObj.addElement(oh.createRect(OFFSET_LEFT + beginRect * RESOLUTION_TASK_DISCOVER * PIX_BY_SEC + 2, 5, (endRect - beginRect) * RESOLUTION_TASK_DISCOVER * PIX_BY_SEC + 2, 18, strokewidth=2, fill='orange', stroke='white'))
            else:
                i += 1


def synchroWorkersTime(workerFileBeginPath):
    global workersTimeDelta
    indexF = 0
    msgTreeList = []
    while os.path.exists(workerFileBeginPath + str(indexF) + ".xml"):
        xmlTree = etree.parse(workerFileBeginPath + str(indexF) + ".xml")
        msgTreeList.append(xmlTree.getroot()[3])    #
        assert msgTreeList[-1].tag == 'commLog'
        indexF += 1

    workersTimeDelta.append(0.)     # Par definition, la reference est le premier worker
    # On va chercher les premiers messages qu'il a envoye a chaque worker

    for i in xrange(1, len(msgTreeList)):
        j = 0
        while int(msgTreeList[0][j].get('otherWorker')) != i or msgTreeList[0][j].get('direc') != "out":
            #print("[0]",msgTreeList[0][j].get('otherWorker'), msgTreeList[0][j].get('msgtag'), msgTreeList[0][j].get('type'))
            j += 1
        msgTagRootWorker, timeRootWorker = int(msgTreeList[0][j].get('msgtag')), float(msgTreeList[0][j].get('time'))

        k = 0
        while int(msgTreeList[i][k].get('otherWorker')) != 0 or msgTreeList[i][k].get('direc') != "in":
            #print("[" +str(i)+"]", msgTreeList[i][k].get('otherWorker'), msgTreeList[i][k].get('msgtag'), msgTreeList[i][k].get('type'))
            k += 1
        msgTagOtherWorker, timeOtherWorker = int(msgTreeList[i][k].get('msgtag')), float(msgTreeList[i][k].get('time'))

        assert msgTagRootWorker == msgTagOtherWorker
        workersTimeDelta.append(timeOtherWorker - timeRootWorker)

    return

def traceWorker(svgO, workerFile, offset, decalageTemps=0.):
    global funcAssignDict
    global taskDict
    oh = ShapeBuilder()
    xmlTree = etree.parse(workerFile)
    print("ADD WORKER ", workerFile)

    assert xmlTree.getroot().tag == 'dtm'

    wbt = float(xmlTree.getroot().get('timeBegin'))

    myStyle = StyleBuilder()
    myStyle.setFontFamily(fontfamily="Verdana")
    myStyle.setFontWeight('bold')
    myStyle.setFontSize('14pt')
    myStyle.setFilling('blue')
    txt = text("Worker " + str(xmlTree.getroot().get('workerId')), 5, offset + HEIGHT_BY_WORKER / 2)
    txt.set_style(myStyle.getStyle())
    svgO.addElement(txt)

    maxEndTime = 0.
    dataTask = ""
    taskTarget = ""
    for taskTag in xmlTree.getroot()[0]:
        beginTimes = []
        endTimes = []
        for taskInfo in taskTag:
            if taskInfo.tag == 'event' and taskInfo.get('type') == "begin" or taskInfo.get('type') == 'wakeUp':
                #print(taskInfo.get('time'))
                beginTimes.append(float(taskInfo.get('time')) - wbt + decalageTemps)
            elif taskInfo.tag == 'event' and taskInfo.get('type') == "end" or taskInfo.get('type') == 'sleep':
                assert len(endTimes) < len(beginTimes)
                endTimes.append(float(taskInfo.get('time')) - wbt + decalageTemps)
                if maxEndTime < endTimes[-1]:
                    maxEndTime = endTimes[-1]
            elif taskInfo.tag == 'target':
                if not taskInfo.get('name') in funcAssignDict:
                    print("Choose color " + colorsList[len(funcAssignDict)])
                    funcAssignDict[taskInfo.get('name')] = colorsList[len(funcAssignDict)]
                dataTask = taskInfo.get('name') + " : "
                taskTarget = taskInfo.get('name')
                indexArg = 0
                while not (taskInfo.get('arg' + str(indexArg)) is None):
                    dataTask += taskInfo.get('arg' + str(indexArg)) + ", "
                    indexArg += 1
        taskDict[taskTag.get('id')] = (float(taskTag.get('creationTime')) - wbt + decalageTemps, beginTimes, endTimes)

        #print(beginTimes, endTimes)
        for i in xrange(len(beginTimes)):
            if endTimes[i] - beginTimes[i] < 5. / PIX_BY_SEC:
                #endTimes[i] += 4. / PIX_BY_SEC
                svgO.addElement(oh.createLine(OFFSET_LEFT + decalageTemps * PIX_BY_SEC + beginTimes[i] * PIX_BY_SEC + 1, offset, OFFSET_LEFT + decalageTemps * PIX_BY_SEC + beginTimes[i] * PIX_BY_SEC + 1, offset + HEIGHT_BY_WORKER, strokewidth=3, stroke=funcAssignDict[taskTarget]))
            else:
                svgO.addElement(oh.createRect(OFFSET_LEFT + decalageTemps * PIX_BY_SEC + beginTimes[i] * PIX_BY_SEC + 2, offset, endTimes[i] * PIX_BY_SEC - 2 - (beginTimes[i] * PIX_BY_SEC + 2), HEIGHT_BY_WORKER, strokewidth=3, stroke=funcAssignDict[taskTarget]))
        #svgO.addElement(text(dataTask, beginTime * PIX_BY_SEC + 25, offset + HEIGHT_BY_WORKER / 2))

    loadsList = []
    timesList = []
    for loadTag in xmlTree.getroot()[1]:
        tmpLoad = []
        for workerState in loadTag:
            if workerState.tag != "workerKnownState":
                continue
            loadWorker = [float(i) for i in workerState.get('load').split(",")]
            tmpLoad.append(loadWorker[0]+loadWorker[1]+loadWorker[2])       # En cours, en attente de demarrage et en attente de redemarrage
        loadsList.append(tmpLoad)
        timesList.append(float(loadTag.get('time')))

    timesList = [t-wbt+decalageTemps for t in timesList]
    plt.figure()
    if len(sys.argv) > 3 and sys.argv[3] == "log":
        plt.yscale('log', nonposy='clip')
    count = 0
    for line in zip(*loadsList):
        plt.plot(timesList, line, label='Worker '+str(count))
        count += 1

    plt.legend()
    plt.xlabel('Temps normalise')
    plt.ylabel('Load estime')
    plt.savefig(sys.argv[2] + 'loads_'+str(xmlTree.getroot().get('workerId'))+'.png')

    return maxEndTime

def traceTimeline(svgO, offset, upTo):
    oh = ShapeBuilder()

    svgO.addElement(oh.createRect(OFFSET_LEFT - 10, offset + 5, OFFSET_LEFT + (upTo + 1) * PIX_BY_SEC + 10, HEIGHT_BY_WORKER / 2))

    for i in range(int(upTo) + 2):
        svgO.addElement(text(str(i), OFFSET_LEFT + i * PIX_BY_SEC - 5 * len(str(i)), offset + 40))

    for i in range((int(upTo) + 2) * 10):
        if i % 10 == 0:
            svgO.addElement(oh.createLine(OFFSET_LEFT + i * PIX_BY_SEC / 10, offset + 5, OFFSET_LEFT + i * PIX_BY_SEC / 10, offset + 20, stroke='red', strokewidth=2))
        else:
            svgO.addElement(oh.createLine(OFFSET_LEFT + i * PIX_BY_SEC / 10, offset + 5, OFFSET_LEFT + i * PIX_BY_SEC / 10, offset + 20, stroke='black', strokewidth=2))
    myStyle = StyleBuilder()
    myStyle.setFontFamily(fontfamily="Verdana")
    myStyle.setFontStyle('italic')
    myStyle.setFontSize('12pt') #no need for the keywords all the time
    txt = text("Time (seconds)", OFFSET_LEFT + 10, offset + 55)
    txt.set_style(myStyle.getStyle())
    svgO.addElement(txt)
    return

def printFuncNames(svgO, offset):
    global funcAssignDict
    myStyle = StyleBuilder()
    myStyle.setFontFamily(fontfamily="Verdana")
    myStyle.setFontWeight('bold')
    myStyle.setFontSize('20pt') #no need for the keywords all the time
    tmpOff = offset
    txt = text("Functions color map :", 10, tmpOff)
    txt.set_style(myStyle.getStyle())
    svgO.addElement(txt)
    tmpOff += 35
    for key in funcAssignDict:
        myStyle.setFilling(funcAssignDict[key])
        txt = text(str(key), 30, tmpOff)
        txt.set_style(myStyle.getStyle())
        svgO.addElement(txt)
        tmpOff += 30

def main():

    global taskDict
    global workersTimeDelta

    objSvg = svg()
    indexF = 0
    maxEndTime = 0.
    tmpEndTime = 0.



    synchroWorkersTime(sys.argv[1]+"/log")
    print(workersTimeDelta)
    while os.path.exists(sys.argv[1]+"/log" + str(indexF) + ".xml"):
        tmpEndTime = traceWorker(objSvg, sys.argv[1]+"/log" + str(indexF) + ".xml", indexF * (HEIGHT_BY_WORKER + 10) + 30, workersTimeDelta[indexF])
        if tmpEndTime > maxEndTime:
            maxEndTime = tmpEndTime
        indexF += 1
    traceTimeline(objSvg, indexF * (HEIGHT_BY_WORKER + 10) + 30, maxEndTime)
    printFuncNames(objSvg, (indexF + 1) * (HEIGHT_BY_WORKER + 10) + 30)

    cb = badDispatchFinder(maxEndTime, taskDict)
    cb.drawParts(objSvg, indexF + 1)

    print("FINISHED...")

    objSvg.save(sys.argv[2])

if __name__ == '__main__':
    print("HOP!")
    main()
