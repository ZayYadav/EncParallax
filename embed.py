from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from PIL import Image
import os, sys, zipfile

lib_path = sys.argv[1]       # user uploaded .so
output_dir = sys.argv[2]     # user folder, e.g., /uploads/<chat_id>

png_path = "PngParallax.png"   # root PNG
key = b"ParallaxOwner123"

# read .so
with open(lib_path, "rb") as f:
    lib_data = f.read()

cipher = AES.new(key, AES.MODE_ECB)
encrypted = cipher.encrypt(pad(lib_data, 16))
size = len(encrypted).to_bytes(8, "big")
payload = size + encrypted

# embed into PNG
img = Image.open(png_path)
pixels = img.load()
bits = "".join(format(b,"08b") for b in payload)
w,h = img.size
bit_index=0
for y in range(h):
    for x in range(w):
        if bit_index>=len(bits): break
        r,g,b = pixels[x,y]
        r = (r&~1)|int(bits[bit_index]); bit_index+=1
        if bit_index<len(bits): g = (g&~1)|int(bits[bit_index]); bit_index+=1
        if bit_index<len(bits): b = (b&~1)|int(bits[bit_index]); bit_index+=1
        pixels[x,y]=(r,g,b)
    if bit_index>=len(bits): break

# save PNG
user_png = os.path.join(output_dir,"LibEnc.png")
img.save(user_png)

# ZIP
zip_path = os.path.join(output_dir,"LibEnc.zip")
with zipfile.ZipFile(zip_path,"w") as zf:
    zf.write(user_png,arcname="LibEnc.png")

print("✅ ZIP ready →", zip_path)
