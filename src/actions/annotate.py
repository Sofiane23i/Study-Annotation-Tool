import os
import tkinter as tk
from PIL import Image, ImageTk
from tkinter import messagebox
import state as S
from .generate_annotation import annotation_file
from .import_annotation import import_annotaion
from .refreshing import refreshing


def annotate():
    """Render annotation UI inside main interface if container exists, else fallback to Toplevel."""
    parent = getattr(S, 'annotation_body', None)
    use_embed = parent is not None

    if use_embed:
        # Clear previous content
        for w in parent.winfo_children():
            w.destroy()
        container = parent
        S.r = container  # maintain existing references
    else:
        S.r = tk.Toplevel()
        S.r.title("Words Annotation")
        container = S.r

    canvas1 = tk.Canvas(container, height=1500, width=1500, bg='#f7f9fc')
    canvas1.pack(fill=tk.BOTH, expand=True)

    # Add Back to Detection button at the top if embedded
    back_btn_window = None
    if use_embed and hasattr(S, 'back_to_detection_from_annotation'):
        back_btn = tk.Button(canvas1, text="⬅ Back to Detection", 
                  command=S.back_to_detection_from_annotation,
                  bg='#6c757d', fg='white', font=('Segoe UI', 10, 'bold'),
                  padx=12, pady=5)
        back_btn_window = canvas1.create_window(10, 10, anchor=tk.NW, window=back_btn)

    yscrollbar = tk.Scrollbar(canvas1)
    yscrollbar.grid(row=0, column=1, sticky=tk.N+tk.S)

    canvas = tk.Canvas(canvas1, bd=0, yscrollcommand=yscrollbar.set, bg='#ffffff', highlightthickness=0)
    canvas.config(height=1000, width=1300, scrollregion=(0, 0, 1500, 2000))

    yscrollbar.config(command=canvas.yview)

    button1 = tk.Button(canvas, text="generateAnnotation", command=annotation_file)

    canvas2 = tk.Canvas(canvas1, bd=0, yscrollcommand=yscrollbar.set, bg='#ffffff', highlightthickness=0)
    button2 = tk.Button(canvas2, text="importAnnotation", command=import_annotaion)
    button2.grid(row=0, column=2, sticky="ns", padx=5, pady=55)

    S.text_box = tk.Text(canvas2, height=40, width=30)
    S.text_box.grid(row=1, column=2, sticky="ns", padx=5, pady=55)

    button3 = tk.Button(canvas2, text="refresh", command=refreshing)
    button3.grid(row=2, column=2, sticky="ns", padx=5, pady=55)

    frame = tk.Frame(canvas2)
    sb = tk.Scrollbar(frame)
    sb.pack(side=tk.RIGHT, fill=tk.BOTH)
    S.text_box.config(yscrollcommand=sb.set)
    sb.config(command=S.text_box.yview)

    # Position canvases - offset if back button exists
    start_y = 50 if back_btn_window else 0
    canvas.place(x=0, y=start_y)
    canvas2.place(x=1310, y=start_y)

    out_dir = getattr(S, 'directoryout', None)
    if not out_dir:
        out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'gan_output_data', 'out'))
        S.directoryout = out_dir
    os.makedirs(out_dir, exist_ok=True)

    crop_files = sorted([f for f in os.listdir(out_dir) if f.lower().endswith('.png')])
    if not crop_files:
        messagebox.showinfo("No word crops", "No cropped words found. Run word detection first.")
        return

    img2 = []
    rowindex = 0
    colindex = 0
    cpt = 0
    S.entries = []
    S.entryText = []

    ent = 0
    for fname in crop_files:
        file_path = os.path.join(out_dir, fname)
        if cpt == 10:
            colindex = (colindex + 130)
            cpt = 0
            rowindex = 0
        try:
            thumb = Image.open(file_path).resize((100, 100))
        except Exception:
            continue
        img2.append(ImageTk.PhotoImage(thumb))
        canvas.create_image(rowindex, colindex, anchor=tk.NW, image=img2[-1])

        S.entryText.append(tk.StringVar())
        S.entries.append(tk.Entry(container, width=13, textvariable=S.entryText[ent]))

        canvas.create_window(rowindex + 55, colindex + 110, window=S.entries[-1])

        rowindex = (rowindex + 130)
        cpt = cpt + 1
        ent = ent + 1

    button1_window = canvas.create_window(rowindex + 55, colindex + 110, anchor=tk.NW, window=button1)

    # --- Autofill logic for both GAN mode and Load mode ---
    import tkinter.messagebox as messagebox
    import state as Sstate
    
    # Determine the input mode and get the appropriate text
    current_mode = S.input_mode_var.get() if hasattr(S, 'input_mode_var') else 'load'
    input_text = None
    
    if current_mode == 'generate':
        # GAN mode: use gan_input_text
        input_text = getattr(Sstate, 'gan_input_text', None)
    else:
        # Load mode: get text from input_text_area widget
        if hasattr(S, 'input_text_area') and S.input_text_area:
            input_text = S.input_text_area.get("1.0", "end-1c").strip()
        elif hasattr(S, 'input_text') and S.input_text:
            input_text = S.input_text.strip()
    
    if input_text:
        try:
            # Extract words from the input text
            words_in_order = []
            for input_line in input_text.splitlines():
                if input_line.strip() == "":
                    continue
                parts = input_line.strip().split()
                for w in parts:
                    if w:
                        words_in_order.append(w)

            # Fill entries with the words in order; tolerate mismatches by filling what we can
            total_entries = len(S.entries)
            if not words_in_order:
                messagebox.showwarning("Annotation", "No words extracted from input text to autofill annotations.")
            else:
                fill_count = min(total_entries, len(words_in_order))
                for i in range(fill_count):
                    try:
                        entry = S.entries[i]
                        word = words_in_order[i]
                        entry.delete(0, tk.END)
                        entry.insert(0, word)
                    except Exception:
                        continue

                # Populate the side text box with the extracted words (one per line)
                S.text_box.delete("1.0", tk.END)
                S.text_box.insert(tk.END, "\n".join(words_in_order))

                # Info message if counts mismatch
                if len(words_in_order) != total_entries:
                    messagebox.showinfo("Annotation Autofill", f"Autofill applied for {fill_count} fields.\\nInput words: {len(words_in_order)}, detected words: {total_entries}.")

        except Exception as e:
            print(f"Autofill failed: {e}")

    S.r.mainloop()
