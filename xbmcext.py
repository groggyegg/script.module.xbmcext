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

import os

import xbmcgui


class Dialog(xbmcgui.Dialog):
    def multiselecttab(self, heading, options):
        ACTION_MOVE_UP = 3
        ACTION_MOVE_DOWN = 4
        ACTION_PREVIOUS_MENU = 10
        ACTION_STOP = 13
        ACTION_NAV_BACK = 92

        selectedItems = {key: [] for key in options.keys()}

        class MultiSelectTabDialog(xbmcgui.WindowXMLDialog):
            def __new__(cls, *args, **kwargs):
                return super().__new__(cls, 'MultiSelectTabDialog.xml', os.path.dirname(__file__), defaultRes='1080i')

            def __init__(self):
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
                        control.getSelectedItem().setLabel('[COLOR orange]{}[/COLOR]'.format(selectedItemLabel))
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
                        self.getControl(1120).addItems(['[COLOR orange]{}[/COLOR]'.format(item) if item in selectedItems[self.selectedLabel] else item
                                                        for item in options[self.selectedLabel]])

        MultiSelectTabDialog().doModal()
        return selectedItems if selectedItems else None
