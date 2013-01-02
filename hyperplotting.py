import pylab as PP
import mpl_toolkits.mplot3d.axes3d as PP3
from numpy import array, exp
from numpy.random import normal
import filtering
import numpy

def hyperscatter(data, *args, **kwargs):
    """
        data
            HyperDatabase
        *args and *kwargs :
            x, y, z, c, s, t
                They correspond to scatter arguments (exemple t). Only x and y are not optional.
                Each of these argument correspond to one dimension in a plot.
                They can be either
                    name
                    (name, parse_func)
                    (name, scale_type)
                    (name, parse_func, scale_type)
                    None (in which case it is ignored)
                where name is a key of data
                and parse_func will be passed to data[name].get_data(...)

                If t (for "text") is specified, we will add specified text at (x,y) or (x,y,z) coords.
                's' can also be an integer

            title
                Title for the graph.

            ax
                Axes where to put the plot

            any other argument will be passed to scatter

    """

    args_keys = 'xyzcst'[:len(args)]
    kwargs.update(dict(zip(args_keys,args)))
    # all args are now in kwargs

    # we separate arguments into two categories
    # the one that are for the data (x,y,z,c,s) and the others, that will be
    # passed to scatter

    data_args = kwargs

    #keys1 = filter(lambda x : True if x in 'xyzcs' else False, data_args)
    #keys2 = filter(lambda x : True if x not in 'xyzcs' else False, data_args)

    #other_args = dict(zip(keys2, [ data_args[k] for k in keys2 ]))
    #data_args = dict(zip(keys1, [ data_args[k] for k in keys1 ]))

    #print 'data_args', data_args
    #print 'other_args', other_args


    if not ('x' in data_args and 'y' in data_args):
        raise ValueError('At least x and y must be passed to HyperPlotter.plot(...)')

    # little shorcuts that returns elements from a list that are also in data_args
    is_provided = lambda a : True if a in data_args and data_args[a] is not None else False
    get_provide_from = lambda l : [ k for k in l if (is_provided(k))]

    # change every argument to (name, parse_func, scale_type)
    for k in get_provide_from('xyzcst'):
        v = data_args[k]

        parse_func = lambda x : x
        scale_type = 'linear'
        # name
        if isinstance(v, str):
            name = v
            data_args[k] = (name, parse_func, scale_type)
        elif hasattr(v, '__getitem__'):
            name = v[0]
            # (name, ?)
            if len(v) == 2:
                # (name, scale_type)
                if isinstance(v[1], str):
                    scale_type = v[1]
                elif hasattr(v[1], '__call__'):
                    parse_func = v[1]
                else:
                    raise TypeError('Wrong arguments associated with parameter %s' % k)
            # (name, parse_func, scale_type)
            elif len(v) == 3:
                if isinstance(v[2], str):
                    scale_type = v[2]
                else:
                    raise TypeError('scales types must be strings (parameter %s)' % k)
                if hasattr(v[1], '__call__'):
                    parse_func = v[1]
                else:
                    raise TypeError('parse_func must be a function (parameter %s)' % k)

            data_args[k] = (name, parse_func, scale_type)






    # 3D or not
    d3 = False
    if 'z' in data_args and data_args['z'] is not None:
        d3 = True
    if not is_provided('ax'):
        fig = PP.figure()
        ax = PP3.Axes3D(fig) if d3 else PP.subplot(111)
    else:
        ax = data_args.pop('ax')

    if is_provided('title'):
        ax.set_title(data_args.pop('title'))

    scatter = ax.scatter3D if d3 else ax.scatter

    scatter_args = {}
    #
    # x y z
    #
    for k in get_provide_from('xyz'):

        name, f, scale = data_args[k]

        # scale
        if scale != 'linear':
            if d3:
                # foo = hack ... that doesn't work yet
                # foo = getattr(ax, 'w_%saxis' % k)
                # getattr(foo, 'set_scale')(scale)
                print "Warning : Log scalling doesn't seem to work with 3D plots. I think it's a bug in matplotlib."
                print "It's disabled for now and won't be effective for axis %s (%s)" % (k, name)
            else:
                getattr(ax, 'set_%sscale' % k)(scale)

        # label
        getattr(ax, 'set_%slabel' % k)(k + ' - ' + name)

        # data itself
        current_data = data.get_data(name,f)

        # noise added to discrete data
        # TODO : This part is buggy and should probably be looked at
        # Also a lot could be improved -- simon
        current_data_set = set(current_data)
        nb_classes = len(current_data_set)
        nb_items = len(current_data)
        nb_el_per_class = 1. * nb_items/nb_classes
        #print 'nb_el_per_class', nb_el_per_class
        if nb_el_per_class  > 2. :
            delta = max(current_data) - min(current_data)
            if delta == 0:
                print "Warning : You are plotting '%s' on axis '%s' which has only one value. You must be kinda stupid!" % ( name, k)
            else:
                # big good looking hack :D
                big_nb_el_per_class = 50
                max_E = 0.25
                E = (nb_el_per_class - 1.) / (big_nb_el_per_class - 1) * max_E
                #print 'E', E
                E = min(E, max_E)
                z = 2.
                #print 'E/z =', E/z
                if scale == 'log':
                    noise = normal(0., E/z * exp(delta) / (nb_classes - 1), size=nb_items)
                    current_data = array(current_data) * exp(noise)
                else:
                    noise = normal(0., E/z * delta / (nb_classes - 1), size=nb_items)
                    current_data = array(current_data) + noise
                print 'Some noise was added to axis %s (%s) because of potentially overlapping classes' % (k, name)

        # in 3d mode, the arguments are xs, ys, zs instead of x, y, z
        if d3:
            k += 's'

        scatter_args[k] = current_data

    # warning if scale != linear for the other args
    for k in get_provide_from('cst'):
        if type(data_args) == tuple:
            name, f, scale = data_args[k]
            if scale != 'linear':
                print 'Warning : %s scale for argument "%s" has no effet (yet!)' % (scale, k)

    # other scatter arguments than x y z
    scatter_args['s'] = 30
    for k in get_provide_from('s'):
        if not hasattr(data_args[k], '__iter__'):
            scatter_args[k] = data_args[k]
        else:
            name, f, scale = data_args[k]
            scatter_args[k] = data.get_data(name, f)

    for k in get_provide_from('c'):
        name, f, scale = data_args[k]
        scatter_args[k] = data.get_data(name,f)

    # plot itself
    plot = scatter(**scatter_args)

    for k in get_provide_from('xyz'):
        _,_,scale = data_args[k]
        current_data = scatter_args[k + ('s' if d3 else '')]
        min_ = min(current_data)
        max_ = max(current_data)

        suf = '3d' if d3 else ''
        if scale == 'log':
            delta = max_ / min_
            getattr(ax, 'set_%slim' % k + suf )(min_ / (delta**(0.05)), max_ * (delta**(.05)))
        else:
            delta = max_ - min_
            getattr(ax, 'set_%slim' % k + suf )(min_ - .02*delta, max_ + .02*delta)


    if is_provided('t'):
        name, f, _ = data_args['t']
        text_args = {}
        for k in get_provide_from('xyz'):
            text_args[k] = scatter_args[k + ('s' if d3 else '')]
        text_args['s'] = data.get_data(name,lambda x : str(f(x)))
        keys = text_args.keys()
        for args in zip(*[text_args[a] for a in keys]):
            ax.text(**dict(zip(keys,args)))

    # colorbar
    if is_provided('c'):
        fig.colorbar(plot)

    return ax

def print_stats(box_costs):
    dmax = numpy.max(box_costs)
    dmean = numpy.mean(box_costs)
    dstderr = numpy.std(box_costs) / len(box_costs)
    incer = max(dmax - dmean, dmean - numpy.min(box_costs))
    print '####tmax: %f, mean: %f +/- %f, error on the mean: %f'%(dmax,dmean,incer,dstderr)


def hyperboxplot(data,
               box_column,
               cost_name,
               cost_label='',
               title='',
               black_list=None,
               box_names=None,
               rotation=15,
               ax1=None,
               order=None,
               return_order=False,):
    """
    Inputs:
        data
            HyperDatabase
        box_column
            string : name of the column ito use for x (categories)
        cost_name
            string : name of the column to use for y
        title
            string : title of the plot
        black_list
            list : list of categories to ignore
        box_names
            dict : labels to use on the x axis of the plot (keys == original category name, values == label)
        rotation
            float : angle (in degrees) of the x labels
        ax1
            axes handle : if None, will create a new figure
        order
            array : Order of the categories, if None, will order by increasing means
        return_order
            boolean : if True, will return the order of the categories

    Outputs:
        ax1 (if return_order is False)
         OR
        ax1, order (if return_order is True)
    """


    boxes=list(set(data.get_data(box_column)))
    if black_list is not None:
        boxes = [str(box) for box in boxes if not box in black_list]
    boxes.sort()
    costs=[]
    for i,box_name in enumerate(boxes):
        print box_column
        data.print_filters()
        data.add_filter(box_column,filtering.eq(box_name, name=box_column))
        print '________', box_name
        box_costs = data.get_data(cost_name)
        print_stats(box_costs)
        costs.append(box_costs)
        data.remove_filter(box_column)
#        data.reset_all_filters()
#        apply_filters(data)

    if order is None:
        means = numpy.array([numpy.mean(cost) for cost in costs])
        order = numpy.argsort(means)

    costs = [costs[i] for i in order]
    if box_names is not None:
        boxes = [box_names.get(boxes[i],boxes[i]) for i in order]
    else:
        boxes = [boxes[i] for i in order]
    if ax1 is None:
        fig = PP.figure()
        ax1 = fig.add_subplot(111)
    PP.subplots_adjust(left=0.10, right=0.90, top=0.9, bottom=0.15)
    ax1.boxplot(costs)
#    ax1.title(title)
#    ticks = PP.xticks(numpy.arange(len(costs))+1,boxes)
    ax1.set_xlim(0.5, len(boxes)+0.5)
    ticks = PP.setp(ax1, xticklabels=boxes)
    PP.setp(ticks, rotation=rotation)#, fontsize=8)
    ax1.set_title(title)
#    ax1.set_xlabel(cost_name)
    if cost_label is not None:
        ax1.set_ylabel(cost_label)
    else:
        ax1.set_ylabel(cost_name)

    if return_order:
        return ax1,order
    else:
        return ax1
