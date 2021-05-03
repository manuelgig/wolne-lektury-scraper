# -*- coding: utf-8 -*-
"""
Created on Sat Feb 6 12:52:56 2021

@author: Manuel Gigena
"""

from bs4 import BeautifulSoup
import urllib.request, requests, os, zipfile
import pandas as pd
import numpy as np

# getBookList takes the url of an author's website in WL (e.g., https://wolnelektury.pl/katalog/autor/bruno-schulz/ ),
# an author name and a list of file types (e.g., ['PDF'], or ['PDF,'MP3']), and scrapes the given url. It returns a pandas df
# wherein each row contains a book name and url's of the book in the desired format.

def getBookList(author_url,author_name,filetypes=['PDF','MP3']):
    
    base_url = 'https://wolnelektury.pl'
    source = urllib.request.urlopen(author_url).read()
    soup = BeautifulSoup(source,'lxml') 
    
    # Get the list of books by the given author hoster at wL (including the books' urls, the urls of their PDF's and MP3's)
    print('Getting list of books by {} @ {} ...'.format(author_name,
                                                        author_url))
    
    book_temp = []
    for row in soup.find(class_='plain-list').find_all('a', href=True):        
        # Get book name and the url of the book's site
        book_name = row.string
        print(book_name)
        site_url = '{}{}'.format(base_url,
                                 row['href'])
        
        # Use the site_url to make a new soup and get the url's of requested filetypes
        source_book = urllib.request.urlopen(site_url).read()
        soup_book = BeautifulSoup(source_book,
                                  'lxml') 
        
        temp_dict = {'book_name':book_name,
                     'site_url':site_url}
        
        soup_urls = soup_book.find(class_='book-box-formats').find_all('a',
                                                                       href=True,
                                                                       class_=False)
        for filetype in filetypes:
            for elem in soup_urls:            
                if elem.string == filetype:
                    temp_dict['{}_url'.format(filetype)] = '{}{}'.format(base_url,
                                                                         elem['href'])
        
        #append the dictionary to book_temp
        book_temp.append(temp_dict)

    # convert the list of dictionaries book_temp into a pandas df
    return pd.DataFrame(book_temp)

# getBookPart downloads the files to a dedicated folder inside an <author_name> folder in the wd. WL stores mp3 files in compressed format, unzip=True will unzip them
def getBookPart(df, author_name, wd, file_type='PDF', unzip=False):    
    
    # Create the <author_name> folder if it does not exist
    wd_author = '{}{}/'.format(wd,
                               author_name)
    
    if len(df['{}_url'.format(file_type)].dropna())>0:
        
        # Check if there is a folder with the given author's name, and creater one otherwise
        if not os.path.exists(wd_author):
            os.makedirs(wd_author)
    
        print('Downloading the {} files...'.format(file_type))
        
        if not os.path.exists('{}/{}/'.format(wd_author, file_type)):
            os.makedirs('{}/{}/'.format(wd_author,
                                        file_type))
        
        # Check if there is a folder for the file type, and create one otherwise
        for file_url in df['{}_url'.format(file_type)].dropna():
            try:
                r = requests.get(file_url,
                                 allow_redirects=True)
                rep_name = file_url[file_url.rfind('/')+1:]
                open('{}{}/{}'.format(wd_author,
                                      file_type,
                                      rep_name), 'wb').write(r.content)
                df.loc[df['{}_url'.format(file_type)]==file_url, '{}_downloaded'.format(file_type)] = 'Yes'
            
                if (unzip==True) and (rep_name[-3:] == 'zip'):
                    with zipfile.ZipFile('{}{}/{}'.format(wd_author,file_type,rep_name), 'r') as zip_ref:
                        zip_ref.extractall('{}{}'.format(wd_author,file_type))
            
            except:
                df.loc[df['{}_url'.format(file_type)]==file_url, '{}_downloaded'.format(file_type)] = 'No'
                continue
            
        print('::: Done :::')
        
    else:
        print('This author has no books in {} format'.format(file_type))


# scraperWL is the scraper proper, combining getBookList and getBookPart
# returns a pandas df with book info, urls and download status
def scraperWL(author_url,author_name,wd,filetypes=['PDF','MP3'],unzip=False):
    df = getBookList(site_url,
                     author,
                     wd)
    
    print()
    
    for ftype in filetypes:
        getBookPart(df,author_name,wd,file_type=ftype,unzip=unzip)
        
    return df.replace(np.NaN,'NA')

""" Example:

path = 'C:/Users/books/'
site_url = 'https://wolnelektury.pl/katalog/autor/bruno-schulz/'
author = 'Schulz, Bruno'

schulz = scraperWL(author_url,author_name,wd,filetypes=['PDF','MP3'])
print(schulz)

"""
