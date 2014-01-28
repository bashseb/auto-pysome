#!/usr/bin/env python2
import subprocess
import re
import sqlite3 as lite
import fnmatch
from PIL import Image
import os

# tmp default
TMP_MEDIA_PATH = '/home/seb/tmp/testfolder/'
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
        self.VidMatch = ['*.avi', '*.AVI', '*.mp4', '*.MP4', '*.MOV', '*.mov']

    def Create(self):
        print "Creating database ('" + str(self.dbPath) + "') using path = " + str(self.mediaPath)
        subprocess.call(["sqlite3", self.dbPath, '.tables .exit'])

        self.traversePath()

        con = lite.connect(self.dbPath)
        with con:
            cur = con.cursor()
            cur.execute('SELECT SQLITE_VERSION()')
            data = cur.fetchone()
            print "SQLite version: %s" % data  
            cur.execute("DROP TABLE IF EXISTS Media")

            cur.execute("CREATE TABLE Media (Id INTEGER PRIMARY KEY, Filename TEXT, Date TEXT, Type INTEGER, Xres INTEGER, Yres INTEGER, Orientation INTEGER, Length FLOAT);") 
            # Type is 0 for image, 100 for video
            self.addImages(cur)
            self.addVideos(cur)



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

        if __debug__:
            print "img files"
            print self.legitIMGfiles
            print "video files"
            print self.legitVIDfiles

    def addImages(self, dbCon):
        for item in self.legitIMGfiles:
            date, reso, orient = self.readExif(item)
            if __debug__:
                print "adding file '{0}' with date '{1}', resolution '{2}' and orientation '{3}'".format(item, date, reso, orient)
            if isinstance(date, basestring):
            #if date != 0:
                # insert with type = 0 (imgs) and Length = 0.
                dbCon.execute("INSERT INTO Media(Filename, Date, Type, Xres, Yres, Orientation, Length) VALUES ('" + item + "', '" + date + "', 0, {0}, {1}, {2}, 0.);".format(reso[0], reso[1], orient))

        self.nImages = dbCon.lastrowid
        print " added images. last index " + str( self.nImages)

    def addVideos(self, dbCon):
        for item in self.legitVIDfiles:
            length, width, height, date  = self.readExifVideo(item)

            if length > 0:
                if __debug__:
                    print "adding file '{0}' with date '{1}', resolution '{2}' and length '{3}'s".format(item, date, (width,height), length)
                dbCon.execute("INSERT INTO Media(Filename, Date, Type, Xres, Yres, Orientation, Length) VALUES ('" + item + "', '" + date + "', 100, {0}, {1}, 1, {2});".format(width, height, length))

        self.nVideos = dbCon.lastrowid
        print " added videos. last index " + str( self.nImages)

    def readExifVideo(self, filename):
        # there isn't really any EXIF standard on video files.  'Hachoir' could be a match, but it seems even easier with mplayer -identify
        # or ffprobe -loglevel error -show_streams ...
        # mplayer -vo dummy -ao dummy -identify 2>/dev/null |  grep ...
        return self.readExifVideoMplayer(filename)

    def readExifVideoMplayer(self, filename):
        # alternative is `ffprobe`, but this doesn't show e.g. Digitization time of 'olympus'
        # length (ID_LENGTH) , resolution (ID_VIDEO_WIDTH, ID_VIDEO_HEIGHT), date (ID_CLIP_INFO
        FNULL = open(os.devnull, 'w')
        p = subprocess.Popen(["mplayer", "-vo", "dummy", "-ao", "dummy", "-identify", filename], stdout=subprocess.PIPE, stderr=FNULL)
        FNULL.close()
        out = subprocess.check_output(('grep', '^ID_'), stdin=p.stdout)

        # regex = re.compile("(?P<key>\w*?)=(?P<value>[0-9.]*)$",re.MULTILINE) # find all ID_..=number fields
        regex = re.compile("(?P<key>ID_LENGTH|ID_VIDEO_WIDTH|ID_VIDEO_HEIGHT*?)=(?P<value>[0-9.]*)$",re.MULTILINE)
        r = regex.findall(out)
        for tup in r:
            if tup[0] == 'ID_VIDEO_WIDTH':
                w=numint(tup[1])
            elif tup[0] == 'ID_VIDEO_HEIGHT':
                h=numint(tup[1])
            elif tup[0] == 'ID_LENGTH':
                try:
                    l = float(tup[1])
                except:
                    print "Value {0} is not a float".format(tup[1])
            else:
                print "Video {0} doesn't parse WIDTH/HEIGHT or LENGTH correctly".format(filename)
                print r
                return 0
        # match date, must start with '20'
        regex = re.compile("(?P<key>ID_CLIP_INFO_VALUE[0-3]*?)=(?P<value>20.*:.*:.*)$",re.MULTILINE)
        r = regex.findall(out)
        if len(r) == 1:
            if isinstance(r[0][1], basestring):
                date = r[0][1]
        else:
            print "Video {0} doesn't parse DATE correctly".format(filename)
            # TODO olympus uses strange date format:
            # [('ID_CLIP_INFO_VALUE0', 'Fri Dec 27 20:48:47 2013'), ('ID_CLIP_INFO_VALUE1', 'OLYMPUS E-P1')]
            # normally 2013-03-06 20:14:48
            print r
            return 0, 0, 0, 0

        return l, w, h, date


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
            if 274 in exif_data:
                # row 0, column 0 default 1: 0,0 top left . 2: top right , 4: bot right, 4: bot left
                # 5: left top, right top, right bot, left bot
                orientation = exif_data[274] 
            else:
                orientation = 1
            return datestr, img.size, orientation
            
        except: 
            # TODO:
            # fallback on file create date
            print filename + str(" ignored.")

        return 0, 0

def numint(s):
    try:
        return int(s)
    except:
        print "Value {0} is not an integer".format(s)

if __name__ == "__main__":
    mydb = db(path="my-test.sqlite", mediaPath=TMP_MEDIA_PATH)
    mydb.Create()
