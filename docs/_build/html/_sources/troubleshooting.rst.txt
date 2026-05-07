Troubleshooting
===============

Common issues
-------------

"No scenes found for the given date and AOI"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The STAC search returned no results.

**Possible causes and fixes:**

* The date is before the sensor launch (Sentinel-2: June 2015,
  Landsat 9: September 2021, Landsat 8: February 2013).
* The AOI is outside the sensor's coverage.
* The **Max cloud cover (tile %)** threshold is too strict — try raising it
  to 80 or 100 to check whether *any* scene exists at all.
* Try widening the search window with the **± days** spin box.

"Scene skipped — too cloudy over AOI"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A scene was found and the QA band was downloaded, but cloud/shadow pixels
over your AOI exceeded the **Max cloud tolerance (AOI %)** threshold.

**Fixes:**

* Raise the cloud tolerance.
* Pick a different date.
* Enable fewer cloud mask classes (e.g. uncheck *Thin cirrus* if it is not
  important for your analysis).

HTTP 503 / 504 errors
~~~~~~~~~~~~~~~~~~~~~

The Planetary Computer API is temporarily unavailable. The plugin retries
automatically up to 3 times with a 5-second delay. If all retries fail:

* Wait a few minutes and try again.
* Check the `Planetary Computer status page <https://planetarycomputer.microsoft.com>`_.

``ImportError: No module named 'shapely'``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``shapely`` package is not installed in QGIS's Python environment.

Open the **OSGeo4W Shell** and run:

.. code-block:: bash

   pip install shapely

Then restart QGIS.

``ImportError: No module named 'requests'``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Same cause and fix as above, but for ``requests``:

.. code-block:: bash

   pip install requests

Plugin not visible after installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Go to **Plugins → Manage and Install Plugins → Installed**.
2. Make sure **Optical Downloader** is ticked.
3. If it does not appear, restart QGIS and check again.
4. Verify the plugin folder name is exactly ``Optical-Downloader`` (with a
   hyphen, not an underscore).

Output GeoTIFF is all zeros / black
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

All pixels were masked as cloud or no-data. This can happen when:

* The cloud tolerance is very high but the SCL band incorrectly classifies
  land as cloud (common over bright surfaces such as snow or desert).
* The selected band combination does not match the sensor (e.g. Sentinel-2
  band names used with a Landsat scene).

Try unchecking some cloud classes or running without any masking first to
inspect the raw data.

Coordinates appear swapped (X / Y transposed)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Make sure you are entering coordinates in the correct fields:

* **Left / Right** = longitude (−180 to +180)
* **Bottom / Top** = latitude (−90 to +90)

If you used the Draw on map tool the coordinates are filled automatically and
should be correct.

Reading the log
---------------

All plugin events are written to the QGIS log:

**View → Panels → Log Messages → Optical Downloader**

The log includes the STAC query URL, the selected scene ID, per-band download
progress, and full Python tracebacks for any errors.

Reporting bugs
--------------

Please open an issue at:
https://github.com/iliasmachairas/Optical-Downloader/issues

Include:

* QGIS version (Help → About)
* Operating system
* The full error message from the log panel
* The AOI coordinates and date you used
