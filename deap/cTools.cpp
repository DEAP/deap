#include <Python.h>

#if PY_MAJOR_VERSION >= 3
#define PY3K
#endif

#include <map>
#include <vector>
#include <iostream>
#include <limits>
#include <algorithm>
#include <cmath>


class FitComp{
    /* Used to compare two individuals against a specific objective (mCompIndex) */
public:
    
    bool operator() (std::pair<std::vector<double>, unsigned int> a, std::pair<std::vector<double>, unsigned int> b){
        return a.first[mCompIndex] < b.first[mCompIndex];
    }
    unsigned int mCompIndex;
};

static PyObject* selTournament(PyObject *self, PyObject *args, PyObject *kwargs){
    /* Args[0] / kwArgs['individuals'] : Individual list
     * Args[1] / kwArgs['k'] : Number of individuals wanted in output
     * Args[2] / kwArgs['tournsize'] : Tournament size
     * Return : k selected individuals from input individual list
     */
    
    PyObject *lListIndv;
    unsigned int k, lTournSize;
    static char *lKwlist[] = {"individuals", "k", "tournsize", NULL};
    PyArg_ParseTupleAndKeywords(args, kwargs, "Oii", lKwlist, &lListIndv, &k, &lTournSize);
    
    // Import the Python random module
    PyObject *lRandomModule = PyImport_ImportModule("random");
    PyObject *lRandomChoiceFunc = PyObject_GetAttrString(lRandomModule, "choice");
    PyObject *lListSelect = PyList_New(0);
    
    PyObject *lCandidate, *lChallenger, *lCandidateFit, *lChallengerFit, *lTupleArgs;
    lTupleArgs = Py_BuildValue("(O)", lListIndv);
    for(unsigned int i=0; i < k; i++){
        // We call random.choice with the population as argument
        lCandidate = PyObject_Call(lRandomChoiceFunc, lTupleArgs, NULL);
        lCandidateFit = PyObject_GetAttrString(lCandidate, "fitness");
        for(unsigned int j=0; j < lTournSize-1; j++){
            lChallenger = PyObject_Call(lRandomChoiceFunc, lTupleArgs, NULL);
            lChallengerFit = PyObject_GetAttrString(lChallenger, "fitness");
            // Is the fitness of the aspirant greater?
            if(PyObject_RichCompareBool(lChallengerFit, lCandidateFit, Py_GT)){
                lCandidate = lChallenger;
                lCandidateFit = lChallengerFit;
            }  
        }
        PyList_Append(lListSelect, lCandidate);    
    }
    return lListSelect;
}

static bool crowdDistComp(std::pair<double, unsigned int> a, std::pair<double, unsigned int> b){
    return a.first < b.first;
}

static bool isDominated(std::vector<double> inIndividual1, std::vector<double> inIndividual2){
    /* Return True if Individual1 is pareto dominated by Individual2 */
    bool notEqual = false;
    for(unsigned int i=0; i < inIndividual1.size(); i++){
        // Assert that inIndividual1.size() == inIndividual2.size()
        if(inIndividual1[i] > inIndividual2[i])
            return false;
        else if(inIndividual1[i] < inIndividual2[i])
            notEqual = true;
    }
    return notEqual;
}

static PyObject* selNSGA2(PyObject *self, PyObject *args){
    /* Args[0] : Individual list
     * Args[1] : Number of individuals wanted in output
     * Return : k selected individuals from input individual list
     */
    PyObject *lListIndv = PyTuple_GetItem(args, 0);
#ifdef PY3K
    unsigned long k = (unsigned long)PyLong_AS_LONG(PyTuple_GetItem(args, 1));
#else
    unsigned int k = (unsigned int)PyInt_AS_LONG(PyTuple_GetItem(args, 1));
#endif
    
    PyObject *lListSelect = PyList_New(0);
    
    unsigned int lLenListIndv = (unsigned int)PyList_Size(lListIndv);
    unsigned int lNbrObjectives = (unsigned int)PyTuple_Size(PyObject_GetAttrString(PyObject_GetAttrString(PyList_GetItem(lListIndv,0), "fitness"), "values"));
    
    if(k == 0)
        return lListSelect;
    
    // First : copy fitness values into an std::vector<std::vector<double> >
    // First vector index is used to identify individuals
    // Second vector index represents an objective
    std::vector<std::vector<double> > lPopFit(lLenListIndv, std::vector<double>(lNbrObjectives,0.));
    for(unsigned int i = 0; i < lLenListIndv; i++){
        for(unsigned int j = 0; j < lNbrObjectives; j++)
            lPopFit[i][j] = PyFloat_AS_DOUBLE(PyTuple_GetItem(PyObject_GetAttrString(PyObject_GetAttrString(PyList_GetItem(lListIndv,i), "fitness"), "wvalues"), j));
    }
    
    
    unsigned int lParetoSorted = 0;
    unsigned int lFrontIndex = 0;
    std::vector<std::vector<unsigned int> > lParetoFront(1, std::vector<unsigned int>(0));
    std::vector<unsigned int> lDominating(lLenListIndv, 0);
    std::vector<std::vector<unsigned int> > lDominatedInds(lLenListIndv, std::vector<unsigned int>(0));
    
    // Rank first pareto front
    for(unsigned int i = 0; i < lLenListIndv; i++){
        for(unsigned int j = i+1; j < lLenListIndv; j++){
            
            if(isDominated(lPopFit[j], lPopFit[i])){
                lDominating[j]++;
                lDominatedInds[i].push_back(j);
            }
            else if(isDominated(lPopFit[i], lPopFit[j])){
                lDominating[i]++;
                lDominatedInds[j].push_back(i);
            }
        }
        if(lDominating[i] == 0){
            lParetoFront[lFrontIndex].push_back(i);
            lParetoSorted++;
        }
    }

    // Rank other pareto fronts, until we reach the *k* limit
    while(lParetoSorted < k && lParetoSorted < lLenListIndv){
        lFrontIndex++;
        lParetoFront.push_back(std::vector<unsigned int>(0));
        for(unsigned int i = 0; i < lParetoFront[lFrontIndex-1].size(); i++){
            unsigned int lIndiceP = lParetoFront[lFrontIndex-1][i];
            for(unsigned int j = 0; j < lDominatedInds[lIndiceP].size(); j++){
                unsigned int lIndiceD = lDominatedInds[lIndiceP][j];
                if(--lDominating[lIndiceD] == 0){
                    lParetoFront[lFrontIndex].push_back(lIndiceD);
                    lParetoSorted++;
                }
            }
        }
    }
    
    // Append individuals from pareto ranking until we reach the limit
    for(unsigned int i = 0; i < lParetoFront.size(); i++){
        if(PyList_Size(lListSelect)+lParetoFront[i].size() <= k){
            for(unsigned int j = 0; j < lParetoFront[i].size(); j++)
                PyList_Append(lListSelect, PyList_GetItem(lListIndv,lParetoFront[i][j]));
        }
        else{
            break;
        }
    }

    // Crowding distance on the last front
    if(PyList_Size(lListSelect) == k)
        return lListSelect;
    
    FitComp lCmpIndvObj;
    std::vector<unsigned int> lLastParetoFront = lParetoFront.back();
    std::vector<std::pair<double, unsigned int> > lDistances(0);
    std::vector<std::pair<std::vector<double>, unsigned int> > lCrowdingList(0);
    double lInfinity = std::numeric_limits<double>::infinity();
    
    // Reserve sufficient memory for the subsequent push_back
    lDistances.reserve(lLastParetoFront.size());
    lCrowdingList.reserve(lLastParetoFront.size());
    
    for(unsigned int i = 0; i < lLastParetoFront.size(); i++){
        // Push initial distance (0.0) and individual index in lPopFit and lListIndv for each individual
        lDistances.push_back(std::pair<double, unsigned int>(0., lLastParetoFront[i]));
        
        // Push fitness and individual index in lDistances for each individual
        lCrowdingList.push_back(std::pair<std::vector<double>, unsigned int>(lPopFit[lLastParetoFront[i]],i));
    }
    
    for(unsigned int i = 0; i < lNbrObjectives; i++){
        // For each objective
        // Set the current objective in the comparison class
        lCmpIndvObj.mCompIndex = i;
        // Sort (stable, in order to keep the same order for equal fitness values)
        stable_sort(lCrowdingList.begin(), lCrowdingList.end(), lCmpIndvObj);
        
        // Set an infinite distance to the extremums
        lDistances[lCrowdingList[0].second].first = lInfinity;
        lDistances[lCrowdingList.back().second].first = lInfinity;

        for(unsigned int j = 1; j < lCrowdingList.size()-1; j++){
            if(lDistances[lCrowdingList[j].second].first < lInfinity)
                lDistances[lCrowdingList[j].second].first += lCrowdingList[j+1].first[i]-lCrowdingList[j-1].first[i];
        }
    }
    
    // Final sorting (again, must be stable)
    stable_sort(lDistances.begin(), lDistances.end(), crowdDistComp);
   
    // Pick the last individuals (with the higher crowding distance) first
    for(unsigned int i = lDistances.size()-1; i >= 0; i--){
        if(PyList_Size(lListSelect) >= k)
            break;
        // While the size of the return list is lesser than *k*, append the next individual
        PyList_Append(lListSelect, PyList_GetItem(lListIndv,lDistances[i].second));  
    }
    
    return lListSelect;
}

static PyMethodDef cToolsMethods[] = {
    {"selNSGA2", selNSGA2, METH_VARARGS,
     "Select using NSGA II."},
    {"selTournament", (PyCFunction)selTournament, METH_VARARGS | METH_KEYWORDS,
     "Select using tournament."},
    {NULL, NULL, 0, NULL}        /* Sentinel (?!?) */
};

#ifdef PY3K
static struct PyModuleDef moduledef = {
    PyModuleDef_HEAD_INIT,
    "cTools",     /* m_name */
    "C version of the tools.",  /* m_doc */
    -1,                  /* m_size */
    cToolsMethods,       /* m_methods */
    NULL,                /* m_reload */
    NULL,                /* m_traverse */
    NULL,                /* m_clear */
    NULL,                /* m_free */
};
#endif

// Needed by Python to initialize the C_nsga2 module
PyMODINIT_FUNC
#ifdef PY3K
PyInit_cTools(void)
#else
initcTools(void)
#endif
{
#ifdef PY3K
    PyObject *lModule = PyModule_Create(&moduledef);
    if(lModule == NULL)
        return NULL;
    
    return lModule;
#else    
    (void) Py_InitModule("cTools", cToolsMethods);
#endif
}