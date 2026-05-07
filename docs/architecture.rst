Architecture
============

High-level overview
--------------------

The plugin is split into a thin QGIS UI layer and a framework-independent
download pipeline. The UI layer owns all Qt and QGIS API calls; the pipeline
has no QGIS dependency and could be run from a plain Python script.

.. code-block:: text

   ┌─────────────────────────────────────────────────┐
   │                   QGIS UI layer                  │
   │                                                  │
   │  OpticalDownloader          (main plugin class)  │
   │  OpticalDownloaderDialog    (dialog + getters)   │
   │  ExtentDrawingTool          (rubber-band tool)   │
   └──────────────────────┬──────────────────────────┘
                          │  spawns
                          ▼
   ┌─────────────────────────────────────────────────┐
   │              DownloadWorker (QThread)            │
   │  emits: progress · message · finished · error   │
   └──────────────────────┬──────────────────────────┘
                          │  calls
                          ▼
   ┌─────────────────────────────────────────────────┐
   │         Download pipeline (pure Python)          │
   │                                                  │
   │  Optical_Downloader.run()                        │
   │    ├── AOI          (bounding box geometry)      │
   │    ├── SentinelSearch (STAC query)               │
   │    ├── SentinelScene  (band I/O, reproject)      │
   │    └── GeoTIFF output                            │
   └─────────────────────────────────────────────────┘

Module reference
----------------

optical_downloader.py
~~~~~~~~~~~~~~~~~~~~~

The main QGIS plugin class. Responsible for:

* Registering the toolbar action and menu entry via ``initGui()``
* Creating the dialog once and reusing it across runs
* Connecting all signal handlers (browse, draw, run, help)
* Launching ``DownloadWorker`` and routing its signals back to the dialog

optical_downloader_dialog.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A thin wrapper around the Qt Designer ``.ui`` file. Exposes typed getter
methods for every user input so that ``optical_downloader.py`` never has to
touch raw Qt widgets:

* ``get_platform()`` → ``"sentinel-2-l2a"`` or ``"landsat-c2-l2"``
* ``get_band_selection()`` → ``"rgb_only"`` / ``"rgb_nir_swir"`` / ``"all_bands"``
* ``get_excluded_flags()`` → list of SCL integer codes to mask
* ``get_aoi_coords()`` → ``(xmin, ymin, xmax, ymax)`` validated floats
* ``get_selected_date()`` → ``datetime.date``
* ``get_max_cloud_tile()`` / ``get_max_cloud_tol()`` → floats

extent_tool.py
~~~~~~~~~~~~~~

A ``QgsMapTool`` subclass that renders a live blue rectangle while the user
drags. On mouse release it:

1. Transforms both corners from the canvas CRS to EPSG:4326.
2. Normalises the bounds (handles right-to-left or bottom-to-top drags).
3. Calls the registered callback with ``(xmin, ymin, xmax, ymax)``.

worker.py
~~~~~~~~~

A ``QThread`` subclass. Runs ``Optical_Downloader.run()`` off the main thread
and translates return values / exceptions into four Qt signals:

+------------+--------------------------------------+
| Signal     | Payload                              |
+============+======================================+
| progress   | integer 0–100                        |
+------------+--------------------------------------+
| message    | status string                        |
+------------+--------------------------------------+
| finished   | dict with status / path / report     |
+------------+--------------------------------------+
| error      | traceback string                     |
+------------+--------------------------------------+

pipeline.py
~~~~~~~~~~~

Orchestrates the ten-step download workflow:

1. Build AOI geometry from four corner points.
2. Query STAC API for the scene with the lowest cloud cover.
3. Extract tile ID, acquisition date, and cloud cover metadata.
4. Instantiate ``SentinelScene``.
5. Load the QA / SCL band.
6. Calculate valid-pixel and cloud/shadow percentages over the AOI.
7. Optionally write a cloud statistics report.
8. Check cloud tolerance — skip if above threshold.
9. Download selected spectral bands.
10. Apply cloud mask, stack bands, save GeoTIFF.

**SCL flag mapping (Sentinel-2)**

+-------+---------------------------+
| Code  | Class                     |
+=======+===========================+
| 0     | No data                   |
+-------+---------------------------+
| 1     | Saturated / defective     |
+-------+---------------------------+
| 2     | Dark area pixels          |
+-------+---------------------------+
| 3     | Cloud shadows             |
+-------+---------------------------+
| 4     | Vegetation                |
+-------+---------------------------+
| 5     | Bare soils                |
+-------+---------------------------+
| 6     | Water                     |
+-------+---------------------------+
| 7     | Clouds — low probability  |
+-------+---------------------------+
| 8     | Clouds — medium prob.     |
+-------+---------------------------+
| 9     | Clouds — high probability |
+-------+---------------------------+
| 10    | Thin cirrus               |
+-------+---------------------------+
| 11    | Snow / ice                |
+-------+---------------------------+

search.py
~~~~~~~~~

Sends a POST request to the Planetary Computer STAC ``/search`` endpoint:

* Filters by AOI geometry, date range, and ``eo:cloud_cover``.
* Sorts results by ascending cloud cover and picks the first item.
* Signs all asset URLs using the Planetary Computer SAS token service.
* Retries up to 3 times (5-second back-off) on HTTP 503/504 and timeouts.

scene.py
~~~~~~~~

Handles all raster I/O:

* Opens remote Cloud-Optimised GeoTIFFs via GDAL ``/vsicurl/``.
* Reprojects and resamples to a common grid with ``gdal.Warp()``
  (bilinear resampling).
* Converts to the requested dtype (default ``float32``).
* Saves the final stack as a GTiff with band descriptions and a
  properly set geotransform and CRS.

aoi.py
~~~~~~

Wraps a GeoJSON bounding-box polygon in a Shapely geometry object and
exposes ``.bounds``, ``.centroid``, and ``.to_geojson`` properties.

External dependencies
---------------------

+----------------------------------------------+----------------------------------------------------+
| Dependency                                   | Used for                                           |
+==============================================+====================================================+
| Planetary Computer STAC API                  | Scene search and asset discovery                   |
+----------------------------------------------+----------------------------------------------------+
| Planetary Computer SAS signing service       | Authenticating COG download URLs                   |
+----------------------------------------------+----------------------------------------------------+
| GDAL ``/vsicurl/``                           | Streaming remote GeoTIFF reads without full copy   |
+----------------------------------------------+----------------------------------------------------+
| Shapely                                      | AOI polygon geometry and bounds extraction         |
+----------------------------------------------+----------------------------------------------------+
| NumPy                                        | Band array masking and stacking                    |
+----------------------------------------------+----------------------------------------------------+
