# Kindle2Evernote

**UPDATE** (March 2019): This repository no longer functions since [Amazon
overhauled](https://ebookfriendly.com/new-amazon-kindle-highlights-mobile-friendly/)
read.amazon.com last year.

HOWEVER, a version using Kindle's My Clippings.txt is also available in the
[kindle2evernote2 repo](https://github.com/benhorvath/kindle2evernote2).

~~This repository contains an easy-to-use, flexible script to add your Kindle highlights to Evernote. Unlike similar projects, it makes direct use of the Evernote API and aims to add all of your highlights in one go, whether you have just a few, or like me, several thousand.~~

## Get Started

### Dependencies

The main dependencies are the HTML parsing library [BeautifulSoup](http://www.crummy.com/software/BeautifulSoup/) and the [Evernote API Python SDK](https://github.com/evernote/evernote-sdk-python).

BeautifulSoup can be installed by:

    pip install BeautifulSoup4

The Evernote DSK requires:

	git submodule add git://github.com/evernote/evernote-sdk-python/ evernote
	git submodule init
	git submodule update

Then go the installed directoy and run setup.py:

	python setup.py install

Finally, you will need pyfiglet:

    pip install pyfiglet

### Evernote Developer Token

You'll need an Evernote Developer token. Go to [https://www.evernote.com/api/DeveloperToken.action](https://www.evernote.com/api/DeveloperToken.action) to get a developer token for you **production** account. Mine looks like: S=aDD:U=DDDDDD:E=15SDFSDFDF:C=35234234:A=en-devtoken:V=2:H=SDFKJSDKFJKSDJFKSDJFKJSD. Note that this is not the Evernote API secret.

Save the key in a text file. You will input this document as a required argument to Kindle2Evernote.py.

### Get Your Highlights

Access your Kindle Highlights via [kindle.amazon.com](https://kindle.amazon.com).

Note that the Your Highlights page uses some kind of scrolling script, so your highlights will not all show up at once. You can manually scroll all the way to the bottom, however, I recommend you use a Chrome [plugin](https://chrome.google.com/webstore/detail/auto-scroll/eochlhpceohhhfogfeladaifggikcjhk) to handle this for you.

Once you have reached the bottom of the page, and all of your Kindle highlights are visible, save the page's HTML to your device.

The path to this HTML file is a required argument to Kindle2Evernote.py.

### Run the Script

Open a terminal window and run:

    python kindle2evernote.py myhighlights.html en_auth.txt

If you wish to specify a specific notebook to add the highlights to, use the -n or --notebook option:

    python kindle2evernote.py myhighlights.html en_auth.txt -n Books

To see log output, use the -v or --verbose option

    python kindle2evernote.py myhighlights.html en_auth.txt -v

## About

This project began as a fork of [**mattnorris's WhisperNote**](https://github.com/mattnorris/whispernote). By the time I was finished with my modifications, however, it was almost a completely new code base. The only remaining similarities between WhisperNote and Kindle2Evernote are the formatting of the notes in Evernote themselves, and the use of myhighlights.html from the kindle.amazon.page. Perhaps the greatest difference is Whispernote used Gmail to load the notes to Evernote, while my script completely relies on the Evernote API. My script also makes heavy use of object oriented paradigmn which is not that case for Whispernote.

### TODO
The base functionality of the project has been completed, but I have several changes in mind for the cuture. See TODO.txt. The biggest change I envision is for Kindle2Evernote to remember what notes it's already added.

## Contact

Please contact me at benhorvath@gmail.com if you encounter any unhandled errors preventing a smooth user experience.
