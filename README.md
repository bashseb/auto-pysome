auto-pysome
===========

A non-cloud clone of Googles *auto awesome videos* to create videos in a similar fashion on your local files

I'm starting to really like the auto awsome videos my mobile phone sometimes spits out. It combines photos and videos taken recently into a short clip with underlying music. The choice of music, pictures and video sequences appears to be rather random. Possibly blurry images/ similar images are descared. I would like to do something similar to the huge collection of videos and photos I have already stored on my computer. 


This program can be used in two modi:

 A. Actions on the database:
 
    * Create database: `auto-pysome.py --db-create [PATH] `
    * Update database: `auto-pysome.py --db-update sqlite-db-file`
    * Reset database:  `auto-pysome.py --db-reset  sqlite-db-file`
    * Show database: `auto-pysome.py --dbinfo sqlite-db-file`
    
 B. Clustering 
 
    * Cluster database: `auto-pysome.py --clustering --dbfile <sqlite-db-file> [--name=<name>] [OPTIONS] `
    * Obtain info/statistics on clusters (also presented at the end of `--clustering`):  `auto-pysome.py --cluster-info [--name=<name>]`
    
  C. Create a video from a cluster
 
    * Create a new random clip from cluster items: `auto-pysome.py --create [--length=60s] [--audio=external (default)|internal] [<cluster-id(s)]`
    * View cluster material: `auto-pysome.py --review <cluster-no>`. Interactive control lets you select or deselect items, and create project.
    * Edit cluster sequence (invokes GUI): `auto-pysome.py --edit-cluster <cluster-id> [project-id]`.
    * Set cluster background audio: `auto-pysome.py --bg-audio=<path-to-audio-file>`
    
    
    
 
 


#### Recall from Google

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
5. present statistics of the clusters
6. Default setting for a auto-pysome video is 1 minute length and 10 photos.

##### Tools used

* sqlite database
* python script (GUI undecided ... TODO later: required to display sliders)
* ffmpeg to split videos
* video effects?
* music files (to be provided by user in a specified location)
* `mplayer` for preview.

