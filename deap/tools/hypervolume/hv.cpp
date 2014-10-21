/*
 * This file is part of DEAP.
 *
 * DEAP is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Lesser General Public License as
 * published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version.
 *
 * DEAP is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with DEAP. If not, see <http://www.gnu.org/licenses/>.
 */

#include <Python.h>

#if PY_MAJOR_VERSION >= 3
#define PY3K
#endif

#include <cstdlib>
#include <iostream>

#include "_hv.h"

static PyObject* hypervolume(PyObject *self, PyObject *args){
    // Args[0]: Point list
    // Args[1]: Reference point
    // Return: The hypervolume as a double

    PyObject *lPyPointSet = PyTuple_GetItem(args, 0);
    PyObject *lPyReference = PyTuple_GetItem(args, 1);

    int lNumPoints = 0;
    int lDim = -1;
    double *lPointSet = NULL;

    if(PySequence_Check(lPyPointSet)){
        lNumPoints = PySequence_Size(lPyPointSet);
        unsigned int lPointCount = 0;

        for(int i = 0; i < lNumPoints; ++i){
            PyObject *lPyPoint = PySequence_GetItem(lPyPointSet, i);
            
            if(PySequence_Check(lPyPoint)){
                if(lDim < 0){
                    lDim = PySequence_Size(lPyPoint);
                    lPointSet = new double[lNumPoints*lDim];
                }
                
                for(int j = 0; j < lDim; ++j){
                    PyObject *lPyCoord = PySequence_GetItem(lPyPoint, j);
                    lPointSet[lPointCount++] = PyFloat_AsDouble(lPyCoord);
                    Py_DECREF(lPyCoord);
                    lPyCoord = NULL;
                    
                    if(PyErr_Occurred()){
                        PyErr_SetString(PyExc_TypeError,"Points must contain double type values");
                        delete[] lPointSet;
                        return NULL;
                    }
                }
                
                Py_DECREF(lPyPoint);
                lPyPoint = NULL;
            } else {
                Py_DECREF(lPyPoint);
                lPyPoint = NULL;
                PyErr_SetString(PyExc_TypeError,"First argument must contain only points");
                free(lPointSet);
                return NULL;
            }
        }

        

    } else {
        PyErr_SetString(PyExc_TypeError,"First argument must be a list of points");
        return NULL;
    }

    double *lReference = NULL;

    if(PySequence_Check(lPyReference)){
        if(PySequence_Size(lPyReference) == lDim){
            lReference = new double[lDim];

            for(int i = 0; i < lDim; ++i){
                PyObject *lPyCoord = PySequence_GetItem(lPyReference, i);
                lReference[i] = PyFloat_AsDouble(lPyCoord);
                Py_DECREF(lPyCoord);
                lPyCoord = NULL;
                    
                if(PyErr_Occurred()){
                    PyErr_SetString(PyExc_TypeError,"Reference point must contain double type values");
                    delete[] lReference;
                    return NULL;
                }
            }

        } else {
            PyErr_SetString(PyExc_TypeError,"Reference point is not of same dimensionality as point set");
            return NULL;
        }

    } else {
        PyErr_SetString(PyExc_TypeError,"Second argument must be a point");
        return NULL;
    }


    double lHypervolume = fpli_hv(lPointSet, lDim, lNumPoints, lReference);
    
    delete[] lPointSet;
    delete[] lReference;

    return PyFloat_FromDouble(lHypervolume);
}

static PyMethodDef hvMethods[] = {
    {"hypervolume", hypervolume, METH_VARARGS,
        "Hypervolume Computation"},
    {NULL, NULL, 0, NULL}        /* Sentinel (?!?) */
};

#ifdef PY3K
static struct PyModuleDef moduledef = {
    PyModuleDef_HEAD_INIT,
    "hv",                /* m_name */
    "C Hypervolumes methods.",  /* m_doc */
    -1,                  /* m_size */
    hvMethods,           /* m_methods */
    NULL,                /* m_reload */
    NULL,                /* m_traverse */
    NULL,                /* m_clear */
    NULL,                /* m_free */
};
#endif

PyMODINIT_FUNC
#ifdef PY3K
PyInit_hv(void)
#else
inithv(void)
#endif
{
#ifdef PY3K
    PyObject *lModule = PyModule_Create(&moduledef);
    if(lModule == NULL)
        return NULL;
    
    return lModule;
#else    
    (void) Py_InitModule("hv", hvMethods);
#endif
}