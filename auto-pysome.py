#!/usr/bin/env python2
from subprocess import call
import sqlite3 as lite
import fnmatch
from PIL import Image

# tmp default
TMP_MEDIA_PATH = '/mnt/esata/pics/Italien/'
imgDBname = 'Imgs'
vidDBname = 'Vids'

class db:
    def __init__(self, path=None, mediaPath=None):
        self.dbPath = path
        self.mediaPath = mediaPath
        self.nImages = None
        self.nVideos = None
        self.ImgMatch = ['*.jpg', '*.JPG']
        self.VidMatch = ['*.avi', '*.mp4']

    def Create(self):
        import os
        print "dbCreate"
        print self.mediaPath
        legitIMGfiles = []
        legitVIDfiles = []
        call(["sqlite3", self.dbPath, '.tables .exit'])


        for root, subfolders, files in os.walk(self.mediaPath):
            
            for ext in self.ImgMatch:
                for filename in fnmatch.filter(files, ext):
                    # print os.path.join(root, filename)
                    legitIMGfiles.append(os.path.join(root,filename))
            for ext in self.VidMatch:
                for filename in fnmatch.filter(files, ext):
                    # print os.path.join(root, filename)
                    legitVIDfiles.append(os.path.join(root,filename))

#         for item in legitIMGfiles:
#             print self.readExif(item)

        con = lite.connect(self.dbPath)

        with con:
            cur = con.cursor()
            cur.execute('SELECT SQLITE_VERSION()')
            data = cur.fetchone()
            print "SQLite version: %s" % data  
            cur.execute("DROP TABLE IF EXISTS " + str(imgDBname))
            cur.execute("DROP TABLE IF EXISTS " + str(vidDBname))


            cur.execute("CREATE TABLE "+ str(imgDBname) + "(Id INTEGER PRIMARY KEY, Filename TEXT, Date TEXT);") 
            for item in legitIMGfiles:
                date = self.readExif(item)
                if isinstance(date, basestring):
                #if date != 0:
                    cur.execute("INSERT INTO " + str(imgDBname) + "(Filename) VALUES ('" + item + ", " + date + "');")

#             cur.execute("CREATE TABLE "+ str(vidDBname) + "(Id INTEGER PRIMARY KEY, Filename TEXT);") 
            self.nImages = cur.lastrowid
            print "last " + str( self.nImages)

    def readExif(self, filename):
        try:
            img = Image.open(filename)
            exif_data = img._getexif()
        #  306: file change date and time
        #  36867: u'2009:03:29 12:00:55', Date time original
        #  36868: u'2009:03:29 12:00:55', date time original  Digitized
            if 306 in exif_data:
                return exif_data[306]
            elif 36867 in exif_data:
                return exif_data[36867]
            elif 36868 in exif_data:
                return exif_data[36868]
            else:
                print "ignoring " + str(filename)
        except: 
            # TODO:
            # fallback on file create date
            print filename + str(" ignored.")

        return 0


if __name__ == "__main__":
    mydb = db(path="my-test.sqlite", mediaPath=TMP_MEDIA_PATH)
    mydb.Create()
