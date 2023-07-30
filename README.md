Wallhaven Downloader
--
Download all your favorite pictures effortlessly without any loss.

![](https://w.wallhaven.cc/full/eo/wallhaven-eom7ml.png)

**The script can:**
  - **Download** uploads/collections of wallhaven.cc users
  - **Download** pictures concurrently (several downloads at a time)
  - **Sort** images by directories (based on collection names).
  - **Delete** unfinished downloads if any error occurs
  - **Skip** pictures which you already have
  - **Collect** info about user's collections
  - Since python works everywhere - **it's cross-platform!**

-----
Usage
-----
The script has user-friendly console interface with many options
for any needs:

```commandline
Usage: main.py [options] --help for more info

    This script helps you to download your or any user's collections / uploads.

    Don't worry, if any error occurs during the download process
    then all corrupted/unfinished images will be deleted.

Options:
  -h, --help            show this help message and exit
  --info, -i username [username ...]
                        Specifies a list of users whose collections you want to view
                        example:
                        -i user1 user2 user3...

  --collections, -c  [ ...]
                        Username-collections list for downloading collections
                        if no collection specified for username all will be downloaded.
                        example:
                        -c USERNAME1 collection1 collection2... -c USERNAME2...

  --uploads, -u  [ ...]
                        List of usernames whose uploads you want to download
                        example:
                        -u username1 username2 username3

  --purity  [ ...]      Filter for purity, only specified purity will be downloaded
                        default: (sfw, sketchy, nsfw)

  --category  [ ...]    Filter for category, only specified category will be downloaded
                        default: (general, people, anime)

  --sync, -s            [IN DEVELOPING]

  --downloads_path, -d
                        Path where all downloads will be located
                        default: ./downloads

  --workers, -w count   Count of simultaneous downloads (default = 1)
                        Beware too many downloads at a time, it can be less stable. (1-6 recommended)

  --api_key, -a your_key
                        API key for accessing the Wallhaven API.
                        you can get it from https://wallhaven.cc/api/
                        Without it you won't be able to download certain wallpapers.

  --limit, -l           Count of requests per second (default = 1)
                        You can increase it to download more wallpapers at a time.
                        But it can be less stable and result TooManyRequestsError sometimes.
                        API is pretty strict about it, but sometimes increasing it may be efficient.
```
**All pictures will be located** in the "downloads" directory by default, 
which is created upon the first download task run.

------------
Requirements
------------
**To run the script you need** to install [python programming language](https://python.org)
in your system and run the following command in the main project directory:
```commandline
pip install -r requirements.txt
```
*This command will install all the necessary packages to run downloader.*


After all you can just run it with options you need, to see [all the
options](#usage) just use `-h` flag:
```commandline
python main.py -h 
```
