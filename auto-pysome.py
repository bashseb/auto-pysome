#!/usr/bin/env python2
from __future__ import division
from __future__ import print_function
import subprocess
import re
import sqlite3 as lite
import fnmatch
from PIL import Image
import sys
import os
import dateutil.parser
import dateutil.relativedelta as relativedelta
import time

#from datetime import date, datetime, time, timedelta




import argparse

# tmp default
TMP_MEDIA_PATH = '/home/seb/tmp/testfolder/'

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

    def create(self, verb = 0):
        print("Creating database ('" + str(self.dbPath) + "') using path = '{}'".format(self.mediaPath))
        subprocess.call(["sqlite3", self.dbPath, '.tables .exit'])

        self.traversePath(verb=verb)
        
        if verb > 0:
            print("Found {} images and {} videos in path '{}'".format(len(self.legitIMGfiles), len(self.legitVIDfiles), self.mediaPath))
            print("Trying to add them to sqlite3 database '{}' .... ".format(self.dbPath))

        con = lite.connect(self.dbPath)
        with con:
            cur = con.cursor()
            cur.execute('SELECT SQLITE_VERSION()')
            data = cur.fetchone()
            if verb > 0:
                print("SQLite version: %s" % data)
            cur.execute("DROP TABLE IF EXISTS Media")

            cur.execute("CREATE TABLE Media (Id INTEGER PRIMARY KEY, Filename TEXT, Date TEXT, Type INTEGER, Xres INTEGER, Yres INTEGER, Orientation INTEGER, Length FLOAT);") 
            # Type is 0 for image, 100 for video
            self.addImages(cur, verb=verb)
            self.addVideos(cur, verb=verb)

    def traversePath(self, verb=0):
        for root, subfolders, files in os.walk(self.mediaPath):
            
            for ext in self.ImgMatch:
                for filename in fnmatch.filter(files, ext):
                    # print os.path.join(root, filename)
                    self.legitIMGfiles.append(os.path.join(root,filename))
            for ext in self.VidMatch:
                for filename in fnmatch.filter(files, ext):
                    # print os.path.join(root, filename)
                    self.legitVIDfiles.append(os.path.join(root,filename))

    def addImages(self, dbCon, verb=0):
        for item in self.legitIMGfiles:
            date, reso, orient = self.readExif(item)
            if verb > 0:
                print("adding file '{0}' with date '{1}', resolution '{2}' and orientation '{3}'".format(item, date, reso, orient))
            if isinstance(date, basestring):
            #if date != 0:
                # insert with type = 0 (imgs) and Length = 0.
                dbCon.execute("INSERT INTO Media(Filename, Date, Type, Xres, Yres, Orientation, Length) VALUES ('" + item + "', '" + date + "', 0, {0}, {1}, {2}, 0.);".format(reso[0], reso[1], orient))

        self.nImages = dbCon.lastrowid
        print(" added images. last index " + str( self.nImages))

    def addVideos(self, dbCon, verb = 0):
        for item in self.legitVIDfiles:
            length, width, height, date  = self.readExifVideo(item)

            if length > 0:
                if verb > 0:
                    print("adding file '{0}' with date '{1}', resolution '{2}' and length '{3}'s".format(item, date, (width,height), length))
                dbCon.execute("INSERT INTO Media(Filename, Date, Type, Xres, Yres, Orientation, Length) VALUES ('" + item + "', '" + date + "', 100, {0}, {1}, 1, {2});".format(width, height, length))

        self.nVideos = dbCon.lastrowid
        print(" added videos. last index " + str( self.nVideos))

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
                    print( "Value {0} is not a float".format(tup[1]))
            else:
                print( "Video {0} doesn't parse WIDTH/HEIGHT or LENGTH correctly".format(filename))
                return 0, 0, 0, 0
        # match date, must start with '20'
        regex = re.compile("(?P<key>ID_CLIP_INFO_VALUE[0-3]*?)=(?P<value>20.*:.*:.*)$",re.MULTILINE)
        r = regex.findall(out)
        if len(r) == 1:
            if isinstance(r[0][1], basestring):
                dates = dateutil.parser.parse(r[0][1]) 

        else:
            print( "Video {0} doesn't parse DATE correctly".format(filename))
            # TODO olympus uses strange date format:
            # [('ID_CLIP_INFO_VALUE0', 'Fri Dec 27 20:48:47 2013'), ('ID_CLIP_INFO_VALUE1', 'OLYMPUS E-P1')]
            # normally 2013-03-06 20:14:48
            return 0, 0, 0, 0

        return l, w, h, dates.isoformat()


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
                print("ignoring " + str(filename))
                return 0, 0, 0
            dates = dateutil.parser.parse(datestr.replace(':','-',2)) # date format is YYYY:MM:DD HH:MM:SS, which is not easily parsable
            if 274 in exif_data:
                # row 0, column 0 default 1: 0,0 top left . 2: top right , 4: bot right, 4: bot left
                # 5: left top, right top, right bot, left bot
                orientation = exif_data[274] 
            else:
                orientation = 1
            return dates.isoformat(), img.size, orientation
            
        except: 
            # TODO:
            # fallback on file create date
            print(filename + str(" ignored."))

        return 0, 0, 0


    def querydb(self, pattern = None, day=None, deltaDays=None, verb=0, pr='Id'):
        if not deltaDays:
            deltaDays = 1
        if verb> 0:
            print("Get rows '{}' from db ('{}') ".format(pr,self.dbPath, self.mediaPath))
            print("Pattern '{}', Day {}, delta days {}".format(pattern, day, deltaDays))

        if day:
            theday = dateutil.parser.parse(day)
            deltaDays=numint(deltaDays)
            fromd = theday - relativedelta.relativedelta(days=deltaDays-1)
            tilld = theday + relativedelta.relativedelta(days=deltaDays)
        else:
            fromd, tilld = self.check(verb=verb);

        if not pattern:
            pattern = '%' # all matching wildcard

        con = lite.connect(self.dbPath)
        with con:
            cur = con.cursor()

            if verb > 0:
                cur.execute("SELECT * FROM Media WHERE date between '{}' and '{}' and Filename like '{}'".format(fromd.isoformat(), tilld.isoformat(),pattern))
                for i in cur.fetchall():
                    print(i)

            cur.execute("SELECT {} FROM Media WHERE date between '{}' and '{}' and Filename like '{}'".format(pr, fromd.isoformat(), tilld.isoformat(),pattern))

            return [a[0] for a in cur.fetchall()]

    def check(self, verb=0):
        if verb> 0:
            print("Show database information ('" + str(self.dbPath) + "') using path = '{}'".format(self.mediaPath))

        con = lite.connect(self.dbPath)
        with con:
            cur = con.cursor()
            cur.execute('SELECT SQLITE_VERSION()')
            data = cur.fetchone()
            if verb > 0:
                print("SQLite version: %s" % data  )
            cur.execute('SELECT COUNT(*) FROM Media')
            nRows = cur.fetchone()

            cur.execute('SELECT COUNT(DISTINCT Type) FROM Media')
            nTypes = cur.fetchone()
            cur.execute('SELECT COUNT(*) FROM Media WHERE Type>=100;')
            self.nVideos = cur.fetchone()[0]
            cur.execute('SELECT COUNT(*) FROM Media WHERE Type<100;')
            self.nImages = cur.fetchone()[0]

            # TODO
            cur.execute('SELECT MIN(Date) FROM Media')
            minMedia = cur.fetchone()[0]
            cur.execute('SELECT MAX(Date) FROM Media')
            maxMedia = cur.fetchone()[0]

            cur.execute('SELECT MIN(Date) FROM Media WHERE Type>=100')
            minVideos = cur.fetchone()[0]
            cur.execute('SELECT MAX(Date) FROM Media WHERE Type>=100')
            maxVideos = cur.fetchone()[0]

            cur.execute('SELECT MIN(Date) FROM Media WHERE Type<100')
            minImages = cur.fetchone()[0]
            cur.execute('SELECT MAX(Date) FROM Media WHERE Type<100')
            maxImages = cur.fetchone()[0]
            # SELECT  Id, Filename, date FROM Media WHERE Type>=100 ORDER BY Date;


            print("{} images taken between {} and {}".format(self.nImages, minImages, maxImages))
            print("{} videos taken between {} and {}".format(self.nVideos, minVideos, maxVideos))

            minMedia = dateutil.parser.parse(minMedia)
            maxMedia = dateutil.parser.parse(maxMedia)

            return minMedia, maxMedia

                # TODO No of folders? 
                # folder names?
    def generateNaive(self, mediaList, verb=0):
        if verb> 0:
            print("Generate naive clip from ('" + str(self.dbPath) + "') ")
        con = lite.connect(self.dbPath)
        # set up temporary directory
        import tempfile
        import shutil
        try:
            dirpath = tempfile.mkdtemp()
    
            with con:
                cur = con.cursor()
    
                if verb > 0:
                    cur.execute("SELECT * FROM Media WHERE Id IN ({})".format(",".join(map(str, mediaList))) )
                    for i in cur.fetchall():
                        print(i)

                # TODO: randomly select/deselect some pictures
                # convert images
                cur.execute("SELECT * FROM Media WHERE Id IN ({}) and Type<100 ".format(",".join(map(str, mediaList))) )
                imgList = cur.fetchall()
                imgVids = []
                for img in imgList:
                    # resizeShave(img[1], (img[4],img[5]), destination=dirpath, orientation=img[6], verb=verb)
                    outfn = resizeShave(img[1], (img[4],img[5]), destination="tmp2/", orientation=img[6], verb=verb, pretend=True)
                    constDuration = 2
                    imgVids.append(renderStill(outfn,length=constDuration, destDir="tmp2/",verb=verb, pretend=True))

                drList = [constDuration] * len(imgVids)
                # muxPath='tmp2/muxl'
                # print( ffmpgConcat(imgVids, drList, muxPath=muxPath, verb=verb))
                concatVid(imgVids, drList, destDir="tmp2/" , verb=verb)

                # TODO: randomly select/deselct some sequences in vids
                cur.execute("SELECT * FROM Media WHERE Id IN ({}) and Type>=100 ".format(",".join(map(str, mediaList))) )
                vidList = cur.fetchall()



        finally:
            try:
                shutil.rmtree(dirpath)
            except OSError as exc:
                if exc.errno != 2:  # code 2 - no such file or directory
                    raise  # re-raise exception


def renderStill(filename, length=3, appendcmd=[], destDir="/tmp", verb=0, pretend=False):
    cmd = ffmpegHeader(overwrite=True) + ffmpgCmdStill(filename,length=length)

    outfilen = os.path.abspath(os.path.join(destDir, os.path.basename(os.path.splitext(filename)[0]) + '.mp4'))
    cmd.append(outfilen)
    if verb>0:
        print(cmd)

    ret = 0
    if not pretend:
        ret = subprocess.call(cmd) # TODO pipe stdout to log
    if ret:
        print("ERROR ffmpeg")
        raise
    return outfilen

    # TODO check if exists

def concatVid(filenList, durList, destDir = "/tmp", outfname='AUTO_PYSOME__.mp4',verb=0, pretend=False):
    cmd = ffmpegHeader() + ffmpgConcat(filenList, durList, os.path.join(destDir,outfname+'.meta'))
    cmd.append(os.path.join(destDir,outfname))
    if verb>0:
        print (cmd)

    ret = 0
    if not pretend:
        ret = subprocess.call(cmd) # TODO pipe stdout to log
    if ret:
        print("ERROR ffmpeg")
        raise
    return outfname


def ffmpegHeader(overwrite=False):
    if overwrite:
        return ["ffmpeg", "-y"]
    else:
        return ["ffmpeg"]

def ffmpgCmdStill(filename, length=1,verb=0):
    # ffmpeg -y -loop 1 -i <inp> -f lavfi -i aevalsrc="0|0:c=2" -t 3 -shortest -s 768x432 -aspect 16:9 -vcodec libx264 -c:a aac -strict -2 out.mp4
    return ['-loop', '1', '-i', '{}'.format(filename),  '-f',  'lavfi', '-i', 'aevalsrc=0|0:c=2', '-t', '{}'.format(length), '-shortest', '-s', '768x432', '-aspect', '16:9', '-vcodec', 'libx264', '-c:a','aac', '-strict', '-2']

def ffmpgAudio(filename, verb=0):
    return " -i {} -strict -2".format(filename)

def ffmpgConcat(filenList, durList, muxPath='/tmp/muxl', verb=0):
    # file test169.mp4
    # duration 3
    #return "ffmpeg -f concat -i muxlist -codec copy outputDouple_wSound.mp4"
    if len(filenList) != len(durList):
        print("Error concat")
        raise
    print(filenList)
    print(durList)
    with open(muxPath, 'w') as f:
        for filen, length in zip(filenList, durList):
            print("file " + filen, file=f)
            print("duration " + str(length), file=f)

    return ['-f', 'concat', '-i', muxPath, '-codec', 'copy' ]



def resizeShave(filename, resolution, destination='/tmp', xres=768, shave=True, orientation=1, verb=0, pretend=False):
    targetYres = xres*9/16

    if not resolution:
        print("ERROR: NOT implemented")
        raise
    else:
        # convert accepts floating point parameter to `-shave` option. seems fine
        if orientation == 1:
            cropy = (xres/resolution[0]*resolution[1] - targetYres)/2
        elif orientation == 6: # right top
            cropy = (xres/resolution[1]*resolution[0] - targetYres)/2
        elif orientation == 8: # left bottom
            # TODO check
            cropy = (xres/resolution[1]*resolution[0] - targetYres)/2
        else:
            print("ERROR: orientation not handled yet")
            raise
    cmd = ["convert", "-regard-warnings", filename]
    # special case for old images which stored portrait photos in x,y format, with x<y
    if resolution[0] < resolution[1]:
        print("WARNING: not auto orientating picture '{}'".format(filename))
    else:
        cmd.append("-auto-orient")

    cmd = cmd + ['-resize', str(xres)]

    if shave:
        cmd = cmd + ['-shave', "0x{}".format(cropy)]

    outfilen = os.path.abspath(os.path.join(destination, os.path.basename(filename)))
    # TODO check if present

    cmd.append(outfilen)
    if verb>0:
        print(cmd)

    ret = 0
    if not pretend:
        ret = subprocess.call(cmd)
    if ret:
        print("ERROR convert")
        raise
    return outfilen




def numint(s):
    try:
        return int(s)
    except ValueError:
        print("Value {0} is not an integer".format(s))

def parseArgs():
    parser = argparse.ArgumentParser(description="Create randomized clips from your image and video collection")
    parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")

    # database options
    parser.add_argument('-c', '--dbcreate', help="create database", action="store_true")
    parser.add_argument('-f', '--dbfile', help="specify database file")
    parser.add_argument('-p', '--path', help="specify media path")
    parser.add_argument('-s', '--dbshow', help="show summary of database", action="store_true")

    # clustering options
    parser.add_argument('-cc', '--cluster', help="perform clustering of database", action="store_true")
    parser.add_argument('-sq', '--sqlLike', help="match filenames in database from a given sql like expression, e.g. --sqlLike=%tmp_[asdf][0-9]% " )
    parser.add_argument('-d', '--day', help="match a particular day (YYYY-MM-DD format)" )
    parser.add_argument('-dd', '--delta', help="return entities within range DELTA days of DAY (see -d option). If there is no -d option, today is assumed." )
    parser.add_argument('-pf', '--printfn', help="print filenames to stdout" )

    # creation options
    parser.add_argument('-x', '--xtest', help="asldkfjaskldfjl", action="store_true") #TODO

    args = parser.parse_args()

    if args.dbcreate:
        path, mediaPath = getPaths(args)
        
        mydb = db(path=path, mediaPath=mediaPath)
        mydb.create(verb=args.verbose)

    elif args.dbshow:
        path, mediaPath = getPaths(args)

        if os.path.isfile(dbpath): 
            if os.path.getsize(dbpath) > 0:
                mydb = db(path=dbpath)
                mydb.check(verb=args.verbose)

                sys.exit(0)

        print("ERROR: {} is not a valid file".format(dbpath))

    elif args.cluster:
        path, mediaPath = getPaths(args)
        if os.path.isfile(path): 
            if os.path.getsize(path) > 0:
                mydb = db(path=path)
                mList =  mydb.querydb(pattern=args.sqlLike, day=args.day, deltaDays=args.delta, verb=args.verbose)

                if mList:
                    if args.xtest:
                        mydb.generateNaive(mList, verb=args.verbose)
                    else:
                        for idm in mList:
                            print(idm)
                else:
                    print("No matches found for this date")
                    sys.exit(1)
                sys.exit(0)
    elif args.xtest:
        path, mediaPath = getPaths(args)
        if os.path.isfile(path): 
            if os.path.getsize(path) > 0:
                mydb = db(path=path)
                #TODO
                #mydb.generateNaive([stdin], verb=args.verbose)

    else:
        print(parser.format_help())

def getPaths(args):
    dbpath = "my-test.sqlite"
    mediaPath=TMP_MEDIA_PATH
    
    if args.dbfile:
        dbpath = args.dbfile
    if args.path:
        mediaPath=args.path
    return dbpath, mediaPath



if __name__ == "__main__":

    parseArgs()
