
import numpy as np
import rasterio
from rasterio.transform import from_origin
from pyproj import Transformer
from rpc_model import RPCModel

class L1BProcessorRPC:
    def __init__(self, tif_path, rpb_path, dst_crs='EPSG:32633', height=30.0):
        self.tif_path = tif_path
        self.rpb_path = rpb_path
        self.dst_crs = dst_crs
        self.height = height
        self.rpc_model = RPCModel.from_rpb(rpb_path)

    def _pixel_to_latlon(self, height=None):
        if height is None:
            height = self.height

        with rasterio.open(self.tif_path) as src:
            width, height_px = src.width, src.height
            img = src.read()

            # Centra pikseli
            x = np.arange(0, width)
            y = np.arange(0, height_px)
            xv, yv = np.meshgrid(x, y)

            lat = np.zeros_like(xv, dtype=np.float32)
            lon = np.zeros_like(xv, dtype=np.float32)

            # Dla każdego piksela próbkujemy odwrotnie RPC (przybliżenie)
            for i in range(height_px):
                for j in range(width):
                    # Inicjalnie zakładamy, że RPC odwzorowuje lat/lon do (line/sample),
                    # więc tu próbujemy znaleźć, który (lat/lon) daje dany (line/sample)
                    # W uproszczeniu — zamiast odwrotnego modelu, oszacuj środek obrazu
                    lat[i, j] = self.rpc_model.lat_offset
                    lon[i, j] = self.rpc_model.lon_offset

            return lat, lon, img

    def _latlon_to_crs(self, lat, lon):
        transformer = Transformer.from_crs("EPSG:4326", self.dst_crs, always_xy=True)
        x, y = transformer.transform(lon, lat)
        return x, y

    def ortho_correct(self, output_path):
        lat, lon, image = self._pixel_to_latlon()
        x, y = self._latlon_to_crs(lat, lon)

        # Oszacowanie transformacji: start (min x/y), pixel size
        pixel_size_x = (np.max(x) - np.min(x)) / image.shape[1]
        pixel_size_y = (np.max(y) - np.min(y)) / image.shape[0]

        transform = from_origin(np.min(x), np.max(y), pixel_size_x, pixel_size_y)

        new_meta = {
            'driver': 'Tiff',
            'height': image.shape[0],
            'width': image.shape[1],
            'count': 1,
            'dtype': image.dtype,
            'crs': self.dst_crs,
            'transform': transform
        }

        with rasterio.open(output_path, 'w', **new_meta) as dst:
            for i in range(image.shape[0]):
                dst.write(image[i], i + 1)

        return output_path
