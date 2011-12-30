# -*- coding: utf-8 -*-
import xbmc, xbmcgui
import xbmcaddon
#python modules
import os, time, stat, re, copy, time
from xml.dom.minidom import parse, Document, _write_data, Node, Element
import pickle
import glob

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
def download(path,src,dst):
    """
    Download image and caching in script directory
    """
    tmpname = ('%s-img/%s' % (path,xbmc.getCacheThumbName(src)))
    if os.path.exists(tmpname):
        os.remove(tmpname)
    urllib.urlretrieve(src, filename = tmpname)
    return tmpname

#Nettoie le code HTML d'après rssclient de xbmc
def htmlentitydecode(s):
    # code from http://snipplr.com/view.php?codeview&id=15261
    # First convert alpha entities (such as &eacute;)
    # (Inspired from http://mail.python.org/pipermail/python-list/2007-June/443813.html)
    def entity2char(m):
        entity = m.group(1)
        if entity in htmlentitydefs.name2codepoint:
            return unichr(htmlentitydefs.name2codepoint[entity])
        return u" "  # Unknown entity: We replace with a space.
    
    t = re.sub(u'&(%s);' % u'|'.join(htmlentitydefs.name2codepoint), entity2char, s)
  
    # Then convert numerical entities (such as &#233;)
    t = re.sub(u'&#(\d+);', lambda x: unichr(int(x.group(1))), t)
   
    # Then convert hexa entities (such as &#x00E9;)
    return re.sub(u'&#x(\w+);', lambda x: unichr(int(x.group(1),16)), t)

def cleanText(txt):
    p = re.compile(r'\s+')
    txt = p.sub(' ', txt)
    
    txt = htmlentitydecode(txt)
    
    p = re.compile(r'<[^<]*?/?>')
    return p.sub('', txt)
  
def ParseRSS(RssName):
    """
    Parse RSS or ATOM file with feedparser
    """
    print "RssName = %s " % RssName
    #Recupere l'adresse du flux dans self.RssFeedName
    RssFeeds = RssName
    NbNews = 0
    # parse the document
    #Si c'est deja fait on lit le fichier 
    if (os.path.isfile('%s-pickle' % RssFeeds)):
        pkl_file = open(('%s-pickle' % RssFeeds), 'rb')
        doc = pickle.load(pkl_file)
        pkl_file.close()
    else:
        #Sinon on le parse
        doc = feedparser.parse('file://%s' % RssFeeds)
    #Récupère le titre du flux
    img_name = ' '
    link_video = 'False'
    #Vide les headlines lors d'un nouveau appel
    headlines = []
    #On recupere les tags suivants :
    #title, entry.content, enclosure pour les images
    #et date
    if doc.status < 400:
        for entry in doc['entries']:
            try:
                #On efface toutes les anciennes images des flux
                if not os.path.isdir('%s-img' % RssFeeds) : os.mkdir('%s-img' % RssFeeds)
                title = unicode(entry.title)
                #Recupere un media associe
                if entry.has_key('enclosures'):
                    if entry.enclosures:
                        #print "Enclosure = %s " % entry.enclosures[0].href
                        #print "Enclosure = %s " % entry.enclosures[0].type
                        #actuellement que les images
                        if 'image' in entry.enclosures[0].type:
                            link_img = entry.enclosures[0].href
                            img_name = download(RssFeeds,link_img,'/tmp/img.jpg')
                        if 'video' in entry.enclosures[0].type:
                            link_video = entry.enclosures[0].href
                            print "link_video = %s " % link_video
                #C'est ici que le recupere la news
                if entry.has_key('content') and len(entry['content']) >= 1:
                    description = unicode(entry['content'][0].value)
                    #type contient le type de texte : html, plain text, etc...
                    type = entry['content'][0].type
                else:
                    #Si pas de content on essaye le summary_detail
                    description = unicode(entry['summary_detail'].value)
                    type = 'text'
                #Recuperation de la date de la news
                if entry.has_key('date'):
                    date = entry['date']
                else:
                    date = 'unknown'
                #On rempli les news
                headlines.append((title, date, description, type, img_name,
                                  link_video))
                NbNews += 1
                #On vide le nom de l'image et l'adresse de la video  pour le prochain tour
                img_name = ' '
                link_video = 'False'
            except AttributeError, e:
                print "AttributeError : %s" % str(e)
                pass
    else:
        print ('Error %s, getting %r' % (doc.status, url))
    #On sauve le headlines dans un fichier
    output = open(('%s-headlines' % RssFeeds), 'wb')
    # Pickle dictionary using protocol 0.
    pickle.dump(headlines, output)
    output.close()

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
                            os.remove('%s-pickle' % RssFeeds)
                            #On le parse de nouveau
                            #On parse le fichier rss et on le sauve sur le disque
                            doc = feedparser.parse('file://%s' % RssFeeds)
                            #print "Version = %s " % doc.version
                        except e:
                            print "Erreur urllib : %s " % str(e)
                        if doc.version != '':
                            #Sauve le doc parse directement
                            output = open(('%s-pickle' % RssFeeds), 'wb')
                            # Pickle dictionary using protocol 0.
                            pickle.dump(doc, output)
                            output.close()
                            ParseRSS(RssFeeds)
                        #On ignore le flux
                        else:
                            print "Erreur RSS : %s " % RssFeeds
                            locstr = "Erreur : %s " % RssFeeds
                            xbmc.executebuiltin("XBMC.Notification(%s : ,%s,30)" %
                                                (locstr, 'Flux RSS non reconnu'))


                        print "date = %f, epoc time = %f  " % (date_modif, time.time())
                else:
                    #Le fichier n'existe pas on le telecharge
                    #urllib.urlretrieve(feed['url'], filename = RssFeeds)
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
                        ParseRSS(RssFeeds)
                    #On ignore le flux
                    else:
                        print "Erreur RSS : %s " % RssFeeds
                        locstr = "Erreur : %s " % RssFeeds
                        xbmc.executebuiltin("XBMC.Notification(%s : ,%s,30)" %
                                            (locstr, 'Flux RSS non reconnu'))
    #initialise start time
    start_time = time.time()
    time.sleep( .5 )
