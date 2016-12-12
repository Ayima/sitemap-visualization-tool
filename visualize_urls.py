'''
Visualize a list of URLs by site path.

This script reads in the sitemap_layers.csv file created by the
categorize_urls.py script and builds a graph visualization using Graphviz.

Graph depth can be specified by executing a call like this in the
terminal:

    python visualize_urls.py --depth 4 --limit 10 --title "My Sitemap" --style "dark" --size "40"

The same result can be achieved by setting the variables manually at the head
of this file and running the script with:

    python visualize_urls.py

'''
from __future__ import print_function


# Set global variables

graph_depth = 3  # Number of layers deep to plot categorization
limit = 50       # Maximum number of nodes for a branch
title = ''       # Graph title
style = 'light'  # Graph style, can be "light" or "dark"
size = '8,5'     # Size of rendered PDF graph


# Import external library dependencies

import pandas as pd
import graphviz
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--depth', type=int, default=graph_depth,
                    help='Number of layers deep to plot categorization')
parser.add_argument('--limit', type=int, default=limit,
                    help='Maximum number of nodes for a branch')
parser.add_argument('--title', type=str, default=title,
                    help='Graph title')
parser.add_argument('--style', type=str, default=style,
                    help='Graph style, can be "light" or "dark"')
parser.add_argument('--size', type=str, default=size,
                    help='Size of rendered PDF graph')
args = parser.parse_args()


# Update variables with arguments if included

graph_depth = args.depth
limit = args.limit
title = args.title
style = args.style
size = args.size


# Main script functions

def make_sitemap_graph(df, layers=3, limit=50, size='8,5'):
    ''' Make a sitemap graph up to a specified layer depth.

    sitemap_layers : DataFrame
        The dataframe created by the peel_layers function
        containing sitemap information.

    layers : int
        Maximum depth to plot.

    limit : int
        The maximum number node edge connections. Good to set this
        low for visualizing deep into site maps.
    '''


    # Check to make sure we are not trying to plot too many layers
    if layers > len(df) - 1:
        layers = len(df)-1
        print('There are only %d layers available to plot, setting layers=%d'
              % (layers, layers))


    # Initialize graph
    f = graphviz.Digraph('sitemap', filename='sitemap_graph_%d_layer' % layers)
    f.body.extend(['rankdir=LR', 'size="%s"' % size])


    def add_branch(f, names, vals, limit, connect_to=''):
        ''' Adds a set of nodes and edges to nodes on the previous layer. '''

        # Get the currently existing node names
        node_names = [item.split('"')[1] for item in f.body if 'label' in item]

        # Only add a new branch it it will connect to a previously created node
        if connect_to:
            if connect_to in node_names:
                for name, val in list(zip(names, vals))[:limit]:
                    f.node(name='%s-%s' % (connect_to, name), label=name)
                    f.edge(connect_to, '%s-%s' % (connect_to, name), label='{:,}'.format(val))


    f.attr('node', shape='rectangle') # Plot nodes as rectangles

    # Add the first layer of nodes
    for name, counts in df.groupby(['0'])['counts'].sum().reset_index()\
                          .sort_values(['counts'], ascending=False).values:
        f.node(name=name, label='{} ({:,})'.format(name, counts))

    if layers == 0:
        return f

    f.attr('node', shape='oval') # Plot nodes as ovals
    f.graph_attr.update()

    # Loop over each layer adding nodes and edges to prior nodes
    for i in range(1, layers+1):
        cols = [str(i_) for i_ in range(i)]
        nodes = df[cols].drop_duplicates().values
        for j, k in enumerate(nodes):

            # Compute the mask to select correct data
            mask = True
            for j_, ki in enumerate(k):
                mask &= df[str(j_)] == ki

            # Select the data then count branch size, sort, and truncate
            data = df[mask].groupby([str(i)])['counts'].sum()\
                    .reset_index().sort_values(['counts'], ascending=False)

            # Add to the graph
            add_branch(f,
                       names=data[str(i)].values,
                       vals=data['counts'].values,
                       limit=limit,
                       connect_to='-'.join(['%s']*i) % tuple(k))

            print(('Built graph up to node %d / %d in layer %d' % (j, len(nodes), i))\
                    .ljust(50), end='\r')

    return f


def apply_style(f, style, title=''):
    ''' Apply the style and add a title if desired. More styling options are
    documented here: http://www.graphviz.org/doc/info/attrs.html#d:style

    f : graphviz.dot.Digraph
        The graph object as created by graphviz.

    style : str
        Available styles: 'light', 'dark'

    title : str
        Optional title placed at the bottom of the graph.
    '''

    dark_style = {
        'graph': {
            'label': title,
            'bgcolor': '#3a3a3a',
            'fontname': 'Helvetica',
            'fontsize': '18',
            'fontcolor': 'white',
        },
        'nodes': {
            'style': 'filled',
            'color': 'white',
            'fillcolor': 'black',
            'fontname': 'Helvetica',
            'fontsize': '14',
            'fontcolor': 'white',
        },
        'edges': {
            'color': 'white',
            'arrowhead': 'open',
            'fontname': 'Helvetica',
            'fontsize': '12',
            'fontcolor': 'white',
        }
    }

    light_style = {
        'graph': {
            'label': title,
            'fontname': 'Helvetica',
            'fontsize': '18',
            'fontcolor': 'black',
        },
        'nodes': {
            'style': 'filled',
            'color': 'black',
            'fillcolor': '#dbdddd',
            'fontname': 'Helvetica',
            'fontsize': '14',
            'fontcolor': 'black',
        },
        'edges': {
            'color': 'black',
            'arrowhead': 'open',
            'fontname': 'Helvetica',
            'fontsize': '12',
            'fontcolor': 'black',
        }
    }

    if style == 'light':
        apply_style = light_style

    elif style == 'dark':
        apply_style = dark_style

    f.graph_attr = apply_style['graph']
    f.node_attr = apply_style['nodes']
    f.edge_attr = apply_style['edges']

    return f


def main():

    # Read in categorized data
    sitemap_layers = pd.read_csv('sitemap_layers.csv', dtype=str)
    # Convert numerical column to integer
    sitemap_layers.counts = sitemap_layers.counts.apply(int)
    print('Loaded {:,} rows of categorized data from sitemap_layers.csv'\
            .format(len(sitemap_layers)))

    print('Building %d layer deep sitemap graph' % graph_depth)
    f = make_sitemap_graph(sitemap_layers, layers=graph_depth,
                           limit=limit, size=size)
    f = apply_style(f, style=style, title=title)

    f.render(cleanup=True)
    print('Exported graph to sitemap_graph_%d_layer.pdf' % graph_depth)


if __name__ == '__main__':
    main()
