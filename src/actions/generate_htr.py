import tkinter as tk
from tkinter import messagebox
import state as S


def generate_htr():
    """Switch the right panel to an HTR generation view with:
    - a textarea
    - two dropdown lists
    - a canvas
    - a generate button
    """
    if S.txt_edit is None:
        return

    # Clear the right panel
    for child in S.txt_edit.winfo_children():
        child.destroy()

    # Container frames for layout
    form = tk.Frame(S.txt_edit)
    form.grid(row=0, column=0, sticky="nw", padx=10, pady=10)

    # Textarea with character limit
    tk.Label(form, text="Input Text:").grid(row=0, column=0, sticky="w")
    text_area = tk.Text(form, width=60, height=10)
    text_area.grid(row=1, column=0, columnspan=3, sticky="w", pady=(2, 10))
    char_limit = 500
    char_count_label = tk.Label(form, text=f"0/{char_limit}")
    char_count_label.grid(row=1, column=3, sticky="e", padx=(10, 0))

    def update_counter():
        length = len(text_area.get("1.0", "end-1c"))
        char_count_label.config(text=f"{length}/{char_limit}")

    def clamp_to_limit():
        content = text_area.get("1.0", "end-1c")
        if len(content) > char_limit:
            text_area.delete(f"1.0+{char_limit}c", "end-1c")
            # optional audible feedback
            if S.window:
                S.window.bell()

    def on_text_change(event=None):
        clamp_to_limit()
        update_counter()

    # Bind updates for typing/paste/cut
    text_area.bind('<KeyRelease>', on_text_change)
    text_area.bind('<<Paste>>', lambda e: S.window.after(1, on_text_change))
    text_area.bind('<<Cut>>', lambda e: S.window.after(1, on_text_change))

    # Dropdowns
    tk.Label(form, text="Model:").grid(row=2, column=0, sticky="w")
    model_var = tk.StringVar(value="Select model")
    model_menu = tk.OptionMenu(form, model_var, "Model A", "Model B", "Model C")
    model_menu.grid(row=2, column=1, sticky="w", padx=(5, 20))

    tk.Label(form, text="Language:").grid(row=2, column=2, sticky="w")
    lang_var = tk.StringVar(value="English")
    lang_menu = tk.OptionMenu(form, lang_var, "English", "French", "German", "Spanish")
    lang_menu.grid(row=2, column=3, sticky="w")

    # Generate action (placed before preview)
    def on_generate():
        content = text_area.get("1.0", "end-1c").strip()
        model = model_var.get()
        lang = lang_var.get()
        if not content:
            messagebox.showinfo("Generate HTR", "Please enter some text in the textarea.")
            return
        # Placeholder: show selection; integrate real generation here later
        messagebox.showinfo("Generate HTR", f"Generating with:\nModel: {model}\nLanguage: {lang}\nChars: {len(content)}")

    generate_btn = tk.Button(form, text="Generate", command=on_generate)
    generate_btn.grid(row=3, column=0, sticky="w", pady=(10, 0))

    # Preview canvas (placed after generate)
    tk.Label(form, text="Preview:").grid(row=4, column=0, sticky="w", pady=(10, 0))
    preview = tk.Canvas(form, width=600, height=300, bg="white", highlightthickness=1, highlightbackground="#ccc")
    preview.grid(row=5, column=0, columnspan=4, sticky="w", pady=(2, 10))

    # Draw a simple placeholder in preview
    preview.create_text(300, 150, text="Preview Area", fill="#999")

    # Expand right panel if needed
    S.txt_edit.rowconfigure(0, weight=1)
    S.txt_edit.columnconfigure(0, weight=1)
