import os
import json
import logging
from lxml.html import fromstring, builder, tostring, xhtml_to_html
from lxml.etree import _Element
from ebooklib import epub
from qt import QTextBrowser

from typing import TYPE_CHECKING

from retype.extras.space import isspaceorempty
from retype.extras.hashing import generate_file_md5

logger = logging.getLogger(__name__)


class LibraryController(object):
    def __init__(self, user_dir, library_paths):
        # type: (LibraryController, str, list[str]) -> None
        self.user_dir = user_dir
        self.library_paths = library_paths
        self._library_items = self.indexLibrary(library_paths)
        self.books = None  # type: dict[int, BookWrapper] | None
        self.save_file_contents = None  # type: Save | None

    @property
    def user_dir(self):
        # type: (LibraryController) -> str
        return self._user_dir

    @user_dir.setter
    def user_dir(self, value):
        # type: (LibraryController, str) -> None
        self._user_dir = value
        self.save_abs_path = os.path.join(value, 'save.json')

    def indexLibrary(self, library_paths):
        # type: (LibraryController, list[str]) -> dict[int, LibraryItem]
        book_checksum_list = []
        library_items = {}
        idn = 0
        for library_path in library_paths:
            for root, dirs, files in os.walk(library_path):
                for f in files:
                    if f.lower().endswith(".epub"):
                        path = os.path.join(root, f)
                        checksum = generate_file_md5(path)
                        if checksum in book_checksum_list:
                            continue
                        book_checksum_list.append(checksum)
                        library_items[idn] = LibraryItem(idn, path, checksum)
                        idn += 1
        return library_items

    def instantiateBooks(self):
        # type: (LibraryController) -> None
        self.books = {}
        for idn, item in self._library_items.items():
            book = BookWrapper(item, self.load(item))
            self.books[idn] = book

    def setBook(self, book_id, book_view, switchView):
        # type: (LibraryController, int, BookView, pyqtBoundSignal) -> None
        if book_view.book:
            book_view.maybeSave()

        if self.books and book_id in self.books:
            book = self.books[book_id]
            logger.info("Loading book {}: {}".format(book_id, book.title))
        else:
            logging.error("book_id {} cannot be found".format(book_id))
            logging.debug("books: {}".format(self.books))
            return

        save_data = book.save_data
        logger.info("Save data: {}".format(save_data))
        book_view.setBook(book, save_data)
        switchView.emit(2)
        book_view.display.centreAroundCursor()

    def save(self, book, data):
        # type: (LibraryController, BookWrapper, SaveData) -> None
        book.save_data = data

        if not os.path.exists(self._user_dir):
            logger.error(f'Unable to find user_dir {self._user_dir}')
            return

        self.addFriendlyName(data, book.path)
        key = book.checksum
        save = self.save_file_contents
        if (save):
            save[key] = data
        else:
            save = self.save_file_contents = {key: data}

        with open(self.save_abs_path, 'w', encoding='utf-8') as f:
            json.dump(save, f, indent=2)

    def migrateV1Save(self, save):
        # type: (LibraryController, Save) -> Save
        book_checksum_list = []
        new_save = {}
        for key in save:
            checksum = None
            if key.lower().endswith(".epub"):
                if (not os.path.exists(key)):
                    logger.warning("Save file contains v1 format save data "
                                   f"for a file that cannot be found: {key}")
                    # Not a checksum; can’t generate it as we cannot find the
                    #  file, but setting it anyway in order that we keep the
                    #  save entry rather than delete it from the save. This
                    #  save data entry cannot be used by retype, but we should
                    #  not delete it as that would be unnecessary data loss and
                    #  user could correct the issue by fixing the path,
                    #  replacing it with a checksum, or moving the file back.
                    checksum = key
                else:
                    checksum = generate_file_md5(key)
                    self.addFriendlyName(save[key], key)
            else:  # assume it’s a checksum
                checksum = key
            if checksum in book_checksum_list:
                logger.warning("Save file contains several entries for the "
                               f"same book (checksum {checksum}). The lowest "
                               "one in the file will be used")
            else:
                book_checksum_list.append(checksum)
            new_save[checksum] = save[key]
        return new_save

    def addFriendlyName(self, data, path):
        # type: (LibraryController, SaveData, str) -> None
        data['friendly_name'] = os.path.basename(path)

    def loadSaveFile(self):
        # type: (LibraryController) -> Save
        if os.path.exists(self.save_abs_path):
            logger.info(f'Read save: {self.save_abs_path}')
            with open(self.save_abs_path, 'r') as f:
                save = json.load(f)  # type: Save
        else:
            logger.debug(
                f'Save path {self.save_abs_path} not found.\n'
                'This is normal if the save file has not been created yet.')
            save = {}

        save = self.migrateV1Save(save)
        self.save_file_contents = save
        return save

    def load(self, item):
        # type: (LibraryController, LibraryItem) -> SaveData | None
        save = None
        if self.save_file_contents is not None:
            save = self.save_file_contents
        else:
            save = self.loadSaveFile()

        key = item.checksum

        if save and key in save:
            return save[key]

        return None


class LibraryItem:
    def __init__(self, idn, path, checksum):
        # type: (LibraryItem, int, str, str) -> None
        self.idn = idn
        self.path = path
        self.checksum = checksum


class BookWrapper(object):
    def __init__(self, library_item, save_data=None):
        # type: (BookWrapper, LibraryItem, SaveData | None) -> None
        self.valid = False
        self._library_item = library_item
        self.path = library_item.path
        self.idn = library_item.idn
        self.checksum = library_item.checksum
        self._book = self._readEpub()
        self.title = self._book.title
        self._chapters = []  # type: list[Chapter]
        self._images = []  # type: list[epub.EpubImage]
        self._author = ''
        self._cover = None  # type: epub.EpubCover | epub.EpubImage | None
        self.documents = {}  # type: dict[str, epub.EpubHtml]
        self._unparsed_chapters = []  # type: list[epub.EpubHtml]
        self.save_data = save_data
        self.dirty = False
        self.progress = save_data['progress'] if save_data else 0.0
        self.progress_subscribers = []  # type: list[Callable[[float], None]]

    def _readEpub(self):
        # type: (BookWrapper) -> epub.EpubBook
        ret = None
        try:
            ret = epub.read_epub(self.path, options={'ignore_ncx': True})
            self.valid = True
        except (LookupError, OSError) as e:
            logger.error(f"Error reading epub {self.idn}:{self.path}:"
                         f"\n{e}", exc_info=True)
        return ret or epub.EpubBook()

    def _parseChaptersContent(self, chapters):
        # type: (BookWrapper, list[epub.EpubHtml]) -> list[Chapter]
        parsed_chapters = []
        self.chapter_lookup = {}  # type: dict[str, int]
        for i, chapter in enumerate(chapters):
            parsed_chapters.append(self.__parseChapterContent(chapter))
            self.chapter_lookup[chapter.file_name.split('/')[-1]] = i

        return parsed_chapters

    def __parseChapterContent(self, chapter):
        # type: (BookWrapper, epub.EpubHtml) -> Chapter
        raw = chapter.content
        # FIXME: This ugly workaround is the only way I found to make lxml
        #  use the correct encoding when an lxml declaration is absent from
        #  the document. Also note this causes lxml to get rid of html and
        #  body tags for some reason, which may be a problem in future.
        declaration = """<?xml version="1.0" encoding="utf-8"?>"""
        tree = fromstring(bytes(declaration, 'utf-8') + raw)

        # Replace xml svg elements with valid html
        svg_elements = tree.xpath('//svg')
        if isinstance(svg_elements, list):
            for svg in svg_elements:
                if not isinstance(svg, _Element):
                    continue
                imgs = svg.xpath('//image')
                if not isinstance(imgs, list):
                    continue
                imaged = imgs[0]
                if not isinstance(imaged, _Element):
                    continue
                attrs = {item[0]: item[1] for item in imaged.items()
                         }  # type: dict[str, str]
                try:
                    href = attrs['xlink:href']
                    del attrs['xlink:href']
                    attrs['src'] = href
                except AttributeError:
                    pass
                proper_img = builder.IMG(**attrs)
                parent = svg.getparent()
                if parent is not None:
                    parent.replace(svg, proper_img)

        # Ensure figure elements appear in their own line
        figure_elements = tree.xpath('//figure')
        if isinstance(figure_elements, list):
            for figure in figure_elements:
                if isinstance(figure, _Element):
                    figure.addprevious(figure.makeelement('div'))

        xhtml_to_html(tree)
        html = tostring(tree, method='xml', encoding='unicode')

        # Get rid of invisible garbage characters
        html = html.replace('\ufeff', '')

        links = tree.xpath('//a/@href')
        image_links = tree.xpath('//img/@src')

        images = []  # type: list[ImageData]
        if isinstance(image_links, list):
            for image_link in image_links:
                for image in self._images:
                    if not isinstance(image_link, str):
                        continue
                    if image_link.lstrip('./') in image.file_name:
                        images.append({'item': image,
                                       'link': image_link,
                                       'raw': image.content})

        # We to store the length of the plain text of all chapters for
        #  progress-calculation purposes
        dummy_display = QTextBrowser()
        dummy_display.setHtml(html)
        plain = dummy_display.toPlainText()

        return {'html': html, 'plain': plain, 'len': len(plain),
                'links': links, 'images': images}

    @property
    def chapters(self):
        # type: (BookWrapper) -> list[Chapter]
        if not self._unparsed_chapters:
            self._getItems(self._book)
        if not self._chapters:
            self._chapters = self._parseChaptersContent(
                self._unparsed_chapters)
        return self._chapters or []

    @property
    def images(self):
        # type: (BookWrapper) -> list[epub.EpubImage]
        if not self._images:
            self._getItems(self._book)
        return self._images

    @property
    def cover(self):
        # type: (BookWrapper) -> epub.EpubCover | epub.EpubImage | None
        if not self._cover:
            self._getItems(self._book)
        return self._cover

    def _getItems(self, book):
        # type: (BookWrapper, epub.EpubBook) -> None
        logger.debug("_getItems called for '{}'".format(book.title))

        # Reset lists
        self._images = []
        self._unparsed_chapters = []

        # Get items
        for item in book.get_items():
            if isinstance(item, epub.EpubCover):
                self._cover = item
            elif isinstance(item, epub.EpubImage):
                if 'cover' in item.id and not self._cover:
                    self._cover = item
                self._images.append(item)
            elif isinstance(item, epub.EpubHtml):
                self.documents[item.id] = item

        # Get chapters
        for spine_item in book.spine:
            uid = spine_item[0]
            if uid in self.documents.keys():
                self._unparsed_chapters.append(self.documents[uid])

        # Workaround to catch some edge cases where the cover is not marked but
        #  is present on the first page
        if not self._cover and len(self._unparsed_chapters):
            first_page = self.__parseChapterContent(self._unparsed_chapters[0])
            if len(first_page['images']) == 1 and \
               isspaceorempty(first_page['plain'], True):
                self._cover = first_page['images'][0]['item']

    @property
    def author(self):
        # type: (BookWrapper) -> str
        book = self._book
        if not self._author:
            for namespace in book.metadata.keys():
                data = book.metadata[namespace]
                for key, value in data.items():
                    if key == 'creator':
                        self._author = value[0][0]
        return self._author

    def updateProgress(self, progress):
        # type: (BookWrapper, float) -> None
        self.progress = progress

        for subscriber in self.progress_subscribers:
            subscriber(progress)


if TYPE_CHECKING:
    from typing import Callable  # noqa: F401
    from qt import pyqtBoundSignal  # noqa: F401
    from retype.ui import BookView, Cover  # noqa: F401
    from retype.extras.metatypes import (  # noqa: F401
        SaveData, Save, ImageData, Chapter)
