Usage
=====

Opening the plugin
------------------

Click the **Optical Satellite Downloader** button in the QGIS toolbar, or
navigate to **Plugins → Optical Satellite Downloader** in the menu bar.

Step 1 — Define the Area of Interest
-------------------------------------

You can specify the area of interest (AOI) in two ways.

**Option A: Type coordinates manually**

Fill in the four coordinate fields (decimal degrees, WGS-84):

+----------+-------------------------------------+
| Field    | Meaning                             |
+==========+=====================================+
| Left     | Minimum longitude (western edge)    |
+----------+-------------------------------------+
| Right    | Maximum longitude (eastern edge)    |
+----------+-------------------------------------+
| Bottom   | Minimum latitude (southern edge)    |
+----------+-------------------------------------+
| Top      | Maximum latitude (northern edge)    |
+----------+-------------------------------------+

Example for central Athens, Greece::

   Left:   23.60   Right: 23.85
   Bottom: 37.85   Top:   38.05

**Option B: Draw on the map**

1. Click **Draw on map** — the dialog minimises and a blue rubber-band tool
   activates on the QGIS canvas.
2. Click and drag a rectangle over the area you want.
3. Release the mouse — coordinates fill automatically and the dialog reopens.

.. note::
   The drawing tool handles any map canvas CRS and converts the result to
   WGS-84 (EPSG:4326) automatically.

Step 2 — Pick a date
--------------------

Click a date in the calendar widget.

Use the **± days** spin box to widen the search window around that date
(default is 0, meaning the exact date only). Increasing it improves the chance
of finding a low-cloud scene.

Step 3 — Choose a platform
--------------------------

+--------------------+---------------------+--------------------+
| Radio button       | STAC collection     | Native resolution  |
+====================+=====================+====================+
| Sentinel-2         | sentinel-2-l2a      | 10 m               |
+--------------------+---------------------+--------------------+
| Landsat 8/9        | landsat-c2-l2       | 30 m               |
+--------------------+---------------------+--------------------+

Step 4 — Select bands
---------------------

+---------------------+---------------------------------------------+-----------------------------+
| Option              | Sentinel-2 bands                            | Landsat 8/9 bands           |
+=====================+=============================================+=============================+
| RGB only            | B04, B03, B02                               | B4, B3, B2                  |
+---------------------+---------------------------------------------+-----------------------------+
| RGB + NIR + SWIR    | B04, B03, B02, B08, B8A, B11, B12           | B4, B3, B2, B5, B6, B7      |
+---------------------+---------------------------------------------+-----------------------------+
| All bands           | B01–B12 (11 bands, excl. B10)               | B1–B7                       |
+---------------------+---------------------------------------------+-----------------------------+

Step 5 — Configure cloud masking
---------------------------------

**Cloud types to mask**

Check any combination of the five Sentinel-2 SCL classes you want excluded
from the output:

* Cloud shadows
* Clouds — low probability
* Clouds — medium probability
* Clouds — high probability
* Thin cirrus

Use **Select All** / **Unselect All** for quick toggling.

**Cloud thresholds**

+------------------------------------+----------------------------------------------------------+---------------+
| Field                              | Meaning                                                  | Default       |
+====================================+==========================================================+===============+
| Max cloud cover (tile %)           | STAC pre-filter. Scenes above this threshold are         | 20            |
|                                    | skipped before any download starts.                      |               |
+------------------------------------+----------------------------------------------------------+---------------+
| Max cloud tolerance (AOI %)        | After the QA band is loaded, if cloud/shadow pixels      | 10            |
|                                    | over your AOI exceed this %, the whole scene is skipped. |               |
+------------------------------------+----------------------------------------------------------+---------------+

Step 6 — Set the output folder
-------------------------------

Click **Browse** and pick a destination directory.

Output files saved there:

* ``<platform>_<tile-id>_<date>.tif`` — cloud-masked GeoTIFF
* ``report.txt`` — cloud statistics (created when the statistics option is on)

If a file with the same name already exists, a numeric suffix is appended
(e.g. ``…_1.tif``, ``…_2.tif``).

Step 7 — Run
------------

Click **Run Download**. The progress bar tracks each pipeline stage:

+----------+-------------------------------------------+
| Progress | Stage                                     |
+==========+===========================================+
| 5 %      | Initializing pipeline                     |
+----------+-------------------------------------------+
| 20 %     | STAC search                               |
+----------+-------------------------------------------+
| 40 %     | QA / SCL band loaded                      |
+----------+-------------------------------------------+
| 55 %     | Cloud analysis complete                   |
+----------+-------------------------------------------+
| 80 %     | Spectral bands downloaded                 |
+----------+-------------------------------------------+
| 90 %     | Cloud mask applied, bands stacked         |
+----------+-------------------------------------------+
| 100 %    | GeoTIFF saved                             |
+----------+-------------------------------------------+

On success a green notification appears in the QGIS message bar and the output
folder opens automatically.

If the scene is too cloudy a yellow warning is shown and no file is written.

Output format
-------------

The output GeoTIFF has the following properties:

* **CRS:** native UTM zone of the scene
* **Resolution:** 10 m (Sentinel-2) or 30 m (Landsat)
* **No-data value:** 0
* **Band names:** stored as band descriptions (visible in layer properties)
* **Cloud-masked pixels:** set to 0 (no-data)

Viewing logs
------------

Detailed per-step logging is available in
**View → Panels → Log Messages → Optical Downloader**.
