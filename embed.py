from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from PIL import Image
import os

# ---------- CONFIGURATION ----------
SOURCE_PNG = "PngParallax.png"   # will be downloaded by workflow
LIB_FILE = "lib.so"               # must be in repo root
OUTPUT_PNG = "stego.png"
KEY = b"ParallaxOwner123"         # 16 bytes AES key
# ----------------------------------

def main():
    # 1. Read the library file
    with open(LIB_FILE, "rb") as f:
        lib_data = f.read()

    # 2. AES encrypt (ECB mode)
    cipher = AES.new(KEY, AES.MODE_ECB)
    encrypted = cipher.encrypt(pad(lib_data, AES.block_size))

    # 3. Prepend length (8 bytes, big-endian)
    payload = len(encrypted).to_bytes(8, "big") + encrypted

    # 4. Convert payload to bits
    bits = "".join(format(b, "08b") for b in payload)

    # 5. Open PNG and embed bits into LSB of RGB channels
    img = Image.open(SOURCE_PNG)
    pixels = img.load()
    w, h = img.size

    bit_index = 0
    for y in range(h):
        for x in range(w):
            if bit_index >= len(bits):
                break
            r, g, b = pixels[x, y]

            r = (r & ~1) | int(bits[bit_index]); bit_index += 1
            if bit_index < len(bits):
                g = (g & ~1) | int(bits[bit_index]); bit_index += 1
            if bit_index < len(bits):
                b = (b & ~1) | int(bits[bit_index]); bit_index += 1

            pixels[x, y] = (r, g, b)
        if bit_index >= len(bits):
            break

    # 6. Save output image
    img.save(OUTPUT_PNG)
    print(f"✅ Parallax Encryption Done → {OUTPUT_PNG}")

if __name__ == "__main__":
    main()
