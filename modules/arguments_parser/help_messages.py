"""
This module defines some help messages constants
"""

PROGRAM_DESCRIPTION = '''
    This script helps you to download any user collections or even yours!
    You can:
      - Download someone's uploads / collections.
      - Filter any downloads (e.g. for skipping nswf/swf content).
      - Check for collections of particular user.
      - Use your api key for nsfw downloading and stuff.
'''

HELP_MSG_INFO = '''Defines a list of users you want to check
example:
-i user1 user2 user3...\n '''

HELP_MSG_COLLECTIONS = '''Defines a collection list (of particular) user you want 
to download, if no collections specified for username all will download.

if you want to download collections from different users
use the following syntax:

-c USERNAME1 collection1 collection2... -c USERNAME2...\n '''

HELP_MSG_UPLOADS = '''Defines a list of users which uploads you want to download
example:
-u username1 username2 username3\n '''

HELP_MSG_SYNC = '''[IN DEVELOPING]\n '''

HELP_MSG_VERBOSE = '''Show extra info about downloading progress
without this option you will only see which task is running now\n '''

HELP_MSG_PARALLEL = '''Count of simultaneous downloads (default = 1)
Beware too many downloads at a time, it could be less stable. (1-6 recommended)
'''