import os
import logging
from lxml import html
from ebooklib import epub

from retype.resource_handler import getLibraryPath

logger = logging.getLogger(__name__)


class LibraryController(object):
    def __init__(self, main_controller):
        self._main_controller = main_controller  #
        self._library_path = getLibraryPath()
        self._book_list = self.indexLibrary(self._library_path)

    def indexLibrary(self, library_path):
        book_path_list = []
        book_list = {}
        for root, dirs, files in os.walk(library_path):
            for f in files:
                if f.lower().endswith(".epub"):
                    book_path_list.append(os.path.join(root, f))
        # internal name assignment
        for i in range(0, len(book_path_list)):
            book_list[i] = book_path_list[i]
        return book_list

    def _instantiateBook(self, book_id):
        if book_id in self._book_list:
            logger.info("Instantiating book {}-{}".format(
                book_id, self._book_list[book_id]))
            book = BookWrapper(self._book_list[book_id], book_id)
        else:
            logger.error("book_id {} cannot be found").format(book_id)
            return
        return book

    def setBook(self, book_id, book_view):
        self.book = self._instantiateBook(book_id)
        book_view.setBook(self.book)
        book_view.setChapter(0, True)
        self._main_controller.switchView(2)


class BookWrapper(object):
    def __init__(self, path, idn):
        self.path = path
        self._book = epub.read_epub(path)
        self.idn = idn
        self.title = self._book.title
        self._chapters = None
        self._images = None
        self._author = None
        self._cover = None
        self._images = []
        self.documents = {}
        self._unparsed_chapters = []

    def _parseChaptersContent(self, chapters):
        parsed_chapters = []
        self.chapter_lookup = {}
        for i, chapter in enumerate(chapters):
            raw = chapter.content
            tree = html.fromstring(raw)
            links = tree.xpath('//a/@href')
            image_links = tree.xpath('//img/@src')

            images = []
            for image_link in image_links:
                for image in self.images:
                    if image_link in image.file_name:
                        images.append({'link': image_link,
                                       'raw': image.content})

            parsed_chapters.append({'raw': raw,
                                    'links': links,
                                    'images': images})
            self.chapter_lookup[chapter.file_name] = i

        return parsed_chapters

    @property
    def chapters(self):
        if not self._unparsed_chapters:
            self._getItems(self._book)
        if not self._chapters:
            self._chapters = self._parseChaptersContent(
                self._unparsed_chapters)
        return self._chapters

    @property
    def images(self):
        if not self._images:
            self._getItems(self._book)
        return self._images

    @property
    def cover(self):
        if not self._images:
            self._getItems(self._book)
        return self._cover

    def _getItems(self, book):
        for item in book.get_items():
            if type(item) is epub.EpubCover:
                self._cover = item
            if type(item) is epub.EpubImage:
                if item.id == 'cover':
                    self._cover = item
                self._images.append(item)
            if type(item) is epub.EpubHtml:
                self.documents[item.id] = item

        for item in book.spine:
            uid = item[0]
            if uid in self.documents.keys():
                self._unparsed_chapters.append(self.documents[uid])

    @property
    def author(self):
        book = self._book
        if not self._author:
            for namespace in book.metadata.keys():
                data = book.metadata[namespace]
                for key, value in data.items():
                    if key == 'creator':
                        self._author = value[0][0]
        return self._author
