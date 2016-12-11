#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Creates Evernote notes for all of your Kindle highlights.

Requires an Evernote developer account (see readme) and a corresponding
authorization token, and an HTML file of all your Kindle highlights from
kindle.amazon.com.

Example usage:

python whispernote.py auth_token.txt myhighlights.html

# no libraries: hashlib, binascii
"""

import argparse
from bs4 import BeautifulSoup
import datetime
from evernote.api.client import EvernoteClient
import evernote.edam.error.ttypes as Errors
import evernote.edam.type.ttypes as Types
import evernote.edam.userstore.constants as UserStoreConstants
import logging
from logging.config import dictConfig
from pyfiglet import Figlet
import re
from time import sleep
import urlparse


class EvernoteAPI(object):
    """ Connects to EvernoteAPI. Allows access to client and note_store.
    """

    def __init__(self, auth_token, notebook=None):

        self.auth_token = auth_token
        self.notebook = notebook
        self.client = EvernoteClient(token=self.auth_token, sandbox=False)
        self.logger = logging.getLogger('whispernote')
        self.logger.info('Initializing EverNote API')

        for i in range(1, 4):
            self.logger.info('Attempting to retrieve Note Store')
            try:
                self.note_store = self.client.get_note_store()
                self.logger.info('Note Store retrieved')
                break
            except Errors.EDAMSystemException as e:
                if e.errorCode == Errors.EDAMErrorCode.RATE_LIMIT_REACHED:
                    self._handle_rate_limit(e)
                else:
                    raise e
                self.logger.info('Retry no. %d' % i)
                continue
            except socket.error:
                self.logger.warn('Socket error: Retrying in 1 minute')
                sleep(60)
                self.logger.info('Retry no. %d' % i)
                continue

        self.notebook_map = self.map_notebook_guids()


    def _handle_rate_limit(self, e):
        """ Wait out rate limit
        """
        wait = int(e.rateLimitDuration) + 60
        self.logger.warn('API rate limit exceeded, '
                         'sleeping for %d seconds, '
                         'resuming at %s' % (wait, now_plus_seconds(wait)))
        limit_exceeded()
        print('\n. . . Script will automatically resume in %d seconds . . .\n' % wait)
        sleep(wait)


    def create_note_title(self, highlight):
        """ Creates note title from the first 11 words of the note's text.
        """
        title_list = highlight['text'].split(' ')
        title = ' '.join(title_list[0:11])
        return title.encode('utf-8')


    def create_note_body(self, highlight):
        """ Takes a highlight dict, adds some HTML structures to it, and
        returns an Evernote XML formatted body.
        """
        template = """
            <p>%s</p>
            <p></p>
            <hr/>
            <p><em>%s</em><br/>
            %s</p>
            <ul>
            <li>Highlight ID: <tt>%s</tt></li>
            <li>Batch ID: <tt>%s</tt></li>
            </ul>
            <p><a href='%s'>Read more...</a></p>
        """
        batch_id = datetime.datetime.now().strftime('batch%Y%m%d%H%M%S')
        body = template % (highlight['text'],
                           highlight['book_title'],
                           highlight['book_author'],
                           highlight['id'],
                           batch_id,
                           highlight['link'].replace('&', '&amp;'))
        body = validate_html(body)
        note_body = ('<?xml version=\"1.0\" encoding=\"UTF-8\"?>'
                     '<!DOCTYPE en-note SYSTEM '
                     '\"http://xml.evernote.com/pub/enml2.dtd\">'
                     '<en-note>%s</en-note>') % body
        return note_body.encode('utf-8')


    def map_notebook_guids(self):
        """ Returns a dictionary of a Note Store's notebook names and GUIDs
        """
        notebooks_list = self.note_store.listNotebooks()
        notebooks_map = dict([(i.name, i.guid) for i in notebooks_list])
        return notebooks_map


    def format_note(self, highlight):
        """ Takes a highlight dict and converts to an Evernote API note object.
        """
        note = Types.Note()
        note.title = self.create_note_title(highlight)
        note.content = self.create_note_body(highlight)

        if self.notebook:
            note.notebookGuid = self.notebook_map[self.notebook]

        return note


    def add_note(self, highlight):
        """ Takes a highlight, converts to an Evernote API note object, then
        attempts to add to Evernote.
        """
        note = self.format_note(highlight)

        for i in range(1, 4):
            self.logger.info('Attempting to create note: %s' % note.title)
            try:
                self.note_store.createNote(self.auth_token, note)
                sleep(1)  # nice to API
                self.logger.info('Success')
                break
            except Errors.EDAMUserException as e:
                self.logger.warn('Unable to parse, skipping: %s' % note.title)
                continue
            except Errors.EDAMSystemException as e:
                if e.errorCode == Errors.EDAMErrorCode.RATE_LIMIT_REACHED:
                    self._handle_rate_limit(e)
                else:
                    raise e
                self.logger.info('Retry no. %d' % i)
                continue
            except socket.error:
                self.logger.warn('Socket error: Retrying in 1 minute')
                sleep(60)
                self.logger.info('Retry no. %d' % i)
                continue


    def add_notes(self, highlights):
        """ For loop to convert a list of highlights to an Evernote note
        object, then adds to Evernote.
        """
        for i, highlight in enumerate(highlights):
            self.add_note(highlight)
            sleep(2) # be nice to API
        self.logger.info('Finished adding notes')


class KindleHighlights(object):
    """ Object input is a kindle.amazon.com highlights HTML file.

    The highlights attribute is a list of dicts, where each dict is a highlight,
    including book_author, text, book_title, link, and ID.

    The parsed attribute is the highlights HTML file with hierarchy.
    """

    def __init__(self, html_file):
        self._highlights = self._get_all_highlights(html_file)

        self.logger = logging.getLogger('whispernote')
        self.logger.info('Initializing Kindle Highlights')


    def __repr__(self):
        return self._highlights


    def __iter__(self):
        for hl in self._highlights:
            yield hl


    def __getitem__(self, i):
        return self._highlights[i]


    def _create_enid(self, huri): 
        """
        Creates an Evernote unique ID based on the highlight's URI. 
        A Kindle highlight is composed of a 'asin', or ISBN of the book, 
        and a location. 

        huri - highlight URI

        kindle://book?action=open&asin=B004TP29C4&location=4063

        will return...

        B004TP29C44063
        """

        asin = urlparse.urlparse(huri).query.split('&')[1].split('=')[1]
        loc = urlparse.urlparse(huri).query.split('&')[2].split('=')[1]

        return asin + loc


    def _get_all_highlights(self, html_file):
        html_doc = open(html_file, 'r').read()
        parsed = self._parse_books(html_doc)
        return self._extract_highlights(parsed)


    def _parse_books(self, html):
       """ Pass in the HTML from the myhighlights.html page, and function adds 
       hierarchy to page. All of a book's highlights divs are subsumed beneath
       the book itself. This allows the highlights to include general book 
       information (title and author). Outputs an html string.
       """
       markup = list(html.split('\n'))

       # Add highlightColumn hierarchy
       for i, line in enumerate(markup):
           if 'class="bookMain yourHighlightsHeader"' in line:
               markup[i] = '</div>' + line + '<div class="highlightColumn">'
       # Remove the very first </div>
       try:
           all_hl_div = (i for i, line in enumerate(markup) 
                         if re.search('.*<div id="allHighlightedBooks">.*', line)
                        ).next()
       except StopIteration:
           print('Did not find DIV id="allHighlightedBooks"')
           raise
       markup[all_hl_div] = markup[all_hl_div].replace('</div>', '')

       new_markup = ''.join(markup)

       return new_markup


    def _extract_highlights(self, html):
        """
        Returns an array of highlight dictionaries - content, link,
        and generated IDs - for all books.
        """

        # Initialize container
        hdicts = []

        # Find all book info divs
        soup = BeautifulSoup(html, 'html.parser')
        books = soup.find_all('div', 'bookMain')

        # Gather book information and highlights
        for book in books:
            book_title = book.find('span', 'title').string.strip()
            book_author = (book.find('span', 'author').string
                           .replace('by', '').strip())
            book_highlights = book.find_all('span', 'highlight')

            # Gather highlights from a specific book
            for highlight in book_highlights:
                hdicts.append(
                    dict(
                        book_title=book_title,
                        book_author=book_author,
                        text=highlight.string,
                        link=highlight.nextSibling.attrs['href'],
                        id=self._create_enid(highlight
                                              .nextSibling.attrs['href'])
                    )
                )

        return hdicts


def now_plus_seconds(seconds):
    """ Gets current time and adds x seconds
    """
    now = datetime.datetime.now()
    future = now + datetime.timedelta(seconds=seconds)
    future_time = future.time()
    return future_time.strftime('%H:%M:%S')


def ascii_art(text, font='standard'):
    """ Prints important messages in  large ASCII font.
    """
    f = Figlet(font=font)
    print('\n')
    print(f.renderText(text))


def limit_exceeded():
    ascii_art('API   Limit\nExceeded')


def validate_html(html):
    """ Convert offensive characters to HTML entities, e.g., '&' to '&amp;'
    """
    bs = BeautifulSoup(html, 'html.parser')
    return bs.prettify(formatter='html')


def generate_logger(debug=False):

    if debug:
        log_level = logging.DEBUG
    else:
        log_level = logging.WARN

    logging_config = dict(
        version=1,
        formatters={
            'f': {'format':
                  '%(asctime)s - %(levelname)s - %(message)s'}
        },
        handlers={
            'h': {'class': 'logging.StreamHandler',
                  'formatter': 'f',
                  'level': log_level}
        },
        root={
            'handlers': ['h'],
            'level': log_level,
         },
    )

    dictConfig(logging_config)
    logger = logging.getLogger()

    return logger


def retrieve_arguments():

    app_description = 'Add Kindle Highlights to your Evernote account'
    parser = argparse.ArgumentParser(description=app_description)
    parser.add_argument('highlights', type=str,
                        help='Kindle highlights HTML document')
    parser.add_argument('api_key_file', type=str,
                        help='Text file containing Evernote dev key')
    parser.add_argument('-n', '--notebook', type=str,
                        help='EverNote notebook to add Kindle highlights')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Print verbose output')
    return parser.parse_args()


def main(args):

    auth_token = open(args.api_key_file, 'r').read()
    evernote = EvernoteAPI(auth_token, args.notebook)
    highlights = KindleHighlights(args.highlights)
    evernote.add_notes(highlights)


if __name__ == '__main__':

    args = retrieve_arguments()

    logger = generate_logger(args.verbose)

    main(args)
