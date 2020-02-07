# ------------------------------------------------------------------------------
# Distutils script; typically installs with:
#
# python setup.py install
#
# See README or README.html for details.
# ------------------------------------------------------------------------------
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
from distutils import log
from distutils.core import setup
from distutils.errors import DistutilsError
from distutils.command import config, build, sdist
from sys import version, hexversion
from os.path import join

try:
    from handlatex import defaults
    from handlatex import __version__ as version
except ImportError:
    defaults = None
    version = "not available"

# ------------------------------------------------------------------------------
class Sdist(sdist.sdist):
    default_format = {"posix": "bztar"}
    formats_info = {"bztar": "tar.bz2", "zip": "zip"}
    user_options = sdist.sdist.user_options + [
        (
            "sign=",
            "s",
            "digitally sign package(s) using given local name "
            + "[default: do not sign]",
        )
    ]

    def initialize_options(self):
        sdist.sdist.initialize_options(self)
        self.sign = None

    def run(self):
        if defaults is None:
            raise ImportError("could not load handlatex module")
        log.info("refreshing hand.def")
        defaults.refresh_handdef("hand.def")
        log.info("refreshing documentation")
        if not defaults.refresh_doc(version):
            log.error("** documentation could not be refreshed **")
            log.error("** package might ship with expired doc **")
        sdist.sdist.run(self)
        if self.sign is not None:
            log.info('signing the package(s) using "%s" key...' % self.sign)
            base_dir = self.distribution.get_fullname()
            base_name = join(self.dist_dir, base_dir)
            for fmt in self.formats:
                name = "%s.%s" % (base_name, self.formats_info[fmt])
                if not defaults.sign(name, self.sign):
                    log.info('** package "%s" signing failed **' % name)


# ------------------------------------------------------------------------------
class Config(config.config):
    def run(self):
        if hexversion < 0x30500F0:
            raise DistutilsError(
                "Python interpreter is too old: python >= 3.5.0 "
                + "needed, %s detected" % version[:5]
            )


# ------------------------------------------------------------------------------
class Build(build.build):
    def run(self):
        Config(self.distribution).run()
        build.build.run(self)


# ------------------------------------------------------------------------------
setup(
    name="handlatex",
    version=version,
    license="GPL2",
    platforms="posix",
    description="Handwriting LaTeX driver and package",
    author="Sylvain Fourmanoit",
    author_email="syfou@users.sourceforge.net",
    url="http://code.google.com/p/handlatex/",
    py_modules=["handlatex"],
    scripts=["handlatex"],
    cmdclass={"config": Config, "build": Build, "sdist": Sdist},
)

# ------------------------------------------------------------------------------
