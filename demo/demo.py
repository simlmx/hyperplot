from numpy import exp, log
from numpy.random import randint, uniform
import os
import hyperplot as H
from hyperplot import *
import pylab
pylab.ion()

#nb_data = 100

#data = HyperDatabase(
#                    # jobman
#                    id = range(nb_data),
#                    jobman_status = [ randint(3) for n in range(nb_data) ],
#                      
#                    # hyper param plausibles
#                    lr = [ 10. ** uniform(-7,-3) for n in range(nb_data) ],
#                    wd = [ 10. ** uniform(-5, 3) for n in range(nb_data) ],
#                    nb_neurones = [ randint(1000) for n in range(nb_data) ],
#                    layer = [ randint(3) for n in range(nb_data) ],
#                    cost = [ uniform(0,10) for n in range(nb_data) ],
#                      
#                    # fake pour tester
#                    param_discret1 = [ 'un deux trois quatre'.split()[randint(4)] for n in range(nb_data) ],
#                    param_discret2 = [ randint(10) for n in range(nb_data) ],
#)


#data = sql2hyperdatabase(user = 'hamelphi', host = 'gershwin.iro.umontreal.ca', db = 'hamelphi_db', table = 'pmsc_view')
csv_file = os.path.join(os.path.split(H.__file__)[0],'demo','pmsc_data.csv')
data = csv2hyperdatabase(csv_file)

print data
data.add_filter('jobman_status', lambda x : x == 2)
# 2d simple
cost = 'validaucroctag'
hyperscatter(data, x = 'lr', y = cost, title = 'valid en fonction du lr')

# 3d
hyperscatter(data, x= 'lr', y = 'meldim', z = cost)
# rajouter un filtre

# 2d avec sans log mais qui devrait + log
hyperscatter(data, x = 'l2', y = cost)
hyperscatter(data, x = ('l2', 'log'), y = cost)

# on rajoute du flafla
hyperscatter(data, x = 'lr', y = 'complexity', c = 'time', t='id', s = 'meldim', z = cost)

# colonne virtuelle
data.add_virtual_column('mean time epoch', ['time', 'batchcount'], lambda t, bc : t/bc)

print data

# plot de la colonne virtuelle
hyperscatter(data, x = 'mean time epoch', y = cost, title = 'demo de colonne virtuelle')

# parse func
#hyperscatter(data, x = 'mean time epoch', y = 'validaucroctag', t = ('jobman_status', lambda x : 'oups' if x == 5 else ''), title = 'demo de colonne virtuelle2')

# bidon pour le bruit
nb_data = 1000
data = HyperDatabase( par1 = [ randint(10) for n in range(nb_data) ],
                      par2 = [ randint(5) for n in range(nb_data) ],
                      par3 = [ randint(3, size=(3)) for n in range(nb_data) ],
                      texte = ['un deux trois'.split()[randint(3)] for n in range(nb_data) ],
                      cost = [ uniform(10) for n in range(nb_data) ],
                    )

hyperscatter( data, x = 'par1', y = 'par2', c = 'cost' )
data.add_filter('par1', filtering.between(0,1, name='par1'))
data.add_filter('par2', filtering.between(0,1, name='par2'))
hyperscatter( data, x = 'par1', y = 'par2', c = 'cost' , t = 'texte')
# parse func
hyperscatter( data, x = 'par1', y = 'par2', c = 'cost' , t = ('texte', lambda x : {'un':1, 'deux':2, 'trois':3}[x]))
data.remove_filter('par1')
# get_el
hyperscatter( data, x = ('par3', lambda x : x[0]), y = ('par3', lambda x : x[1]), title='gel_el')

#, c = 'time', t = 'id', z = 'meldim', )
#hyperscattter(data, x = 'meldim', y = 'lr', z = 'validaucroctag')
#hyperscatter(data, x = 'l2', y = 'validaucroctag', title = 'valid en fonction du lr', c = 'time', t = 'id', z = 'meldim', s =  )

raw_input()


                      
