Optical Downloader
====================

.. image:: _static/icon.png
   :width: 48px
   :align: left

Optical Downloader is a QGIS 3 plugin that searches `Microsoft Planetary Computer
<https://planetarycomputer.microsoft.com/>`_ for the least-cloudy Sentinel-2 L2A or
Landsat 8/9 Collection 2 L2 scene over an area and date you choose, applies
cloud/shadow masking, and writes a georeferenced multi-band GeoTIFF.

No account or API key is required — Sentinel-2 and Landsat are in Planetary
Computer's open, public collection tier, so the plugin searches and downloads
anonymously.

Plugin source: https://github.com/iliasmachairas/Optical-Downloader

.. toctree::
   :maxdepth: 2
   :caption: Contents

   installation
   usage
   platforms
