from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from PIL import Image
import os, sys, zipfile

lib_path = sys.argv[1]       # user uploaded .so
output_dir = sys.argv[2]     # user folder, e.g., /uploads/<chat_id>

# Ensure PngParallax.png is in the same directory where the script is executed
png_path = "PngParallax.png"   
key = b"ParallaxOwner123"

try:
    # 1. Read .so file
    with open(lib_path, "rb") as f:
        lib_data = f.read()

    # 2. Encrypt (Note: AES ECB mode is generally not recommended for high security)
    cipher = AES.new(key, AES.MODE_ECB)
    encrypted = cipher.encrypt(pad(lib_data, 16))
    size = len(encrypted).to_bytes(8, "big")
    payload = size + encrypted

    # 3. Embed into PNG
    # FIX: Converted to RGB to prevent crashes on indexed/RGBA PNGs
    img = Image.open(png_path).convert('RGB') 
    pixels = img.load()
    bits = "".join(format(b, "08b") for b in payload)
    
    w, h = img.size
    bit_index = 0
    
    # Check if payload exceeds image capacity (w * h * 3 bits max)
    if len(bits) > w * h * 3:
        print("Error: Image is too small to hold the payload.")
        sys.exit(1)

    for y in range(h):
        for x in range(w):
            if bit_index >= len(bits): break
            r, g, b = pixels[x, y]
            
            # Modify LSB (Least Significant Bit)
            r = (r & ~1) | int(bits[bit_index]); bit_index += 1
            if bit_index < len(bits): 
                g = (g & ~1) | int(bits[bit_index]); bit_index += 1
            if bit_index < len(bits): 
                b = (b & ~1) | int(bits[bit_index]); bit_index += 1
                
            pixels[x, y] = (r, g, b)
        if bit_index >= len(bits): break

    # 4. Save modified PNG
    user_png = os.path.join(output_dir, "LibEnc.png")
    img.save(user_png)

    # 5. Create ZIP
    zip_path = os.path.join(output_dir, "LibEnc.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # arcname prevents zipping the absolute path of the server
        zf.write(user_png, arcname="LibEnc.png")

    print(f"✅ ZIP ready → {zip_path}")
    sys.exit(0)

except Exception as e:
    print(f"Error: {str(e)}")
    sys.exit(1)
