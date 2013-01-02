from copy import copy
import csv, os
from os.path import exists, join
from filtering import Filter
import numpy

class ColumnBase(object):
    def get_data(self):
        raise NotImplementedError('You have to subclass ColumnBase AND implement get_data')

    def __getitem__(self,i):
        return self.get_data(indices=[i])[0]

    @property
    def nb(self):
        """ Returns the number of data. """
        return len(self.get_data())


class Column(ColumnBase):
    def __init__(self, data):
        self._data = data

        self.isvirtual = False

    def get_data(self, parse_func=None, indices=None):
        """ Gets the data."""
        if parse_func is None:
            parse_func = lambda x : x

        if indices is None:
            data = self._data
        else:
            data = [self._data[i] for i in indices]

        return map(parse_func, data)


class VirtualColumn(ColumnBase):
    """ A Column that is a function of other columns. """

    def __init__(self, columns, func, ignore_nones = True):
        """
            columns
                Column from which we will calculate stuff.
                Can be an iterable of columns or a single columns.
            func
                Function that will use the other functions to calculate stuff.
            ignore_nones:
                If True, func will return None if one of his arguments is None, without actually applying func.

            e.g.
            if columns = ('a','b') and func = lambda x,y : x + y
            The resulting column (self) will act just like a column that is the sum of columns 'a' and 'b'.
        """
        if isinstance(columns, ColumnBase):
            columns = [columns]
        self._columns = columns

        old_func = func
        if ignore_nones:
            def new_func(*args):
                for a in args:
                    if a is None:
                        return None
                return old_func(*args)
            func = new_func

        self._func = func

        self.isvirtual = True

    def get_data(self, parse_func=None, indices=None):
        """ Gets the data."""
        if parse_func is None:
            parse_func = lambda x : x
        func = self._func
        cols = self._columns

        return [parse_func(func(*args)) for args in zip(*[ c.get_data(indices=indices) for c in cols ])]


class HyperDatabase(object):
    """
        Typically, each row represent an experiment, and each column represent an hyperparameter or cost etc.
        self.columns contains the columns and each column contains the corresponding row elements.

        e.g.

        cost | hyper1 | hyper2
        -----+--------+-------
        55   |   2    |    1
        4    |   2    |    2
        2    |   1    |    1
        10   |   1    |    2

        would be reprsented here as three columns, 'cost', 'hyper1' and 'hyper2' with every column containing
        4 elements ( resp. [55,4,2,10], [2,2,1,1], [1,2,1,2] )


        These can then be filtered using Filters. e.g.
        self.add_filter('cost', lambda x : True if x > 3 else False) would discard the third row.
        self.get_data('hyper1') would then return [2,2,1] (third row skiped)

    """
    def __init__(self, *args, **kwargs):
        """ args
                couples of the form (name, data)
            kwargs
                keys = name, values = data

            They all will be put in one dictionary.
        """
        self.columns = kwargs
        self.columns.update(args)
        for k,v in self.columns.iteritems():
            self.columns[k] = Column(v)

        self._filters = []
        self._indices = range(self.nb)

        # we will set this to true when we change something (e.g. add/delete) to a filter
        self._filters_need_update = False

        self.id_dict={} # mapping between the id of a row and its index in the data lost
        if 'id' not in self.column_names:
            for id in self._indices:
                self.id_dict[id] = id
        else:
            ids = self.get_data('id')
            for id,data_id in zip(ids,self._indices):
                self.id_dict[id] = data_id

    @property
    def nb(self):
        """ Gets the nb of rows (before filtering). """
        return self.columns[self.columns.keys()[0]].nb

    @property
    def nb_eff(self):
        """ Get the effective nb of rows (after filtering). """
        self.update_filters()
        return len(self._indices)

    @property
    def column_names(self):
        """ Gets the list of all the names the hyper parameters.
        """
        return self.columns.keys()

    @property
    def real_column_names(self):
        """ Gets the list of all the names the hyper parameters.
        """
        return self.get_real_columns().keys()

    def __len__(self):
        return self.nb_eff

    def __getitem__(self,i):
        return self.get_row(i)

    def __iter__(self):
        for i in range(len(self)):
            yield self[i]

    def get_real_columns(self):
        columns={}
        for key,column in self.columns.iteritems():
            if not column.isvirtual:
                columns[key] = column
        return columns

    def get_data(self, name, parse_func=None, indices=None):
        """ Gets data for a single column.

            name
                The name of the column.
            parse_func
                A function to be mapped to the data
            indices
                Only return those indices. By default, everything but filtered out data.
        """
        if indices is None:
            self.update_filters()
            indices = self._indices
        return self.columns[name].get_data(parse_func, indices)

    def get_all_data(self, name, parse_func=None):
        """
        returns all data from a column, ignoring filters
        """
        return self.columns[name].get_data(parse_func, indices = None)

    def get_column_idx(self,column_name):
        """
        returns the index of a column
        """
        for i,col in enumerate(self.column_names):
            if col == column_name:
                return i
        print 'Column %s not found' % column_name

    def add_virtual_column(self, name, columns, func, ignore_nones = True):
        """ Adds a virtual column.

            columns
                Names for the columns from which we will calculate stuff.
                Can be an iterable of column names or a single column name.
            func
                Function that will use the other functions to calculate stuff.
            ignore_nones:
                If True, func will return None if one of his arguments is None, without actually applying func.

            e.g.
            if columns = ('a','b') and func = lambda x,y : x + y
            The resulting column (self) will act just like a column that is the sum of columns 'a' and 'b'.
        """
        if isinstance(columns, str): columns = [columns]

        self.columns[name] = VirtualColumn([self.columns[c] for c in columns], func, ignore_nones)

    def filter(self, *args, **kwargs):
        print 'Warning : Database.filter is deprecated, use Database.add_filter instead'
        self.add_filter(*args, **kwargs)

    def add_filter(self, column_name, filter):
        """ Adds a filter.

            column_name
                Name of the column you want to filter.
            filter
                A filtering.Filter object, or a function (which takes one element and returns True of False) that will be
                converted into a Filter.

                Be careful, if you want to be able to remove the filter, you have to give him a name,
                e.g. self.add_filter('col', filtering.Filter(lambda x : True, name='stupid_filter'))

            We will keep the indices of the elements of the column `column_name`
            that returned True and reject the others when calling self.get_data.
        """

        if not isinstance(filter, Filter):
            filter = Filter(filter)

        if filter.name != '':
            for _,f in self._filters:
                if f.name == filter.name:
                    raise ValueError('There already is a filter with the name %s' % f.name)

        self._filters.append((column_name, filter))
        self._filters_need_update = True

    def remove_filter(self, filter_name):
        """ Removes a filter. """
        filter_found=False

        if isinstance(filter_name,int):
            self.remove_filter_idx(filter_name)
            filter_found=True

        elif isinstance(filter_name,str):
            for i,(c_name, f) in enumerate(self._filters):
                if f.name == filter_name:
                    self.remove_filter_idx(i)
                    filter_found=True

        if not filter_found:
            print 'Filter %s not found.' % (str(filter_name))
        else:
            self._filters_need_update = True

    def remove_filter_idx(self, filter_idx):
        """ Removes a filter from the filter list """
        if filter_idx < len(self._filters):
            self._filters.pop(filter_idx)
            self._filters_need_update = True
        else:
            print 'Filter index %i out of range' % filter_idx

    def remove_last_filter(self):
        """ Removes the last added filter.
            Can be called multiple times
        """
        self._filters.pop(-1)
        self._filters_need_update = True

    def remove_all_filters(self):
        """ Removes all the filters. """
        self._filters = []
        self._filters_need_update = True

    def update_filters(self):
        """ Put together all filters.
            This will be automatically called, if necessary, when calling self.get_data(...)
        """
        if self._filters_need_update:
            # s is what will be printed if something changes
            s = ''
            s += '** Updating the filters. **'
            s += '\nStarting with %i elements.' % self.nb
            indices = range(self.nb)
            for col_name, filter in self._filters:
                filter_strrepr = ' (%s)' % filter.strrepr if isinstance(filter, Filter) and not filter.strrepr == '' else ''
                name = filter.name
                s += '\nApplying filter %son column %s' % ('"%s" ' % name if name is not '' else '', col_name) + filter_strrepr
                data = self.get_data(col_name, indices=range(self.nb))
                indices = [ i for i in indices if filter(data[i]) ]
                s += '. There are now %i elements left' % len(indices)

            # If nothing changed, we don't bother printing what the filters did.
            # There is the possibily that an other set of *different* filters end up with the same results... but let's
            # say we don't care. I (Simon) prefer it this way, printing every time something might've change gives a lot
            # of printing sometimes.
            if indices != self._indices:
                self._indices = indices
                print s
            self._filters_need_update = False

    def print_filters(self):
        """ Prints the filters. """
        print '** Filters **'
        if len(self._filters) == 0:
            print ' There are no filters.'
        for i, (col_name, filter) in enumerate(self._filters):
            name = filter.name
            if name == '' : name = '<no name>'
            strrepr = filter.strrepr
            if strrepr != '': strrepr = ', checking if %s' % strrepr
            print ' Filter %i (%s) applied on %s%s' % (i, name, col_name, strrepr)

    def print_keys(self,keylist):
        st=''
        print_data = []
        for k in keylist:
            st+=k
            st+='\t'
            print_data.append( self.get_data(k))
        st+='\n____________________________________________________________________________\n'
        print_data = numpy.array(print_data).T
        for d in print_data:
            for v in d:
                st+=str(v)
                st+=' |\t'
            st+='\n'
        print st

    def column_class(self, column_name, new_column_name, order_func=None):
        """
        Generates a virtual column with each category in the original column
        corresponding to an integer in the new column
        """
        col_dat = self.get_all_data(column_name)
        categories = list(set(col_dat))

        if order_func is None:
            ordered_cats = sorted(categories)
        else:
            ordered_cats = order_func(categories)

        cat_dict = {}
        for i,cat in enumerate(ordered_cats):
            cat_dict[cat] = i
            print i,cat

        func = lambda x: cat_dict.get(x,'None')
        self.add_virtual_column(new_column_name, column_name, func)

    def get_row(self,i,real_only=False):
        row = []
        if real_only:
            column_names = self.get_real_columns()
        else:
            column_names = self.column_names
        for column in column_names:
            row.append(self.columns[column][i])
        return row

    def get_row_dict(self,i):
        rowdict={}
        for column in self.column_names:
            rowdict[column] = self.columns[column][i]
        return rowdict

    def get_row_by_id(self,id,real_only=False):
        i = self.id_dict.get(id,None)
        if i is not None:
            return self.get_row(i,real_only=real_only)
        else:
            print 'Id %i not found in database' % id

    def __str__(self):
        self.update_filters()
        s =  '<Database - contains %i elements' % self.nb
        if self.nb != self.nb_eff:
            s += ' ( %i after filtering )' % self.nb_eff
        for n in sorted(self.columns.iterkeys()):
            a = "\n  '%s'"  % n

            data = self.get_data(n)

            def data2str(d):
                s = str(d)
                if len(s) > 22:
                    s = s[:20] + '..'
                return s

            if len(data) > 3:
                b = ' :  [ %s, %s, ... , %s ]' % tuple([data2str(data[i]) for i in [0,1,-1]])
            elif len(data) <= 3 and len(data) > 0:
                b = ' :\t[ '
                for d in data:
                    b += '%s,' % data2str(d)
                b = b[:-1]
                b += ' ]'
            else:
                b = ''

            s += a + b
        return s + '\n>'

    def dump(self,filename,post_filter=True,real_only=True):
        """
        Dumps the data to a csv file.
        """
        f = csv.writer(open(filename,'w'))

        if real_only:
            column_names = self.real_column_names
            if self._filters_need_update:
                self.update_filters()
            rows_idx = self._indices
        else:
            column_names = self.column_names
            rows_idx = range(self.nb)

        f.writerow(column_names)

        for i in rows_idx:
            row_data = self.get_row(i, real_only)
            f.writerow(map(data2str_item, row_data))



################
###   CSV  #####
################

def str2data_item(item):
    """ parse a single item """
    if isinstance(item, str):
        item = item.strip('\N"')
        if item == '':
            return None
        try:
            item_eval = eval(item)
            #check if it is a function, if yes, keep the string
            if not hasattr(item_eval, '__call__'):
                item = item_eval
        except:
            pass
#            item = item
    return item

def data2str_item(item):
    if item is None:
        return ''
    else:
        return str(item)

def csv2hyperdatabase(csvfile_path):
    """ imports from a csv file to our "hyper_data" framework """
    f = csv.reader(open(csvfile_path))
    headers = f.next()
    columns = zip(*f)
    for i,c in enumerate(columns):
        columns[i] = map(str2data_item, c)

    return HyperDatabase(*zip(headers, columns))

###############
###   SQL   ###
###############

def sql2hyperdatabase(user, host, db, table):

    # password
    # is it possible that someone would not have a $HOME env variable?
    home = os.environ['HOME']
    path = join(home, '.jobman_%s_db' % user)
    pg_pass_path = join(home, '.pgpass')

    if exists(pg_pass_path):
        passw = None
    elif exists(path):
        passw = open(path).read().strip()
    else:
        import getpass
        passw = getpass.getpass('Password :')

    # sql
    import pg
    db = pg.connect(dbname = db, host = host, user = user, passwd = passw)

    res = db.query('select * from  %s' % table).dictresult()
    keys = res[0].keys()
    data = HyperDatabase(*[(k, [ str2data_item(d[k]) for d in res]) for k in keys])
    return data


############################
## some parsing functions ##
############################

def get_el(*args):
    """
        f = get_element(1,2,3)
        f(a) will return a[1][2][3]
    """
    def f(x):
        for a in args:
            x = x[a]
        return x
    return f
