import sys
from unittest.mock import patch, ANY
from PyQt5.Qt import QApplication

from retype.controllers.library import LibraryController, BookWrapper


class FakeBookWrapper:
    def __init__(self):
        self.save_data = None


def _setup():
    library = LibraryController('', [''])
    book = FakeBookWrapper()
    key = "hey"
    data = {"test": "data"}
    save = {"dummykey": {"test": "data"}}
    return library, book, key, data, save


@patch('os.path.exists')
@patch('builtins.open')
@patch('json.load')
@patch('json.dump')
class TestLibraryControllerSaveFunction:
    def test_save_file_exists_and_has_key(
            self, m_jsondump, m_jsonload, m_open, m_exists):
        (library, book, key, data, save) = _setup()

        m_exists.return_value = True
        m_jsonload.return_value = {key: data}

        library.save(book, key, data)

        m_jsonload.assert_called_once()
        m_jsondump.assert_called_once_with({key: data}, ANY, indent=2)
        assert book.save_data == data

    def test_save_file_exists_and_does_not_have_key(
            self, m_jsondump, m_jsonload, m_open, m_exists):
        (library, book, key, data, save) = _setup()

        m_exists.return_value = True
        m_jsonload.return_value = save

        library.save(book, key, data)

        m_jsonload.assert_called_once()
        new_save = save
        new_save[key] = data
        m_jsondump.assert_called_once_with(new_save, ANY, indent=2)
        assert book.save_data == data

    def test_save_file_does_not_exist(
            self, m_jsondump, m_jsonload, m_open, m_exists):
        (library, book, key, data, save) = _setup()

        m_exists.return_value = False

        library.save(book, key, data)

        m_jsonload.assert_not_called()
        m_jsondump.assert_called_once_with({key: data}, ANY, indent=2)
        assert book.save_data == data


@patch('os.path.exists')
@patch('builtins.open')
@patch('json.load')
class TestLibraryControllerLoadFunction:
    def test_load_save_file_exists(self, m_jsonload, m_open, m_exists):
        (library, _, _, data, _) = _setup()
        key = "dummykey"
        save = {key: data}

        m_exists.return_value = True
        m_jsonload.return_value = save

        loaded = library.load(key)

        m_jsonload.assert_called_once()
        assert loaded == data

    def test_load_save_file_does_not_exist(self, m_jsonload, m_open, m_exists):
        (library, _, _, data, _) = _setup()
        key = "dummykey"

        m_exists.return_value = False

        loaded = library.load(key)
        m_jsonload.assert_not_called()
        assert loaded is None

    def test_load_save_file_exists_and_does_not_have_key(
            self, m_jsonload, m_open, m_exists):
        (library, _, _, data, _) = _setup()
        key = "dummykey"
        save = {key: data}

        m_exists.return_value = True
        m_jsonload.return_value = save

        loaded = library.load("nonexistent-key")

        m_jsonload.assert_called_once()
        assert loaded is None


SAMPLE_CONTENT = b'<span>\
Hello. <a href="another-chapter">Here is a link to another chapter.</a>\
</span>'

SAMPLE_CONTENT2 = b'<span>\
Hello again.<br/>\
<img src="inline-image"/>\
<svg blah="blah">\
<crap inside/>\
<image width="100" xlink:href="cover.jpg"/>\
</svg>\
<img src="image-we-dont-know-about"/>\
</span>'

SAMPLE_CONTENT2_EXPECTED_REPLACEMENT = '<span>\
Hello again.<br/>\
<img src="inline-image"/>\
<img width="100" src="cover.jpg"/>\
<img src="image-we-dont-know-about"/>\
</span>'


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
        assert parsed_chapters[0]['html'] == str(SAMPLE_CONTENT, 'utf-8')
        plain = 'Hello. Here is a link to another chapter.'
        assert parsed_chapters[0]['plain'] == plain
        assert parsed_chapters[0]['len'] == len(plain)
        assert parsed_chapters[0]['links'] == ['another-chapter']
        assert parsed_chapters[0]['images'] == []

        assert parsed_chapters[1]['html'] == \
            SAMPLE_CONTENT2_EXPECTED_REPLACEMENT
        plain = 'Hello again.\n\ufffc\ufffc\ufffc'
        assert parsed_chapters[1]['plain'] == plain
        assert parsed_chapters[1]['len'] == len(plain)
        assert parsed_chapters[1]['links'] == []
        assert parsed_chapters[1]['images'] == [
            {'item': book._images[1], 'link': 'inline-image', 'raw': None},
            {'item': book._images[2], 'link': 'cover.jpg', 'raw': None},
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
