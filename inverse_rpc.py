import numpy as np
from pyproj import Transformer
from rpc_model import RPCModel
import rasterio
from rasterio.transform import from_origin
from rasterio.warp import transform

def rpc_inverse(rpc, line, sample, height_func, max_iter=10, tol=1e-3):
    lat = rpc.lat_offset
    lon = rpc.lon_offset

    for _ in range(max_iter):
        h = height_func(lat, lon)
        proj_line, proj_samp = rpc.project(lat, lon, h)
        delta_line = line - proj_line
        delta_samp = sample - proj_samp

        lat += delta_line * 1e-5
        lon += delta_samp * 1e-5

        if abs(delta_line) < tol and abs(delta_samp) < tol:
            break

    return lat, lon

def load_dem_function(dem_path):
    dem_src = rasterio.open(dem_path)
    dem_crs = dem_src.crs

    def get_height(lat, lon):
        lonlat = [(lon, lat)]
        if dem_crs.to_epsg() != 4326:
            x, y = Transformer.from_crs("EPSG:4326", dem_crs, always_xy=True).transform(lon, lat)
            coords = [(x, y)]
        else:
            coords = lonlat
        try:
            for val in dem_src.sample(coords):
                return float(val[0])
        except Exception:
            return 30.0  # fallback
    return get_height

def ortho_rpc_grid_with_dem(tif_path, rpb_path, dem_path, dst_crs="EPSG:32633", spacing=50):
    rpc = RPCModel.from_rpb(rpb_path)
    height_func = load_dem_function(dem_path)

    with rasterio.open(tif_path) as src:
        img = src.read()
        height_px, width_px = img.shape[1], img.shape[2]

        grid_lines = np.arange(0, height_px, spacing)
        grid_samples = np.arange(0, width_px, spacing)

        lat_grid = []
        lon_grid = []

        for i in grid_lines:
            row_lat = []
            row_lon = []
            for j in grid_samples:
                lat, lon = rpc_inverse(rpc, i, j, height_func)
                row_lat.append(lat)
                row_lon.append(lon)
            lat_grid.append(row_lat)
            lon_grid.append(row_lon)

        lat_grid = np.array(lat_grid)
        lon_grid = np.array(lon_grid)

        transformer = Transformer.from_crs("EPSG:4326", dst_crs, always_xy=True)
        x_grid, y_grid = transformer.transform(lon_grid, lat_grid)

        x_min, x_max = np.min(x_grid), np.max(x_grid)
        y_min, y_max = np.min(y_grid), np.max(y_grid)

        pixel_size_x = (x_max - x_min) / width_px
        pixel_size_y = (y_max - y_min) / height_px

        transform = from_origin(x_min, y_max, pixel_size_x, pixel_size_y)

        meta = {
            'driver': 'GTiff',
            'height': height_px,
            'width': width_px,
            'count': img.shape[0],
            'dtype': img.dtype,
            'crs': dst_crs,
            'transform': transform
        }

        with rasterio.open("output_rpc_dem_ortho.tif", "w", **meta) as dst:
            for i in range(img.shape[0]):
                dst.write(img[i], i+1)

    return "output_rpc_dem_ortho.tif"
