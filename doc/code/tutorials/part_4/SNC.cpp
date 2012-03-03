/*
    This file is part of DEAP.

    DEAP is free software: you can redistribute it and/or modify
    it under the terms of the GNU Lesser General Public License as
    published by the Free Software Foundation, either version 3 of
    the License, or (at your option) any later version.

    DEAP is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public
    License along with DEAP. If not, see <http://www.gnu.org/licenses/>.
*/

/* This file is an example of a C evaluation function interfaced with DEAP;
 * It implements the evaluator of the sorting network problems, making it
 * about five times faster (up to 16x if used in combination with the
 * optimized cTools.nsga2 selection algorithm).
 * 
 * To compile it, you may want to use distutils to simplify the linking, like
 * the installSN.py script provided with this package. 
 * You may then import it like any other Python module :

 import SNC
 SNC.evalNetwork(dimension, individual)
 
 * See 4_5_home_made_eval_func.py for a comprehensive example.
 */
#include <Python.h>
#include <map>
#include <vector>
#include <iostream>

// Set of connectors that can be applied in parallel.
typedef std::map<unsigned int,unsigned int> Level;


static PyObject* evalNetwork(PyObject *self, PyObject *args){
    
    // Retrieve arguments (first : network dimensions; second : list of connectors [tuples])
    PyObject *inDimensions = PyTuple_GetItem(args, 0);
    PyObject *listNetwork = PyTuple_GetItem(args, 1);
    
    std::vector<Level> mNetwork;
    
    const unsigned int inputs_size = (unsigned int)PyInt_AS_LONG(inDimensions);
    const unsigned int lNbTests = (1u << inputs_size);
    unsigned long lCountMisses = 0;
    unsigned int inWire1, inWire2;
    const unsigned long lgth = PyList_Size(listNetwork);
    
    // Network creation
    for(unsigned int k = 0; k < lgth; k++){
        // Retrieve endpoint values
        inWire1 = (unsigned int)PyInt_AS_LONG(PyTuple_GetItem(PyList_GetItem(listNetwork,k),0));
        inWire2 = (unsigned int)PyInt_AS_LONG(PyTuple_GetItem(PyList_GetItem(listNetwork,k),1));
               
        // Check values of inWire1 and inWire2
        if(inWire1 == inWire2) continue;
        if(inWire1 > inWire2) {
            const unsigned int lTmp = inWire1;
            inWire1 = inWire2;
            inWire2 = lTmp;
        }
        
        // Nothing in network, create new level and connector
        if(mNetwork.empty()) {
            Level lLevel;
            lLevel[inWire1] = inWire2;
            mNetwork.push_back(lLevel);
            continue;
        }
        
        // Iterator to the connector at current level, after mWire1
        bool lConflict = false;
        Level::const_iterator lIterConnNext = mNetwork.back().begin();
        for(; (lIterConnNext != mNetwork.back().end()) && (inWire1 > lIterConnNext->first); ++lIterConnNext);
        if(lIterConnNext != mNetwork.back().end()) {
            // Check if conflict with next connector and inWire2
            if(inWire2 >= lIterConnNext->first) lConflict = true;
        }
        if(lIterConnNext != mNetwork.back().begin()) {
            // Iterator to the connector at current level, before mWire1
            Level::const_iterator lIterConnPrev = lIterConnNext;
            --lIterConnPrev;
            // Check if conflict with previous connector and inWire1
            if(inWire1 <= lIterConnPrev->second) lConflict = true;
        }
        
        // Add connector
        if(lConflict) {                          // Add new level of connectors
            Level lNextLevel;
            lNextLevel[inWire1] = inWire2;
            mNetwork.push_back(lNextLevel);
        }
        else {                                   // Add connector to current level
            mNetwork.back()[inWire1] = inWire2;
        }
    }

    // Network test
    for(unsigned int i=0; i<lNbTests; ++i) {
        std::vector<double> lSeqIOrig(inputs_size, 0.0);
        
        for(unsigned int j=0; j<inputs_size; ++j) {
            const unsigned int lValIJ = (1u << j);
            if((i & lValIJ) == lValIJ) lSeqIOrig[j] = 1.0;
        }
        
        std::vector<double> lSeqISorted(lSeqIOrig);
                            
        for(unsigned int z=0; z<mNetwork.size(); ++z) {
            for(Level::const_iterator lIter = mNetwork[z].begin();
                lIter != mNetwork[z].end(); ++lIter) {
                const unsigned int lId1 = lIter->first;
                const unsigned int lId2 = lIter->second;
                if(lSeqISorted[lId1] > lSeqISorted[lId2]) {
                    const double lTmp = lSeqISorted[lId1];
                    lSeqISorted[lId1] = lSeqISorted[lId2];
                    lSeqISorted[lId2] = lTmp;
                }
            }
        }
        
        bool lIsSorted = true;
        bool lLastWasOne = false;
        for(unsigned int w=0; w<lSeqISorted.size(); ++w) {
            if(lLastWasOne && (lSeqISorted[w] == 0.0)) {
                lIsSorted = false;
                break;
            }
            lLastWasOne = (lSeqISorted[w] == 1.0);
        }
        if(lIsSorted == false)
            ++lCountMisses;
    }
    
    // Compute the number of comparison-swap used.
    unsigned int lengthWanted = 0;
    for(unsigned int z=0; z<mNetwork.size(); ++z) {
        lengthWanted += mNetwork[z].size();
    }
    
    // Pack the return values into a tuple (fit, depth, length)
    PyObject* retVal = Py_BuildValue("(i,i,i)", lCountMisses, mNetwork.size(), lengthWanted);
    
    return retVal;
}


static PyMethodDef SNCMethods[] = {
    {"evalNetwork", evalNetwork, METH_VARARGS,
     "Evaluate a sorting network."},
    {NULL, NULL, 0, NULL}        /* Sentinel (?!?) */
};

// Needed by Python to initialize the SNC module
PyMODINIT_FUNC
initSNC(void)
{
    (void) Py_InitModule("SNC", SNCMethods);
}
