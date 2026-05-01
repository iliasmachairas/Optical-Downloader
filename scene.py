# -*- coding: utf-8 -*-
import os
import gc
import numpy as np
from osgeo import gdal, osr
from .aoi import AOI


class SentinelScene:
    def __init__(self, item, aoi: AOI, resolution=10, dtype="float32", fill_value=0.0):
        self.item          = item
        self.aoi           = aoi
        self.resolution    = resolution
        self.dtype         = dtype
        self.fill_value    = np.dtype(dtype).type(fill_value)
        self._epsg         = None
        self._bounds_ll    = None
        self._geotransform = None
        self._projection   = None

    def _get_epsg_and_bounds(self):
        if self._epsg is None:
            props = self.item.get("properties", {}) if isinstance(self.item, dict) \
                else getattr(self.item, "properties", {})
            self._epsg     = props.get("proj:epsg", 32632)
            self._bounds_ll = self.aoi.bounds
        return self._epsg, self._bounds_ll

    def _get_asset_url(self, band_name):
        assets = self.item.get("assets", {}) if isinstance(self.item, dict) \
            else getattr(self.item, "assets", {})
        if band_name not in assets:
            raise ValueError(
                f"Band '{band_name}' not found. Available: {list(assets.keys())}")
        asset = assets[band_name]
        return asset.get("href") if isinstance(asset, dict) else getattr(asset, "href", None)

    def _transform_bounds(self, src_epsg, dst_epsg, minx, miny, maxx, maxy):
        osr.UseExceptions()
        src = osr.SpatialReference()
        src.ImportFromEPSG(src_epsg)
        src.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
        dst = osr.SpatialReference()
        dst.ImportFromEPSG(dst_epsg)
        dst.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
        xform   = osr.CoordinateTransformation(src, dst)
        corners = [(minx,miny),(maxx,miny),(maxx,maxy),(minx,maxy)]
        pts     = [xform.TransformPoint(x, y)[:2] for x, y in corners]
        xs, ys  = [p[0] for p in pts], [p[1] for p in pts]
        return min(xs), min(ys), max(xs), max(ys)

    def load_bands(self, band_names, res=None):
        epsg, bounds_ll = self._get_epsg_and_bounds()
        res             = res or self.resolution
        bounds_target   = self._transform_bounds(4326, epsg, *bounds_ll)
        result          = {}

        for band_name in band_names:
            src_ds = None
            try:
                url    = self._get_asset_url(band_name)
                src_ds = gdal.Open(f"/vsicurl/{url}", gdal.GA_ReadOnly)
                if src_ds is None:
                    raise RuntimeError(f"GDAL could not open {band_name}: {gdal.GetLastErrorMsg()}")

                geo       = src_ds.GetGeoTransform()
                src_minx  = geo[0]
                src_maxx  = geo[0] + src_ds.RasterXSize * geo[1]
                src_maxy  = geo[3]
                src_miny  = geo[3] + src_ds.RasterYSize * geo[5]

                src_srs       = src_ds.GetSpatialRef()
                src_epsg_code = src_srs.GetAuthorityCode(None) if src_srs else None
                needs_reproj  = (src_epsg_code != str(epsg))

                if not needs_reproj:
                    tx, ty, tx2, ty2 = bounds_target
                    ix  = max(src_minx, tx);  iy  = max(src_miny, ty)
                    ix2 = min(src_maxx, tx2); iy2 = min(src_maxy, ty2)
                    bounds_use = (ix, iy, ix2, iy2) if ix < ix2 and iy < iy2 \
                                 else (src_minx, src_miny, src_maxx, src_maxy)
                else:
                    bounds_use = bounds_target

                dst_srs = osr.SpatialReference()
                dst_srs.ImportFromEPSG(epsg)

                warped = gdal.Warp('', src_ds, options=gdal.WarpOptions(
                    outputBounds=bounds_use,
                    outputBoundsSRS=f"EPSG:{epsg}",
                    xRes=res, yRes=res,
                    dstSRS=dst_srs if needs_reproj else None,
                    resampleAlg=gdal.GRA_Bilinear,
                    format='MEM',
                    outputType=gdal.GDT_Float32,
                ))
                if warped is None:
                    raise RuntimeError(f"gdal.Warp failed for {band_name}: {gdal.GetLastErrorMsg()}")

                bnd      = warped.GetRasterBand(1)
                nodata   = bnd.GetNoDataValue()
                data     = bnd.ReadAsArray().copy()

                if nodata is not None:
                    mask        = np.isnan(data) if np.isnan(nodata) else (data == nodata)
                    data[mask]  = self.fill_value

                data = data.astype(self.dtype)

                if self._geotransform is None:
                    self._geotransform = warped.GetGeoTransform()
                    wsrs = warped.GetSpatialRef()
                    if wsrs:
                        self._projection = wsrs.ExportToWkt()

                result[band_name] = data
                print(f"[Scene] Loaded {band_name}: {data.shape}")
                bnd = warped = None
                gc.collect()

            except Exception as e:
                print(f"[Scene] ERROR — {band_name}: {e}")
                raise
            finally:
                if src_ds:
                    src_ds.FlushCache()
                    src_ds = None
                gc.collect()

        return result

    def save_tiff(self, array, output_path, nodata_value=None, band_names=None):
        if self._geotransform is None or self._projection is None:
            raise ValueError("No geotransform — load at least one band first.")

        nd = nodata_value if nodata_value is not None else self.fill_value
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        if array.ndim == 2:
            arrays = [array]
            height, width = array.shape
        else:
            height, width, n = array.shape
            arrays = [array[:, :, i] for i in range(n)]

        dtype_map = {
            'uint8': gdal.GDT_Byte,   'uint16': gdal.GDT_UInt16,
            'int16': gdal.GDT_Int16,  'float32': gdal.GDT_Float32,
            'float64': gdal.GDT_Float64,
        }
        gdal_dtype = dtype_map.get(str(array.dtype), gdal.GDT_Float32)

        ds = gdal.GetDriverByName('GTiff').Create(
            output_path, width, height, len(arrays), gdal_dtype)
        if ds is None:
            raise RuntimeError(f"Failed to create: {output_path}")

        ds.SetGeoTransform(self._geotransform)
        ds.SetProjection(self._projection)

        try:
            for i, data in enumerate(arrays, 1):
                b = ds.GetRasterBand(i)
                b.WriteArray(data)
                if nd is not None:
                    b.SetNoDataValue(nd)
                if band_names and i <= len(band_names):
                    b.SetDescription(band_names[i - 1])
                b.FlushCache()
            ds = None
            print(f"[Scene] Saved: {output_path} ({len(arrays)} bands, {width}×{height})")
        except Exception as e:
            ds = None
            try:
                os.remove(output_path)
            except Exception:
                pass
            raise RuntimeError(f"Failed to write TIFF: {e}") from e
