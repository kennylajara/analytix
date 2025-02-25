analytix
========

.. note::
   These docs are moving! From version 4.0, the docs will be hosted on
   `GitHub Pages <https://parafoxia.github.io/analytix>`__. While these
   docs are not finished, they should provide a good insight into what
   will change in version 4.0.

|PyPi version| |PyPI - Status| |Downloads| |GitHub last commit|
|License|

|CI| |Read the Docs| |Maintainability| |Test Coverage|

A simple yet powerful wrapper for the YouTube Analytics API.

CPython versions 3.7 through 3.11-dev and PyPy versions 3.7 through 3.9
are officially supported.

Windows, MacOS, and Linux are all supported.

Features
--------

-  Pythonic syntax lets you feel right at home
-  Dynamic error handling saves hours of troubleshooting, and makes sure
   only valid requests count toward your API quota
-  A clever interface allows you to make multiple requests across
   multiple sessions without reauthorising
-  Extra support allows the native saving of CSV files and conversion to
   DataFrame objects
-  Easy enough for beginners, but powerful enough for advanced users

What does *analytix* do?
------------------------

The YouTube Studio provides a fantastic interface where creators can
view some incredibly detailed analytics for their channel. However,
there’s no way to perform programmatical operations on the data to do
some proper analysis on it. This is where *analytix* comes in.

The process of analysing data on the YouTube Studio is comprised of two
steps:

1. Retrieving the data to be analysed and visualised
2. Presenting that data to the user

*analytix* aims to handle step one as comprehensively as possible,
allowing analysts to use tools such as *pandas* and *Matplotlib* to work
on the data without having to faff around with Google’s offerings.

Installation
------------

To install the latest stable version of *analytix*, use the following
command:

.. code:: sh

   pip install analytix

You can also install the latest development version using the following
command:

.. code:: sh

   pip install git+https://github.com/parafoxia/analytix

You may need to prefix these commands with a call to the Python
interpreter depending on your OS and Python configuration.

Additional support
------------------

You can also install *analytix* with additional libraries to provide
extra functionality:

-  ``analytix[arrow]`` — *Apache Arrow* support (including Feather and Parquet files)
-  ``analytix[dev]`` — development dependencies
-  ``analytix[excel]`` — support for exporting reports to *Excel*
   spreadsheets
-  ``analytix[modin]`` — *Modin* support (note: this installs **all**
   engines; if you want to use a specific engine, you will need to do so
   manually)
-  ``analytix[pandas]`` — *pandas* support (``analytix[df]`` does the
   same, but is deprecated)
-  ``analytix[types]`` — type stubs for type-hinted projects

To install multiple at once, use commas:

.. code:: sh

   pip install "analytix[excel,modin,types]

OAuth authentication
--------------------

All requests to the YouTube Analytics API need to be authorised through
OAuth 2. In order to do this, you will need a Google Developers project
with the YouTube Analytics API enabled. You can find instructions on how
to do that in the `API setup
guide <https://analytix.readthedocs.io/en/latest/guides/console.html>`__,
or on `this video <https://www.youtube.com/watch?v=1Xday10ZWeg>`__.

When *analytix* boots up for the first time, it will display a link and
ask for a code. You’ll need to follow that link, run through all the
steps, and enter the code to authorise it. Once that’s done, *analytix*
saves the tokens to the disk (if you plan to run *analytix* on a server,
make sure these are in a safe place). This includes your refresh token,
which *analytix* will automatically use to refresh your access token
when needed.

This means you should only have to authorise *analytix*, at most, every
week. More details regarding how and when refresh tokens expire can be
found on the `Google Identity
documentation <https://developers.google.com/identity/protocols/oauth2#expiration>`__.

Logging
-------

If you want to see what *analytix* is doing, you can enable the packaged
logger:

.. code:: py

   import analytix

   analytix.setup_logging()

If anything is going wrong, or *analytix* appears to be taking a long
time to fetch data, try enabling the logger in DEBUG mode.

Usage
-----

Retrieving reports from the YouTube Analytics API is easy. The below
example loads credentials from a secrets file, and gets as much
information as possible from the last 28 days:

.. code:: py

   from analytix import Analytics

   client = Analytics.with_secrets("./secrets.json")
   report = client.retrieve(dimensions=("day",))
   report.to_csv("./analytics.csv")

This can also be done asynchronously:

.. code:: py

   import datetime as dt

   from analytix import AsyncAnalytics

   client = await AsyncAnalytics.with_secrets("./secrets.json")
   report = await client.retrieve(
       dimensions=("country",),
       start_date=dt.date.today() - dt.timedelta(days=7),
   )
   await report.to_csv("./async-analytics.csv")

If you want to analyse this data using additional tools such as
*pandas*, you can directly export the report as a DataFrame (note that
*pandas* is an optional dependency – `see
above <#additional-support>`__):

.. code:: py

   df = report.to_dataframe()

To read up further, `have a look at the
documentation <https://analytix.readthedocs.io>`__, or `have a look at
some
examples <https://github.com/parafoxia/analytix/tree/main/examples>`__.

Contributing
------------

Contributions are very much welcome! To get started:

-  Familiarise yourself with the `code of
   conduct <https://github.com/parafoxia/analytix/blob/main/CODE_OF_CONDUCT.md>`__
-  Have a look at the `contributing
   guide <https://github.com/parafoxia/analytix/blob/main/CONTRIBUTING.md>`__

License
-------

The *analytix* module for Python is licensed under the `BSD 3-Clause
License <https://github.com/parafoxia/analytix/blob/main/LICENSE>`__.

.. |PyPi version| image:: https://img.shields.io/pypi/v/analytix.svg
   :target: https://pypi.python.org/pypi/analytix/
.. |PyPI - Status| image:: https://img.shields.io/pypi/status/analytix
   :target: https://pypi.python.org/pypi/analytix/
.. |Downloads| image:: https://pepy.tech/badge/analytix
   :target: https://pepy.tech/project/analytix
.. |GitHub last commit| image:: https://img.shields.io/github/last-commit/parafoxia/analytix
   :target: https://github.com/parafoxia/analytix
.. |License| image:: https://img.shields.io/github/license/parafoxia/analytix.svg
   :target: https://github.com/parafoxia/analytix/blob/main/LICENSE
.. |CI| image:: https://github.com/parafoxia/analytix/actions/workflows/ci.yml/badge.svg
   :target: https://github.com/parafoxia/analytix/actions/workflows/ci.yml
.. |Read the Docs| image:: https://img.shields.io/readthedocs/analytix
   :target: https://analytix.readthedocs.io/en/latest/index.html
.. |Maintainability| image:: https://api.codeclimate.com/v1/badges/8819bdebb2d4aa8dfcb7/maintainability
   :target: https://codeclimate.com/github/parafoxia/analytix/maintainability
.. |Test Coverage| image:: https://api.codeclimate.com/v1/badges/8819bdebb2d4aa8dfcb7/test_coverage
   :target: https://codeclimate.com/github/parafoxia/analytix/test_coverage

.. toctree::
    :maxdepth: 1
    :caption: Guides
    :glob:
    :hidden:

    guides/*

.. toctree::
    :maxdepth: 1
    :caption: Classes
    :glob:
    :hidden:

    api/classes/*

.. toctree::
    :maxdepth: 1
    :caption: Data and functions
    :glob:
    :hidden:

    api/data/*

.. toctree::
    :maxdepth: 1
    :caption: Additional information
    :glob:
    :hidden:

    info/*
