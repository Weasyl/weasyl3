Welcome to Weasyl 3!
====================

.. highlight:: console

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


Weasyl root CA certificate
--------------------------

Some of the below instructions require fetching from
<https://deploy.i.weasyl.com/>, which has a certificate signed by the Weasyl
root CA. This certificate is available at
<https://projects.weasyl.com/bin/uploads/ad/74/41/ad744132f16717f4c9f99ed91bce502a447286c3966d39b6ea855472ca790137.der>
and will probably have to be installed for some of these steps to not fail with
a certificate error.


Quickstart
----------

The easiest way to get Weasyl 3 running is to use `Vagrant`_ (1.6 or greater)
with `VirtualBox`_ (4.3.16 or greater). From inside the ``weasyl3`` directory,
simply run::

  $ make setup-vagrant

After libweasyl is cloned, Vagrant will fetch the base box, and then provision
the VM with all of the dependencies listed above. To start the server running,
one then runs::

  $ make host-run

Weasyl will then start running on <https://lo3.weasyl.com:28443/>.


Fetching packages from weasyl
-----------------------------

Weasyl publishes packages for python 3.4, nginx 1.6.0, and libxml2 2.9.0 for
Debian 7 systems, if one is more inclined to install the packages onto a local
Debian 7 system instead of into a VM::

  deb http://apt.i.weasyl.com/repos/apt/debian wheezy main

The signing key for the packages is available at
<https://deploy.i.weasyl.com/weykent-key.asc>.

ImageMagick is also available from Weasyl's apt repository, but the package
name is ``imagemagick-6.8.9``.


Non-Vagrant installation
------------------------

If one is more inclined to use one's system instead of a VM, first install all
of the dependencies listed above. Then, if it has not already been done, create
a postgres role for one's current user::

  $ sudo -u postgres createuser -drs $(whoami)

A database can then be created::

  $ createdb -O $(whoami) weasyl

And then the database can be populated::

  $ curl https://deploy.i.weasyl.com/weasyl-latest.sql.xz | xzcat | psql weasyl

It's safe to ignore any errors about a missing ``weasyl`` role.

The default ``development.ini`` file is mostly sufficient, but one line must be
edited::

  $ cp etc/development.ini.example etc/development.ini
  # change weasyl.static_root to point to $(pwd)/weasyl/static
  $ $EDITOR etc/development.ini

Finally, nginx must be placed in front of weasyl, with a self-signed
SSL certificate::

  $ mkdir ssl
  $ openssl req -subj '/CN=lo3.weasyl.com' -nodes -new -newkey rsa:2048 \
        -keyout ssl/weasyl3.key.pem -out ssl/weasyl3.req.pem
  $ openssl x509 -req -days 3650 -in /tmp/weasyl3.req.pem \
        -signkey ssl/weasyl3.key.pem -out ssl/weasyl3.crt.pem
  # /etc/nginx/sites-available might be in a different location on your system
  $ sudo cp etc/nginx.conf /etc/nginx/sites-available/weasyl3
  # fill in the paths to point to various places under $(pwd)
  $ sudo $EDITOR /etc/nginx/sites-available/weasyl3
  $ sudo ln -s /etc/nginx/sites-available/weasyl3 /etc/nginx/sites-enabled
  # this will vary depending on your OS
  $ sudo service nginx reload

Optionally, but recommended, install a local copy of libweasyl::

  $ make install-libweasyl

If ``pyvenv`` is on ``$PATH``, all that's required is::

  $ make run

Otherwise, ``PYVENV`` must be specified to ``make``. For example, if
``pyvenv-3.4`` is on ``$PATH`` instead::

  $ make run PYVENV=pyvenv-3.4

Now, Weasyl 3 should be running on <https://lo3.weasyl.com:8443/>.


.. _nodesource: https://github.com/nodesource/distributions
.. _Vagrant: http://www.vagrantup.com
.. _VirtualBox: https://www.virtualbox.org
