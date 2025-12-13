import os
import tkinter as tk
from tkinter import simpledialog, messagebox
from PIL import Image, ImageTk
import json
import state as S

def character_annotate():
    S.r = tk.Toplevel()
    S.r.title("Character Annotation")

    canvas = tk.Canvas(S.r, width=800, height=600, bg='gray')
    canvas.pack(fill=tk.BOTH, expand=True)

    # Load word images
    word_img_dir = S.directoryout if hasattr(S, 'directoryout') else None
    if not word_img_dir or not os.path.isdir(word_img_dir):
        messagebox.showerror("Error", "Word images directory not found.")
        S.r.destroy()
        return
    word_imgs = [os.path.join(word_img_dir, f) for f in os.listdir(word_img_dir) if f.endswith('.png')]
    if not word_imgs:
        messagebox.showerror("Error", "No word images found.")
        S.r.destroy()
        return
    
    img_idx = 0
    boxes = []
    current_img = None
    tk_img = None

    def load_image(idx):
        nonlocal current_img, tk_img
        current_img = Image.open(word_imgs[idx])
        tk_img = ImageTk.PhotoImage(current_img.resize((800, 600)))
        canvas.delete('all')
        canvas.create_image(0, 0, anchor=tk.NW, image=tk_img)
        S.r.title(f"Character Annotation - {os.path.basename(word_imgs[idx])}")
        for box in boxes:
            if box['img_idx'] == idx:
                draw_box(box)

    def draw_box(box):
        x1, y1, x2, y2 = box['coords']
        canvas.create_rectangle(x1, y1, x2, y2, outline='red', width=2)
        canvas.create_text(x1+5, y1+10, anchor=tk.NW, text=box['label'], fill='yellow', font=('Arial', 12, 'bold'))

    start = [None, None]
    rect = [None]

    def on_mouse_down(event):
        start[0], start[1] = event.x, event.y
        rect[0] = canvas.create_rectangle(event.x, event.y, event.x, event.y, outline='red', width=2)

    def on_mouse_drag(event):
        if rect[0]:
            canvas.coords(rect[0], start[0], start[1], event.x, event.y)

    def on_mouse_up(event):
        if rect[0]:
            x1, y1, x2, y2 = start[0], start[1], event.x, event.y
            label = simpledialog.askstring("Character Label", "Enter character:")
            if label:
                box = {'img_idx': img_idx, 'coords': (x1, y1, x2, y2), 'label': label}
                boxes.append(box)
                draw_box(box)
            canvas.delete(rect[0])
            rect[0] = None

    def save_annotations():
        # Export in COCO format (minimal)
        coco = {'images': [], 'annotations': [], 'categories': []}
        cat_map = {}
        cat_id = 1
        ann_id = 1
        for idx, img_path in enumerate(word_imgs):
            img_id = idx + 1
            img = Image.open(img_path)
            coco['images'].append({
                'id': img_id,
                'file_name': os.path.basename(img_path),
                'width': img.width,
                'height': img.height
            })
            for box in [b for b in boxes if b['img_idx'] == idx]:
                label = box['label']
                if label not in cat_map:
                    cat_map[label] = cat_id
                    coco['categories'].append({'id': cat_id, 'name': label})
                    cat_id += 1
                x1, y1, x2, y2 = box['coords']
                x, y = min(x1, x2), min(y1, y2)
                w, h = abs(x2 - x1), abs(y2 - y1)
                coco['annotations'].append({
                    'id': ann_id,
                    'image_id': img_id,
                    'category_id': cat_map[label],
                    'bbox': [x, y, w, h],
                    'area': w * h,
                    'iscrowd': 0
                })
                ann_id += 1
        save_path = tk.filedialog.asksaveasfilename(defaultextension='.json', filetypes=[('JSON', '*.json')])
        if save_path:
            with open(save_path, 'w') as f:
                json.dump(coco, f, indent=2)
            messagebox.showinfo("Saved", f"Annotations saved to {save_path}")

    def next_image():
        nonlocal img_idx
        if img_idx < len(word_imgs) - 1:
            img_idx += 1
            load_image(img_idx)

    def prev_image():
        nonlocal img_idx
        if img_idx > 0:
            img_idx -= 1
            load_image(img_idx)

    btn_frame = tk.Frame(S.r)
    btn_frame.pack(fill=tk.X)
    tk.Button(btn_frame, text='Prev', command=prev_image).pack(side=tk.LEFT)
    tk.Button(btn_frame, text='Next', command=next_image).pack(side=tk.LEFT)
    tk.Button(btn_frame, text='Save Annotations', command=save_annotations).pack(side=tk.RIGHT)

    canvas.bind('<ButtonPress-1>', on_mouse_down)
    canvas.bind('<B1-Motion>', on_mouse_drag)
    canvas.bind('<ButtonRelease-1>', on_mouse_up)

    load_image(img_idx)
    S.r.mainloop()
