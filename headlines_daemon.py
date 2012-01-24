# -*- coding: utf-8 -*-
"""
Get rss news in background for rss/atom reader : headlines
"""
import xbmc
import xbmcaddon
#python modules
import os, time, re, sys, glob, shutil
from xml.dom.minidom import parse 
import pickle
from headlines_parse import *

# rdf modules
import feedparser
import urllib

__author__     = "Senufo"
__scriptid__   = "script.headlines"
__scriptname__ = "headlines_daemon"

Addon          = xbmcaddon.Addon(__scriptid__)

__cwd__        = Addon.getAddonInfo('path')
__version__    = Addon.getAddonInfo('version')
__language__   = Addon.getLocalizedString

__profile__    = xbmc.translatePath(Addon.getAddonInfo('profile'))
__resource__   = xbmc.translatePath(os.path.join(__cwd__, 'resources', 
                                                 'lib'))

#DEBUG = False
DEBUG_LOG = True
#DEBUG_LOG = False
#Function Debug
def debug_log(msg):
    """
    print message if DEBUG_LOG == True
    """
    if DEBUG_LOG == True: print " [headlines_daemon] : %s " % ( msg)


#Teste si le repertoire script.headlines existe
DATA_PATH = xbmc.translatePath( 
        "special://profile/addon_data/script.headlines/")
if not os.path.exists(DATA_PATH): 
    os.makedirs(DATA_PATH)

RssFeedsPath = xbmc.translatePath('special://userdata/RssFeeds.xml')
debug(RssFeedsPath)
try:
    feedsTree = parse(RssFeedsPath)
except:
    print "Erreur self.feedsTree : %s" % sys.exc_info()[0] 
#Recupere la liste des flux dans RSSFeeds.xml
if feedsTree:
    #self.feedsList = self.getCurrentRssFeeds()
    feedsList = dict()
    sets = feedsTree.getElementsByTagName('set')
    for s in sets:
        setName = 'set'+s.attributes["id"].value
        feedsList[setName] = {'feedslist':list(), 'attrs':dict()}
        #get attrs
        for attrib in s.attributes.keys():
            feedsList[setName]['attrs'][attrib] = s.attributes[attrib].value
        #get feedslist
        feeds = s.getElementsByTagName('feed')
        for feed in feeds:
            feedsList[setName]['feedslist'].append(
                {'url':feed.firstChild.toxml(), 
                 'updateinterval':feed.attributes['updateinterval'].value})

get_time = time.time() + (60)    

#Verifie que xbmc tourne
while (not xbmc.abortRequested):
#Partie de recuperation de flux rss sur le net
    NbNews = 0
    #Sauve les flux RSS
    for setName in feedsList:
        i = 0
        for feed in feedsList[setName]['feedslist']:
            i += 1
            #print "=>url = %s " % feed['url']
            #Pour éviter les erreurs avec des & et espaces mal encodés
            encurl = feed['url'].replace("amp;", "&").replace(' ', '%20')
            #debug('encurl = %s ' % encurl)
            updateinterval = int(feed['updateinterval']) * 60
            current_time = time.time()
            diff_time  = current_time - (get_time + updateinterval)
            #if (current_time > (get_time + updateinterval)):
            #if True:
            #    get_time = time.time()
            #On recupere l'url et on la transforme en nom de fichier
            filename = feed['url']
            filename = re.sub('^http://.*/', 'Rss-', filename)
            RssFeeds = '%s/%s' % (DATA_PATH, filename)

            #teste si le fichier du flux existe
            if (os.path.isfile(RssFeeds)):
                date_modif = os.stat(RssFeeds).st_mtime
                diff = time.time() - date_modif
                debug_log('diff = %i, date_modif = %i, update = %d ' % (diff,
                                                               date_modif,updateinterval))
                #Si le flux est plus ancien que 
                #le updateinterval on le telecharge de nx
                if (diff > updateinterval):
                    RSStream = ParseRSS()
                    RSStream.getRSS(encurl)
                    debug_log('Appel getRSS')
            #Le fichier n'existe pas on le telecharge
            else:
                RSStream = ParseRSS()
                RSStream.getRSS(encurl)
                debug_log('Appel getRSS 114')

    #initialise start time
    start_time = time.time()
    time.sleep( .5 )
