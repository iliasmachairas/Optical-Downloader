Installation
============

Prerequisites
-------------

+---------------------+-------------------------------------------+
| Requirement         | Notes                                     |
+=====================+===========================================+
| QGIS ≥ 3.0          | Bundled with Python 3 and GDAL            |
+---------------------+-------------------------------------------+
| Python 3.x          | Provided by the QGIS installer            |
+---------------------+-------------------------------------------+
| GDAL                | Provided by the QGIS installer            |
+---------------------+-------------------------------------------+
| ``shapely``         | Must be installed separately (see below)  |
+---------------------+-------------------------------------------+
| ``requests``        | Must be installed separately (see below)  |
+---------------------+-------------------------------------------+

Installing Python dependencies
-------------------------------

Open the **OSGeo4W Shell** (available in the Start Menu after installing QGIS)
and run:

.. code-block:: bash

   pip install shapely requests

.. note::
   Do **not** use a regular terminal or Anaconda environment — the packages
   must be installed into the Python that QGIS uses.

Deploying the plugin
--------------------

Option 1 — Copy manually
~~~~~~~~~~~~~~~~~~~~~~~~~

Copy the ``Optical-Downloader/`` folder to the QGIS plugins directory:

.. code-block:: text

   C:\Users\<your-username>\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\

The folder name inside the plugins directory must be ``Optical-Downloader``.

Enabling the plugin
-------------------

1. Open QGIS.
2. Go to **Plugins → Manage and Install Plugins**.
3. Select the **Installed** tab.
4. Tick the checkbox next to **Optical Downloader**.

The plugin icon (|icon|) appears in the QGIS toolbar.

.. |icon| replace:: 🛰

