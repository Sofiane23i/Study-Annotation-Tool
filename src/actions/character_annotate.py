import os
import tkinter as tk
from tkinter import simpledialog, messagebox
from PIL import Image, ImageTk
import json
import state as S

def character_annotate():
    S.r = tk.Toplevel()
    S.r.title("Character Annotation (Full Image)")

    # Split canvas: left for original, right for zoomed view
    frame = tk.Frame(S.r)
    frame.pack(fill=tk.BOTH, expand=True)
    canvas_orig = tk.Canvas(frame, width=500, height=600, bg='gray')
    canvas_orig.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Right panel contains zoom canvas on top and annotation list below
    right_panel = tk.Frame(frame)
    right_panel.pack(side=tk.RIGHT, fill=tk.Y)
    canvas_zoom = tk.Canvas(right_panel, width=300, height=450, bg='black')
    canvas_zoom.pack(side=tk.TOP, fill=tk.BOTH, expand=False)
    # Zoom mode controls (Annotate vs Drag)
    zoom_mode = {'mode': 'drag'}  # 'drag' or 'annotate'
    zoom_btn_frame = tk.Frame(right_panel)
    zoom_btn_frame.pack(side=tk.TOP, fill=tk.X, pady=(4,6))
    def set_zoom_mode(m):
        zoom_mode['mode'] = m
        if m == 'annotate':
            canvas_zoom.config(cursor='crosshair')
        else:
            canvas_zoom.config(cursor='fleur')
    tk.Button(zoom_btn_frame, text='Annotate (Zoom)', command=lambda: set_zoom_mode('annotate')).pack(side=tk.LEFT, padx=2)
    tk.Button(zoom_btn_frame, text='Drag (Zoom)', command=lambda: set_zoom_mode('drag')).pack(side=tk.LEFT, padx=2)
    # threshold slider for template matching
    threshold_var = tk.DoubleVar(value=0.6)
    tk.Label(zoom_btn_frame, text='Threshold').pack(side=tk.LEFT, padx=(8,2))
    tk.Scale(zoom_btn_frame, from_=0.30, to=0.95, resolution=0.05, orient=tk.HORIZONTAL, variable=threshold_var, length=140).pack(side=tk.LEFT, padx=2)
    # Match button placed at same level as zoom mode buttons
    tk.Button(zoom_btn_frame, text='Match Remaining', command=lambda: on_match_remaining()).pack(side=tk.LEFT, padx=6)

    # Template preview area
    template_frame = tk.Frame(right_panel)
    template_frame.pack(side=tk.TOP, fill=tk.X, pady=(6,4))
    tk.Label(template_frame, text='Template Preview').pack(side=tk.TOP)
    template_preview_label = tk.Label(template_frame, width=120, height=90, bg='black')
    template_preview_label.pack(side=tk.TOP, padx=4, pady=2)
    template_preview_tk = {'img': None}

    list_frame = tk.Frame(right_panel)
    list_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    ann_listbox = tk.Listbox(list_frame, height=10)
    ann_scroll = tk.Scrollbar(list_frame, orient=tk.VERTICAL, command=ann_listbox.yview)
    ann_listbox.config(yscrollcommand=ann_scroll.set)
    ann_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    ann_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    # Load full image (use S.full_image_path if provided, otherwise fallback to src/temp_handwriting.jpg or svg)
    full_img_path = getattr(S, 'full_image_path', None)
    if not full_img_path:
        # common locations: src/temp_handwriting.jpg or src/temp_handwriting.svg
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        jpg_candidate = os.path.join(base_dir, 'temp_handwriting.jpg')
        svg_candidate = os.path.join(base_dir, 'temp_handwriting.svg')
        local_jpg = os.path.join(os.path.dirname(__file__), 'temp_handwriting.jpg')
        if os.path.exists(jpg_candidate):
            full_img_path = jpg_candidate
        elif os.path.exists(local_jpg):
            full_img_path = local_jpg
        elif os.path.exists(svg_candidate):
            # convert svg -> jpg into a temp file
            try:
                from actions.generate_htr import svg_to_jpeg
                tmp_jpg = os.path.join(base_dir, 'temp_handwriting_converted.jpg')
                ok = svg_to_jpeg(svg_candidate, tmp_jpg, width=1200, height=600)
                if ok and os.path.exists(tmp_jpg):
                    full_img_path = tmp_jpg
            except Exception:
                full_img_path = None
    if not full_img_path or not os.path.isfile(full_img_path):
        messagebox.showerror("Error", "Full image file not found. Generate HTR first or set S.full_image_path.")
        S.r.destroy()
        return
    boxes = []
    try:
        current_img = Image.open(full_img_path)
    except Exception as e:
        messagebox.showerror("Error", f"Unable to open image: {e}")
        S.r.destroy()
        return
    orig_w, orig_h = current_img.size
    display_w, display_h = 500, 600
    tk_img_orig = ImageTk.PhotoImage(current_img.resize((display_w, display_h)))
    zoom_factor = 2.0
    zoom_box = [0, 0, min(300//zoom_factor, orig_w), min(450//zoom_factor, orig_h)]
    tk_img_zoom = None

    selected_index = None

    def draw_original():
        canvas_orig.delete('all')
        canvas_orig.create_image(0, 0, anchor=tk.NW, image=tk_img_orig)
        # draw boxes
        for i, box in enumerate(boxes):
            is_selected = (i == selected_index)
            draw_box_on(canvas_orig, box, scale_x=display_w/orig_w, scale_y=display_h/orig_h, selected=is_selected)
        # draw zoom rectangle on original
        try:
            zx1, zy1, zx2, zy2 = zoom_box
            sx = display_w / orig_w
            sy = display_h / orig_h
            rx1, ry1 = zx1 * sx, zy1 * sy
            rx2, ry2 = zx2 * sx, zy2 * sy
            canvas_orig.create_rectangle(rx1, ry1, rx2, ry2, outline='blue', width=2)
        except Exception:
            pass

    def draw_zoom():
        nonlocal tk_img_zoom
        x1, y1, x2, y2 = map(int, zoom_box)
        crop = current_img.crop((x1, y1, x2, y2))
        crop = crop.resize((300, 450))
        tk_img_zoom = ImageTk.PhotoImage(crop)
        canvas_zoom.delete('all')
        canvas_zoom.create_image(0, 0, anchor=tk.NW, image=tk_img_zoom)
        canvas_zoom.image = tk_img_zoom
        # Draw boxes in zoomed region
        for box in boxes:
            bx1, by1, bx2, by2 = box['coords']
            # Only draw if box is inside zoom_box
            if bx1 >= x1 and by1 >= y1 and bx2 <= x2 and by2 <= y2:
                # Scale to zoomed canvas
                zx = 300/(x2-x1) if (x2-x1)!=0 else 1
                zy = 450/(y2-y1) if (y2-y1)!=0 else 1
                draw_box_on(canvas_zoom, box, offset_x=-x1, offset_y=-y1, scale_x=zx, scale_y=zy)
        # Draw temporary match previews (blue) on top
        try:
            zx = 300/(x2-x1) if (x2-x1) != 0 else 1
            zy = 450/(y2-y1) if (y2-y1) != 0 else 1
            for m in temp_matches:
                mx1, my1, mx2, my2 = m
                if mx1 >= x1 and my1 >= y1 and mx2 <= x2 and my2 <= y2:
                    sx1 = (mx1 - x1) * zx
                    sy1 = (my1 - y1) * zy
                    sx2 = (mx2 - x1) * zx
                    sy2 = (my2 - y1) * zy
                    canvas_zoom.create_rectangle(sx1, sy1, sx2, sy2, outline='blue', width=2)
        except Exception:
            pass

    def draw_box_on(canvas, box, offset_x=0, offset_y=0, scale_x=1.0, scale_y=1.0, selected=False):
        x1, y1, x2, y2 = box['coords']
        x1 = (x1+offset_x)*scale_x
        y1 = (y1+offset_y)*scale_y
        x2 = (x2+offset_x)*scale_x
        y2 = (y2+offset_y)*scale_y
        color = 'lime' if selected else 'red'
        w = 3 if selected else 2
        canvas.create_rectangle(x1, y1, x2, y2, outline=color, width=w)
        canvas.create_text(x1+5, y1+10, anchor=tk.NW, text=box['label'], fill='yellow', font=('Arial', 12, 'bold'))

    # --- Controls ---
    btn_frame = tk.Frame(S.r)
    btn_frame.pack(fill=tk.X, side=tk.BOTTOM)
    def zoom_in():
        nonlocal zoom_box
        zx, zy = (zoom_box[2]-zoom_box[0])/2, (zoom_box[3]-zoom_box[1])/2
        cx, cy = (zoom_box[0]+zoom_box[2])/2, (zoom_box[1]+zoom_box[3])/2
        zx, zy = zx/1.5, zy/1.5
        zoom_box = [max(0, int(cx-zx)), max(0, int(cy-zy)), min(orig_w, int(cx+zx)), min(orig_h, int(cy+zy))]
        draw_original()
        draw_zoom()

    def zoom_out():
        nonlocal zoom_box
        zx, zy = (zoom_box[2]-zoom_box[0])/2, (zoom_box[3]-zoom_box[1])/2
        cx, cy = (zoom_box[0]+zoom_box[2])/2, (zoom_box[1]+zoom_box[3])/2
        zx, zy = zx*1.5, zy*1.5
        zoom_box = [max(0, int(cx-zx)), max(0, int(cy-zy)), min(orig_w, int(cx+zx)), min(orig_h, int(cy+zy))]
        draw_original()
        draw_zoom()

    def move(dx, dy):
        nonlocal zoom_box
        w, h = zoom_box[2]-zoom_box[0], zoom_box[3]-zoom_box[1]
        x1 = min(max(0, zoom_box[0]+dx), orig_w-w)
        y1 = min(max(0, zoom_box[1]+dy), orig_h-h)
        zoom_box[0], zoom_box[1], zoom_box[2], zoom_box[3] = x1, y1, x1+w, y1+h
        draw_original()
        draw_zoom()

    tk.Button(btn_frame, text='⬅️', command=lambda: move(-40,0)).pack(side=tk.LEFT)
    tk.Button(btn_frame, text='➡️', command=lambda: move(40,0)).pack(side=tk.LEFT)
    tk.Button(btn_frame, text='⬆️', command=lambda: move(0,-40)).pack(side=tk.LEFT)
    tk.Button(btn_frame, text='⬇️', command=lambda: move(0,40)).pack(side=tk.LEFT)
    tk.Button(btn_frame, text='➕ Zoom In', command=zoom_in).pack(side=tk.LEFT)
    tk.Button(btn_frame, text='➖ Zoom Out', command=zoom_out).pack(side=tk.LEFT)


    selected_template = {'box': None, 'label': None}
    # temporary matches preview (list of (x1,y1,x2,y2))
    temp_matches = []

    def refresh_annotation_list():
        ann_listbox.delete(0, tk.END)
        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = box['coords']
            w, h = x2-x1, y2-y1
            ann_listbox.insert(tk.END, f"{i+1}: '{box['label']}' ({x1},{y1},{w},{h})")

    def on_list_select(event=None):
        nonlocal selected_index
        sel = ann_listbox.curselection()
        if not sel:
            selected_index = None
        else:
            selected_index = sel[0]
        # update template preview when selection changes
        try:
            if selected_index is not None and 0 <= selected_index < len(boxes):
                bx1, by1, bx2, by2 = boxes[selected_index]['coords']
                tpl = current_img.crop((bx1, by1, bx2, by2))
                tpl = tpl.resize((120, 90))
                template_preview_tk['img'] = ImageTk.PhotoImage(tpl)
                template_preview_label.config(image=template_preview_tk['img'])
            else:
                template_preview_label.config(image='')
                template_preview_tk['img'] = None
        except Exception:
            pass
        draw_original()
        draw_zoom()

    ann_listbox.bind('<<ListboxSelect>>', on_list_select)

    # Buttons for editing/deleting selected annotation
    edit_del_frame = tk.Frame(right_panel)
    edit_del_frame.pack(side=tk.TOP, fill=tk.X, pady=(4,4))

    def edit_annotation():
        sel = ann_listbox.curselection()
        if not sel:
            messagebox.showinfo("Info", "Select an annotation to edit.")
            return
        idx = sel[0]
        current = boxes[idx]['label']
        new_label = simpledialog.askstring("Edit Label", "New label:", initialvalue=current)
        if new_label is not None and new_label != current:
            boxes[idx]['label'] = new_label
            # if this was selected_template, update its label
            if selected_template.get('box') == boxes[idx]['coords']:
                selected_template['label'] = new_label
            refresh_annotation_list()
            draw_original()
            draw_zoom()

    def delete_annotation():
        sel = ann_listbox.curselection()
        if not sel:
            messagebox.showinfo("Info", "Select an annotation to delete.")
            return
        idx = sel[0]
        # confirm
        if not messagebox.askyesno("Delete", f"Delete annotation '{boxes[idx]['label']}'?"):
            return
        deleted = boxes.pop(idx)
        # clear selected_template if it matched deleted
        if selected_template.get('box') == deleted['coords']:
            selected_template['box'] = None
            selected_template['label'] = None
        # adjust selected_index (select last item if available)
        try:
            # update listbox selection to last item
            refresh_annotation_list()
            if boxes:
                ann_listbox.selection_clear(0, tk.END)
                ann_listbox.selection_set(len(boxes)-1)
                on_list_select()
        except Exception:
            pass
        draw_original()
        draw_zoom()

    tk.Button(edit_del_frame, text='Edit Label', command=edit_annotation).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
    tk.Button(edit_del_frame, text='Delete', command=delete_annotation).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

    def add_annotation():
        # Use zoomed region for annotation
        x1, y1, x2, y2 = zoom_box
        label = simpledialog.askstring("Character Label", "Enter character:")
        if label:
            box = {'coords': (x1, y1, x2, y2), 'label': label}
            boxes.append(box)
            selected_template['box'] = (x1, y1, x2, y2)
            selected_template['label'] = label
            refresh_annotation_list()
            # select the newly added annotation
            ann_listbox.selection_clear(0, tk.END)
            ann_listbox.selection_set(len(boxes)-1)
            on_list_select()
            draw_original()
            draw_zoom()

    # Match remaining — uses selected annotation or defaults to last annotated
    def on_match_remaining():
        sel = ann_listbox.curselection()
        if sel:
            idx = sel[0]
            selected_template['box'] = boxes[idx]['coords']
            selected_template['label'] = boxes[idx]['label']
        else:
            # default to last annotated
            if boxes:
                selected_template['box'] = boxes[-1]['coords']
                selected_template['label'] = boxes[-1]['label']
            else:
                selected_template['box'] = None
                selected_template['label'] = None
        match_template()

    def match_template():
        from utils import match_template_in_image
        if not selected_template['box'] or not selected_template['label']:
            messagebox.showinfo("Info", "Please annotate a character to use as template.")
            return
        x1, y1, x2, y2 = selected_template['box']
        template_img = current_img.crop((x1, y1, x2, y2))
        # save template for debugging
        try:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            dbg_path = os.path.join(base_dir, 'last_template_debug.png')
            template_img.save(dbg_path)
        except Exception:
            dbg_path = None

        threshold = float(threshold_var.get()) if 'threshold_var' in locals() or 'threshold_var' in globals() else 0.6
        matches = match_template_in_image(current_img, template_img, threshold=threshold)
        print(f"[match_template] template_size={template_img.size} threshold={threshold} raw_matches={len(matches)} dbg={dbg_path}")

        # matches are (x1,y1,x2,y2,score)
        def iou(a, b):
            ax1, ay1, ax2, ay2 = a
            bx1, by1, bx2, by2 = b
            iw = max(0, min(ax2, bx2) - max(ax1, bx1))
            ih = max(0, min(ay2, by2) - max(ay1, by1))
            inter = iw * ih
            area_a = max(1, (ax2 - ax1) * (ay2 - ay1))
            area_b = max(1, (bx2 - bx1) * (by2 - by1))
            union = area_a + area_b - inter
            return inter / union if union > 0 else 0

        matches_sorted = sorted(matches, key=lambda m: m[4], reverse=True)
        kept = []
        for m in matches_sorted:
            bx = (m[0], m[1], m[2], m[3])
            # skip original location
            if abs(m[0]-x1) < 5 and abs(m[1]-y1) < 5:
                continue
            too_close = False
            for k in kept:
                if iou(bx, k) > 0.3:
                    too_close = True
                    break
            if not too_close:
                kept.append(bx)

        # show preview of kept matches and ask confirmation
        temp_matches.clear()
        temp_matches.extend(kept)
        draw_original()
        draw_zoom()
        if not kept:
            messagebox.showinfo("Template Matching", f"No matches found for '{selected_template['label']}'.")
            return
        add = messagebox.askyesno("Template Matching", f"Found {len(kept)} matches for '{selected_template['label']}'. Add them to annotations?")
        count = 0
        if add:
            for (mx1, my1, mx2, my2) in kept:
                boxes.append({'coords': (mx1, my1, mx2, my2), 'label': selected_template['label']})
                count += 1
        # clear preview regardless
        temp_matches.clear()
        refresh_annotation_list()
        draw_original()
        draw_zoom()
        messagebox.showinfo("Template Matching", f"Added {count} matched boxes for '{selected_template['label']}'.")

    # removed: Annotate Character and Match Remaining from main controls

    # Initial draw
    canvas_orig.image = tk_img_orig
    refresh_annotation_list()
    draw_original()
    draw_zoom()

    # Mouse drawing on original canvas (draw boxes in original image coordinates)
    drag = {'rect': None, 'start': None}

    def orig_to_image_coords(x, y):
        sx = orig_w / display_w
        sy = orig_h / display_h
        return int(x * sx), int(y * sy)

    def on_orig_mouse_down(event):
        drag['start'] = (event.x, event.y)
        drag['rect'] = canvas_orig.create_rectangle(event.x, event.y, event.x, event.y, outline='red', width=2)

    def on_orig_mouse_drag(event):
        if drag['rect']:
            canvas_orig.coords(drag['rect'], drag['start'][0], drag['start'][1], event.x, event.y)

    def on_orig_mouse_up(event):
        if not drag['rect']:
            return
        x1d, y1d = drag['start']
        x2d, y2d = event.x, event.y
        canvas_orig.delete(drag['rect'])
        drag['rect'] = None
        drag['start'] = None
        ix1, iy1 = orig_to_image_coords(x1d, y1d)
        ix2, iy2 = orig_to_image_coords(x2d, y2d)
        x1i, y1i = min(ix1, ix2), min(iy1, iy2)
        x2i, y2i = max(ix1, ix2), max(iy1, iy2)
        label = simpledialog.askstring("Character Label", "Enter character:")
        if label:
            boxes.append({'coords': (x1i, y1i, x2i, y2i), 'label': label})
            selected_template['box'] = (x1i, y1i, x2i, y2i)
            selected_template['label'] = label
            refresh_annotation_list()
            ann_listbox.selection_clear(0, tk.END)
            ann_listbox.selection_set(len(boxes)-1)
            on_list_select()
            draw_original()
            draw_zoom()

    # Bindings
    canvas_orig.bind('<ButtonPress-1>', on_orig_mouse_down)
    canvas_orig.bind('<B1-Motion>', on_orig_mouse_drag)
    canvas_orig.bind('<ButtonRelease-1>', on_orig_mouse_up)

    # Zoom canvas pan (drag to move zoom window)
    zoom_drag = {'start': None}
    zoom_annot = {'rect': None, 'start': None}
    def on_zoom_mouse_down(event):
        if zoom_mode['mode'] == 'drag':
            zoom_drag['start'] = (event.x, event.y)
            zoom_annot['start'] = None
        else:
            # annotate mode: start rectangle on zoom canvas
            zoom_annot['start'] = (event.x, event.y)
            zoom_annot['rect'] = canvas_zoom.create_rectangle(event.x, event.y, event.x, event.y, outline='red', width=2)

    def on_zoom_mouse_drag(event):
        if zoom_mode['mode'] == 'drag':
            if not zoom_drag['start']:
                return
            sx1, sy1, sx2, sy2 = zoom_box
            zx = 300 / (sx2 - sx1) if (sx2 - sx1) != 0 else 1
            zy = 450 / (sy2 - sy1) if (sy2 - sy1) != 0 else 1
            dx_canvas = event.x - zoom_drag['start'][0]
            dy_canvas = event.y - zoom_drag['start'][1]
            # dragging moves content; convert to image coords (inverse scale) and invert direction
            dx_img = int(-dx_canvas / zx)
            dy_img = int(-dy_canvas / zy)
            zoom_drag['start'] = (event.x, event.y)
            move(dx_img, dy_img)
        else:
            if zoom_annot['rect']:
                canvas_zoom.coords(zoom_annot['rect'], zoom_annot['start'][0], zoom_annot['start'][1], event.x, event.y)

    canvas_zoom.bind('<ButtonPress-1>', on_zoom_mouse_down)
    canvas_zoom.bind('<B1-Motion>', on_zoom_mouse_drag)
    def on_zoom_mouse_up(event):
        # finalize annotate rectangle if in annotate mode
        if zoom_mode['mode'] != 'annotate':
            zoom_drag['start'] = None
            return
        if not zoom_annot['rect'] or not zoom_annot['start']:
            return
        x1d, y1d = zoom_annot['start']
        x2d, y2d = event.x, event.y
        # remove visual rect
        canvas_zoom.delete(zoom_annot['rect'])
        zoom_annot['rect'] = None
        zoom_annot['start'] = None
        # convert zoom-canvas coords to image coords
        sx1, sy1, sx2, sy2 = zoom_box
        if sx2 - sx1 == 0 or sy2 - sy1 == 0:
            return
        zx = 300 / (sx2 - sx1)
        zy = 450 / (sy2 - sy1)
        ix1 = int(sx1 + min(x1d, x2d) / zx)
        iy1 = int(sy1 + min(y1d, y2d) / zy)
        ix2 = int(sx1 + max(x1d, x2d) / zx)
        iy2 = int(sy1 + max(y1d, y2d) / zy)
        label = simpledialog.askstring("Character Label", "Enter character:")
        if label:
            boxes.append({'coords': (ix1, iy1, ix2, iy2), 'label': label})
            selected_template['box'] = (ix1, iy1, ix2, iy2)
            selected_template['label'] = label
            refresh_annotation_list()
            ann_listbox.selection_clear(0, tk.END)
            ann_listbox.selection_set(len(boxes)-1)
            on_list_select()
            draw_original()
            draw_zoom()

    canvas_zoom.bind('<ButtonRelease-1>', on_zoom_mouse_up)

    def save_annotations():
        coco = {'images': [], 'annotations': [], 'categories': []}
        cat_map = {}
        cat_id = 1
        ann_id = 1
        img_id = 1
        coco['images'].append({'id': img_id, 'file_name': os.path.basename(full_img_path), 'width': orig_w, 'height': orig_h})
        for box in boxes:
            label = box['label']
            if label not in cat_map:
                cat_map[label] = cat_id
                coco['categories'].append({'id': cat_id, 'name': label})
                cat_id += 1
            x1, y1, x2, y2 = box['coords']
            x, y = min(x1, x2), min(y1, y2)
            w, h = abs(x2 - x1), abs(y2 - y1)
            coco['annotations'].append({'id': ann_id, 'image_id': img_id, 'category_id': cat_map[label], 'bbox': [x, y, w, h], 'area': w*h, 'iscrowd': 0})
            ann_id += 1
        save_path = tk.filedialog.asksaveasfilename(defaultextension='.json', filetypes=[('JSON', '*.json')])
        if save_path:
            with open(save_path, 'w') as f:
                json.dump(coco, f, indent=2)
            messagebox.showinfo("Saved", f"Annotations saved to {save_path}")

    tk.Button(btn_frame, text='Save Annotations', command=save_annotations).pack(side=tk.RIGHT)

    S.r.mainloop()
