"""
handlatex driver
"""
from __future__ import with_statement

"""
Copyright (C) 2008 Sylvain Fourmanoit <syfou@users.sourceforge.net

This code is released under the terms of the GNU General Public License
(GPL), version 2. You should have received a complete copy of the licence
along the software: see COPYING.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the 'Software'), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies of the Software and its documentation and acknowledgment shall be
given in the documentation and software packages that this Software was used.

THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
# ------------------------------------------------------------------------------
# Imports
import sys
import traceback
import logging
import re

from optparse import OptionParser
from math import exp
from textwrap import fill, dedent
from logging import debug, info, error
from random import SystemRandom
from time import strftime
from os import system

# ------------------------------------------------------------------------------
# Distutils hooks
class SetupHelper(dict):
    """
    Collection of distutils helper routines, grouped here to optimize setup.py
    portability.
    """

    def refresh_handdef(self, path):
        """
        Update LaTeX-level defaults
        """
        with open(path, "w") as f:
            f.write(
                "\\def\\handReleaseInfo{%s, v%s}%%\n%s\n"
                % (
                    strftime("%Y/%d/%m"),
                    __version__,
                    "\n".join(
                        [("\\def\\hand%s{%s}%%" % (k, v[1])) for k, v in self.items()]
                    ),
                )
            )

    def refresh_doc(self, version):
        """
        Update the documentation
        """
        return system("set -x ; gmake -C doc VERSION=%s" % version) == 0

    def sign(self, path, gpgname):
        """
        Authenticate a file by crypto-signature.
        """
        return (
            system(
                "set -x; gpg --local-user %s --armor --detach-sign %s" % (gpgname, path)
            )
            == 0
        )


# ------------------------------------------------------------------------------
# A few global settings
defaults = SetupHelper(
    {
        "driver": (str, "latex"),
        "encoding": (str, "utf-8"),
        "minparangle": (int, -2),
        "maxparangle": (int, 2),
        "minparscale": (float, 0.8),
        "maxparscale": (float, 1.25),
        "lowwordangle": (int, -2),
        "highwordangle": (int, 2),
        "freqword": (float, 0.4),
    }
)
__version__ = "1.0.0"
__copyright__ = """
Copyright (C) 2008 Sylvain Fourmanoit <syfou@users.sourceforge.net>

This is free software. You may redistribute copies of it under the terms of the
GNU General Public License version 2 <http://www.gnu.org/licenses/gpl2.html>.
There is NO WARRANTY, to the extent permitted by law.
""".strip()

# ------------------------------------------------------------------------------
# Utility functions
#fixed for PEP 479 python Python 3.7
def izip(*iterables):
    """Itering zip"""
    its = [iter(it) for it in iterables]
    while True:
        try:
            yield tuple([next(it) for it in its])
        except StopIteration:
            return


def autocount(method):
    """Method decorator for automatic access count"""
    attrname = "_count_%s" % method.__name__

    def counter(self, *args, **kw):
        setattr(self, attrname, getattr(self, attrname, 0) + 1)
        return method(self, *args, **kw)

    counter.__name__ = method.__name__
    return counter


def count(method):
    """Companion of autocount decorator"""
    return getattr(method.__self__, "_count_%s" % method.__name__, 0)


# ------------------------------------------------------------------------------
class HandError(Exception):
    """Runtime, fatal handlatex error"""

    pass


# ------------------------------------------------------------------------------
class Handpar_Process:
    """
    Handpar randomizer: see Cli() for usage.
    """

    def __init__(self, **lopts):
        self.random = SystemRandom()
        if len(lopts) > 0:
            self.update(lopts)

    def update(self, lopts):
        self.__dict__.update(lopts)
        self.parangle = self.markovwalk(
            getattr(self, "minparangle", 0), getattr(self, "maxparangle", 0)
        )

    @autocount
    def __call__(self, par):
        return "\\begin{handparfull}{%d}{%.2f}\n%s\n\end{handparfull}" % (
            next(self.parangle),
            self.random.uniform(self.minparscale, self.maxparscale),
            fill(
                " ".join(
                    [
                        (self.rotatebox(word) if state else word)
                        for state, word in izip(
                            self.bernouilli(self.freqword),
                            [
                                self.wordcount(i)
                                for i in re.split("\s+", par.group(1))
                                if len(i) > 0
                            ],
                        )
                    ]
                )
            ),
        )

    @autocount
    def wordcount(self, word):
        return word

    @autocount
    def rotatebox(self, word):
        return "\\handword{%d}{%s}" % (
            self.randpick((self.lowwordangle, self.highwordangle)),
            word,
        )

    def bernouilli(self, freq):
        while True:
            yield True if (self.random.uniform(0, 1) <= freq) else False

    def markovwalk(self, a, b):
        pos = self.random.randint(a, b)
        while True:
            step = self.random.randint(-1, 1)
            pos += step
            if (pos < a) or (pos > b):
                pos -= step
            yield pos

    def randpick(self, pick):
        return pick[self.random.randint(0, len(pick) - 1)]


# ------------------------------------------------------------------------------
class Cli:
    """
    Command line interface
    """

    class ConsoleFormatter(logging.Formatter):
        def format(self, rec):
            return "%s%s" % (
                ("(ERROR) " if rec.levelno >= logging.ERROR else ""),
                "%s%s" % (rec.msg[0].upper(), rec.msg[1:]),
            )

    class LateStream:
        def __init__(self):
            self.f = None

        def open(self, filename, *args):
            self.f = open(filename, *args)

        def write(self, *args):
            if self.f is not None:
                self.f.write(*args)

        def flush(self, *args):
            if self.f is not None:
                self.f.flush(*args)

    def __call__(self, args=None, console=None):
        """
        Invoke the handlatex driver:

        - args if the list of arguments (or sys.argv[1:] if not given)
        - console is the stream to log too (or sys.stderr if not given)
        """
        self.log = self.LateStream()
        self.handpar = Handpar_Process()
        if console is None:
            console = sys.stderr
        try:
            self._cli(args if args is not None else sys.argv[1:], console)
        except HandError as e:
            error(str(e))
        except SystemExit:
            pass
        except:
            typ, val, tb = sys.exc_info()
            error("unexpected problem occured: %s" % val)
            msg = "%(sep)s\n%(msg)s\n%(sep)s" % {
                "msg": ("".join(traceback.format_exception(typ, val, tb))).strip(),
                "sep": "=" * 80,
            }
            for stream in (self.log, console):
                print(msg, file=stream)
        else:
            debug("operation completed successfully")
            info(
                ", ".join(
                    [
                        "%d %s" % (count(getattr(self.handpar, name)), desc)
                        for desc, name in (
                            ("paragraphs", "__call__"),
                            ("words", "wordcount"),
                            ("rotated words", "rotatebox"),
                        )
                    ]
                )
            )
        finally:
            if hasattr(self.log.f, "name"):
                info('high-level transcript written on "%s"' % self.log.f.name)

    def _cli(self, args, console):
        """Process a document based on the command line"""

        # Set basic console logger
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s %(levelname)s %(message)s",
            stream=self.log,
        )

        # Log to the console as well using a different format
        con = logging.StreamHandler(console)
        con.setLevel(logging.DEBUG)
        con.setFormatter(self.ConsoleFormatter())
        logging.getLogger("").addHandler(con)

        # Build and parse the command line
        p = OptionParser(
            usage=dedent(
                """\
            %prog [options] input_file

            Process the LaTeX input_file with the handwriting driver.
            """
            ).strip(),
            version="%%prog %s\n%s" % (__version__, __copyright__),
        )

        for optname, (opttype, optval) in defaults.items():
            p.add_option(
                "--%s" % optname,
                type=opttype,
                help=dedent(
                    """\
        force %s option (see hand package doc;\
        default value: %s)"""
                    % (optname, optval)
                ),
            )

        options, args = p.parse_args(args)

        if len(args) == 0:
            p.error("no input_file given")
        basename = ".".join(args[0].split(".")[:-1])

        # Open file log
        self.log.open("%s.hlog" % basename, "w")

        # Welcome message
        info("this is handLaTex %s" % __version__)

        # Load the file
        debug('loading "%s"' % args[0])
        doc = open(args[0]).read()

        # Retrieve options
        m = re.search("\\\\usepackage\[([^\]]*)\]\{hand\}", doc, re.MULTILINE)
        if m is None:
            raise HandError("input_file does not use the hand package")

        # Build up options dictionnary from three sources:
        # 1) the default dictionnary (if there is nothing else available)
        # 2) the document usepackage options (that's the normal way)
        # 3) handlatex command line (forced parameters)
        self.lopts = dict(
            [(k, v[1]) for k, v in defaults.items()]
            + [
                (k, defaults[k][0](v))
                for k, v in [
                    [i.strip() for i in keyval.split("=")]
                    for keyval in m.group(1).split(",")
                    if len(keyval.strip()) > 0
                ]
            ]
            + [
                (optname, getattr(options, optname))
                for optname in defaults
                if getattr(options, optname) is not None
            ]
        )
        self.handpar.update(self.lopts)

        # Decode to unicode
        try:
            debug("decoding the file as %s..." % self.lopts["encoding"])
            doc = open(args[0], encoding=self.lopts["encoding"]).read()
        except (UnicodeDecodeError, LookupError) as e:
            raise HandError(
                "decoding the document failed (bad encoding parameter?), %s" % e
            )

        # Process hand paragraphs one by one.
        debug("randomizing the document...")
        doc = re.sub(
            "\\\\begin{handpar}([^}]*)\\\\end{handpar}", self.handpar, doc, re.MULTILINE
        )

        # Output it
        outname = "%s.htex" % basename
        with open(outname, "w", encoding=self.lopts["encoding"]) as out:
            debug('writing to "%s"...' % outname)
            out.write(doc)

        # Create the driver file
        drvname = "%s.hand" % basename
        debug('creating batch file "%s"...' % drvname)
        dedented_output = dedent(
            """\
        \def\handLaTeXRevision{%s}
        \input %s
        \endbatchfile"""
            % (__version__, outname)
        )
        print(dedented_output, file=open(drvname, "w"))

        # Invoke the driver on it
        cmd = "%s %s" % (self.lopts["driver"], drvname)
        debug('invoking driver as "%s"...' % cmd)
        if system(cmd) != 0:
            raise HandError('driver "%s" failed' % self.lopts["driver"])


cli = Cli()
