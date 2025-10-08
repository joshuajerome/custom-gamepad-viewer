# save as tools/make_ico.py and run: python tools/make_ico.py logo.png packaging/windows/CustomGamepadViewer.ico
import sys
from PIL import Image

src = sys.argv[1]
dst = sys.argv[2]
sizes = [(256,256),(128,128),(64,64),(48,48),(32,32),(24,24),(16,16)]

img = Image.open(src).convert("RGBA")
# Ensure square; add padding if needed
w, h = img.size
if w != h:
    side = max(w, h)
    bg = Image.new("RGBA", (side, side), (0,0,0,0))
    bg.paste(img, ((side-w)//2, (side-h)//2))
    img = bg

img.save(dst, sizes=sizes)
print("Wrote", dst)
