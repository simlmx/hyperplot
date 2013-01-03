class Filter(object):
    def __init__(self, test_func, name='', strrepr='', parse_func=None):
        """
        A filter function.

        test_funcs
            A function to test on each element.\

        name
            A name for the filter. 
            
        parse_func
            A function to parse an element before testing it.
            
        strrepr
            A string representing the function (e.g. " > .5")
        
        e.g. if test_funcs = f1
             and parse_func = lambda x : x[0]
             when calling self.__call__(x), we will return True iff f1(x[0]) is True
        """
                    
        self.test_func = test_func
        
        if not hasattr(test_func, '__call__'):
            raise TypeError('The filter must be callable.')

        
        if parse_func is None:
            parse_func = lambda x : x
        self.parse_func = parse_func
        
        self.strrepr = strrepr
        if not isinstance(name,str):
            print 'Warning: filter name should be a string. Casting it to string'
            name = str(name)
        self._name = name
        
    @property
    def name(self):
        """ Gets the name of the filter. """
        return self._name  
        
    def __call__(self, x):
        """
        See __init__ doc.
        """

        v = self.test_func(self.parse_func(x))      
        #print '%s %s == result %s' % (str(self.parse_func(x)), self.strrepr, str(v))
        return v

##        
# some ready-to-use filters
##

def notnull(name='') : return Filter(lambda x : False if x is None else True, strrepr = 'is not null', name=name)
notnone = notnull
def gt(b, name='', parse_func=None): return Filter(lambda x : x > b, strrepr = '> %s' % b, name=name, parse_func=parse_func)
def ge(b, name='', parse_func=None) : return Filter(lambda x : x >= b, strrepr = '>= %s' % b, name=name, parse_func=parse_func)
def lt(a, name='', parse_func=None): return Filter(lambda x : x < a, strrepr = '< %s' % a, name=name, parse_func=parse_func)
def le(a, name='', parse_func=None): return Filter(lambda x : x <= a, strrepr = '<= %s' % a, name=name, parse_func=parse_func)
def eq(a, name='', parse_func=None): return Filter(lambda x : x == a, strrepr = '== %s' % a, name=name, parse_func=parse_func)
def neq(a, name='', parse_func=None): return Filter(lambda x : x != a, strrepr = '!= %s' % a, name=name, parse_func=parse_func)
def between(a,b, include_a=True, include_b=True, name='', parse_func=None):
    def f(x):
        if a < x < b:
            return True
        if x == a and include_a:
            return True
        if x == b and include_b:
            return True
        return False
        
    left = '[' if include_a else ']'
    right = ']' if include_b else '[' 
    
    return Filter(f, strrepr = 'in %s%f, %f%s' % (left, a, b, right), name = name, parse_func = parse_func)
    
def outside(a, b, include_a=True, include_b=True, name='', parse_func=None):
    def f(x):
        if x > b or x < a:
            return True
        if x == a and include_a:
            return True
        if x == b and include_b:
            return True
        return False
        
    left = ']' if include_a else '['
    right = '[' if include_b else ']' 
    return Filter(f, strrepr = 'outside %s%f, %f%s' % (left, a, b, right), name = name, parse_func = parse_func)

def find(s, name='', parse_func=None): return Filter(lambda x : x.find(s) != -1, name=name, parse_func=parse_func)
def notfind(s, name='', parse_func=None): return Filter(lambda x : x.find(s) == -1, name=name, parse_func=parse_func)
