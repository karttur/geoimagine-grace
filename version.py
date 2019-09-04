'''
Created on 18 Oct 2018

@author: thomasgumbricht
'''
__version__ = '0.3.1'
VERSION = tuple( int(x) for x in __version__.split('.') )
metadataD = { 'name':'grace', 'author':'Thomas Gumbricht', 
             'author_email':'thomas.gumbricht@gmail.com',
             'title':'GRACE specific processing', 
             'label':'Processes specific for GRACE data, including importing, organizing, gap filling and solution averaging',
             'image':'avg-trmm-3b43v7-precip_3B43_trmm_2001-2016_A'}