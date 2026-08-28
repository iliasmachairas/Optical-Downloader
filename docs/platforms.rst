Supported platforms
=====================

.. list-table::
   :header-rows: 1

   * - Platform
     - Collection ID
     - QA layer
     - Native resolution
   * - Sentinel-2 L2A
     - ``sentinel-2-l2a``
     - SCL (Scene Classification Layer)
     - 10 m
   * - Landsat 8/9 C2 L2
     - ``landsat-c2-l2``
     - QA_Pixel bitmask
     - 30 m

Band values follow each collection's own scaling convention:

* Sentinel-2 surface reflectance is scaled by 10000.
* Landsat Collection 2 Level-2 follows its own documented scale/offset.

Band selections
-----------------

Each platform exposes the same three band-selection presets, mapped to that
platform's own asset names:

* **RGB only** — Red, Green, Blue.
* **RGB + NIR + SWIR** — adds near-infrared and both shortwave-infrared bands.
* **All bands** — every optical band the collection provides (excluding
  thermal/panchromatic).
