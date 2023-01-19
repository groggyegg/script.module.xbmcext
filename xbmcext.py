"""
MIT License

Copyright (c) 2022 groggyegg

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import enum
import inspect
import json
import os
import re
import sys

import six.moves.urllib.parse as six
import typing
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

if sys.version_info.major == 2:
    inspect.getfullargspec = inspect.getargspec
    xbmcvfs.translatePath = xbmc.translatePath


class Dialog(xbmcgui.Dialog):
    """
    The graphical control element dialog box (also called dialogue box or just dialog) is a small window that communicates information to the user and prompts
    them for a response.
    """

    def multiselecttab(self, heading, options):
        """
        Show a multi-select tab dialog.

        :param heading: Dialog heading.
        :type heading: str
        :param options: Options to choose from.
        :type options: dict[str, list[str]]
        :return: Returns the selected items, or None if cancelled.
        :rtype: dict[str, list[str]] | None
        """
        DIALOG_TITLE = 1100
        DIALOG_CONTENT = 1110
        DIALOG_SUBCONTENT = 1120
        DIALOG_OK_BUTTON = 1131
        DIALOG_CLEAR_BUTTON = 1132

        selectedItems = {key: [] for key in options.keys()}

        class MultiSelectTabDialog(xbmcgui.WindowXMLDialog):
            def __init__(self, xmlFilename, scriptPath, defaultSkin='Default', defaultRes='720p', isMedia=False):
                super(MultiSelectTabDialog, self).__init__(xmlFilename, scriptPath, defaultSkin, defaultRes, isMedia)
                self.selectedLabel = None

            def onInit(self):
                self.getControl(DIALOG_TITLE).setLabel(heading)
                self.getControl(DIALOG_CONTENT).addItems(list(options.keys()))
                self.setFocusId(DIALOG_CONTENT)

            def onAction(self, action):
                if action.getId() in (xbmcgui.ACTION_PREVIOUS_MENU, xbmcgui.ACTION_STOP, xbmcgui.ACTION_NAV_BACK):
                    selectedItems.clear()
                    self.close()
                elif action.getId() in (xbmcgui.ACTION_MOVE_UP, xbmcgui.ACTION_MOVE_DOWN):
                    self.onSelectedItemChanged(self.getFocusId())

            def onClick(self, controlId):
                if controlId == DIALOG_SUBCONTENT:
                    control = self.getControl(controlId)
                    selectedItemLabel = options[self.selectedLabel][control.getSelectedPosition()]

                    if selectedItemLabel in selectedItems[self.selectedLabel]:
                        control.getSelectedItem().setLabel(selectedItemLabel)
                        selectedItems[self.selectedLabel].remove(selectedItemLabel)
                    else:
                        selectedItems[self.selectedLabel].append(selectedItemLabel)
                        control.getSelectedItem().setLabel('[COLOR orange]{}[/COLOR]'.format(selectedItemLabel))
                elif controlId == DIALOG_OK_BUTTON:
                    self.close()
                elif controlId == DIALOG_CLEAR_BUTTON:
                    for item in selectedItems.values():
                        item.clear()

                    for index in range(len(options[self.selectedLabel])):
                        self.getControl(DIALOG_SUBCONTENT).getListItem(index).setLabel(options[self.selectedLabel][index])

            def onFocus(self, controlId):
                self.onSelectedItemChanged(controlId)

            def onSelectedItemChanged(self, controlId):
                if controlId == DIALOG_CONTENT:
                    selectedLabel = self.getControl(controlId).getSelectedItem().getLabel()

                    if self.selectedLabel != selectedLabel:
                        self.selectedLabel = selectedLabel
                        self.getControl(DIALOG_SUBCONTENT).reset()
                        self.getControl(DIALOG_SUBCONTENT).addItems(['[COLOR orange]{}[/COLOR]'.format(item) if item in selectedItems[self.selectedLabel]
                                                                     else item for item in options[self.selectedLabel]])

        dialog = MultiSelectTabDialog('MultiSelectTabDialog.xml', os.path.dirname(os.path.dirname(__file__)), defaultRes='1080i')
        dialog.doModal()
        del dialog
        return selectedItems if selectedItems else None


class ListItem(xbmcgui.ListItem):
    def __new__(cls, label='', label2='', iconImage='', thumbnailImage='', posterImage='', path='', offscreen=True):
        """
        The list item control is used for creating item lists in Kodi.

        :param label: The label to display on the item.
        :type label: str
        :param label2: The label2 of the item.
        :type label2: str
        :param iconImage: Image filename.
        :type iconImage: str
        :param thumbnailImage: Image filename.
        :type thumbnailImage: str
        :param posterImage: Image filename.
        :type posterImage: str
        :param path: The path for the item.
        :type path: str
        :param offscreen: If GUI based locks should be avoided. Most of the times listitems are created offscreen and added later to a container for display (e.g. plugins) or they are not even displayed (e.g. python scrapers). In such cases, there is no need to lock the GUI when creating the items (increasing your addon performance).
        :type offscreen: bool
        """
        return super(ListItem, cls).__new__(cls, label, label2, path=path, offscreen=offscreen)

    def __init__(self, label='', label2='', iconImage='', thumbnailImage='', posterImage='', path='', offscreen=True):
        """
        The list item control is used for creating item lists in Kodi.

        :param label: The label to display on the item.
        :type label: str
        :param label2: The label2 of the item.
        :type label2: str
        :param iconImage: Image filename.
        :type iconImage: str
        :param thumbnailImage: Image filename.
        :type thumbnailImage: str
        :param posterImage: Image filename.
        :type posterImage: str
        :param path: The path for the item.
        :type path: str
        :param offscreen: If GUI based locks should be avoided. Most of the times listitems are created offscreen and added later to a container for display (e.g. plugins) or they are not even displayed (e.g. python scrapers). In such cases, there is no need to lock the GUI when creating the items (increasing your addon performance).
        :type offscreen: bool
        """
        self.setArt({label: value for label, value in (('thumb', thumbnailImage), ('poster', posterImage), ('icon', iconImage)) if value})


class Log(object):
    """
    Write a string to Kodi's log file and the debug window.
    """

    @staticmethod
    def debug(msg):
        """
        In depth information about the status of Kodi. This information can pretty much only be deciphered by a developer or long time Kodi power user.

        :param msg: Text to output.
        :type msg: str
        """
        xbmc.log(msg, xbmc.LOGDEBUG)

    @staticmethod
    def error(msg):
        """
        This event is bad. Something has failed. You likely noticed problems with the application be it skin artifacts, failure of playback a crash, etc.

        :param msg: Text to output.
        :type msg: str
        """
        xbmc.log(msg, xbmc.LOGERROR)

    @staticmethod
    def fatal(msg):
        """
        We're screwed. Kodi is about to crash.

        :param msg: Text to output.
        :type msg: str
        """
        xbmc.log(msg, xbmc.LOGFATAL)

    @staticmethod
    def info(msg):
        """
        Something has happened. It's not a problem, we just thought you might want to know. Fairly excessive output that most people won't care about.

        :param msg: Text to output.
        :type msg: str
        """
        xbmc.log(msg, xbmc.LOGINFO)

    @staticmethod
    def warning(msg):
        """
        Something potentially bad has happened. If Kodi did something you didn't expect, this is probably why. Watch for errors to follow.

        :param msg: Text to output.
        :type msg: str
        """
        xbmc.log(msg, xbmc.LOGWARNING)


class NotFoundException(Exception):
    """
    Throws an exception when a resource is not found.
    """


class Plugin(object):
    def __init__(self, handle=None, url=None):
        """
        This class is responsible for matching incoming request and dispatch those request to the plugins endpoints.

        :param handle: Handle the plugin was started with.
        :type handle: int | None
        :param url: URL of the entry.
        :type url: str | None
        """
        self.classtypes = {
            'bool': bool,
            'float': float,
            'int': int,
            'str': str
        }
        self.functions = {
            're': lambda pattern: pattern
        }
        self.handle = int(sys.argv[1]) if handle is None else handle
        self.routes = []
        self.scheme, self.netloc, path, params, query, fragment = six.urlparse(sys.argv[0] + sys.argv[2] if url is None else url)
        path = path.rstrip('/')
        self.path = path if path else '/'
        self.query = {name: json.loads(value) for name, value in six.parse_qsl(query)}

    def __call__(self):
        """
        Handles incoming request and dispatch to the endpoint.
        """
        Log.info('[script.module.xbmcext] Routing "{}"'.format(self.getFullPath()))

        for pattern, classtypes, function in self.routes:
            match = re.match('^{}$'.format(pattern), self.path)

            if match:
                kwargs = match.groupdict()

                for name, classtype in classtypes.items():
                    kwargs[name] = classtype(kwargs[name])

                kwargs.update(self.query)
                argspec = inspect.getfullargspec(function)

                if set(kwargs) == set(argspec.args):
                    Log.info('[script.module.xbmcext] Calling "{}"'.format(function.__name__))
                    function(**kwargs)
                    return

        raise NotFoundException('A route could not be found in the route collection.')

    def addDirectoryItems(self, items):
        """
        Callback function to pass directory contents back to Kodi as a list.

        :param items: List of (url, listitem, isFolder) as a tuple to add.
        :type items: list[(str, ListItem, bool)]
        """
        xbmcplugin.addDirectoryItems(self.handle, items, len(items))

    def addSortMethods(self, *sortMethods):
        """
        Adds sorting methods for the media list.

        :param sortMethods: The sorting methods.
        :type sortMethods: SortMethod
        """
        for sortMethod in sortMethods:
            xbmcplugin.addSortMethod(self.handle, sortMethod)

    def endOfDirectory(self, succeeded=True, updateListing=False, cacheToDisc=True):
        """
        Callback function to tell Kodi that the end of the directory listing in a virtualPythonFolder module is reached.

        :param succeeded: True if script completed successfully; otherwise False.
        :type succeeded: bool
        :param updateListing: True if this folder should update the current listing; otherwise False.
        :type updateListing: bool
        :param cacheToDisc: True if folder will cache if extended time; otherwise False.
        :type cacheToDisc: bool
        """
        xbmcplugin.endOfDirectory(self.handle, succeeded, updateListing, cacheToDisc)

    def getFullPath(self):
        """
        Returns a relative URL.

        :return: A relative URL.
        :rtype: str
        """
        return six.urlunsplit(('', '', self.path, six.urlencode(self.query), ''))

    def getSerializedFullPath(self):
        """
        Returns a relative URL.

        :return: A relative URL.
        :rtype: str
        """
        return six.urlunsplit(('', '', self.path, six.urlencode({name: json.dumps(value) for name, value in self.query.items()}), ''))

    def getSerializedUrlFor(self, path, **query):
        """
        Returns an absolute URL.

        :param path: The path for combining into a complete URL. Accepts any query found in path.
        :type path: str
        :param query: The query for serialization and combining into a complete URL.
        :type query: Any
        :return: An absolute URL.
        :rtype: str
        """
        scheme, netloc, path, params, querystring, fragment = six.urlparse(path)
        query.update(six.parse_qsl(querystring))
        return six.urlunsplit((self.scheme, self.netloc, path, six.urlencode({name: json.dumps(value) for name, value in query.items()}), ''))

    def redirect(self, path, **query):
        """
        Redirects to a new path.

        :param path: The target path.
        :type path: str
        :param query: The HTTP query.
        :type query: Any
        """
        path = path.rstrip('/')
        self.path = path if path else '/'
        self.query = query
        self()

    def route(self, path):
        """
        Adds a route that matches the specified pattern.

        :param path: The path pattern of the route.
        :type path: str
        :return: A decorator to the function.
        :rtype: typing.Callable
        """
        classtypes = {}
        path = path.rstrip('/')
        segments = (path if path else '/').split('/')
        path = []

        for segment in segments:
            match = re.match(r'^{(?:(\w+?)(?::(\w+?))?)?(?::(\w+?\(.+?\)))?}$', segment)

            if match:
                name, classtype, constraint = match.groups()
                constraint = eval(constraint.replace('\\', '\\\\'), self.functions) if constraint else '[^/]+'

                if name:
                    classtypes[name] = self.classtypes[classtype] if classtype else str
                    path.append('(?P<{}>{})'.format(name, constraint))
                else:
                    path.append(constraint)
            else:
                path.append(re.escape(segment))

        def decorator(function):
            self.routes.append(('/'.join(path), classtypes, function))
            return function

        return decorator

    def setContent(self, content):
        """
        Sets the plugins content. Available content strings

        - albums
        - artists
        - episodes
        - files
        - games
        - images
        - movies
        - musicvideos
        - songs
        - tvshows
        - videos

        :param content: Content type (e.g. movies).
        :type content: str
        """
        xbmcplugin.setContent(self.handle, content)

    def setResolvedUrl(self, succeeded, listitem):
        """
        Callback function to tell Kodi that the file plugin has been resolved to a url.

        :param succeeded: True if script completed successfully; otherwise False.
        :type succeeded: bool
        :param listitem: Item the file plugin resolved to for playback.
        :type listitem: ListItem
        """
        xbmcplugin.setResolvedUrl(self.handle, succeeded, listitem)


class SortMethod(enum.IntEnum):
    """
    Sorting methods for the media list.

    :var ALBUM: Sort by the album.
    :var ALBUM_IGNORE_THE: Sort by the album and ignore "The" before.
    :var ARTIST: Sort by the artist.
    :var ARTIST_IGNORE_THE: Sort by the artist and ignore "The" before.
    :var BITRATE: Sort by the bitrate.
    :var CHANNEL: Sort by the channel.
    :var COUNTRY: Sort by the country.
    :var DATE: Sort by the date.
    :var DATEADDED: Sort by the added date.
    :var DATE_TAKEN: Sort by the taken date.
    :var DRIVE_TYPE: Sort by the drive type.
    :var DURATION: Sort by the duration.
    :var EPISODE: Sort by the episode.
    :var FILE: Sort by the file.
    :var FULLPATH: Sort by the full path name.
    :var GENRE: Sort by the genre.
    :var LABEL: Sort by label.
    :var LABEL_IGNORE_FOLDERS: Sort by the label names and ignore related folder names.
    :var LABEL_IGNORE_THE: Sort by the label and ignore "The" before.
    :var LASTPLAYED: Sort by last played date.
    :var LISTENERS: Sort by the listeners.
    :var MPAA_RATING: Sort by the mpaa rating.
    :var NONE: Do not sort.
    :var PLAYCOUNT: Sort by the play count.
    :var PLAYLIST_ORDER: Sort by the playlist order.
    :var PRODUCTIONCODE: Sort by the production code.
    :var PROGRAM_COUNT: Sort by the program count.
    :var SIZE: Sort by the size.
    :var SONG_RATING: Sort by the song rating.
    :var SONG_USER_RATING: Sort by the rating of the user of song.
    :var STUDIO: Sort by the studio.
    :var STUDIO_IGNORE_THE: Sort by the studio and ignore "The" before.
    :var TITLE: Sort by the title.
    :var TITLE_IGNORE_THE: Sort by the title and ignore "The" before.
    :var TRACKNUM: Sort by the track number.
    :var UNSORTED: Use list not sorted.
    :var VIDEO_RATING: Sort by the video rating.
    :var VIDEO_RUNTIME: Sort by video runtime.
    :var VIDEO_SORT_TITLE: Sort by the video sort title.
    :var VIDEO_SORT_TITLE_IGNORE_THE: Sort by the video sort title and ignore "The" before.
    :var VIDEO_TITLE: Sort by the video title.
    :var VIDEO_USER_RATING: Sort by the rating of the user of video.
    :var VIDEO_YEAR: Sort by the year.
    """
    ALBUM = xbmcplugin.SORT_METHOD_ALBUM
    ALBUM_IGNORE_THE = xbmcplugin.SORT_METHOD_ALBUM_IGNORE_THE
    ARTIST = xbmcplugin.SORT_METHOD_ARTIST
    ARTIST_IGNORE_THE = xbmcplugin.SORT_METHOD_ARTIST_IGNORE_THE
    BITRATE = xbmcplugin.SORT_METHOD_BITRATE
    CHANNEL = xbmcplugin.SORT_METHOD_CHANNEL
    COUNTRY = xbmcplugin.SORT_METHOD_COUNTRY
    DATE = xbmcplugin.SORT_METHOD_DATE
    DATEADDED = xbmcplugin.SORT_METHOD_DATEADDED
    DATE_TAKEN = xbmcplugin.SORT_METHOD_DATE_TAKEN
    DRIVE_TYPE = xbmcplugin.SORT_METHOD_DRIVE_TYPE
    DURATION = xbmcplugin.SORT_METHOD_DURATION
    EPISODE = xbmcplugin.SORT_METHOD_EPISODE
    FILE = xbmcplugin.SORT_METHOD_FILE
    FULLPATH = xbmcplugin.SORT_METHOD_FULLPATH
    GENRE = xbmcplugin.SORT_METHOD_GENRE
    LABEL = xbmcplugin.SORT_METHOD_LABEL
    LABEL_IGNORE_FOLDERS = xbmcplugin.SORT_METHOD_LABEL_IGNORE_FOLDERS
    LABEL_IGNORE_THE = xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE
    LASTPLAYED = xbmcplugin.SORT_METHOD_LASTPLAYED
    LISTENERS = xbmcplugin.SORT_METHOD_LISTENERS
    MPAA_RATING = xbmcplugin.SORT_METHOD_MPAA_RATING
    NONE = xbmcplugin.SORT_METHOD_NONE
    PLAYCOUNT = xbmcplugin.SORT_METHOD_PLAYCOUNT
    PLAYLIST_ORDER = xbmcplugin.SORT_METHOD_PLAYLIST_ORDER
    PRODUCTIONCODE = xbmcplugin.SORT_METHOD_PRODUCTIONCODE
    PROGRAM_COUNT = xbmcplugin.SORT_METHOD_PROGRAM_COUNT
    SIZE = xbmcplugin.SORT_METHOD_SIZE
    SONG_RATING = xbmcplugin.SORT_METHOD_SONG_RATING
    SONG_USER_RATING = xbmcplugin.SORT_METHOD_SONG_USER_RATING
    STUDIO = xbmcplugin.SORT_METHOD_STUDIO
    STUDIO_IGNORE_THE = xbmcplugin.SORT_METHOD_STUDIO_IGNORE_THE
    TITLE = xbmcplugin.SORT_METHOD_TITLE
    TITLE_IGNORE_THE = xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE
    TRACKNUM = xbmcplugin.SORT_METHOD_TRACKNUM
    UNSORTED = xbmcplugin.SORT_METHOD_UNSORTED
    VIDEO_RATING = xbmcplugin.SORT_METHOD_VIDEO_RATING
    VIDEO_RUNTIME = xbmcplugin.SORT_METHOD_VIDEO_RUNTIME
    VIDEO_SORT_TITLE = xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE
    VIDEO_SORT_TITLE_IGNORE_THE = xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE_IGNORE_THE
    VIDEO_TITLE = xbmcplugin.SORT_METHOD_VIDEO_TITLE
    VIDEO_USER_RATING = xbmcplugin.SORT_METHOD_VIDEO_USER_RATING
    VIDEO_YEAR = xbmcplugin.SORT_METHOD_VIDEO_YEAR


def getAddonId():
    """
    Returns the addon id.

    :return: Addon id.
    :rtype: str
    """
    return Addon.getAddonInfo('id')


def getAddonPath():
    """
    Returns the addon path.

    :return: Addon path.
    :rtype: str
    """
    return xbmcvfs.translatePath(Addon.getAddonInfo('path'))


def getAddonProfilePath():
    """
    Returns the addon profile path.

    :return: Addon profile path.
    :rtype: str
    """
    return xbmcvfs.translatePath(Addon.getAddonInfo('profile'))


Addon = xbmcaddon.Addon()
Keyboard = xbmc.Keyboard
executebuiltin = xbmc.executebuiltin
getLocalizedString = Addon.getLocalizedString
getSettingString = Addon.getSettingString
sleep = xbmc.sleep
