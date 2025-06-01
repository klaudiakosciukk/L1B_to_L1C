
import numpy as np

class RPCModel:
    def __init__(self, metadata):
        self.metadata = metadata
        self._parse()

    @staticmethod
    def from_rpb(file_path):
        metadata = {}
        with open(file_path, 'r') as f:
            lines = f.readlines()

        current_key = None
        current_values = []

        key_aliases = {
            "LINENUMCOEF": "LINE_NUM_COEFF",
            "LINEDENCOEF": "LINE_DEN_COEFF",
            "SAMPNUMCOEF": "SAMP_NUM_COEFF",
            "SAMPDENCOEF": "SAMP_DEN_COEFF",
            "LATOFFSET": "LAT_OFFSET",
            "LONGOFFSET": "LONG_OFFSET",
            "HEIGHTOFFSET": "HEIGHT_OFFSET",
            "LINEOFFSET": "LINE_OFFSET",
            "SAMPOFFSET": "SAMP_OFFSET",
            "LATSCALE": "LAT_SCALE",
            "LONGSCALE": "LONG_SCALE",
            "HEIGHTSCALE": "HEIGHT_SCALE",
            "LINESCALE": "LINE_SCALE",
            "SAMPSCALE": "SAMP_SCALE"
        }

        for line in lines:
            line = line.strip().replace(");", "").replace(")", "").replace(";", "")
            if not line or line.startswith("satId") or line.startswith("bandId"):
                continue

            if '=' in line:
                if current_key and current_values:
                    metadata[current_key] = current_values
                    current_key = None
                    current_values = []

                key, value = line.split('=', 1)
                key = key.strip().replace(" ", "").replace("_", "").lower()
                key = key_aliases.get(key.upper(), key.upper())
                value = value.strip()

                if value.startswith('('):
                    current_key = key
                    value = value[1:]
                    current_values = [float(v) for v in value.replace(')', '').split(',') if v.strip()]
                else:
                    try:
                        metadata[key] = float(value)
                    except ValueError:
                        metadata[key] = value.strip().strip('"')
            else:
                if current_key:
                    current_values += [float(v) for v in line.split(',') if v.strip()]
                    metadata[current_key] = current_values

        return RPCModel(metadata)

    def _parse(self):
        md = self.metadata
        try:
            self.line_offset = float(md.get("LINE_OFFSET", 0))
            self.samp_offset = float(md.get("SAMP_OFFSET", 0))
            self.lat_offset = float(md.get("LAT_OFFSET", 0))
            self.lon_offset = float(md.get("LONG_OFFSET", 0))
            self.height_offset = float(md.get("HEIGHT_OFFSET", 0))

            self.line_scale = float(md.get("LINE_SCALE", 1))
            self.samp_scale = float(md.get("SAMP_SCALE", 1))
            self.lat_scale = float(md.get("LAT_SCALE", 1))
            self.lon_scale = float(md.get("LONG_SCALE", 1))
            self.height_scale = float(md.get("HEIGHT_SCALE", 1))

            self.line_num = [float(x) for x in md["LINE_NUM_COEFF"]]
            self.line_den = [float(x) for x in md["LINE_DEN_COEFF"]]
            self.samp_num = [float(x) for x in md["SAMP_NUM_COEFF"]]
            self.samp_den = [float(x) for x in md["SAMP_DEN_COEFF"]]

            assert all(len(lst) == 20 for lst in [self.line_num, self.line_den, self.samp_num, self.samp_den])
        except KeyError as e:
            raise ValueError(f"Missing key in RPB file: {e}. Please check if the RPB file is valid and contains all required coefficients.")
        except AssertionError:
            raise ValueError("RPC coefficient lists must contain exactly 20 values each.")

    def _poly(self, coeffs, lat, lon, h):
        terms = np.array([
            1, lat, lon, h,
            lat * lon, lat * h, lon * h,
            lat ** 2, lon ** 2, h ** 2,
            lon * lat * h,
            lat ** 3, lat * lon ** 2, lat * h ** 2,
            lon ** 3, lon * lat ** 2, lon * h ** 2,
            h ** 3, h * lat ** 2, h * lon ** 2
        ])
        return np.dot(coeffs, terms)

    def project(self, lat, lon, h):
        lat_n = (lat - self.lat_offset) / self.lat_scale
        lon_n = (lon - self.lon_offset) / self.lon_scale
        h_n = (h - self.height_offset) / self.height_scale

        l = self._poly(self.line_num, lat_n, lon_n, h_n) / self._poly(self.line_den, lat_n, lon_n, h_n)
        s = self._poly(self.samp_num, lat_n, lon_n, h_n) / self._poly(self.samp_den, lat_n, lon_n, h_n)

        line = l * self.line_scale + self.line_offset
        samp = s * self.samp_scale + self.samp_offset

        return line, samp
