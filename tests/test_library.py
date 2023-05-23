import sys
from unittest.mock import patch, ANY
from PyQt5.Qt import QApplication

from retype.controllers.library import LibraryController, BookWrapper


class FakeLibraryItem:
    def __init__(self):
        self.idn = 0
        self.path = 'mock-path.epub'
        self.checksum = 'mock-checksum'


class FakeBookWrapper:
    def __init__(self, item):
        self._library_item = item
        self.checksum = item.checksum
        self.path = item.path
        self.save_data = None


def _setup():
    library = LibraryController('', [''])
    book = FakeBookWrapper(FakeLibraryItem())
    data = {"test": "data"}
    save = {"dummykey": {"test": "data"}}
    return library, book, data, save


@patch('os.path.exists')
@patch('builtins.open')
@patch('json.dump')
class TestLibraryControllerSaveFunction:
    def test_save_file_exists_and_has_book_save_data_already(
            self, m_jsondump, m_open, m_exists):
        (library, book, data, save) = _setup()

        m_exists.return_value = True
        library.save_file_contents = {book.checksum: 'other-data'}

        library.save(book, data)

        m_jsondump.assert_called_once_with(
            {book.checksum: data}, ANY, indent=2)
        assert book.save_data == data

    def test_save_file_exists_and_does_not_have_book_save_data_yet(
            self, m_jsondump, m_open, m_exists):
        (library, book, data, _) = _setup()

        m_exists.return_value = True

        library.save(book, data)

        m_jsondump.assert_called_once_with(
            {book.checksum: data}, ANY, indent=2)
        assert book.save_data == data

    def test_save_file_two_books_in_save(
            self, m_jsondump, m_open, m_exists):
        (library, book, data, _) = _setup()
        save = {'other': data, book.checksum: data}

        m_exists.return_value = True
        library.save_file_contents = save

        library.save(book, data)

        m_jsondump.assert_called_once_with(save, ANY, indent=2)
        assert book.save_data == data

    def test_save_file_does_not_exist(
            self, m_jsondump, m_open, m_exists):
        (library, book, data, save) = _setup()

        m_exists.return_value = False

        library.save(book, data)

        m_jsondump.assert_called_once_with(
            {book.checksum: data}, ANY, indent=2)
        assert book.save_data == data


@patch('retype.controllers.library.generate_file_md5')
@patch('os.path.exists')
@patch('builtins.open')
@patch('json.load')
class TestLibraryControllerLoadFunction:
    def test_load_save_file_exists_and_has_key(
            self, m_jsonload, m_open, m_exists, _):
        (library, book, data, _) = _setup()
        key = book.checksum
        save = {key: data}

        m_exists.return_value = True
        m_jsonload.return_value = save

        loaded = library.load(book._library_item)

        m_jsonload.assert_called_once()
        assert loaded == data

    def test_load_save_file_does_not_exist(self, m_jsonload, m_open, m_exists, _):
        (library, book, data, _) = _setup()

        m_exists.return_value = False

        loaded = library.load(book._library_item)
        m_jsonload.assert_not_called()
        assert loaded is None

    def test_load_save_file_exists_and_does_not_have_key(
            self, m_jsonload, m_open, m_exists, _):
        (library, book, _, save) = _setup()

        m_exists.return_value = True
        m_jsonload.return_value = save

        loaded = library.load(book._library_item)

        m_jsonload.assert_called_once()
        assert loaded is None

    def test_load_save_file_exists_and_has_v1_format_key(
            self, m_jsonload, m_open, m_exists, m_hash):
        (library, book, data, _) = _setup()
        save = {book.path: data}

        m_exists.return_value = True
        m_jsonload.return_value = save
        m_hash.return_value = book.checksum

        loaded = library.load(book._library_item)

        m_jsonload.assert_called_once()
        m_hash.assert_called_once_with(book.path)
        assert loaded == data

    def test_load_save_file_v1_path_does_not_exist(
            self, m_jsonload, m_open, m_exists, m_hash):
        (library, book, data, _) = _setup()
        save = {book.path: data}

        m_exists.side_effect = [True, False]
        m_jsonload.return_value = save

        loaded = library.load(book._library_item)

        m_jsonload.assert_called_once()
        m_hash.assert_not_called()
        assert loaded is None

    def test_load_save_file_v1_two_books_same_checksum(
            self, m_jsonload, m_open, m_exists, m_hash):
        (library, book, data, _) = _setup()
        save = {book.path: {'different': 'data'}, book.checksum: data}

        m_exists.return_value = True
        m_jsonload.return_value = save
        m_hash.return_value = book.checksum

        loaded = library.load(book._library_item)

        m_jsonload.assert_called_once()
        m_hash.assert_called_once_with(book.path)
        assert loaded == data


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
        book = BookWrapper(FakeLibraryItem())
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
        book = BookWrapper(FakeLibraryItem())

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
        book = BookWrapper(FakeLibraryItem())

        def dummySubscriber(progress):
            calls = getattr(dummySubscriber, 'calls', None) or []
            calls.append(progress)
            setattr(dummySubscriber, 'calls', calls)

        book.progress_subscribers.append(dummySubscriber)

        book.updateProgress(10)
        book.updateProgress(34)
        book.updateProgress(3248)
        assert getattr(dummySubscriber, 'calls') == [10, 34, 3248]
