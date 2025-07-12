import struct
import zlib
import binascii
import io
from typing import Tuple


class PNG:
    SIGNATURE = b"\x89PNG\r\n\x1a\n"
    
    @staticmethod
    def _chunk(tag: bytes, data: bytes) -> bytes:
        # returns a png chunk
        # tag is the type of the chunk (e.g. IHDR, IDAT, IEND)
        length = struct.pack("!I", len(data))
        crc = struct.pack("!I", binascii.crc32(tag + data) & 0xFFFFFFFF)
        return length + tag + data + crc

    @staticmethod
    def encode(width: int, height: int, pixels: bytes) -> bytes:
        assert 0 < width < 2 ** 31 and 0 < height < 2 ** 31, "Dimensions out of range"
        assert len(pixels) == width * height * 4, "Pixel buffer size mismatch"

        # Add filter byte 0 (None) to the start of each scan line
        stride = width * 4
        filtered = bytearray()
        for y in range(height):
            filtered.append(0)  # filter type None
            offset = y * stride
            filtered.extend(pixels[offset : offset + stride])

        compressed = zlib.compress(filtered, level=9)

        ihdr = PNG._chunk(
            b"IHDR",
            struct.pack("!IIBBBBB", width, height, 8, 6, 0, 0, 0),
        )
        idat = PNG._chunk(b"IDAT", compressed)
        iend = PNG._chunk(b"IEND", b"")

        return PNG.SIGNATURE + ihdr + idat + iend

    @staticmethod
    def decode(data: bytes) -> Tuple[int, int, bytes]:
        """Returns ``(width, height, rgba_bytes)``."""
        stream = io.BytesIO(data)
        assert stream.read(8) == PNG.SIGNATURE, "Missing PNG signature"

        width: int
        height: int
        compressed_parts = bytearray()

        while True:
            length_bytes = stream.read(4)
            if not length_bytes:
                break
            length = struct.unpack("!I", length_bytes)[0]
            tag = stream.read(4)
            chunk_data = stream.read(length)
            stream.read(4)  # TODO: CRC (ignored - could validate)

            if tag == b"IHDR":
                (width, height, bit_depth, color_type, c_method, f_method, i_method) = struct.unpack(
                    "!IIBBBBB", chunk_data
                )
                assert (bit_depth, color_type, c_method, f_method, i_method) == (8, 6, 0, 0, 0), "Unsupported PNG variant: only 8-bit RGBA, no interlace"
            elif tag == b"IDAT":
                compressed_parts.extend(chunk_data)
            elif tag == b"IEND":
                break  # done!

        assert width is not None, "IHDR chunk missing"

        raw = zlib.decompress(bytes(compressed_parts))
        stride = width * 4
        pixels = bytearray()
        offset = 0

        for _ in range(height):
            filter_type = raw[offset]
            assert filter_type == 0, "Unsupported filter %d (only None=0)" % filter_type
            offset += 1
            pixels.extend(raw[offset : offset + stride])
            offset += stride

        return width, height, bytes(pixels)

    @staticmethod
    def write(path: str, width: int, height: int, pixels: bytes) -> None:
        with open(path, "wb") as f:
            f.write(PNG.encode(width, height, pixels))

    @staticmethod
    def read(path: str) -> Tuple[int, int, bytes]:
        """Returns ``(width, height, rgba_bytes)``."""
        with open(path, "rb") as f:
            return PNG.decode(f.read())