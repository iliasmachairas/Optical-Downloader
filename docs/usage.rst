Usage
=====

Using the QGIS dialog
----------------------

#. Open the plugin from the toolbar icon or **Plugins -> Optical Downloader**.
#. Pick a **date** and a **+/- day search window**. The plugin searches Planetary
   Computer for the least-cloudy scene inside that window and picks the best one.
#. Choose **Sentinel-2 L2A** or **Landsat 8/9 C2 L2**.
#. Set the **cloud thresholds**:

   * *Max tile cloud cover* pre-filters the STAC search results.
   * *Max AOI cloud tolerance* strictly blocks the download if the scene's cloud
     cover over your area of interest exceeds it — the report is still written
     either way.
#. Tick the **cloud/shadow types** to mask out (SCL flags for Sentinel-2,
   QA_Pixel flags for Landsat).
#. Set the **area of interest**, either by typing coordinates (WGS-84 decimal
   degrees, EPSG:4326) directly, or by clicking **Draw on map** and dragging a
   rectangle on the canvas.
#. Choose a **band selection** — RGB only, RGB + NIR + SWIR, or all bands.
#. Pick an **output folder** and click **Run Download**.

The download runs in a background thread, so QGIS stays responsive while a
progress bar and status messages track each stage: querying the STAC API,
analysing cloud cover, downloading bands, applying the cloud mask, and saving
the GeoTIFF.

Output
------

.. list-table::
   :header-rows: 1

   * - File
     - Description
   * - ``{PLATFORM}_{DATE}_{TILE}_report.txt``
     - Cloud/shadow statistics and quality metrics for the selected scene
   * - ``{PLATFORM}_{DATE}_{TILE}_{BAND_SELECTION}.tif``
     - Multi-band georeferenced GeoTIFF

If the best available scene exceeds your cloud tolerance, only the report is
written — no GeoTIFF is produced for that run.

Command-line / batch use
--------------------------

For scripted or repeated downloads outside QGIS, edit ``config.py`` in the
plugin folder and run:

.. code-block:: bash

   python verify_config.py   # sanity-check the resolved date range first
   python main.py

This drives the exact same ``pipeline.py`` module the QGIS dialog uses, so
results are identical either way — it's just a different front end for the
same pipeline.
