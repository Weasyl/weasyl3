Welcome to Weasyl 3!
====================

Weasyl 3 is the latest and greatest iteration of the Weasyl project. Here are
the things that are necessary to develop on it:

- git (``git`` executable)
- python 3.4 or greater (``pyvenv`` or ``pyvenv-3.4`` executable;
  ``python3.4-venv`` package for debian-esque systems)
- sass 3.2 or greater (``sass`` executable; ``ruby-sass`` package for
  debian-esque systems)
- node 0.10.5 or greater and npm (``npm`` executable; ``npm`` package from
  `nodesource`_ on debian-esque systems)
- postgresql 9.1 or greater, including development headers and HSTORE
  (``postgresql-contrib-9.1`` and ``libpq-dev`` packages on debian-esque
  systems)
- libxml2 and libxslt, including development headers (``libxml2-dev`` and
  ``libxslt-dev`` packages on debian-esque systems)
- ImageMagick 6.8 or greater, including development headers
  (``libmagickcore-dev`` package on debian-esque systems)
- nginx 1.6.0 or greater
- memcached (not always required, but some site features do require it)


Quickstart
----------

The easiest way to get Weasyl 3 running is to use `Vagrant`_ with
`VirtualBox`_. From inside the ``weasyl3`` directory, simply run::

  vagrant up

Vagrant will fetch the base box, and then provision the VM with all of the
dependencies listed above. To start the server running, one then simply runs::

  vagrant ssh

Then, from inside the VM::

  cd weasyl3
  make run PYVENV=pyvenv-3.4

Weasyl will then start running on <https://lo3.weasyl.com:28443/>.


Fetching packages from weasyl
-----------------------------

Weasyl publishes packages for python 3.4 and nginx 1.6.0 for Debian 7 systems,
if one is more inclined to install the packages onto a local Debian 7 system
instead of into a VM::

  deb http://apt.i.weasyl.com/repos/apt/debian wheezy main

The signing key for the packages is available at
<https://deploy.i.weasyl.com/weykent-key.asc>.

ImageMagick is also available from Weasyl's apt repository, but the package
name is ``imagemagick-6.8.9``.


.. _nodesource: https://github.com/nodesource/distributions
.. _Vagrant: http://www.vagrantup.com
.. _VirtualBox: https://www.virtualbox.org
