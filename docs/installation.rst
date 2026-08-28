Installation
============

Requirements
------------

* QGIS 3.0 or newer.
* No Planetary Computer account or API key — Sentinel-2 and Landsat are public,
  unauthenticated collections.

Installing the plugin
----------------------

From a ZIP file
^^^^^^^^^^^^^^^^

#. Build the ZIP with ``./build_plugin.sh`` from the plugin source, or download a
   release from the `GitHub repository
   <https://github.com/iliasmachairas/Optical-Downloader>`_.
#. In QGIS, open **Plugins -> Manage and Install Plugins -> Install from ZIP**.
#. Select the downloaded ZIP and click **Install Plugin**.

From the QGIS Plugin Repository
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Once published, search for **Optical Downloader** under **Plugins -> Manage and
Install Plugins** and click **Install Plugin**.

Python dependencies
--------------------

The plugin needs ``requests``, ``numpy``, and ``shapely`` on top of what QGIS
already ships (GDAL/OSGeo, PyQt):

.. code-block:: bash

   pip install -r requirements.txt

GDAL must be available to QGIS's own Python interpreter — it already is in any
standard QGIS install, so this step is normally only needed for the standalone
command-line workflow (see :doc:`usage`).
