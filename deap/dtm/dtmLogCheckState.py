
from lxml import etree

import sys

import os
import os.path




def main():

    global taskDict
    global workersTimeDelta


    # chemin fichier xml, borne temps inf, borne temps sup,
    xmlTree = etree.parse(sys.argv[1])
    borneMin, borneMax = float(sys.argv[2]), float(sys.argv[3])

    initTime = float(xmlTree.getroot().get('timeBegin'))
    for decisionTag in xmlTree.getroot()[1]:
       # print( float(decisionTag.get('time')) - initTime, borneMin, borneMax)
        if float(decisionTag.get('time')) - initTime > borneMin and float(decisionTag.get('time')) - initTime < borneMax:
            print("##########################################################")
            print("At " + str(float(decisionTag.get('time')) - initTime))
            print("Workers known state (current, not started, waiting for restart, waiting) :")
            for infoTag in decisionTag.iterchildren(tag='workerKnownState'):
                print("\t[" + infoTag.get('id') + "] : " + infoTag.get('load'))
            print("\n")
            print("Actions :")
            for actionTag in decisionTag.iterchildren(tag='action'):
                if actionTag.get('type') == 'sendtasks':
                    print("\tSend " + actionTag.get('tasksinfo') + " tasks to workers " + actionTag.get('destination'))
                elif actionTag.get('type') == 'checkavail':
                    print("\tWants to send tasks, workers score : " + actionTag.get('destination'))
                elif actionTag.get('type') == 'sendrequest':
                    print("\tSend request to get tasks to " + actionTag.get('destination'))
            print("\n\n")

if __name__ == '__main__':
    main()
