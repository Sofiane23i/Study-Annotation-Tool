import os
import cairosvg

svg = r'd:\HTR\Study-Annotation-Tool\src\gan_output_data\batch\batch_1.svg'
out_png = r'd:\HTR\Study-Annotation-Tool\src\gan_output_data\batch\test_cairosvg.png'
try:
    cairosvg.svg2png(url=svg, write_to=out_png, output_width=1200, output_height=600)
    size = os.path.getsize(out_png)
    print(f"SUCCESS: wrote {out_png} size={size} bytes")
    # Quick sanity: ensure file starts with PNG signature
    with open(out_png, 'rb') as f:
        sig = f.read(8)
    print(f"PNG sig: {sig}")
except Exception as e:
    print(f"ERROR: {e}")
    raise
