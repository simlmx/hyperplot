import hyperplot as H
#from hyperplot import hyperscatter, filtering
#from hyperplot.hyperdatabase import csv2hyperdatabase, sql2hyperdatabase, get_el, HyperDatabase
from numpy.random import uniform, normal, randint
from numpy import exp, log
import os
try:
    import pylab
    pylab.ion()
except:
    print 'Matplotlib does not seem to be installed. You will not be able to do much.'

def generate_data():
    print H.__file__

    data = H.HyperDatabase(
        ('hyper_par1', uniform(size=100)),
        ('hyper_par2', normal(size=100)),
        ('couples', normal(size = (100,2))),
        ('cost', normal(2, 3, size=100)),
        ('log_1d', exp(uniform(2,3, size=100))),
        ('log_tuples', exp(uniform(log(2),log(20000), size=(100,3,2)))),
        autre_hyper = uniform(100,101, size=100),
        discrete = randint(6, size=(100,10)),
        texte = [ ['text1', 'text2'][randint(2)] for x in range(100) ],
        texte2 = [ ['a' ,'b', 'c', 'd'][randint(4)] for x in range(100) ],
        tzz = range(100),
    )
    data.add_virtual_column('sum_of_hyper1_and_hyper2', ['hyper_par1', 'hyper_par2'], lambda x,y : x+y)
    data.add_virtual_column('texte_texte2', ['texte', 'texte2'], lambda x,y : '%s_%s' % (x,y))
    return data

def hyper_test():
    data = generate_data()

    # 2D
    H.hyperscatter(data, x = 'hyper_par1', y = 'cost', title='2d')
    # 2D + size
    H.hyperscatter(data, x = 'hyper_par1', y = 'cost', title='2d', s = ('cost', lambda x:abs(x)*10.))
    # 2D + color
    H.hyperscatter(data, x = 'hyper_par1', y = 'cost', c = 'hyper_par2', title='2d + color')
    #fixed size
    H.hyperscatter(data, x = 'hyper_par1', y = 'cost', c = 'hyper_par2', s = 100, title='2d + color')
    # 3D
    H.hyperscatter(data, x = 'hyper_par1', y = 'hyper_par2', z = 'cost', title='3d')
    # 3D + color + parse_func
    H.hyperscatter(data, x = 'hyper_par1', y = 'hyper_par2', z = 'cost', c = ('couples', H.get_el(0)), title='3d + color + parse_func')
    # 2d + log + parse_func + color
    H.hyperscatter(data, x = ('log_1d', 'log'), y = 'autre_hyper', c = ('couples', H.get_el(0)), title='3d + log + parse_func + color')
    # 3D + log + parse_func
    H.hyperscatter(data, x = ('log_tuples', H.get_el(-1,-1), 'log'), y = 'hyper_par2', z = 'cost', c = ('couples', H.get_el(0)), title='3d log')
    # 3D + discrete
    H.hyperscatter(data, x = 'hyper_par1', y = 'hyper_par2', z = ('discrete', H.get_el(5)), title='3d discrete')
    # other args
    H.hyperscatter(data, x='hyper_par1', y='hyper_par2', title='titre au graph')

    # texte 2D
    H.hyperscatter(data, x='hyper_par1', y = 'hyper_par2', c = 'tzz', t='texte_texte2')
    # text 3D
    H.hyperscatter(data, x='hyper_par1', y = 'hyper_par2', z = ('discrete', H.get_el(5)), c = 'hyper_par2', t=('hyper_par2', lambda x : '%0.2f' % x))
    # 3D + text + size + color
    H.hyperscatter(data,
        x = 'hyper_par1',
        y = 'hyper_par2',
        z = ('discrete', H.get_el(5)),
        c = 'cost',
        t = ('cost', lambda x : '%0.2f' % x),
        s = ('cost', lambda x : 5.*x*x)
    )



def filter_test():
    data = generate_data()
    print data
    data.print_filters()
    data.add_filter('discrete', H.filtering.outside(3,5, include_b=False, parse_func=H.get_el(5)))
    data.add_filter('hyper_par1', H.filtering.ge(.1))
    data.print_filters
    data.add_filter('texte_texte2', H.filtering.eq('text1_c', name='patate'))
    data.remove_last_filter()
    data.print_filters()
    data.add_filter('texte_texte2', H.filtering.eq('text1_c', name='patate_filter'))
    data.print_filters()
    data.remove_filter('patate_filter')
    data.print_filters()
    data.remove_all_filters()
    data.print_filters()

    data.add_filter('hyper_par1', H.filtering.ge(.1, name = 'filter1'))
    normal = False
    try:
        data.add_filter('hyper_par2', H.filtering.ge(.2, name='filter1'))
    except ValueError:
        normal = True
    assert normal
    normal = False
    try:
        data.add_filter('texte_texte2', 123)
    except TypeError:
        normal = True
    assert normal

    data.print_filters()

    print data


    #H.hyperscatter(data, x = ('discrete', H.get_el(4)), y = 'hyper_par1', c = ('texte', lambda x : {'text1' : 0, 'text2' : 1}[x]), title='filters')


def csv_test():
    csv_file = os.path.join(os.path.split(H.__file__)[0],'test','csv_test.csv')
    data = H.csv2hyperdatabase(csv_file)
#    data.filter_all_null()
    for name in data.column_names:
        data.add_filter(name, H.filtering.notnull(name= 'notnull_' + name))
    H.hyperscatter(data, x=('poolingfactors', H.get_el(0,0)), y=('poolingfactors', H.get_el(1,0)), c = 'bestkendall', title='csv1')

#    data.filter('bestkendall', filter_lt(.66))
    data.add_filter('poolingfactors', H.filtering.outside(2,8, parse_func=H.get_el(0,0)))
    data.add_filter('poolingfactors', H.filtering.between(4,5, parse_func=H.get_el(1,0)))

    print data

    H.hyperscatter(data, x=('poolingfactors', H.get_el(0,0)), y=('poolingfactors', H.get_el(1,0)), c = 'bestkendall', title='csv2')

try:
    import pg
    is_pg_installed = True
    def sql_test():
        user = os.environ['USER'].lower()
        do_test = False
        if user in ['lemiesim', 'simon']:
            user = 'lemiesim'
            table = 'view_apr28_arch5'
            do_test = True
        elif user in ['hamelphi','phil']:
           user = 'hamelphi'
           table = 'conv_filter1_view'
           do_test = True
        if do_test:

            data = H.sql2hyperdatabase(user = user, host = 'gershwin.iro.umontreal.ca', db = user + '_db', table = table)

            if user == 'lemiesim':
                data.add_filter('bestkendall', H.filtering.notnull())
                H.hyperscatter(data, x=('poolingfactors', H.get_el(0,0)), y=('poolingfactors', H.get_el(1,0)), z='bestkendall', title='salut')

            elif user == 'hamelphi':
                data.add_filter('jobman_status', H.filtering.eq(2))
                data.add_filter('validcost', H.filtering.notnull())
                H.hyperscatter(data, x='lr', y = ('pcadim', lambda x : {80:0,120:1}[x]), c='validcost', title='scatterplot')

            print data._filters
            print data
except ImportError:
    print 'Skipping the sql tests. Install pygresql ton enable.'
    is_pg_installed = False


if __name__ == '__main__':
    generate_data()
    filter_test()
    hyper_test()
    csv_test()
    if is_pg_installed:
        sql_test()
    raw_input('press Enter to quit')





