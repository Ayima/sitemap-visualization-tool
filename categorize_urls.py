'''
Categorize a list of URLs by site path.

The file containing the URLs should exist in the working directory and be
named sitemap_urls.dat. It should contain one URL per line.

Categorization depth can be specified by executing a call like this in the
terminal (where we set the granularity depth level to 5):

    python categorize_urls.py --depth 5

The same result can be achieved by setting the categorization_depth variable
manually at the head of this file and running the script with:

    python categorize_urls.py

'''
from __future__ import print_function


# Set global variables

categorization_depth = 3


# Import external library dependencies

import pandas as pd
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--depth', type=int, default=categorization_depth,
                    help='Number of layers deep to categorize')
args = parser.parse_args()


# Update variables with arguments if included

categorization_depth = args.depth



# Main script functions


def peel_layers(urls, layers=3):
    ''' Builds a dataframe containing all unique page identifiers up
    to a specified depth and counts the number of sub-pages for each.
    Prints results to a CSV file.

    urls : list
        List of page URLs.

    layers : int
        Depth of automated URL search. Large values for this parameter
        may cause long runtimes depending on the number of URLs.
    '''

    # Store results in a dataframe
    sitemap_layers = pd.DataFrame()

    # Get base levels
    bases = pd.Series([url.split('//')[-1].split('/')[0] for url in urls])
    sitemap_layers[0] = bases

    # Get specified number of layers
    for layer in range(1, layers+1):

        page_layer = []
        for url, base in zip(urls, bases):
            try:
                page_layer.append(url.split(base)[-1].split('/')[layer])
            except:
                # There is nothing that deep!
                page_layer.append('')

        sitemap_layers[layer] = page_layer

    # Count and drop duplicate rows + sort
    sitemap_layers = sitemap_layers.groupby(list(range(0, layers+1)))[0].count()\
                     .rename('counts').reset_index()\
                     .sort_values('counts', ascending=False)\
                     .sort_values(list(range(0, layers)), ascending=True)\
                     .reset_index(drop=True)

    # Convert column names to string types and export
    sitemap_layers.columns = [str(col) for col in sitemap_layers.columns]
    sitemap_layers.to_csv('sitemap_layers.csv', index=False)

    # Return the dataframe
    return sitemap_layers


def main():

    sitemap_urls = open('sitemap_urls.dat', 'r').read().splitlines()
    print('Loaded {:,} URLs'.format(len(sitemap_urls)))

    print('Categorizing up to a depth of %d' % categorization_depth)
    sitemap_layers = peel_layers(urls=sitemap_urls,
                                 layers=categorization_depth)
    print('Printed {:,} rows of data to sitemap_layers.csv'.format(len(sitemap_layers)))


if __name__ == '__main__':
    main()
