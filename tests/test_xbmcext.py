import unittest

import xbmcext


class PluginTest(unittest.TestCase):
    def test_classtype(self):
        plugin = xbmcext.Plugin(0, 'plugin://plugin.video.example/event/2023')

        @plugin.route('/event/{id:int}')
        def event(id):
            self.assertEqual(id, 2023)

        plugin()

    def test_constraint(self):
        plugin = xbmcext.Plugin(0, 'plugin://plugin.video.example/video/vi3337078041/')

        @plugin.route(r'/video/{:re("vi\d{10}")}')
        def video():
            pass

        plugin()

    def test_literal(self):
        plugin = xbmcext.Plugin(0, 'plugin://plugin.video.example/')

        @plugin.route('/')
        def home():
            pass

        plugin()

    def test_name(self):
        plugin = xbmcext.Plugin(0, 'plugin://plugin.video.example/title/tt5180504')

        @plugin.route(r'/title/{id:re("tt\d{7}")}')
        def title(id):
            self.assertEqual(id, 'tt5180504')

        plugin()

    def test_query(self):
        plugin = xbmcext.Plugin(0, 'plugin://plugin.video.example/video/search?q="Stranger"')

        @plugin.route('/video/search')
        def search(q):
            self.assertEqual(q, 'Stranger')

        plugin()

    def test_redirect(self):
        plugin = xbmcext.Plugin(0, 'plugin://plugin.video.example/')

        @plugin.route('/')
        def home():
            pass

        @plugin.route('/video/{videoId}')
        def video(videoId, listId):
            self.assertEqual(videoId, 'vi4275684633')
            self.assertEqual(listId, 53181649)

        plugin.redirect('/video/vi4275684633', listId=53181649)
