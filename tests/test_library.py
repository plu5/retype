import sys
from unittest.mock import patch, ANY
from PyQt5.Qt import QApplication

from retype.controllers.library import LibraryController, BookWrapper


class FakeBookWrapper:
    def __init__(self):
        self.save_data = None


class TestLibraryController:
    @patch('os.path.exists')
    @patch('builtins.open')
    @patch('json.load')
    @patch('json.dump')
    def test_save(self, m_jsondump, m_jsonload, m_open, m_exists):
        library = LibraryController(None)
        book = FakeBookWrapper()
        key = "hey"
        data = {"test": "data"}
        save = {"dummykey": {"test": "data"}}

        # Save file exists and has key
        m_exists.return_value = True
        m_jsonload.return_value = {key: data}
        library.save(book, key, data)
        m_jsonload.assert_called_once()
        m_jsondump.assert_called_once_with({key: data}, ANY,
                                           ensure_ascii=False, indent=2)
        assert book.save_data == {key: data}

        m_jsonload.reset_mock()
        m_jsondump.reset_mock()

        # Save file exists and does not have key
        m_exists.return_value = True
        m_jsonload.return_value = save
        library.save(book, key, data)
        m_jsonload.assert_called_once()
        new_save = save
        new_save[key] = data
        m_jsondump.assert_called_once_with(new_save, ANY,
                                           ensure_ascii=False, indent=2)
        assert book.save_data == {key: data}

        m_jsonload.reset_mock()
        m_jsondump.reset_mock()

        # Save file does not exist
        m_exists.return_value = False
        library.save(book, key, data)
        m_jsonload.assert_not_called()
        m_jsondump.assert_called_once_with({key: data}, ANY,
                                           ensure_ascii=False, indent=2)
        assert book.save_data == {key: data}

        m_jsonload.reset_mock()
        m_jsondump.reset_mock()

    @patch('os.path.exists')
    @patch('builtins.open')
    @patch('json.load')
    def test_load(self, m_jsonload, m_open, m_exists):
        library = LibraryController(None)
        key = "dummykey"
        data = {"test": "data"}
        save = {key: data}

        # Save file exists
        m_exists.return_value = True
        m_jsonload.return_value = save
        return_value = library.load(key)
        m_jsonload.assert_called_once()
        assert return_value == data

        m_jsonload.reset_mock()

        # Save file does not exist
        m_exists.return_value = False
        return_value = library.load(key)
        m_jsonload.assert_not_called()
        assert return_value is None

        m_jsonload.reset_mock()

        # Save file exists, key does not exist
        m_exists.return_value = True
        m_jsonload.return_value = save
        return_value = library.load("nonexistent-key")
        m_jsonload.assert_called_once()
        assert return_value is None


SAMPLE_CONTENT = b'<html><body>\
Hello. <a href="another-chapter">Here is a link to another chapter.</a>\
</body></html>'

SAMPLE_CONTENT2 = b'<html><body>\
Hello again.<br/>\
<img src="inline-image"/>\
<svg blah="blah">\
<crap inside/>\
<image width="100" xlink:href="cover.jpg"/>\
</svg>\
<img src="image-we-dont-know-about"/>\
</body></html>'

SAMPLE_CONTENT2_EXPECTED_REPLACEMENT = b'<html><body>\
Hello again.<br/>\
<img src="inline-image"/>\
<img width="100" src="cover.jpg"/>\
<img src="image-we-dont-know-about"/>\
</body></html>'


class FakeChapter:
    def __init__(self, raw, name="hi"):
        self.content = raw
        self.file_name = name


class FakeImage:
    def __init__(self, name):
        self.file_name = name
        self.content = None


# This is here just to be able to use QTextBrowser, as without a
#  QApplication Qt doesn’t let you instantiate QWidgets.
app = QApplication(sys.argv)


class TestBookWrapper:
    @patch('ebooklib.epub.read_epub')
    def test_parseChaptersContent(self, _):
        book = BookWrapper(None, None)
        chapters = [FakeChapter(SAMPLE_CONTENT, "one"),
                    FakeChapter(SAMPLE_CONTENT2, "two")]

        book._images = [FakeImage('dummy'), FakeImage('inline-image'),
                        FakeImage('cover.jpg')]

        parsed_chapters = book._parseChaptersContent(chapters)
        assert parsed_chapters[0]['raw'] == SAMPLE_CONTENT
        plain = 'Hello. Here is a link to another chapter.'
        assert parsed_chapters[0]['plain'] == plain
        assert parsed_chapters[0]['len'] == len(plain)
        assert parsed_chapters[0]['links'] == ['another-chapter']
        assert parsed_chapters[0]['images'] == []

        assert parsed_chapters[1]['raw'] == \
            SAMPLE_CONTENT2_EXPECTED_REPLACEMENT
        plain = 'Hello again.\n\ufffc\ufffc\ufffc'
        assert parsed_chapters[1]['plain'] == plain
        assert parsed_chapters[1]['len'] == len(plain)
        assert parsed_chapters[1]['links'] == []
        assert parsed_chapters[1]['images'] == [
            {'link': 'inline-image', 'raw': None},
            {'link': 'cover.jpg', 'raw': None},
        ]

        assert book.chapter_lookup["one"] == 0
        assert book.chapter_lookup["two"] == 1

    @patch('retype.controllers.library.BookWrapper._parseChaptersContent')
    @patch('retype.controllers.library.BookWrapper._getItems')
    @patch('ebooklib.epub.read_epub')
    def test_chapters(self, _, m_getItems, m_parseChaptersContent):
        book = BookWrapper(None, None)

        def side_effect(*args):
            setattr(book, "_unparsed_chapters", "mock_unparsed_chapters")

        m_getItems.side_effect = side_effect
        m_parseChaptersContent.return_value = "mock_chapters"

        book.chapters
        m_getItems.assert_called_once()
        m_parseChaptersContent.assert_called_once_with(
            "mock_unparsed_chapters")

        m_getItems.reset_mock()
        m_parseChaptersContent.reset_mock()

        # Ensure repeated calls don’t try to get items or parse chapters again
        book.chapters
        book.chapters
        return_value = book.chapters
        m_getItems.assert_not_called()
        m_parseChaptersContent.assert_not_called()
        assert return_value == "mock_chapters"

    @patch('ebooklib.epub.read_epub')
    def test_updateProgress(self, _):
        book = BookWrapper(None, None)

        def dummySubscriber(progress):
            calls = getattr(dummySubscriber, 'calls', None) or []
            calls.append(progress)
            setattr(dummySubscriber, 'calls', calls)

        book.progress_subscribers.append(dummySubscriber)

        book.updateProgress(10)
        book.updateProgress(34)
        book.updateProgress(3248)
        assert getattr(dummySubscriber, 'calls') == [10, 34, 3248]
