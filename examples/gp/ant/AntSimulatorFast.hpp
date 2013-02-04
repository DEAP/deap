#include <Python.h>

#if PY_MAJOR_VERSION >= 3
#define PY3K
#endif

#include <string>
#include <map>
#include <vector>
#include <iostream>
#include <fstream>
#include <limits>
#include <algorithm>
#include <cmath>

#define ROWS_NBR 32
#define COLS_NBR 32

class AntSimulatorFast
{
public:
    
    enum State {eStart='S', eEmpty='.', ePassed='x',
                eFoodPiece='#', eEatenPiece='@',
                eAntNorth='^', eAntEast='}', eAntSouth='v', eAntWest='{'};
    
    AntSimulatorFast(unsigned int inMaxMoves);
    void parseMatrix(char* inFileStr);
    
    void turnLeft(void);
    void turnRight(void);
    void moveForward(void);
    
    void ifFoodAhead(PyObject* inIfTrue, PyObject* inIfFalse);
    
    void run(PyObject* inWrappedFunc);
       
    unsigned int mNbPiecesEaten;  //!< Number of food pieces eaten.
    
private:
    void reset(void);
    
    std::vector< std::vector<char> > mOrigTrail; //!< Initial trail set-up.
    unsigned int mMaxMoves;       //!< Maximum number of moves allowed.
    unsigned int mNbPiecesAvail;  //!< Number of food pieces available.
    unsigned int mRowStart;       //!< Row at which the ant starts collecting food.
    unsigned int mColStart;       //!< Column at which the ant starts collecting food.
    unsigned int mDirectionStart; //!< Direction at which the ant is looking when starting.

    std::vector< std::vector<char> > mExecTrail; //!< Execution trail set-up.
    unsigned int mNbMovesAnt;     //!< Number of moves done by the ant.
    unsigned int mRowAnt;         //!< Row of the actual ant position.
    unsigned int mColAnt;         //!< Column of the actual ant position.
    char         mDirectionAnt;   //!< Direction in which the ant is looking.
}; 
