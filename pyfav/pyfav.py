"""
This is PyFav. It's a python package that helps you download favicons.

Find the project on GitHub at https://github.com/phillipsm/pyfav
and in PyPI at http://python.org/pypi/pyfav



The simplest way to get started is to use the download_favicon function.

To download a favicon for it's as simple as,

============
from favicon import download_favicon

favicon_saved_at = download_favicon('https://www.python.org/')

============
If you want to be specific in where that favicon gets written to disk,
============
favicon_saved_at = download_favicon('https://www.python.org/', \
    target_dir='/tmp/favicon-downloads')
============


If you'd prefer to handle the write to disk piece, use the get_favicon_url
function by itself,
============
favicon_url = get_favicon_url('https://www.python.org/')
============
"""


import urllib, os.path, string
from urlparse import urlparse
import requests
from bs4 import BeautifulSoup

# get domain name
import tldextract

# Some hosts don't like the requests default UA. Use this one instead.
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) \
        AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.152 \
        Safari/537.36'
}


def download_favicon(url, target_dir='/tmp'):
    """
    Given a URL download the save it to disk
    
    Keyword arguments:
    url -- A string. This is the location of the favicon
    target_dir -- The location where the favicon will be saved.
    
    Returns:
    The file location of the downloaded favicon. A string.
    """
    
    parsed_site_uri = urlparse(url)



    # Help the user out if they didn't give us a protocol
    if not parsed_site_uri.scheme:
        url = 'http://' + url
        parsed_site_uri = urlparse(url)

    if not parsed_site_uri.scheme or not parsed_site_uri.netloc:
        # do not raise exception
        return None
        #raise Exception("Unable to parse URL, %s" % url)



    favicon_url = get_favicon_url(url)

    if not favicon_url:
        # do not raise exception
        return None
        #raise Exception("Unable to find favicon for, %s" % url)
    
    # favicon name
    ext = tldextract.extract(url)
    if ext.subdomain=='www' or ext.subdomain == '':
        domain = '.'.join(ext[1:3])
    else:
        domain = '.'.join(ext[:3])

    file_name = 'icon_' + domain + '.ico'

    # We finally have a URL for our favicon. Get it. 
    response = requests.get(favicon_url, headers=headers)

    sanitized_filename = os.path.join(target_dir, file_name)
    
    with open(sanitized_filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024): 
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)
                    f.flush()
                    
    return sanitized_filename


def parse_markup_for_favicon(markup, url):
    """
    Given markup, parse it for a favicon URL. The favicon URL is adjusted
    so that it can be retrieved independently. If no favicon is found in the 
    markup we return None.
    
    Keyword arguments:
    markup -- A string containing the HTML markup.
    url -- A string containing the URL where the supplied markup can be found.
    We use this URL in cases where the favicon path in the markup is relative.
    
    Retruns:
    The URL of the favicon. A string. If not found, returns None.
    """
    
    parsed_site_uri = urlparse(url)
    
    soup = BeautifulSoup(markup)
        
    # Do we have a link element with the icon?
    icon_link = soup.find('link', rel='icon')
    if icon_link and icon_link.has_attr('href'):
        
        favicon_url = icon_link['href']
        
        # Sometimes we get a protocol-relative path
        if favicon_url.startswith('//'):
            parsed_uri = urlparse(url)
            favicon_url = parsed_uri.scheme + ':' + favicon_url

        # An absolute path relative to the domain
        elif favicon_url.startswith('/'):
            favicon_url = parsed_site_uri.scheme + '://' + \
                parsed_site_uri.netloc + favicon_url
        
        # A relative path favicon    
        elif not favicon_url.startswith('http'):
            path, filename  = os.path.split(parsed_site_uri.path)
            favicon_url = parsed_site_uri.scheme + '://' + \
                parsed_site_uri.netloc + '/' + os.path.join(path, favicon_url)
        
        # We found a favicon in the markup and we've formatted the URL
        # so that it can be loaded independently of the rest of the page
        return favicon_url

    
    # No favicon in the markup
    return None


def get_favicon_url(url):
    """
    Returns a favicon URL for the URL passed in. We look in the markup returned
    from the URL first and if we don't find a favicon there, we look for the 
    default location, e.g., http://example.com/favicon.ico . We return None if
    unable to find the file.
    
    Keyword arguments:
    url -- A string. This is the URL that we'll find a favicon for.
    
    Returns:
    The URL of the favicon. A string. If not found, returns None.
    """

    parsed_site_uri = urlparse(url)

    # Get the markup
    try:
        response = requests.get(url, headers=headers)
    except:
        return None
        #raise Exception("Unable to find URL. Is it valid? %s" % url)
    
    if response.status_code == requests.codes.ok:
        favicon_url = parse_markup_for_favicon(response.content, url)

        # We found a favicon in our markup. Return the URL
        if favicon_url:
            return favicon_url
            
    # The favicon doesn't appear to be in the makrup
    # Let's look at the common locaiton, url/favicon.ico
    favicon_url = '{uri.scheme}://{uri.netloc}/favicon.ico'.format(\
        uri=parsed_site_uri)
                        
    response = requests.get(favicon_url, headers=headers)
    if response.status_code == requests.codes.ok:
        return favicon_url

    # No favicon in the markup or at url/favicon.ico
    return None
