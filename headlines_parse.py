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

DEBUG = True

class ParseRSS:
    def __init__(self):
        #Teste si le repertoire script.headlines existe
        self.DATA_PATH = xbmc.translatePath( "special://profile/addon_data/script.headlines/")
        if not os.path.exists(self.DATA_PATH): os.makedirs(self.DATA_PATH)

    def download(self,path,src,dst):
        """
        Download image and caching in script directory
        """
        tmpname = ('%s-img/%s' % (path,xbmc.getCacheThumbName(src)))
        if os.path.exists(tmpname):
            os.remove(tmpname)
        urllib.urlretrieve(src, filename = tmpname)
        return tmpname


    def Run(self, RssName):
        """
        Parse RSS or ATOMM fole with feedparser
        """
        if DEBUG == True: print "[headlines_parse] RssName = %s " % RssName
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
                #On vide les commentaires 
                #Reponses = '[CR]<p>==== COMMENTAIRES ====</p>[CR]'
                Reponses = ' '
                try:
                    #On efface toutes les anciennes images des flux
                    if not os.path.isdir('%s-img' % RssFeeds) : os.mkdir('%s-img' % RssFeeds)
                    title = unicode(entry.title)
                    #Recupere un media associe
                    if entry.has_key('enclosures'):
                        if entry.enclosures:
                            #print "Enclosure = %s " % entry.enclosures[0]
                            #actuellement que les images
                            if 'image' in entry.enclosures[0].type:
                                link_img = entry.enclosures[0].href
                                img_name = self.download(RssFeeds,link_img,'/tmp/img.jpg')
                            if 'video' in entry.enclosures[0].type:
                                link_video = entry.enclosures[0].href
                                if DEBUG == True: print "[headlines_parse] link_video = %s " % link_video
                    if entry.has_key('media_thumbnail'):
                        #print "media_thumbnail % s" % entry['media_thumbnail']
                        #Ajout d'une image en vignettei comme il peut
                        #y en avoir plusieurs on les parcours toutes
                        for thumb in entry['media_thumbnail']:
                            if DEBUG == True: print "[headlines_parse] thumb = %s " % thumb['url']
                            link_img = thumb['url']
                            img_name = self.download(RssFeeds,link_img,'/tmp/img.jpg')
                     #Video YouTube
                    if entry.has_key('media_content'):
                        #Recupere les videos, Youtubes et autres ?
                        link_video =  entry.media_content[0]['url']
                        if DEBUG == True: print "[headlines_parse] link_video youtube = %s " % link_video
                    
                    #C'est ici que le recupere la news
                    if entry.has_key('content') and len(entry['content']) >= 1:
                        description = unicode(entry['content'][0].value)
                        #type contient le type de texte : html, plain text, etc...
                        type = entry['content'][0].type
                    else:
                        #Si pas de content on essaye le summary_detail
                        description = unicode(entry['summary_detail'].value)
                        type = 'text'
                    #Lit les commentaires
                    if entry.has_key('wfw_commentrss'):
                        link_comment = entry['wfw_commentrss']
                        if DEBUG == True: print "[headlines_parse] link_comment = %s " % entry['wfw_commentrss']
                        comments = feedparser.parse(link_comment)
                        #if comments.status < 400:
                        if comments.feed:
                            for commentaire in comments['entries']:
                                try:
                                    #if commentaire.has_hey('title'):
                                    Reponses += 'Titre : %s [CR]' % unicode(commentaire['title'])
                                    if commentaire.has_key('content') and len(commentaire['content']) >= 1:
                                        Reponses += '<div><p>'
                                        Reponses += unicode(commentaire['content'][0].value)
                                        Reponses += '</p></div>[CR]'
                                    #if commentaire.has_hey('author'):
                                    Reponses += 'Auteur : %s [CR][CR]' % unicode(commentaire['author'])

                                except AttributeError, e:
                                    if DEBUG == True: print "[headlines_parse] Comment AttributeError : %s, commentaire = %s " % (str(e), commentaire)
 
                     #Recuperation de la date de la news
                    if entry.has_key('date'):
                        date = entry['date']
                    else:
                        date = 'unknown'
                    #On rempli les news
                    description += Reponses
                    headlines.append((title, date, description, type, img_name,
                                      link_video))
                    NbNews += 1
                    #On vide le nom de l'image et l'adresse de la video  pour le prochain tour
                    img_name = ' '
                    link_video = 'False'
                except AttributeError, e:
                    print "[headlines_parse] AttributeError : %s" % str(e)
                    pass
        else:
            print ('Error %s, getting %r' % (doc.status, url))
        #On sauve le headlines dans un fichier
        output = open(('%s-headlines' % RssFeeds), 'wb')
        # Pickle dictionary using protocol 0.
        pickle.dump(headlines, output)
        output.close()

    def getRSS(self,url):
        if DEBUG == True: print "[headlines_parse] RssURL = %s " % url
        updateinterval = 1
        filename = url
        filename = re.sub('^http://.*/','Rss-',filename)
        RssFeeds = '%s/%s' % (self.DATA_PATH,filename)
        if DEBUG == True: print "[headlines_parse] 152"
        #teste si le fichier existe
        if (os.path.isfile(RssFeeds)):
            if DEBUG == True: print "[headlines_parse] 155"
            date_modif = os.stat(RssFeeds).st_mtime
            diff = time.time() - date_modif
            #print "diff = %f, date_modif = %f, updateinterval %d" % (diff,date_modif,updateinterval )
            #Si le flux est plus ancien que le updateinterval on le telecharge de nx
            if (diff > updateinterval):
                #print "=>filename = %s, RssFeeds = %s, url = %s, encurl = %s" % (filename,RssFeeds, feed['url'], encurl)
                #urllib.urlretrieve(feed['url'], filename = RssFeeds)
                #Test au cas ou pb de connexion
                try:
                    urllib.urlretrieve(url, filename = RssFeeds)
                    #On efface le doc deja parser
                    try:
                        os.remove('%s-pickle' % RssFeeds)
                    except OSError, e:
                        print "[headlines_parse] Error : %s " % str(e)

                    #On le parse de nouveau
                    #On parse le fichier rss et on le sauve sur le disque
                    doc = feedparser.parse('file://%s' % RssFeeds)
                    #print "Version = %s " % doc.version
                except IOError, e:
                    print "[headlines_parse] Erreur urllib : %s " % str(e)
                if doc.version != '':
                    #Sauve le doc parse directement
                    output = open(('%s-pickle' % RssFeeds), 'wb')
                    # Pickle dictionary using protocol 0.
                    pickle.dump(doc, output)
                    output.close()
                    #RSStream = self.ParseRSS()
                    self.Run(RssFeeds)
                #On ignore le flux
                else:
                    print "[headlines_parse] Erreur RSS : %s " % RssFeeds
                    locstr = "Erreur : %s " % RssFeeds
                    xbmc.executebuiltin("XBMC.Notification(%s : ,%s,30)" %
                                        (locstr, 'Flux RSS non reconnu'))


                if DEBUG == True: print "[headlines_parse] date = %f, epoc time = %f  " % (date_modif, time.time())
        else:
                if DEBUG == True: print "[headlines_parse] 196Telecharge RssURL = %s " % url
                #Le fichier n'existe pas on le telecharge
                #urllib.urlretrieve(feed['url'], filename = RssFeeds)
                #Ajoute erreur timeout si pb de connexion
                try:
                    if DEBUG == True: print "[headlines_parse] Telecharge RssURL = %s " % url
                    urllib.urlretrieve(url, filename = RssFeeds)
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
                        #RSStream = self.ParseRSS()
                        self.Run(RssFeeds)
                        #On ignore le flux
                    else:
                        print "[headlines_parse] Erreur RSS : %s " % RssFeeds
                        locstr = "Erreur : %s " % RssFeeds
                        xbmc.executebuiltin("XBMC.Notification(%s : ,%s,30)" %
                                            (locstr, 'Flux RSS non reconnu'))
                except IOError, e:
                    print "[headlines_parse] Erreur urllib : %s " % str(e)

