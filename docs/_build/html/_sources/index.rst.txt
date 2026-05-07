Optical Downloader
==================

A QGIS 3.0+ plugin that downloads cloud-masked satellite imagery from
**Sentinel-2 L2A** and **Landsat 8/9 Collection 2** via Microsoft Planetary
Computer's STAC API.

.. toctree::
   :maxdepth: 2
   :caption: Contents

   installation
   usage
   architecture
   troubleshooting

Overview
--------

Optical Downloader lets you select a date, draw an area of interest on the
QGIS map canvas, and receive a georeferenced, cloud-masked GeoTIFF — all
without leaving QGIS. The download runs in a background thread so the
interface stays responsive throughout.

**Supported platforms**

* Sentinel-2 L2A (10 m resolution)
* Landsat 8/9 Collection 2 Level-2 (30 m resolution)

**Key capabilities**

* Two-stage cloud filtering (STAC pre-filter + per-AOI tolerance check)
* Five maskable cloud classes using the Sentinel-2 SCL band
* Three band presets: RGB · RGB + NIR + SWIR · All bands
* Interactive rubber-band AOI drawing directly on the QGIS canvas
* Cloud statistics report saved alongside the output GeoTIFF

Source code
-----------

https://github.com/iliasmachairas/Optical-Downloader

Indices and tables
------------------

* :ref:`genindex`
* :ref:`search`
