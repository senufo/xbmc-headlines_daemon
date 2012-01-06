# -*- coding: utf-8 -*-
import xbmc, xbmcgui
import xbmcaddon
#python modules
import os, time, stat, re, copy, time
from xml.dom.minidom import parse, Document, _write_data, Node, Element
import pickle
import glob
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

DEBUG = False

#Teste si le repertoire script.headlines existe
DATA_PATH = xbmc.translatePath( "special://profile/addon_data/script.headlines/")
if not os.path.exists(DATA_PATH): os.makedirs(DATA_PATH)

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
    for s in sets:
        setName = 'set'+s.attributes["id"].value
        feedsList[setName] = {'feedslist':list(), 'attrs':dict()}
        #get attrs
        for attrib in s.attributes.keys():
            feedsList[setName]['attrs'][attrib] = s.attributes[attrib].value
        #get feedslist
        feeds = s.getElementsByTagName('feed')
        for feed in feeds:
            feedsList[setName]['feedslist'].append({'url':feed.firstChild.toxml(), 'updateinterval':feed.attributes['updateinterval'].value})

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

            updateinterval = int(feed['updateinterval']) * 60
            current_time = time.time()
            diff_time  = current_time - (get_time + updateinterval)
            #if (current_time > (get_time + updateinterval)):
            if True:
                get_time = time.time()
                #On recuper l'url et on la transforme en non de fichier
                filename = feed['url']
                filename = re.sub('^http://.*/','Rss-',filename)
                RssFeeds = '%s/%s' % (DATA_PATH,filename)
                #teste si le fichier existe
                if (os.path.isfile(RssFeeds)):
                    date_modif = os.stat(RssFeeds).st_mtime
                    diff = time.time() - date_modif
                    #print "diff = %f, date_modif = %f, updateinterval %d" % (diff,date_modif,updateinterval )
                    #Si le flux est plus ancien que le updateinterval on le telecharge de nx
                    if (diff > updateinterval):
                        #print "=>filename = %s, RssFeeds = %s, url = %s, encurl = %s" % (filename,RssFeeds, feed['url'], encurl)
                        #urllib.urlretrieve(feed['url'], filename = RssFeeds)
                        #Test au cas ou pb de connexion
                        try:
                            urllib.urlretrieve(encurl, filename = RssFeeds)
                            #On efface le doc deja parser
                            try:
                                os.remove('%s-pickle' % RssFeeds)
                            except OSError, e:
                                print "Error : %s " % str(e)

                            #On le parse de nouveau
                            #On parse le fichier rss et on le sauve sur le disque
                            doc = feedparser.parse('file://%s' % RssFeeds)
                            #print "Version = %s " % doc.version
                        except IOError, e:
                            print "Erreur urllib : %s " % str(e)
                        if doc.version != '':
                            #Sauve le doc parse directement
                            output = open(('%s-pickle' % RssFeeds), 'wb')
                            # Pickle dictionary using protocol 0.
                            pickle.dump(doc, output)
                            output.close()
                            RSStream = ParseRSS()
                            RSStream.Run(RssFeeds)
                        #On ignore le flux
                        else:
                            print "Erreur RSS : %s " % RssFeeds
                            locstr = "Erreur : %s " % RssFeeds
                            xbmc.executebuiltin("XBMC.Notification(%s : ,%s,30)" %
                                                (locstr, 'Flux RSS non reconnu'))


                        if DEBUG == True: print "date = %f, epoc time = %f  " % (date_modif, time.time())
                else:
                    #Le fichier n'existe pas on le telecharge
                    #urllib.urlretrieve(feed['url'], filename = RssFeeds)
                    #Ajoute erreur timeout si pb de connexion
                    try:
                        urllib.urlretrieve(encurl, filename = RssFeeds)
                        #On parse le fichier rss et on le sauve sur le disque
                        #print "Download = %s " % RssFeeds
                        doc = feedparser.parse('file://%s' % RssFeeds)
                        #print "Version 248 = %s " % doc.version
                        #Vérifie si c'est un flux rss ou atom
                        if doc.version != '':
                            #Sauve le doc parse directement
                            output = open(('%s-pickle' % RssFeeds), 'wb')
                            # Pickle dictionary using protocol 0.
                            pickle.dump(doc, output)
                            output.close()
                            RSStream = ParseRSS()
                            RSStream.Run(RssFeeds)
                        #On ignore le flux
                        else:
                            print "Erreur RSS : %s " % RssFeeds
                            locstr = "Erreur : %s " % RssFeeds
                            xbmc.executebuiltin("XBMC.Notification(%s : ,%s,30)" %
                                            (locstr, 'Flux RSS non reconnu'))
                    except IOError, e:
                            print "Erreur urllib : %s " % str(e)

    #initialise start time
    start_time = time.time()
    time.sleep( .5 )
