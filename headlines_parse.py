# -*- coding: utf-8 -*-
"""
Class to get and parse RSS/ATOM stream
"""
import xbmc
#python modules
import os, time, re
import pickle

# rdf modules
import feedparser
import urllib

#DEBUG_LOG = True
DEBUG_LOG = False
#Function Debug
def debug(msg):
    """
    print message if DEBUG_LOG == True
    """
    if DEBUG_LOG == True: print " [headlines_parse] : %s " % ( msg)


class ParseRSS:
    def __init__(self):
        """
        Initialize DATA_PATH
        """
        #Teste si le repertoire script.headlines existe
        self.DATA_PATH = xbmc.translatePath( 
            "special://profile/addon_data/script.headlines/")
        if not os.path.exists(self.DATA_PATH): os.makedirs(self.DATA_PATH)

    def download(self, path, src, NoNews):
        """
        Download image and caching in script directory
        """
        if not os.path.isdir('%s-img/%d' % (path, NoNews)) : 
            os.mkdir('%s-img/%d' % (path, NoNews))
            debug('MKDIR = %s-img/%d' % (path, NoNews))
        tmpname = ('%s-img/%d/%s' % (path, NoNews, xbmc.getCacheThumbName(src)))
        debug('tmpname = %s ' % tmpname)
        #if os.path.exists(tmpname):
        #    os.remove(tmpname)
        urllib.urlretrieve(src, filename = tmpname)
        return tmpname


    def Run(self, RssName):
        """
        Parse RSS or ATOMM fole with feedparser
        """
        debug( " RssName = %s " % RssName )
        #Recupere l'adresse du flux dans self.RssFeedName
        RssFeeds = RssName
        NbNews = 1
        ImageCount = 0
        SlideShowable = False
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
        img_name = ''
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
                    if not os.path.isdir('%s-img' % RssFeeds) : 
                        os.mkdir('%s-img' % RssFeeds)
                    title = unicode(entry.title)
                    #Recupere un media associe
                    if entry.has_key('enclosures'):
                        if entry.enclosures:
                            #print "Enclosure = %s " % entry.enclosures[0]
                            #actuellement que les images
                            if 'image' in entry.enclosures[0].type:
                                link_img = entry.enclosures[0].href
                                img_name = self.download(
                                            RssFeeds,link_img, NbNews)
                                ImageCount += 1
                            if 'video' in entry.enclosures[0].type:
                                link_video = entry.enclosures[0].href
                                debug( " link_video = %s " %
                                     link_video )
                    if entry.has_key('media_thumbnail'):
                        #print "media_thumbnail % s" % entry['media_thumbnail']
                        #Ajout d'une image en vignette comme il peut
                        #y en avoir plusieurs on les parcours toutes
                        for thumb in entry['media_thumbnail']:
                            debug( " thumb = %s " %
                                  thumb['url'] )
                            link_img = thumb['url']
                            img_name = self.download(
                                RssFeeds,link_img, NbNews)
                            ImageCount += 1
                     #Video YouTube
                    if entry.has_key('media_content'):
                        #Recupere les videos, Youtubes et autres ?
                        link_video =  entry.media_content[0]['url']
                        debug( " link_video youtube = %s " %
                              link_video )
                    
                    #C'est ici que le recupere la news
                    if entry.has_key('content') and len(entry['content']) >= 1:
                        description = unicode(entry['content'][0].value)
                        #type contient le type de texte : 
                        #html, plain text, etc...
                        content_type = entry['content'][0].type
                    else:
                        #Si pas de content on essaye le summary_detail
                        description = unicode(entry['summary_detail'].value)
                        content_type = 'text'
                    #Lit les commentaires
                    if entry.has_key('wfw_commentrss'):
                        link_comment = entry['wfw_commentrss']
                        debug( " link_comment = %s " %
                              entry['wfw_commentrss'] )
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
                                    debug( " Comment  AttributeError : %s, commentaire = %s " % (str(e), commentaire) )
 
                     #Recuperation de la date de la news
                    if entry.has_key('date'):
                        date = entry['date']
                    else:
                        date = 'unknown'
                    #On rempli les news
                    description += Reponses
                    #Si il y a plusieurs image on peux faire un diaporama
                    if ImageCount > 1:
                        SlideShowable = True
                    headlines.append((title, date, description, content_type, img_name,
                                      link_video, NbNews, ImageCount,
                                      SlideShowable ))
                    NbNews += 1
                    debug('NbNews = %d ' % NbNews)
                    #On vide le nom de l'image et l'adresse de la video  pour le prochain tour
                    img_name = ''
                    link_video = 'False'
                except AttributeError, e:
                    print " AttributeError : %s" % str(e)
                    
        else:
            print ('Error %s, getting %r' % (doc.status, RssName))
        #On sauve le headlines dans un fichier
        output = open(('%s-headlines' % RssFeeds), 'wb')
        # Pickle dictionary using protocol 0.
        pickle.dump(headlines, output)
        output.close()

    def getRSS(self, url):
        """
        Get url rss for parse doc
        """
        debug( " RssURL = %s " % url )
        #updateinterval = 1
        filename = url
        filename = re.sub('^http://.*/', 'Rss-', filename)
        RssFeeds = '%s/%s' % (self.DATA_PATH, filename)
        try:
            urllib.urlretrieve(url, filename = RssFeeds)
            #On efface le doc deja parser
            try:
                os.remove('%s-pickle' % RssFeeds)
            except OSError, e:
                print " Error : %s " % str(e)

            #On le parse de nouveau
            #On parse le fichier rss et on le sauve sur le disque
            doc = feedparser.parse('file://%s' % RssFeeds)
            #print "Version = %s " % doc.version
        except IOError, e:
            print " Erreur urllib : %s " % str(e)
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
            print " Erreur RSS : %s " % RssFeeds
            locstr = "Erreur : %s " % RssFeeds
            xbmc.executebuiltin("XBMC.Notification(%s : ,%s,30)" %
                                  (locstr, 'Flux RSS non reconnu'))
