#include "AntSimulatorFast.hpp"

AntSimulatorFast::AntSimulatorFast(unsigned int inMaxMoves) :
        mMaxMoves(inMaxMoves),
        mNbPiecesAvail(0),
        mRowStart(0),
        mColStart(0),
        mDirectionStart(AntSimulatorFast::eAntEast),
        mNbMovesAnt(0),
        mNbPiecesEaten(0),
        mRowAnt(0),
        mColAnt(0),
        mDirectionAnt(AntSimulatorFast::eAntEast)
    { }


void AntSimulatorFast::parseMatrix(char* inFileStr){
    std::fstream lFileHandle;
    
    lFileHandle.open(inFileStr, std::fstream::in);
        
    mOrigTrail.resize(ROWS_NBR);
    mExecTrail.resize(ROWS_NBR);    
    for(unsigned int i = 0; i < ROWS_NBR; i++){
        mOrigTrail[i].resize(COLS_NBR);
        mExecTrail[i].resize(COLS_NBR);
    }
    
    char lBuffer;
    for(unsigned int i=0; i<mOrigTrail.size(); ++i) {
        for(unsigned int j=0; j<mOrigTrail[i].size(); ++j) {
            lFileHandle >> lBuffer;
            switch(lBuffer) {
            case eStart: {
                mOrigTrail[i][j] = eStart;
                mRowStart = i;
                mColStart = j;
                mExecTrail[i][j] = eStart;
                break;
            }
            case eEmpty:
            case eFoodPiece: {
                mOrigTrail[i][j] = lBuffer;
                mExecTrail[i][j] = lBuffer;
                break;
            }
            case ePassed: {
                mOrigTrail[i][j] = eEmpty;
                mExecTrail[i][j] = ePassed;
                break;
            }
            case eEatenPiece: {
                mOrigTrail[i][j] = eFoodPiece;
                mExecTrail[i][j] = eEatenPiece;
                break;
            }
            case eAntNorth:
            case eAntEast:
            case eAntSouth:
            case eAntWest: {
                mOrigTrail[i][j] = eEmpty;
                mExecTrail[i][j] = lBuffer;
                break;
            }
            default: { }
            }
        }
    }
    lFileHandle.close();
}


void AntSimulatorFast::turnLeft(void){
    if(mNbMovesAnt >= mMaxMoves) return;
    ++mNbMovesAnt;
    switch(mDirectionAnt) {
    case eAntNorth: {
        mDirectionAnt = eAntWest;
        break;
    }
    case eAntEast: {
        mDirectionAnt = eAntNorth;
        break;
    }
    case eAntSouth: {
        mDirectionAnt = eAntEast;
        break;
    }
    case eAntWest: {
        mDirectionAnt = eAntSouth;
        break;
    }
    default: { }
    }
}
    
void AntSimulatorFast::turnRight(void){
    if(mNbMovesAnt >= mMaxMoves) return;
    ++mNbMovesAnt;
    switch(mDirectionAnt) {
    case eAntNorth: {
        mDirectionAnt = eAntEast;
        break;
    }
    case eAntEast: {
        mDirectionAnt = eAntSouth;
        break;
    }
    case eAntSouth: {
        mDirectionAnt = eAntWest;
        break;
    }
    case eAntWest: {
        mDirectionAnt = eAntNorth;
        break;
    }
    default: { }
    }
}


void AntSimulatorFast::moveForward(void){
    if(mNbMovesAnt >= mMaxMoves) return;
    ++mNbMovesAnt;
    
    switch(mDirectionAnt) {
    case eAntNorth: {
        if(mRowAnt == 0) mRowAnt = (mExecTrail.size()-1);
        else --mRowAnt;
        break;
    }
    case eAntEast: {
        ++mColAnt;
        if(mColAnt >= mExecTrail.front().size()) mColAnt = 0;
        break;
    }
    case eAntSouth: {
        ++mRowAnt;
        if(mRowAnt >= mExecTrail.size()) mRowAnt = 0;
        break;
    }
    case eAntWest: {
        if(mColAnt == 0) mColAnt = (mExecTrail.front().size()-1);
        else --mColAnt;
        break;
    }
    default: { }
    }
    switch(mExecTrail[mRowAnt][mColAnt]) {
    case eStart:
    case ePassed:
    case eEatenPiece:
        break;
    case eEmpty: {
        mExecTrail[mRowAnt][mColAnt] = ePassed;
        break;
    }
    case eFoodPiece: {
        mExecTrail[mRowAnt][mColAnt] = eEatenPiece;
        ++mNbPiecesEaten;
        break;
    }
    default: { }
    }
}

void AntSimulatorFast::ifFoodAhead(PyObject* inIfTrue, PyObject* inIfFalse){
    unsigned int lAheadRow = mRowAnt;
    unsigned int lAheadCol = mColAnt;
    switch(mDirectionAnt) {
    case eAntNorth: {
        if(lAheadRow == 0) lAheadRow = (mExecTrail.size()-1);
        else --lAheadRow;
        break;
    }
    case eAntEast: {
        ++lAheadCol;
        if(lAheadCol >= mExecTrail.front().size()) lAheadCol = 0;
        break;
    }
    case eAntSouth: {
        ++lAheadRow;
        if(lAheadRow >= mExecTrail.size()) lAheadRow = 0;
        break;
    }
    case eAntWest: {
        if(lAheadCol == 0) lAheadCol = (mExecTrail.front().size()-1);
        else --lAheadCol;
        break;
    }
    default: { }
    }
    
    PyObject_CallFunctionObjArgs((mExecTrail[lAheadRow][lAheadCol] == eFoodPiece) ? inIfTrue : inIfFalse, NULL);
}

void AntSimulatorFast::run(PyObject* inWrappedFunc){
    this->reset();
    while(mNbMovesAnt < mMaxMoves)
        PyObject_CallFunctionObjArgs(inWrappedFunc, NULL);
}

void AntSimulatorFast::reset(void){
    mExecTrail = mOrigTrail;
    mNbMovesAnt = 0;
    mNbPiecesEaten = 0;
    mRowAnt = mRowStart;
    mColAnt = mColStart;
    mDirectionAnt = mDirectionStart;
}


/* 
 *
 * Python wrappers 
 *
 *
 */

typedef struct {
    PyObject_HEAD
    AntSimulatorFast *mInnerClass;
} AntSimulatorWrapper;


static int wrapAntSimulatorConstructor(AntSimulatorWrapper *self, PyObject *args, PyObject *kwargs){
    int lMaxMoves;
    const char *keywords[] = {"max_moves", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, (char *) "i", (char **) keywords, &lMaxMoves)) {
        return -1;
    }
    self->mInnerClass = new AntSimulatorFast(lMaxMoves);
    return 0;
}

static PyObject* wrapTurnLeft(AntSimulatorWrapper *self){
    self->mInnerClass->turnLeft();
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject* wrapTurnRight(AntSimulatorWrapper *self){
    self->mInnerClass->turnRight();
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject* wrapMoveForward(AntSimulatorWrapper *self){
    self->mInnerClass->moveForward();
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject* wrapIfFoodAhead(AntSimulatorWrapper *self, PyObject *args){
    self->mInnerClass->ifFoodAhead(PyTuple_GET_ITEM(args, 0),
                                    PyTuple_GET_ITEM(args, 1));
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject* wrapRun(AntSimulatorWrapper *self, PyObject *args){
    PyObject* func = PyTuple_GetItem(args, 0);
    self->mInnerClass->run(func);
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject* wrapParseMatrix(AntSimulatorWrapper *self, PyObject *args){  
    self->mInnerClass->parseMatrix(PyString_AsString(PyFile_Name(PyTuple_GetItem(args, 0))));
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject* wrapGetEaten(AntSimulatorWrapper *self, void *closure){
    PyObject *py_retval;

    py_retval = Py_BuildValue((char *) "i", self->mInnerClass->mNbPiecesEaten);
    return py_retval;
}

// Getters and setters (here only for the 'eaten' attribute)
static PyGetSetDef AntSimulatorWrapper_getsets[] = {
    {
        (char*) "eaten", /* attribute name */
        (getter) wrapGetEaten, /* C function to get the attribute */
        NULL, /* C function to set the attribute */
        NULL, /* optional doc string */
        NULL /* optional additional data for getter and setter */
    },
    { NULL, NULL, NULL, NULL, NULL }
};

// Class method declarations
static PyMethodDef AntSimulatorWrapper_methods[] = {
    {(char *) "turn_left", (PyCFunction) wrapTurnLeft, METH_NOARGS, NULL },
    {(char *) "turn_right", (PyCFunction) wrapTurnRight, METH_NOARGS, NULL },
    {(char *) "move_forward", (PyCFunction) wrapMoveForward, METH_NOARGS, NULL },
    {(char *) "if_food_ahead", (PyCFunction) wrapIfFoodAhead, METH_VARARGS, NULL },
    {(char *) "parse_matrix", (PyCFunction) wrapParseMatrix, METH_VARARGS, NULL },
    {(char *) "run", (PyCFunction) wrapRun, METH_VARARGS, NULL },
    {NULL, NULL, 0, NULL}
};

static void AntSimulatorWrapperDealloc(AntSimulatorWrapper *self){
    delete self->mInnerClass;
    self->ob_type->tp_free((PyObject*)self);
}

static PyObject* AntSimulatorWrapperRichcompare(AntSimulatorWrapper *self, AntSimulatorWrapper *other, int opid){
    Py_INCREF(Py_NotImplemented);
    return Py_NotImplemented;
}


PyTypeObject AntSimulatorWrapper_Type = {
    PyObject_HEAD_INIT(NULL)
    0,                                 /* ob_size */
    (char *) "AntC.AntSimulatorFast",            /* tp_name */
    sizeof(AntSimulatorWrapper),                  /* tp_basicsize */
    0,                                 /* tp_itemsize */
    /* methods */
    (destructor)AntSimulatorWrapperDealloc,        /* tp_dealloc */
    (printfunc)0,                      /* tp_print */
    (getattrfunc)NULL,       /* tp_getattr */
    (setattrfunc)NULL,       /* tp_setattr */
    (cmpfunc)NULL,           /* tp_compare */
    (reprfunc)NULL,             /* tp_repr */
    (PyNumberMethods*)NULL,     /* tp_as_number */
    (PySequenceMethods*)NULL, /* tp_as_sequence */
    (PyMappingMethods*)NULL,   /* tp_as_mapping */
    (hashfunc)NULL,             /* tp_hash */
    (ternaryfunc)NULL,          /* tp_call */
    (reprfunc)NULL,              /* tp_str */
    (getattrofunc)NULL,     /* tp_getattro */
    (setattrofunc)NULL,     /* tp_setattro */
    (PyBufferProcs*)NULL,  /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT,                      /* tp_flags */
    NULL,                        /* Documentation string */
    (traverseproc)NULL,     /* tp_traverse */
    (inquiry)NULL,             /* tp_clear */
    (richcmpfunc)AntSimulatorWrapperRichcompare,   /* tp_richcompare */
    0,             /* tp_weaklistoffset */
    (getiterfunc)NULL,          /* tp_iter */
    (iternextfunc)NULL,     /* tp_iternext */
    (struct PyMethodDef*)AntSimulatorWrapper_methods, /* tp_methods */
    (struct PyMemberDef*)0,              /* tp_members */
    AntSimulatorWrapper_getsets,                     /* tp_getset */
    NULL,                              /* tp_base */
    NULL,                              /* tp_dict */
    (descrgetfunc)NULL,    /* tp_descr_get */
    (descrsetfunc)NULL,    /* tp_descr_set */
    0,                 /* tp_dictoffset */
    (initproc)wrapAntSimulatorConstructor,             /* tp_init */
    (allocfunc)PyType_GenericAlloc,           /* tp_alloc */
    (newfunc)PyType_GenericNew,               /* tp_new */
    (freefunc)0,             /* tp_free */
    (inquiry)NULL,             /* tp_is_gc */
    NULL,                              /* tp_bases */
    NULL,                              /* tp_mro */
    NULL,                              /* tp_cache */
    NULL,                              /* tp_subclasses */
    NULL,                              /* tp_weaklist */
    (destructor) NULL                  /* tp_del */
};

PyObject* progn(PyObject *self, PyObject *args){
    for(Py_ssize_t i = 0; i < PyTuple_Size(args); i++)
        PyObject_CallFunctionObjArgs(PyTuple_GET_ITEM(args, i), NULL);
    Py_INCREF(Py_None);
    return Py_None;
}

static PyMethodDef AntC_functions[] = {
    {"progn", progn, METH_VARARGS, "Boum"},
    {NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC
initAntC(void)
{
    PyObject *m;
    m = Py_InitModule3((char *) "AntC", AntC_functions, NULL);
    if (m == NULL) {
        return;
    }
    /* Register the 'AntSimulatorWrapper' class */
    if (PyType_Ready(&AntSimulatorWrapper_Type)) {
        return;
    }
    PyModule_AddObject(m, (char *) "AntSimulatorFast", (PyObject *) &AntSimulatorWrapper_Type);
}
