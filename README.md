auto-pysome
===========

A non-cloud clone of Googles *auto awesome videos* to create videos in a similar fashion on your local files.

I'm starting to really like the auto awsome videos my mobile phone sometimes spits out. It combines photos and videos taken recently into a short clip with underlying music. The choice of music, pictures and video sequences appears to be rather random. I started this project to perform similar *memory compression* on my local files, without the need to do actual manual video editing. Minimal controls are exposed, making it simple and fun to edit videos.

Right now, I'm building on a stack of proven technologies available on every *Linux* system. I'd need help to provide a version for *MAC* or *Windows*.

This is a complete program, but only command line interface is provided. Feel free to fork/extend it.

## Status: early development

#### Dependencies

 * `sqlite3` to store meta info of files
 * `python2`, but syntax is compatible to python 3
 * `ffmpeg` to render and concatenate the clip. Eventually simple effects like sliding photos are going to be implemented using this or a different tool.
 * `convert` from *Imagemagick* to transform input images
 * `mplayer` to preview (also to `-identify`)

This program can be used in three modi:

A. Actions on the database:
 
  * Create database: `auto-pysome.py --dbcreate [-f database file] [-p media path to scan]`
  * **TODO** Update database: `auto-pysome.py --db-update sqlite-db-file`
  * Show database: `auto-pysome.py --dbshow [-f database file]`
    
B. Clustering 
 
 * Cluster database: `auto-pysome.py --cluster [-f database file]  [OPTIONS]`
   Outputs the database IDs of the matching elements to stdout.
      
    Usage example: 
     * `auto-pysome.py --cluster --regex='*prague*' > id-file`
     * `auto-pysome.py --cluster --day=2010-06-01 --deltadays=2 | gzip > id-file.tgz`
	
              
    OPTIONS:
     * `-r`, `--regex=`  match *filenames* in database with a regular expression
     * `-d`, `--day=` match a particular day (format is *YYYY-MM-DD*)
     * `-dd`, `--deltadays` when combined with `-d` returns all entries within +- that day. If not, `-d<today>` is assumed.
       
  * Obtain info/statistics on clusters: **TODO** `auto-pysome.py --cluster-info [--name=<name>]`
    
C. Create a video from a cluster
 
  * Create a new random clip from cluster items: `auto-pysome.py --create [--length=60s] [--audio=external (default)|internal] [<cluster-id(s)]`
    - `auto-pysome.py --create < 1 4 6 10`
    - `auto-pysome.py --create < $(zcat id-file.tgz)

  * View cluster material: `auto-pysome.py --review <cluster-no>`. Interactive control lets you select or deselect items, and create project.
  * Edit cluster sequence (invokes GUI): `auto-pysome.py --edit-cluster <cluster-id> [project-id]`.
  * Set cluster background audio: `auto-pysome.py --bg-audio=<path-to-audio-file>`
    

#### Recall from Google

Eventually, blurry images/,similar images are descared, faces are tracked and audio channel of video is analyzed. 
I would like to do something similar, but simpler, to the huge collection of videos and photos I have already stored on my computer. 


The photo app capable of doing these videos has minimal controls:

 * title
 * video length, 5s to 3m
 * video effect 
 * sound: include audio from video
 * select background audio.
 * edit sequence
    - presents a list of videos/photos used
    - videos/photos can be removed, or added and draged
    - videos sequence can be changed in length using sliders ("most difficult")


#### Architecture

1. Your files belong to you. This program runs on your own PC, using just your own local files.
2. Image and video files are scanned from a given folder and information on them is collected in a **sqlite** database.
3. Data collected
    * filename
    * date of creation (if available from file info, otherwise time stamp of the file itself)
    * if video: length, 
    * if it has been used already: `IS_USED_ALREADY` = ['projectA', 'projectB', ...]
    * flag `DO_NOT_USE`: for blurry images and videos too short (e.g < 3s)
    * ???
    * future: location
4. Run a time clustering algorithm to separate the stream of photos/videos into clusters.
   * Clustering by default is done by *folders*, since this is the most likely organizational unit. If files within the same date range of a folder are found in different folders, they are merged into the cluster. 
   * Alternative clustering methods is *nearest-date-neighbors* with a specified interval (in units of *days*).

5. present statistics of the clusters. 
6. preview content of cluster
6. Default setting for a auto-pysome video is 1 minute length and 10 photos.

##### Tools used

* sqlite database
* python script (GUI undecided ... TODO later: required to display sliders)
* ffmpeg to split videos
* video effects?
* music files (to be provided by user in a specified location)
* `mplayer` for preview.

