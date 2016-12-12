'''
Extract the URLs from an XML sitemap.

Specify the sitemap index file URL (an XML page containing links to other
XML files) by executing a call like this in the terminal:

    python extract_urls.py --url "site.com/sitemap-index.xml"

If the URL points directly to the sitemap then add the not_index argument:

    python extract_urls.py --url "site.com/sitemap.xml" --not_index

If the XML sitemap files are in gzip format, the script should be run like this:

    python extract_urls.py --url "site.com/sitemap-index.xml" --gzip

The same results can be achieved by editing the variables at the head of this
file and running the script with:

    python extract_urls.py

'''
from __future__ import print_function


# Set global variables

sitemap_url = 'https://www.sportchek.ca/sitemap.xml'
sitemap_is_index = True # Does sitemap_url point to other XML pages?
sitemap_is_gzip = False # Are the XML pages in compressed format?


# Import external library dependencies

import requests
from bs4 import BeautifulSoup

# Required if sitemap_is_gzip == True
import os
import gzip
import glob

# For argument passing
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--url', type=str,
                    help='Link to XML sitemap')
parser.add_argument('--not_index', action='store_true',
                    help='Does the given URL contain the sitemap directly?')
parser.add_argument('--gzip', action='store_true',
                    help='Are the XML files in gzip (.gz) format?')
args = parser.parse_args()


# Update variables with arguments if specified

if args.url:
    sitemap_url = args.url
else:
    print('No sitemap URL argument passed, using %s.' % sitemap_url)
    print('Read usage details in file header for more information on passing arguments.')

if args.not_index:
    sitemap_is_index = False

if args.gzip:
    sitemap_is_gzip = True



# Main script functions


def get_urls(url):
    ''' Extract URLs from XML by looking for <loc> tag contents. '''

    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    links = [element.text for element in soup.findAll('loc')]
    return links


def get_all_urls(sitemap_url):
    ''' Loop over get_urls function for all XML pages. '''

    # Get list of .xml files
    urls = get_urls(sitemap_url)
    urls_not_gz = [u for u in urls if u[-3:] != '.gz']
    for i, url in enumerate((set(urls) - set(urls_not_gz))):
        if i == 0:
            print('Warning - ignoring the following gzip files:')
        print(url)
    urls = urls_not_gz

    sitemap_urls = []
    for i, url in enumerate(urls):
        links = get_urls(url)
        print('Searched through %s XML file(s)' % (i+1), end='\r')
        sitemap_urls += links

    return sitemap_urls


def get_gzip_urls(f_):
    ''' Extract URLs from gzip XML by looking for <loc> tag contents. '''

    f = gzip.open(f_)
    soup = BeautifulSoup(f.read(), 'html.parser')
    links = [item.text for item in soup.findAll('loc')]
    return links


def get_all_gzip_urls(sitemap_url):
    ''' Loop over get_gzip_urls function for all XML pages. Index XML page
    is assumed to be unzipped. '''

    # Get list of .xml.gz files
    urls = get_urls(sitemap_url)
    urls_gz = [u for u in urls if u[-3:] == '.gz']
    for i, url in enumerate((set(urls) - set(urls_gz))):
        if i == 0:
            print('Warning - ignoring the following non-gzip files:')
        print(url)
    urls = urls_gz

    # Download the sitemap files
    for i, url in enumerate(urls):
        filename = url.split('/')[-1]
        page = requests.get(url)
        with open('gzip-sitemaps/' + filename, 'wb') as f:
            f.write(page.content)

    # Extract urls from sitemap files
    sitemap_urls = []
    all_sitemaps = glob.glob('gzip-sitemaps/*.gz')
    for i, f_ in enumerate(all_sitemaps):
        links = get_gzip_urls(f_)
        print('Searched through %s XML file(s)' % (i+1), end='\r')
        sitemap_urls += links

    return sitemap_urls


def main():

    # If the XML files are not compressed
    if not sitemap_is_gzip:

        # If the XML sitemap is an index to other XML files
        if sitemap_is_index:
            sitemap_urls = get_all_urls(sitemap_url)

        # If the XML sitemap contains the page links directly
        if not sitemap_is_index:
            sitemap_urls = get_urls(sitemap_url)

    # If the XML files are compressed
    else:

        # Make a folder to hold gzip files
        if not os.path.exists('gzip-sitemaps'):
            os.makedirs('gzip-sitemaps')

        # If the XML sitemap is an index to other XML files
        if sitemap_is_index:
            sitemap_urls = get_all_gzip_urls(sitemap_url)

        # If the XML sitemap contains the page links directly
        if not sitemap_is_index:
            filename = sitemap_url.split('/')[-1]
            page = requests.get(sitemap_url)
            with open('gzip-sitemaps/' + filename, 'wb') as f:
                f.write(page.content)
            sitemap_urls = get_gzip_urls('gzip-sitemaps/' + filename)

    # Print the URLs to a file
    with open('sitemap_urls.dat', 'w') as f:
        for url in sitemap_urls:
            f.write(url + '\n')

    # Print the number of URLs found
    print('Found {:,} URLs in the sitemap and saved them to sitemap_urls.dat'\
            .format(len(sitemap_urls)))


if __name__ == '__main__':
    main()
