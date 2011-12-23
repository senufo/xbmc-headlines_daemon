import xbmc, xbmcgui
import xbmcaddon
import time
#python modules
import os, time, stat, re, copy, time
from xml.dom.minidom import parse, Document, _write_data, Node, Element
import pickle

# rdf modules
import feedparser
import urllib

# to decode html entities
from BeautifulSoup import BeautifulStoneSoup


__author__     = "Senufo"
__scriptid__   = "script.rss_atom"
__scriptname__ = "rss_daemon"

Addon          = xbmcaddon.Addon(__scriptid__)

__cwd__        = Addon.getAddonInfo('path')
__version__    = Addon.getAddonInfo('version')
__language__   = Addon.getLocalizedString

__profile__    = xbmc.translatePath(Addon.getAddonInfo('profile'))
__resource__   = xbmc.translatePath(os.path.join(__cwd__, 'resources',
                                                 'lib'))

#sys.path.append (__resource__)
RssFeedsPath = xbmc.translatePath('special://userdata/RssFeeds.xml')
try:
    feedsTree = parse(RssFeedsPath)
except:
    print "Erreur self.feedsTree"
#Recupere la liste des flux dans RSSFeeds.xml
if feedsTree:
    #self.feedsList = self.getCurrentRssFeeds()
    feedsList = dict()
    sets = feedsTree.getElementsByTagName('set')
    print "SET = %s " % sets
    for s in sets:
        setName = 'set'+s.attributes["id"].value
        print "SETNAME = %s " % setName
        feedsList[setName] = {'feedslist':list(), 'attrs':dict()}
        #get attrs
        for attrib in s.attributes.keys():
            feedsList[setName]['attrs'][attrib] = s.attributes[attrib].value
        #get feedslist
        feeds = s.getElementsByTagName('feed')
        for feed in feeds:
            feedsList[setName]['feedslist'].append({'url':feed.firstChild.toxml(), 'updateinterval':feed.attributes['updateinterval'].value})
    for setName in feedsList:
        val = setName[0]
        print "%s = %s " % (setName,val)
        print "url = %s " % feedsList[setName]
        #for set in feedsList[setName]:
        #    print "SET = %s" % set
        for feed in feedsList[setName]['feedslist']:
            print "url = %s " % feed['url']
    print "URL = %s " % feedsList['set1']

get_time = time.time() + (60)    

#Verifie que xbmc tourne
while (not xbmc.abortRequested):
#Partie de recuperation de flux rss sur le net
    NbNews = 0
    time_debut = time.time()
    #print "TIME debut = %f " % time.time() 
    #Sauve les flux RSS
    for setName in feedsList:
        i = 0
        for feed in feedsList[setName]['feedslist']:
            i += 1
            #print "=>url = %s " % feed['url']
            updateinterval = int(feed['updateinterval']) * 60
            current_time = time.time()
            diff_time  = current_time - (get_time + updateinterval)
            #print "diff_time = %f" % diff_time
            #if (current_time > (get_time + updateinterval)):
            if True:
                get_time = time.time()    
                #http://www.lequipe.fr/Xml/actu_rss.xml
                filename = feed['url']
                filename = re.sub('^http://.*/','Rss-',filename)
                #self.RssFeeds = xbmc.translatePath('special://userdata/%s' % filename)
                RssFeeds = '%s/%s' % (__profile__,filename)
                #teste si le fichier existe
                if (os.path.isfile(RssFeeds)):
                    date_modif = os.stat(RssFeeds).st_mtime
                    diff = time.time() - date_modif
                    #print "diff = %f, date_modif = %f, updateinterval %d" % (diff,date_modif,updateinterval )
                    #Si le flux est plus ancien que le updateinterval on le telecharge de nx
                    if (diff > updateinterval):
                        print "=>filename = %s, RssFeeds = %s, url = %s " % (filename,RssFeeds, feed['url'])
                        urllib.urlretrieve(feed['url'], filename = RssFeeds)
                        #On efface le doc deja parser
                        os.remove('%s-pickle' % RssFeeds)
                        #On le parse de nouveau
                        #On parse le fichier rss et on le sauve sur le disque
                        doc = feedparser.parse('file://%s' % RssFeeds)
                        #Sauve le doc parse directement
                        output = open(('%s-pickle' % RssFeeds), 'wb')
                        # Pickle dictionary using protocol 0.
                        pickle.dump(doc, output)
                        output.close()

                        print "date = %f, epoc time = %f  " % (date_modif, time.time())
                else:
                    #Le fichier n'existe pas on le telecharge
                    urllib.urlretrieve(feed['url'], filename = RssFeeds)
                    #On parse le fichier rss et on le sauve sur le disque
                    doc = feedparser.parse('file://%s' % RssFeeds)
                    #Sauve le doc parse directement
                    output = open(('%s-pickle' % RssFeeds), 'wb')
                    # Pickle dictionary using protocol 0.
                    pickle.dump(doc, output)
                    output.close()

    #initialise start time
    start_time = time.time()
    time.sleep( 5 )
