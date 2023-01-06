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

import inspect
import json
import os
import re
import sys

import six.moves.urllib.parse as six
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

if sys.version_info.major == 2:
    inspect.getfullargspec = inspect.getargspec
    xbmcvfs.translatePath = xbmc.translatePath


class Dialog(xbmcgui.Dialog):
    def multiselecttab(self, heading, options):
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
    def __new__(cls, label='', label2='', iconImage='', thumbnailImage='', posterImage='', path='', offscreen=False):
        return super(ListItem, cls).__new__(cls, label, label2, path=path, offscreen=offscreen)

    def __init__(self, label='', label2='', iconImage='', thumbnailImage='', posterImage='', path='', offscreen=False):
        self.setArt({'thumb': thumbnailImage, 'poster': posterImage, 'icon': iconImage})

    def setArt(self, values):
        super(ListItem, self).setArt({label: value for label, value in values.items() if value})


class NotFoundException(Exception):
    pass


class Plugin(object):
    def __init__(self, handle=None, url=None):
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
        xbmc.log('[script.module.xbmcext] Routing "{}"'.format(self.getFullPath()), xbmc.LOGINFO)

        for pattern, classtypes, function in self.routes:
            match = re.match('^{}$'.format(pattern), self.path)

            if match:
                kwargs = match.groupdict()

                for name, classtype in classtypes.items():
                    kwargs[name] = classtype(kwargs[name])

                kwargs.update(self.query)
                argspec = inspect.getfullargspec(function)

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

    def addSortMethods(self, sortMethods=None):
        if sortMethods:
            for sortMethod in sortMethods:
                xbmcplugin.addSortMethod(self.handle, sortMethod)

    def getFullPath(self):
        return six.urlunsplit(('', '', self.path, six.urlencode({name: json.dumps(value) for name, value in self.query.items()}), ''))

    def getUrlFor(self, path, **query):
        return six.urlunsplit((self.scheme, self.netloc, path, six.urlencode({name: json.dumps(value) for name, value in query.items()}), ''))

    def redirect(self, path, **query):
        path = path.rstrip('/')
        self.path = path if path else '/'
        self.query = query
        self()

    def route(self, path):
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

    def setDirectoryItems(self, items):
        xbmcplugin.addDirectoryItems(self.handle, items)
        xbmcplugin.endOfDirectory(self.handle)

    def setContent(self, content):
        xbmcplugin.setContent(self.handle, content)

    def setResolvedUrl(self, succeeded, listitem):
        xbmcplugin.setResolvedUrl(self.handle, succeeded, listitem)


def getPath():
    return xbmcvfs.translatePath(getAddonInfo('path'))


def getProfilePath():
    return xbmcvfs.translatePath(getAddonInfo('profile'))


getAddonInfo = xbmcaddon.Addon().getAddonInfo
getLocalizedString = xbmcaddon.Addon().getLocalizedString
getSettingString = xbmcaddon.Addon().getSettingString
