# handLaTeX

handLatex makes it easy to inject automated, pseudo-random variations in LaTeX documents' output reproducing the typical quirks of a left to right, top to bottom handwriting.

## Getting Started

The package has two components:

  1. a LaTeX package, `hand`, that can be included in any valid LaTeX document via the usual

  2. a specialized command-line frontend, `handlatex`, able to process LaTeX documents using the `hand` package.

What the package does *NOT* include is a handwritten font to go with your document. A good start point is the [LaTeX Font Catalogue of Calligraphical and Handwritten Fonts](https://tug.org/FontCatalogue/calligraphicalfonts.html).

### Prerequisites

- A working TeX distribution, supporting LaTeX 2e

- Python 3.5.x or higher

### Installing

The two components are meant to be installed separately:

- the `hand` package (coposed of the files `hand.dtx`, `hand.ins`, and `hand.def`) should be installed as any other LaTeX package, following yout local TeX distribution's documentation. For example, under [TeX Live](http://www.tug.org/texlive/) it is sufficient to execute:

```
latex hand.ins
```

- the `handlatex` frontend should be installed as any other Python module, using the provided distutils script (`setup.py`). Typical invokation will be, with proper privileges:

```
 python setup.py install
```

Be warned that since the installation uses distutils, it does *not* produce enough metadata about the installed files. As a consequence, it is *NOT* possible to remove the package using pip>10.0

You can verify that installation has completed successfully by running:
```
handlatex sample.tex
```


## Contributing

This project was originally developed by [Sylvain Fourmanoit](mailto:syfou@users.sourceforge.net), and hosted at [handlatex.googlecode.com](http://handlatex.googlecode.com/) under the GPLv2 License - see the [LICENSE](LICENSE) file for details.

The package is considered mature, and the only work done by [Davide Fauri](https://github.com/DavideFauri) was to update the script to make it compatible with Python 3.5 or higher, and to update this README.

If you have any modifications to suggest, feel free to ask.

## Authors

* **Sylvain Fourmanoit** - *Initial work*
* **Davide Fauri** - *Upgrade to Python3*



