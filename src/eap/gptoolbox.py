from functools import partial

class UnaryOperation():
      def __init__(self,symbol):
          self.mSymbol = symbol
          self.mArity = 1
      def __call__(self,right):
          return "%s(%s)" % (str(self.mSymbol), str(right)) # compatible with Python 2.3 to 2.5.2
      def __repr__(self):
          return self.mSymbol

class BinaryOperation():
      def __init__(self,symbol):
          self.mSymbol = symbol
          self.mArity = 2
      def __call__(self,left,right):
          return "(%s %s %s)" % (str(left), str(self.mSymbol), str(right)) # compatible with Python 2.3 to 2.5.2
      def __repr__(self):
          return self.mSymbol
          
class Function():
     def __init__(self, func, arity = None):
         self.mName = func.__name__
         if arity == None:
             try:
                 self.mArity = func.func_code.co_argcount
             except AttributeError:
                 raise TypeError("Arity of the function couldn't be computed.")
         else:
             self.mArity = arity
         # Create the template string based on the arity
         lString = []
         lString.append(self.mName)
         lString.append('(')
         for i in xrange(self.mArity):
              lString.append('%s')
              lString.append(',')
         lString[-1] = ")"
         self.mSeq = "".join(lString)
         
     def __call__(self,*args):
         if len(args) == self.mArity:
             return self.mSeq % args # compatible with Python 2.3 to 2.5.2
         else:
             lError = "%s() takes exactly %s argument (%s given)" % (self.mName, str(self.mArity), str(len(args)) )
             raise TypeError(lError)
             
class ToolboxGP(dict):
     def __init__(self):
          self.mPrimitiveSet = []
          self.mTerminalSet = []
          self.mSymbolSet = []
          self.mFuncDict = dict()
     def addFunction(self, func, arity=None):
          setattr(self, func.__name__, Function(func, arity))
          self.mFuncDict[func.__name__] = func
          self.mPrimitiveSet.append(getattr(self, func.__name__))
     def addOperation(self, name, opSymbol, type='binary'):
          if type == 'binary':
              setattr(self, name, BinaryOperation(opSymbol))
          elif type == 'unary':
              setattr(self, name, UnaryOperation(opSymbol))
          self.mPrimitiveSet.append(getattr(self, name))
     def addSymbol(self, symbol):
          self.mSymbolSet.append(symbol)
          self.mTerminalSet.append(symbol)
     def addTerminal(self, term):
          def reprFunction(func):
              return repr(func())
          try:
              setattr(self, term.__name__, partial(reprFunction, term))
              self.mFuncDict[term.__name__] = term
              self.mTerminalSet.append(getattr(self, term.__name__))
          except AttributeError:
              self.mTerminalSet.append(term)

    
if __name__ == '__main__':
    import math
    def safeDiv(left, right):
        try:
            return left / right
        except ZeroDivisionError:
            return 0
    lToolBox = ToolboxGP()
    lToolBox.addOperation('add', '+')
    lToolBox.addOperation('sub', '-')
    lToolBox.addOperation('neg', '-', 'unary')
    lToolBox.addFunction(safeDiv)
    lToolBox.addFunction(math.cos, 1)
    print lToolBox.add(1,2)
    print lToolBox.neg(1)
    print lToolBox.sub(1,2)
    print lToolBox.safeDiv(12,2)
    print lToolBox.cos('x')
    print lToolBox
