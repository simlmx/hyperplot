import os
import pylab
import hyperplot as H

## Fetching the database on the sql server.
#user = 'hamelphi'
#host = 'gershwin.iro.umontreal.ca'
#db = 'hamelphi_db'
#table = 'agg_feat2_view'
#data = H.sql2hyperdatabase(user=user,host=host,table=table,db=db)

# Loading from CSV instead (Because of permissions)
csv_file = os.path.join(os.path.split(H.__file__)[0],'demo','pfc_data.csv')
data = H.csv2hyperdatabase(csv_file)

# Applying a couple of filters.
data.add_filter('jobman_status', H.filtering.eq(2))
data.add_filter('pcadim', H.filtering.eq(120))
data.add_filter('overlap', H.filtering.eq(2))
data.add_filter('agglen', H.filtering.between(100,200))
data.add_filter('validaucroctag', H.filtering.gt(0.5))
data.add_filter('time', H.filtering.between(1000,20000))
data.add_filter('dataset',H.filtering.notfind('mfcc'))


# Filtering categories, and changing some category names.
black_list=[]
#box_names={}
black_list = ['skew','kurt','moments','moments_max','moments_max_min']
box_names = {'skew':'3rd moment',
            'kurt':'4th moment',
            'moments':'all moments',
            'moments_max_min':'all functions',
            'var':'    var    ',
            'max':'    max    ',
            'mean':'   mean    ',
            'min':'    min    ',
            'max_min':'  max_min  ',}
    
    

box_column = 'aggtype'
rotation = 15.5

fig = pylab.figure()
fig.subplots_adjust(hspace=0.4)

ax1 = fig.add_subplot(211)
ax1,order = H.hyperboxplot(data,
                   box_column=box_column,
                   title='PFC pooling functions',
                   black_list=black_list,
                   cost_name='validaucroctag',
                   cost_label='Valid AUC-tag',
                   box_names=box_names,
                   ax1=ax1,
                   rotation=rotation,
                   return_order=True)

ax1 = fig.add_subplot(212)
ax1 = H.hyperboxplot(data,
                   box_column=box_column,
                   title='Training time',
                   black_list=black_list,
                   cost_name='time',
                   cost_label='Training time (s)',
                   box_names=box_names,
                   ax1=ax1,
                   rotation=rotation,
                   order=order)
