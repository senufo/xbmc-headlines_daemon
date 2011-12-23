import xbmc, xbmcgui
import xbmcaddon
import time
#python modules
import os, time, stat, re, copy, time
from xml.dom.minidom import parse, Document, _write_data, Node, Element
import pickle
import htmlentitydefs
from html2text import *
from threading import Thread

# rdf modules
import feedparser
import urllib

# to decode html entities
from BeautifulSoup import BeautifulStoneSoup


__author__     = "Senufo"
__scriptid__   = "service.rss_daemon"
__scriptname__ = "rss_daemon"

Addon          = xbmcaddon.Addon(__scriptid__)

__cwd__        = Addon.getAddonInfo('path')
__version__    = Addon.getAddonInfo('version')
__language__   = Addon.getLocalizedString

__profile__    = xbmc.translatePath(Addon.getAddonInfo('profile'))
__resource__   = xbmc.translatePath(os.path.join(__cwd__, 'resources',
                                                 'lib'))

#sys.path.append (__resource__)
self.RssFeedsPath = xbmc.translatePath('special://userdata/RssFeeds.xml')
try:
    self.feedsTree = parse(self.RssFeedsPath)
except:
    print "Erreur self.feedsTree"
#Recupere la liste des flux dans RSSFeeds.xml
if self.feedsTree:
    #self.feedsList = self.getCurrentRssFeeds()
    self.feedsList = dict()
    sets = self.feedsTree.getElementsByTagName('set')
    print "SET = %s " % sets
    for s in sets:
        setName = 'set'+s.attributes["id"].value
        print "SETNAME = %s " % setName
        self.feedsList[setName] = {'feedslist':list(), 'attrs':dict()}
        #get attrs
        for attrib in s.attributes.keys():
            self.feedsList[setName]['attrs'][attrib] = s.attributes[attrib].value
        #get feedslist
        feeds = s.getElementsByTagName('feed')
        for feed in feeds:
            self.feedsList[setName]['feedslist'].append({'url':feed.firstChild.toxml(), 'updateinterval':feed.attributes['updateinterval'].value})
    for setName in self.feedsList:
        val = setName[0]
        print "%s = %s " % (setName,val)
        print "url = %s " % self.feedsList[setName]
        #for set in feedsList[setName]:
        #    print "SET = %s" % set
        for feed in self.feedsList[setName]['feedslist']:
            print "url = %s " % feed['url']
    print "URL = %s " % self.feedsList['set1']

#Verifie que xbmc tourne
while (not xbmc.abortRequested):
#Partie de recuperation de flux rss sur le net
    NbNews = 0
    time_debut = time.time()
    print "TIME debut = %f " % time.time() 
    #Sauve les flux RSS
    for setName in self.feedsList:
        i = 0
        for feed in self.feedsList[setName]['feedslist']:
            i += 1
            print "=>url = %s " % feed['url']
            updateinterval = int(feed['updateinterval']) * 60
            #http://www.lequipe.fr/Xml/actu_rss.xml
            filename = feed['url']
            filename = re.sub('^http://.*/','Rss-',filename)
            #self.RssFeeds = xbmc.translatePath('special://userdata/%s' % filename)
            self.RssFeeds = '%s/%s' % (__profile__,filename)
            #teste si le fichier existe
            if (os.path.isfile(self.RssFeeds)):
                date_modif = os.stat(self.RssFeeds).st_mtime
                diff = time.time() - date_modif
                print "diff = %f, date_modif = %f, updateinterval %d" % (diff,date_modif,updateinterval )
                #Si le flux est plus ancien que le updateinterval on le telecharge de nx
                if (diff > updateinterval):
                    print "=>filename = %s, self.RssFeeds = %s, url = %s " % (filename,self.RssFeeds, feed['url'])
                    urllib.urlretrieve(feed['url'], filename = self.RssFeeds)
                    #On efface le doc deja parser
                    os.remove('%s-pickle' % self.RssFeeds)
                    #On le parse de nouveau
                    #On parse le fichier rss et on le sauve sur le disque
                    doc = feedparser.parse('file://%s' % self.RssFeeds)
                    #Sauve le doc parse directement
                    output = open(('%s-pickle' % self.RssFeeds), 'wb')
                    # Pickle dictionary using protocol 0.
                    pickle.dump(doc, output)
                    output.close()

                    print "date = %f, epoc time = %f  " % (date_modif, time.time())
            else:
                #Le fichier n'existe pas on le telecharge
                urllib.urlretrieve(feed['url'], filename = self.RssFeeds)
                #On parse le fichier rss et on le sauve sur le disque
                doc = feedparser.parse('file://%s' % self.RssFeeds)
                #Sauve le doc parse directement
                output = open(('%s-pickle' % self.RssFeeds), 'wb')
                # Pickle dictionary using protocol 0.
                pickle.dump(doc, output)
                output.close()


    #initialise start time
    start_time = time.time()
    time.sleep( .5 )
