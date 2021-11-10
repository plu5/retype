import os
import json
import logging
from lxml.html import fromstring, builder, tostring, xhtml_to_html
from ebooklib import epub
from PyQt5.Qt import QTextBrowser

logger = logging.getLogger(__name__)


class LibraryController(object):
    def __init__(self, user_dir, library_paths):
        self.save_abs_path = os.path.join(user_dir, 'save.json')
        self.library_paths = library_paths
        self._book_files = self.indexLibrary(library_paths)
        self.books = None

    def indexLibrary(self, library_paths):
        book_path_list = []
        book_list = {}
        for library_path in library_paths:
            for root, dirs, files in os.walk(library_path):
                for f in files:
                    if f.lower().endswith(".epub"):
                        path = os.path.join(root, f)
                        if path not in book_path_list:
                            book_path_list.append(path)
        # internal name assignment
        for i in range(0, len(book_path_list)):
            book_list[i] = book_path_list[i]
        return book_list

    def instantiateBooks(self):
        self.books = {}
        for idn, path in self._book_files.items():
            book = BookWrapper(path, idn, self.load(path))
            self.books[idn] = book

    def setBook(self, book_id, book_view, switchView):
        if book_id in self.books:
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

    def save(self, book, key, data):
        if os.path.exists(self.save_abs_path):
            with open(self.save_abs_path, 'r') as f:
                save = json.load(f)
                save[key] = data
        else:
            save = {key: data}
        with open(self.save_abs_path, 'w', encoding='utf-8') as f:
            json.dump(save, f, ensure_ascii=False, indent=2)

        book.save_data = {key: data}

    def load(self, key):
        if os.path.exists(self.save_abs_path):
            with open(self.save_abs_path, 'r') as f:
                save = json.load(f)
                if key in save:
                    return save[key]
        return None


class BookWrapper(object):
    def __init__(self, path, idn, save_data=None):
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
        self.save_data = save_data
        self.progress = save_data['progress'] if save_data else None
        self.progress_subscribers = []

    def _parseChaptersContent(self, chapters):
        parsed_chapters = []
        self.chapter_lookup = {}
        for i, chapter in enumerate(chapters):
            raw = chapter.content
            tree = fromstring(raw)

            # Replace xml svg elements with valid html
            svg_elements = tree.xpath('//svg')
            if svg_elements:
                for svg in svg_elements:
                    image = svg.xpath('//image')[0]
                    attrs = {item[0]: item[1] for item in image.items()}
                    try:
                        href = attrs['xlink:href']
                        del attrs['xlink:href']
                        attrs['src'] = href
                    except AttributeError:
                        pass
                    proper_img = builder.IMG(**attrs)
                    svg.getparent().replace(svg, proper_img)

            xhtml_to_html(tree)
            raw = tostring(tree, method='xml')

            links = tree.xpath('//a/@href')
            image_links = tree.xpath('//img/@src')

            images = []
            for image_link in image_links:
                for image in self.images:
                    if image_link in image.file_name:
                        images.append({'link': image_link,
                                       'raw': image.content})

            # We to store the length of the plain text of all chapters for
            #  progress-calculation purposes
            dummy_display = QTextBrowser()
            dummy_display.setHtml(str(raw, 'utf-8'))
            plain = dummy_display.toPlainText()

            parsed_chapters.append({'raw': raw,
                                    'plain': plain,
                                    'len': len(plain),
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

    def updateProgress(self, progress):
        self.progress = progress

        for subscriber in self.progress_subscribers:
            subscriber(progress)
