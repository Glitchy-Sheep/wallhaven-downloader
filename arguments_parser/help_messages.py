"""
This module defines some help messages constants
"""

# Please avoid to remove spaces in the end of help messages
# they make the formatting of the help more structured .

PROGRAM_DESCRIPTION = '''
    This script helps you to download your or any user's collections.
    You can:
      - Download someone's uploads / collections.
      - Filter any downloads (e.g. for skipping nsfw/sfw content).
      - Check for collections of particular user.'''

HELP_MSG_INFO = '''Specifies a list of users whose collections you want to view
example:
-i user1 user2 user3...\n\n'''

HELP_MSG_COLLECTIONS = '''Username-collections list for downloading collections
if no collection specified for username all will be downloaded.
example:
-c USERNAME1 collection1 collection2... -c USERNAME2...\n\n'''

HELP_MSG_UPLOADS = '''List of usernames whose uploads you want to download
example:
-u username1 username2 username3\n\n'''

HELP_MSG_SYNC = '''[IN DEVELOPING]\n\n'''

HELP_MSG_VERBOSE = '''Show extra info about downloading progress
without this option you will only see overall progress\n\n'''

HELP_MSG_THREADS = '''Count of simultaneous downloads (default = 1)
Beware too many downloads at a time, it can be less stable. (1-6 recommended)\n\n'''

HELP_MSG_PURITY = '''Filter for purity, only specified purity will be downloaded
default: (sfw, sketchy, nsfw)\n\n'''

HELP_MSG_CATEGORY = '''Filter for category, only specified category will be downloaded
default: (general, people, anime)\n\n'''
