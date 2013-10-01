zapd_grab_py
============

http://archiveteam.org/index.php?title=Zapd

**BUGS: Does not download HTTPS images into warc file.**


Install
+++++++

* Python 2
* PySide: ``apt-get python-pyside``
* lxml: ``apt-get install python-lxml`` or ``pip install lxml``
* Ghost.py: ``pip install Ghost.py``

What's already included:

* iramari/WarcProxy (with some unused imports removed)
* Tornado 2.4 (because I'm too lazy to fix WarcProxy)


Running
+++++++

Command::

    python zapd_grab.py USERNAME.zapd.com

Use ``--help`` option for more options.
