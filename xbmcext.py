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

import copy
import inspect
import json
import os
import re
import sys

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

if sys.version_info.major == 2:
    from urllib import urlencode
    from urlparse import parse_qsl, urlparse, urlunsplit
    from xbmc import translatePath
else:
    from urllib.parse import parse_qsl, urlencode, urlparse, urlunsplit
    from xbmcvfs import translatePath

__all__ = ['Dialog', 'ListItem', 'NotFoundException', 'Plugin', 'getLocalizedString', 'getPath', 'getProfilePath']


class Dialog(xbmcgui.Dialog):
    def multiselecttab(self, heading, options):
        ACTION_MOVE_UP = 3
        ACTION_MOVE_DOWN = 4
        ACTION_PREVIOUS_MENU = 10
        ACTION_STOP = 13
        ACTION_NAV_BACK = 92

        selectedItems = {key: [] for key in options.keys()}

        class MultiSelectTabDialog(xbmcgui.WindowXMLDialog):
            def __init__(self, xmlFilename, scriptPath, defaultSkin='Default', defaultRes='720p', isMedia=False):
                super(MultiSelectTabDialog, self).__init__(xmlFilename, scriptPath, defaultSkin, defaultRes, isMedia)
                self.selectedLabel = None

            def onInit(self):
                self.getControl(1100).setLabel(heading)
                self.getControl(1110).addItems(list(options.keys()))
                self.setFocusId(1110)

            def onAction(self, action):
                if action.getId() in (ACTION_PREVIOUS_MENU, ACTION_STOP, ACTION_NAV_BACK):
                    selectedItems.clear()
                    self.close()
                elif action.getId() in (ACTION_MOVE_UP, ACTION_MOVE_DOWN):
                    self.onSelectedItemChanged(self.getFocusId())

            def onControl(self, control):
                pass

            def onClick(self, controlId):
                if controlId == 1120:
                    control = self.getControl(controlId)
                    selectedItemLabel = options[self.selectedLabel][control.getSelectedPosition()]

                    if selectedItemLabel in selectedItems[self.selectedLabel]:
                        control.getSelectedItem().setLabel(selectedItemLabel)
                        selectedItems[self.selectedLabel].remove(selectedItemLabel)
                    else:
                        selectedItems[self.selectedLabel].append(selectedItemLabel)
                        control.getSelectedItem().setLabel('[COLOR orange]' + selectedItemLabel + '[/COLOR]')
                elif controlId == 1131:
                    self.close()
                elif controlId == 1132:
                    for item in selectedItems.values():
                        item.clear()

                    for index in range(len(options[self.selectedLabel])):
                        self.getControl(1120).getListItem(index).setLabel(options[self.selectedLabel][index])

            def onFocus(self, controlId):
                self.onSelectedItemChanged(controlId)

            def onSelectedItemChanged(self, controlId):
                if controlId == 1110:
                    selectedLabel = self.getControl(controlId).getSelectedItem().getLabel()

                    if self.selectedLabel != selectedLabel:
                        self.selectedLabel = selectedLabel
                        self.getControl(1120).reset()
                        self.getControl(1120).addItems(['[COLOR orange]' + item + '[/COLOR]' if item in selectedItems[self.selectedLabel] else item
                                                        for item in options[self.selectedLabel]])

        MultiSelectTabDialog('MultiSelectTabDialog.xml', os.path.dirname(os.path.dirname(__file__)), defaultRes='1080i').doModal()
        return selectedItems if selectedItems else None


class ListItem(xbmcgui.ListItem):
    def __new__(cls, label='', label2='', iconImage='', thumbnailImage='', posterImage='', path='', offscreen=True):
        if isinstance(label, int):
            label = getLocalizedString(label)

        if isinstance(label2, int):
            label2 = getLocalizedString(label2)

        return super(ListItem, cls).__new__(cls, label, label2, path=path, offscreen=offscreen)

    def __init__(self, label='', label2='', iconImage='', thumbnailImage='', posterImage='', path='', offscreen=True):
        super(ListItem, self).setArt({'thumb': thumbnailImage, 'poster': posterImage, 'icon': iconImage})

    def addContextMenuItems(self, items, replaceItems=False):
        super(ListItem, self).addContextMenuItems([(getLocalizedString(label) if isinstance(label, int) else label, action) for label, action in items], replaceItems)

    def setArt(self, values):
        if isinstance(values, str):
            super(ListItem, self).setArt({'thumb': values,
                                          'poster': values,
                                          'banner': values,
                                          'fanart': values,
                                          'clearart': values,
                                          'clearlogo': values,
                                          'landscape': values,
                                          'icon': values})
        else:
            super(ListItem, self).setArt(values)


class NotFoundException(Exception):
    pass


class Plugin(object):
    def __init__(self):
        def cast(value):
            try:
                value = float(value)
                return int(value) if value == int(value) else value
            except ValueError:
                pass

            if value == str(True):
                return True

            if value == str(False):
                return False

            try:
                return json.loads(value)
            except ValueError:
                pass

            return value

        self.classtypes = {
            'bool': bool,
            'float': float,
            'int': int,
            'str': str
        }

        self.functions = {
            're': lambda pattern: pattern
        }

        self.handle = int(sys.argv[1])
        self.routes = []
        self.scheme, self.netloc, path, params, query, fragment = urlparse(sys.argv[0] + sys.argv[2])
        path = path.rstrip('/')
        self.path = path if path else '/'
        self.query = dict((name, cast(value)) for name, value in parse_qsl(query))

    def __call__(self):
        xbmc.log('Routing "' + self.getFullPath() + '"', xbmc.LOGINFO)

        for pattern, classtypes, function in self.routes:
            match = re.match('^' + pattern + '$', self.path)

            if match:
                kwargs = match.groupdict()

                for name, classtype in classtypes.items():
                    kwargs[name] = classtype(kwargs[name])

                kwargs.update(copy.deepcopy(self.query))
                argspec = inspect.getargspec(function)

                if argspec.defaults:
                    positional = set(argspec.args[:-len(argspec.defaults)])
                    keyword = set(argspec.args) - positional

                    if set(kwargs) - keyword == positional:
                        function(**kwargs)
                        return
                else:
                    if set(kwargs) == set(argspec.args):
                        function(**kwargs)
                        return

        raise NotFoundException('A route could not be found in the route collection.')

    def getFullPath(self):
        return urlunsplit(('', '', self.path, urlencode(dict((name, json.dumps(value) if isinstance(value, list) else value) for name, value in self.query.items())), ''))

    def getUrlFor(self, path, **query):
        return urlunsplit((self.scheme, self.netloc, path, urlencode(dict((name, json.dumps(value) if isinstance(value, list) else value) for name, value in query.items())), ''))

    def redirect(self, path, **query):
        path = path.rstrip('/')
        self.path = path if path else '/'
        self.query = query
        self()

    def route(self, path):
        classtypes = {}
        path = path.rstrip('/')
        segments = re.split('/', path if path else '/')
        path = []

        for segment in segments:
            match = re.match(r'^{(\w+?)(?::(\w+?))?(?::(\w+?\(.+?\)))?}$', segment)

            if match:
                name, classtype, constraint = match.groups()
                constraint = eval(constraint, self.functions) if constraint else '[^/]+'

                if name:
                    classtypes[name] = self.classtypes[classtype] if classtype else str
                    path.append('(?P<' + name + '>' + constraint + ')')
                else:
                    path.append(constraint)
            else:
                path.append(re.escape(segment))

        def decorator(function):
            self.routes.append(('/'.join(path), classtypes, function))
            return function

        return decorator

    def setDirectoryItems(self, items, content=None, sortMethods=[]):
        xbmcplugin.addDirectoryItems(self.handle, items)

        if content:
            xbmcplugin.setContent(self.handle, content)

        xbmcplugin.addSortMethod(self.handle, xbmcplugin.SORT_METHOD_UNSORTED)
        for sortMethod in sortMethods:
            xbmcplugin.addSortMethod(self.handle, sortMethod)

        xbmcplugin.endOfDirectory(self.handle)

    def setResolvedUrl(self, succeeded, listitem):
        xbmcplugin.setResolvedUrl(self.handle, succeeded, listitem)


def getPath():
    return translatePath(getAddonInfo('path'))


def getProfilePath():
    return translatePath(getAddonInfo('profile'))


getAddonInfo = xbmcaddon.Addon().getAddonInfo
getLocalizedString = xbmcaddon.Addon().getLocalizedString
getSettingString = xbmcaddon.Addon().getSettingString
