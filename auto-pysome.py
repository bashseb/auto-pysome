#!/usr/bin/env python2
from subprocess import call
import sqlite3 as lite
import fnmatch
from PIL import Image
import os

# tmp default
TMP_MEDIA_PATH = '/mnt/esata/pics/Italien/Rom 2009/'
imgDBname = 'Imgs'
vidDBname = 'Vids'

class db:
    def __init__(self, path=None, mediaPath=None):
        self.dbPath = path
        self.mediaPath = mediaPath
        self.nImages = None
        self.nVideos = None
        self.legitIMGfiles = []
        self.legitVIDfiles = []
        self.ImgMatch = ['*.jpg', '*.JPG']
        self.VidMatch = ['*.avi', '*.AVI', '*.mp4', '*.MP4']

    def Create(self):
        print "Creating database ('" + str(self.dbPath) + "') using path = " + str(self.mediaPath)
        call(["sqlite3", self.dbPath, '.tables .exit'])

        self.traversePath()


#         for item in self.legitIMGfiles:
#             print self.readExif(item)

        con = lite.connect(self.dbPath)

        with con:
            cur = con.cursor()
            cur.execute('SELECT SQLITE_VERSION()')
            data = cur.fetchone()
            print "SQLite version: %s" % data  
            cur.execute("DROP TABLE IF EXISTS " + str(imgDBname))
            cur.execute("DROP TABLE IF EXISTS " + str(vidDBname))

            self.addImages(cur)



    def traversePath(self):
        for root, subfolders, files in os.walk(self.mediaPath):
            
            for ext in self.ImgMatch:
                for filename in fnmatch.filter(files, ext):
                    # print os.path.join(root, filename)
                    self.legitIMGfiles.append(os.path.join(root,filename))
            for ext in self.VidMatch:
                for filename in fnmatch.filter(files, ext):
                    # print os.path.join(root, filename)
                    self.legitVIDfiles.append(os.path.join(root,filename))

    def addImages(self, dbCon):
        dbCon.execute("CREATE TABLE "+ str(imgDBname) + "(Id INTEGER PRIMARY KEY, Filename TEXT, Date TEXT, Xres INTEGER, Yres INTEGER);") 
        for item in self.legitIMGfiles:
            date, reso = self.readExif(item)
            if isinstance(date, basestring):
            #if date != 0:
                dbCon.execute("INSERT INTO " + str(imgDBname) + "(Filename) VALUES ('" + item + ", " + date + ", {0}, {1}');".format(reso[0], reso[1]))

        self.nImages = dbCon.lastrowid
        print " added images. last index " + str( self.nImages)

    def addVideos(self, dbCon):
        dbCon.execute("CREATE TABLE "+ str(vidDBname) + "(Id INTEGER PRIMARY KEY, Filename TEXT, Date TEXT);") 
        for item in self.legitVIDfiles:
            date = self.readExifVideo(item)
            # if isinstance(date, basestring):
                # dbCon.execute("INSERT INTO " + str(vidDBname) + "(Filename) VALUES ('" + item + ", " + date + "');")

        self.nVideos = dbCon.lastrowid
        print " added videos. last index " + str( self.nImages)

    def readExifVideo(self, filename):
        # TODO: read resolution, length
        return 0

    def readExif(self, filename):
        try:
            img = Image.open(filename)
            exif_data = img._getexif()
        #  306: file change date and time
        #  36867: u'2009:03:29 12:00:55', Date time original
        #  36868: u'2009:03:29 12:00:55', date time original  Digitized
            datestr = ''
            if 306 in exif_data:
                datestr =  exif_data[306]
            elif 36867 in exif_data:
                datestr = exif_data[36867]
            elif 36868 in exif_data:
                datestr = exif_data[36868]
            else:
                print "ignoring " + str(filename)
                return 0, 0
            return datestr, img.size
            
        except: 
            # TODO:
            # fallback on file create date
            print filename + str(" ignored.")

        return 0, 0


if __name__ == "__main__":
    mydb = db(path="my-test.sqlite", mediaPath=TMP_MEDIA_PATH)
    mydb.Create()
