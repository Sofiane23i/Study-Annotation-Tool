import os
import tkinter as tk
from PIL import Image, ImageTk
import state as S
from .generate_annotation import annotation_file
from .import_annotation import import_annotaion
from .refreshing import refreshing


def annotate():
    S.r = tk.Toplevel()
    S.r.title("Words Annotation")

    canvas1 = tk.Canvas(S.r, height=1500, width=1500)
    canvas1.pack()

    yscrollbar = tk.Scrollbar(canvas1)
    yscrollbar.grid(row=0, column=1, sticky=tk.N+tk.S)

    canvas = tk.Canvas(canvas1, bd=0, yscrollcommand=yscrollbar.set)
    canvas.config(height=1000, width=1300, scrollregion=(0, 0, 1500, 2000))

    yscrollbar.config(command=canvas.yview)

    button1 = tk.Button(canvas, text="generateAnnotation", command=annotation_file)

    canvas2 = tk.Canvas(canvas1, bd=0, yscrollcommand=yscrollbar.set)
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

    canvas.grid(row=0, column=0, sticky="ew")
    canvas2.grid(row=0, column=2)

    print(len(os.listdir(S.directoryout + '/')))

    img2 = []
    rowindex = 0
    colindex = 0
    cpt = 0
    S.entries = []
    S.entryText = []

    ent = 0
    for jj in range(S.nbr - len(os.listdir(S.directoryout + '/')), S.nbr):
        if cpt == 10:
            colindex = (colindex + 130)
            cpt = 0
            rowindex = 0
        img2.append(ImageTk.PhotoImage(Image.open(S.directoryout + '/' + str(jj) + '.png').resize((100, 100))))
        canvas.create_image(rowindex, colindex, anchor=tk.NW, image=img2[abs(S.nbr - len(os.listdir(S.directoryout + '/')) - jj)])

        S.entryText.append(tk.StringVar())
        S.entries.append(tk.Entry(S.r, width=13, textvariable=S.entryText[ent]))

        canvas.create_window(rowindex + 55, colindex + 110, window=S.entries[abs(S.nbr - len(os.listdir(S.directoryout + '/')) - jj)])

        rowindex = (rowindex + 130)
        cpt = cpt + 1
        ent = ent + 1

    button1_window = canvas.create_window(rowindex + 55, colindex + 110, anchor=tk.NW, window=button1)

    # --- GAN autofill logic using GAN input text but in 7-line batches ---
    import tkinter.messagebox as messagebox
    import state as Sstate
    if (not S.list_of_files or len(S.list_of_files) <= S.pos):
        try:
            gan_input = getattr(Sstate, 'gan_input_text', None)
            if gan_input:
                # Reuse the same wrapping logic as generate_htr to produce logical lines
                maxlen = 75
                wrapped_lines = []
                for input_line in gan_input.splitlines():
                    if input_line.strip() == "":
                        wrapped_lines.append("")
                        continue
                    words_line = input_line.split()
                    current_line = ""
                    for word in words_line:
                        add_len = len(word) + (1 if current_line else 0)
                        if len(current_line) + add_len <= maxlen:
                            current_line = (current_line + " " + word) if current_line else word
                        else:
                            if current_line:
                                wrapped_lines.append(current_line)
                            if len(word) > maxlen:
                                for i in range(0, len(word), maxlen):
                                    chunk = word[i:i+maxlen]
                                    wrapped_lines.append(chunk)
                                current_line = ""
                            else:
                                current_line = word
                    if current_line:
                        wrapped_lines.append(current_line)

                # Group into batches of 7 lines (matching GAN output batches)
                batch_size = 7
                batches = [wrapped_lines[i:i+batch_size] for i in range(0, len(wrapped_lines), batch_size)]

                # Extract words from batches in order (line by line)
                words_in_order = []
                for batch in batches:
                    for line in batch:
                        if line is None:
                            continue
                        parts = line.strip().split()
                        for w in parts:
                            if w:
                                words_in_order.append(w)

                # Fill entries with the words in order; tolerate mismatches by filling what we can
                total_entries = len(S.entries)
                if not words_in_order:
                    messagebox.showwarning("GAN Annotation", "No words extracted from GAN input to autofill annotations.")
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

                    # Warn if counts mismatch
                    if len(words_in_order) != total_entries:
                        messagebox.showwarning("GAN Annotation", f"Autofill applied for {fill_count} fields. GAN words: {len(words_in_order)}, annotation fields: {total_entries}.")

        except Exception as e:
            print(f"GAN batch autofill failed: {e}")

    S.r.mainloop()
