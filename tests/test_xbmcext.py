from parameterized import parameterized
from unittest import TestCase
from unittest.mock import Mock
from xbmcext import Plugin


class PluginTest(TestCase):
    @parameterized.expand([
        ('plugin://plugin.video.example/', None),
        ('plugin://plugin.video.example/title/tt5180504', 'tt5180504'),
        ('plugin://plugin.video.example/event/2023', '2023')
    ])
    def test_call(self, url, expected):
        mock = Mock()
        plugin = Plugin(0, url)

        @plugin.route('/')
        def home():
            mock(None)

        @plugin.route(r'/title/{id:re("tt\\d{7}")}')
        def title(id):
            mock(id)

        @plugin.route('/event/{id}')
        def event(id):
            mock(id)

        plugin()
        mock.assert_called_with(expected)

    def test_redirect(self):
        pass
