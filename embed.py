from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from PIL import Image
import sys
import os

# --- Configuration ---
SOURCE_PNG = "PngParallax.png"   # Carrier image
LIB_FILE = "libbgmi.so"          # File to hide
OUTPUT_PNG = "stego.png"         # Output image
KEY = b"ParallaxOwner123"        # 16-byte AES key
# --------------------

def main():
    # 1. File Existence Checks
    if not os.path.exists(LIB_FILE):
        print(f"❌ Error: {LIB_FILE} not found in the repository root.")
        sys.exit(1)
    if not os.path.exists(SOURCE_PNG):
        print(f"❌ Error: {SOURCE_PNG} not found. Workflow will download it.")
        sys.exit(1)

    print("✅ All required files found. Starting process...")

    # 2. Read and Encrypt the Library
    print(f"📖 Reading {LIB_FILE}...")
    with open(LIB_FILE, "rb") as f:
        lib_data = f.read()

    print(f"🔐 Encrypting with AES-ECB...")
    cipher = AES.new(KEY, AES.MODE_ECB)
    try:
        encrypted = cipher.encrypt(pad(lib_data, AES.block_size))
    except Exception as e:
        print(f"❌ Encryption failed: {e}")
        sys.exit(1)

    # 3. Prepare Payload: [8-byte length] + [encrypted data]
    payload = len(encrypted).to_bytes(8, "big") + encrypted

    # 4. Convert Payload to Binary String
    bits = "".join(format(b, "08b") for b in payload)
    data_len_bits = len(bits)
    print(f"📊 Total bits to embed: {data_len_bits}")

    # 5. Open Image and Check Capacity
    img = Image.open(SOURCE_PNG)
    pixels = img.load()
    width, height = img.size

    max_bits_capacity = width * height * 3
    if data_len_bits > max_bits_capacity:
        print(f"❌ Error: Image too small to hold the data.")
        print(f"   Capacity: {max_bits_capacity} bits, Required: {data_len_bits} bits.")
        print(f"   Please use a larger image.")
        sys.exit(1)

    # 6. Embed Data into LSB of RGB Pixels
    print(f"🖼️  Embedding data into {SOURCE_PNG}...")
    bit_index = 0
    for y in range(height):
        for x in range(width):
            if bit_index >= data_len_bits:
                break
            r, g, b = pixels[x, y]

            r = (r & ~1) | int(bits[bit_index]); bit_index += 1
            if bit_index < data_len_bits:
                g = (g & ~1) | int(bits[bit_index]); bit_index += 1
            if bit_index < data_len_bits:
                b = (b & ~1) | int(bits[bit_index]); bit_index += 1

            pixels[x, y] = (r, g, b)

    # 7. Save the Result
    img.save(OUTPUT_PNG)
    print(f"✨ Success! Steganography image saved as {OUTPUT_PNG}")

if __name__ == "__main__":
    main()
