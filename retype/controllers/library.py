import os
from resource_handler import getLibraryPath
from ebooklib import epub, ITEM_DOCUMENT


class LibraryController(object):  # bookcontroller?
    def __init__(self, view):
        self._view = view  # ?
        self._library_path = getLibraryPath()
        self._book_list = self.indexLibrary(self._library_path)

    def indexLibrary(self, library_path):  # _?
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

    def loadBook(self, book):
        # should instantiate a bookwrapper
        pass


class BookWrapper(object):
    def __init__(self, path):
        self._path = path
        self._book = epub.read_epub(path)
        self.title = self._book.title
        self.chapters = self._initChapters(self._book)

    def _initChapters(self, book):
        chapters = []
        for document in book.get_items_of_type(ITEM_DOCUMENT):
            chapters.append(document)
        return chapters
