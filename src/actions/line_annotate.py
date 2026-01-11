"""
Line-based annotation module for handwriting recognition.

This module provides:
1. Line detection using horizontal projection profile
2. Word segmentation within each line
3. Line-by-line annotation interface
"""

import os
import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog
from PIL import Image, ImageTk
import cv2
import numpy as np
import state as S


def detect_text_lines(img_gray, min_line_height=15, merge_gap=10):
    """
    Detect text lines using horizontal projection profile.
    
    Args:
        img_gray: Grayscale numpy array of the image
        min_line_height: Minimum height for a valid text line
        merge_gap: Maximum gap between lines to merge them
        
    Returns:
        List of (y_start, y_end) tuples representing line boundaries
    """
    # Binarize image (dark text on light background)
    _, binary = cv2.threshold(img_gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # Calculate horizontal projection (sum of white pixels per row)
    projection = np.sum(binary, axis=1)
    
    # Normalize projection
    if projection.max() > 0:
        projection = projection / projection.max()
    
    # Find threshold for line detection
    threshold = 0.05  # 5% of max projection
    
    # Find line regions
    in_line = projection > threshold
    lines = []
    start = None
    
    for i, val in enumerate(in_line):
        if val and start is None:
            start = i
        elif not val and start is not None:
            if i - start >= min_line_height:
                lines.append((start, i))
            start = None
    
    # Handle case where line extends to bottom
    if start is not None and len(img_gray) - start >= min_line_height:
        lines.append((start, len(img_gray)))
    
    # Merge close lines
    merged_lines = []
    for line in lines:
        if merged_lines and line[0] - merged_lines[-1][1] < merge_gap:
            # Merge with previous line
            merged_lines[-1] = (merged_lines[-1][0], line[1])
        else:
            merged_lines.append(line)
    
    return merged_lines


def detect_words_in_line(img_gray, y_start, y_end, min_word_width=10, word_gap=15):
    """
    Detect words within a single text line using vertical projection.
    
    Args:
        img_gray: Grayscale numpy array of the full image
        y_start, y_end: Line boundaries
        min_word_width: Minimum width for a valid word
        word_gap: Minimum gap between words
        
    Returns:
        List of (x_start, x_end) tuples representing word boundaries
    """
    # Extract line region
    line_img = img_gray[y_start:y_end, :]
    
    # Binarize
    _, binary = cv2.threshold(line_img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # Calculate vertical projection
    projection = np.sum(binary, axis=0)
    
    # Normalize
    if projection.max() > 0:
        projection = projection / projection.max()
    
    threshold = 0.02
    in_word = projection > threshold
    
    words = []
    start = None
    gap_start = None
    
    for i, val in enumerate(in_word):
        if val:
            if start is None:
                start = i
            gap_start = None
        else:
            if start is not None:
                if gap_start is None:
                    gap_start = i
                elif i - gap_start >= word_gap:
                    # End of word
                    if gap_start - start >= min_word_width:
                        words.append((start, gap_start))
                    start = None
                    gap_start = None
    
    # Handle last word
    if start is not None:
        end = gap_start if gap_start else len(projection)
        if end - start >= min_word_width:
            words.append((start, end))
    
    return words


def segment_line_into_words(img_gray, line_bbox, padding=2):
    """
    Segment a line into individual word bounding boxes.
    
    Args:
        img_gray: Full grayscale image
        line_bbox: (y_start, y_end) of the line
        padding: Padding to add around word boxes
        
    Returns:
        List of (x, y, w, h) word bounding boxes
    """
    y_start, y_end = line_bbox
    words = detect_words_in_line(img_gray, y_start, y_end)
    
    word_boxes = []
    for x_start, x_end in words:
        x = max(0, x_start - padding)
        y = max(0, y_start - padding)
        w = min(img_gray.shape[1], x_end + padding) - x
        h = min(img_gray.shape[0], y_end + padding) - y
        word_boxes.append((x, y, w, h))
    
    return word_boxes


class LineAnnotationWindow:
    """Window for line-based annotation."""
    
    def __init__(self, image_path=None, detected_lines=None, auto_text=None):
        """
        Initialize line annotation window.
        
        Args:
            image_path: Path to the image file
            detected_lines: Optional list of pre-detected (y_start, y_end) line tuples
            auto_text: Optional list of text strings to auto-fill for each line
        """
        self.window = tk.Toplevel()
        self.window.title("Line-Based Annotation")
        self.window.geometry("1200x800")
        
        # State
        self.image_path = image_path
        self.original_img = None
        self.img_gray = None
        self.lines = detected_lines if detected_lines else []  # List of (y_start, y_end)
        self.auto_text = auto_text if auto_text else []  # Pre-filled text for lines
        self.line_words = {}  # {line_idx: [(x, y, w, h), ...]}
        self.line_texts = {}  # {line_idx: "transcription text"}
        self.current_line_idx = 0
        self.display_scale = 1.0
        
        self._setup_ui()
        self._load_image()
        
        # If we have pre-detected lines, update the display
        if self.lines:
            self._update_lines_display()
    
    def _setup_ui(self):
        """Setup the user interface."""
        # Main container
        main_frame = tk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Image display
        left_panel = tk.Frame(main_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Canvas with scrollbars
        canvas_frame = tk.Frame(left_panel)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.v_scroll = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL)
        self.h_scroll = tk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)
        
        self.canvas = tk.Canvas(
            canvas_frame, 
            width=700, 
            height=600,
            bg='gray',
            xscrollcommand=self.h_scroll.set,
            yscrollcommand=self.v_scroll.set
        )
        
        self.v_scroll.config(command=self.canvas.yview)
        self.h_scroll.config(command=self.canvas.xview)
        
        self.canvas.grid(row=0, column=0, sticky='nsew')
        self.v_scroll.grid(row=0, column=1, sticky='ns')
        self.h_scroll.grid(row=1, column=0, sticky='ew')
        
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)
        
        # Control buttons below canvas
        btn_frame = tk.Frame(left_panel)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        tk.Button(btn_frame, text="📂 Load Image", command=self._browse_image).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="🔍 Detect Lines", command=self._detect_lines).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="➕ Zoom In", command=lambda: self._zoom(1.2)).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="➖ Zoom Out", command=lambda: self._zoom(0.8)).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="🔄 Reset Zoom", command=lambda: self._zoom(None)).pack(side=tk.LEFT, padx=2)
        
        # Right panel - Annotation
        right_panel = tk.Frame(main_frame, width=400)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        right_panel.pack_propagate(False)
        
        # Line list
        tk.Label(right_panel, text="Detected Lines:", font=('Arial', 11, 'bold')).pack(anchor='w')
        
        list_frame = tk.Frame(right_panel)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 10))
        
        self.line_listbox = tk.Listbox(list_frame, height=10, font=('Arial', 10))
        list_scroll = tk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.line_listbox.yview)
        self.line_listbox.config(yscrollcommand=list_scroll.set)
        
        self.line_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.line_listbox.bind('<<ListboxSelect>>', self._on_line_select)
        
        # Current line preview
        tk.Label(right_panel, text="Current Line Preview:", font=('Arial', 11, 'bold')).pack(anchor='w', pady=(10, 5))
        
        self.line_preview = tk.Canvas(right_panel, width=380, height=80, bg='white', highlightthickness=1)
        self.line_preview.pack(fill=tk.X)
        
        # Transcription input
        tk.Label(right_panel, text="Line Transcription:", font=('Arial', 11, 'bold')).pack(anchor='w', pady=(15, 5))
        
        self.text_entry = tk.Text(right_panel, height=3, font=('Arial', 11), wrap=tk.WORD)
        self.text_entry.pack(fill=tk.X)
        self.text_entry.bind('<KeyRelease>', self._on_text_change)
        
        # Word count info
        self.word_info_label = tk.Label(right_panel, text="Words: 0 detected, 0 in transcription", font=('Arial', 9))
        self.word_info_label.pack(anchor='w', pady=(5, 0))
        
        # Navigation buttons
        nav_frame = tk.Frame(right_panel)
        nav_frame.pack(fill=tk.X, pady=(15, 0))
        
        tk.Button(nav_frame, text="⬆️ Previous Line", command=self._prev_line).pack(side=tk.LEFT, padx=2)
        tk.Button(nav_frame, text="⬇️ Next Line", command=self._next_line).pack(side=tk.LEFT, padx=2)
        tk.Button(nav_frame, text="✅ Apply to All Words", command=self._apply_transcription).pack(side=tk.RIGHT, padx=2)
        
        # Auto-detect words checkbox
        self.auto_segment = tk.BooleanVar(value=True)
        tk.Checkbutton(right_panel, text="Auto-segment words in line", variable=self.auto_segment).pack(anchor='w', pady=(10, 0))
        
        # Export section
        tk.Label(right_panel, text="Export:", font=('Arial', 11, 'bold')).pack(anchor='w', pady=(20, 5))
        
        export_frame = tk.Frame(right_panel)
        export_frame.pack(fill=tk.X)
        
        tk.Button(export_frame, text="💾 Export IAM Format", command=self._export_iam).pack(side=tk.LEFT, padx=2)
        tk.Button(export_frame, text="📄 Export JSON", command=self._export_json).pack(side=tk.LEFT, padx=2)
        
        # Status bar
        self.status_label = tk.Label(right_panel, text="Ready. Load an image to begin.", font=('Arial', 9), fg='gray')
        self.status_label.pack(anchor='w', pady=(20, 0))
    
    def _browse_image(self):
        """Open file dialog to select image."""
        filetypes = [
            ('Image files', '*.jpg *.jpeg *.png *.bmp *.tiff'),
            ('All files', '*.*')
        ]
        path = filedialog.askopenfilename(title="Select Image", filetypes=filetypes)
        if path:
            self.image_path = path
            self._load_image()
    
    def _load_image(self):
        """Load and display the image."""
        if not self.image_path or not os.path.exists(self.image_path):
            # Try to use GAN-generated image
            gan_jpg = os.path.join(os.path.dirname(__file__), '..', 'temp_handwriting.jpg')
            if os.path.exists(gan_jpg):
                self.image_path = os.path.abspath(gan_jpg)
            else:
                self.status_label.config(text="No image loaded. Click 'Load Image' to select one.")
                return
        
        try:
            self.original_img = Image.open(self.image_path)
            self.img_gray = cv2.imread(self.image_path, cv2.IMREAD_GRAYSCALE)
            
            # Reset state
            self.lines = []
            self.line_words = {}
            self.line_texts = {}
            self.current_line_idx = 0
            self.display_scale = 1.0
            
            self._redraw_canvas()
            self.line_listbox.delete(0, tk.END)
            self.text_entry.delete('1.0', tk.END)
            self.line_preview.delete('all')
            
            self.status_label.config(text=f"Loaded: {os.path.basename(self.image_path)}. Click 'Detect Lines' to find text lines.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {e}")
    
    def _redraw_canvas(self):
        """Redraw the canvas with current image and annotations."""
        if self.original_img is None:
            return
        
        # Scale image
        w, h = self.original_img.size
        new_w = int(w * self.display_scale)
        new_h = int(h * self.display_scale)
        
        scaled_img = self.original_img.resize((new_w, new_h), Image.LANCZOS)
        self.tk_img = ImageTk.PhotoImage(scaled_img)
        
        # Clear and redraw
        self.canvas.delete('all')
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_img)
        
        # Draw line boxes
        for idx, (y_start, y_end) in enumerate(self.lines):
            color = 'lime' if idx == self.current_line_idx else 'blue'
            width = 3 if idx == self.current_line_idx else 2
            
            y1 = int(y_start * self.display_scale)
            y2 = int(y_end * self.display_scale)
            
            self.canvas.create_rectangle(
                0, y1, new_w, y2,
                outline=color, width=width
            )
            
            # Line number label
            self.canvas.create_text(
                5, y1 + 5,
                anchor=tk.NW,
                text=f"L{idx + 1}",
                fill=color,
                font=('Arial', 10, 'bold')
            )
            
            # Draw word boxes within line
            if idx in self.line_words:
                for (x, y, ww, hh) in self.line_words[idx]:
                    x1 = int(x * self.display_scale)
                    y1_w = int(y * self.display_scale)
                    x2 = int((x + ww) * self.display_scale)
                    y2_w = int((y + hh) * self.display_scale)
                    self.canvas.create_rectangle(x1, y1_w, x2, y2_w, outline='red', width=1)
        
        # Update scroll region
        self.canvas.config(scrollregion=(0, 0, new_w, new_h))
    
    def _zoom(self, factor):
        """Zoom the image."""
        if factor is None:
            self.display_scale = 1.0
        else:
            self.display_scale = max(0.2, min(5.0, self.display_scale * factor))
        self._redraw_canvas()
    
    def _detect_lines(self):
        """Detect text lines in the image."""
        if self.img_gray is None:
            messagebox.showwarning("Warning", "Please load an image first.")
            return
        
        self.lines = detect_text_lines(self.img_gray)
        
        if not self.lines:
            messagebox.showinfo("Info", "No text lines detected. Try adjusting the image.")
            return
        
        self._update_lines_display()
    
    def _update_lines_display(self):
        """Update the display with detected/provided lines and auto-fill text."""
        if not self.lines:
            return
        
        # Detect words in each line
        self.line_words = {}
        for idx, line in enumerate(self.lines):
            if self.auto_segment.get():
                self.line_words[idx] = segment_line_into_words(self.img_gray, line)
        
        # Auto-fill text from auto_text list
        for idx, text in enumerate(self.auto_text):
            if idx < len(self.lines):
                self.line_texts[idx] = text.strip()
        
        # Update listbox
        self.line_listbox.delete(0, tk.END)
        for idx, (y_start, y_end) in enumerate(self.lines):
            word_count = len(self.line_words.get(idx, []))
            has_text = "✓" if idx in self.line_texts and self.line_texts[idx] else " "
            self.line_listbox.insert(tk.END, f"[{has_text}] Line {idx + 1}: y={y_start}-{y_end}, {word_count} words")
        
        self.current_line_idx = 0
        self.line_listbox.selection_set(0)
        self._update_line_preview()
        self._redraw_canvas()
        
        # Load first line's auto-filled text
        self.text_entry.delete('1.0', tk.END)
        if 0 in self.line_texts:
            self.text_entry.insert('1.0', self.line_texts[0])
        
        auto_filled = sum(1 for i in self.line_texts if self.line_texts.get(i))
        self.status_label.config(text=f"Detected {len(self.lines)} lines. Auto-filled {auto_filled} transcriptions.")
    
    def _on_line_select(self, event=None):
        """Handle line selection from listbox."""
        selection = self.line_listbox.curselection()
        if selection:
            self.current_line_idx = selection[0]
            self._update_line_preview()
            self._redraw_canvas()
            
            # Load existing transcription
            self.text_entry.delete('1.0', tk.END)
            if self.current_line_idx in self.line_texts:
                self.text_entry.insert('1.0', self.line_texts[self.current_line_idx])
            
            self._update_word_info()
    
    def _update_line_preview(self):
        """Update the line preview canvas."""
        if not self.lines or self.original_img is None:
            return
        
        y_start, y_end = self.lines[self.current_line_idx]
        
        # Crop line from image
        line_img = self.original_img.crop((0, y_start, self.original_img.width, y_end))
        
        # Scale to fit preview
        preview_w, preview_h = 380, 80
        img_w, img_h = line_img.size
        scale = min(preview_w / img_w, preview_h / img_h)
        new_w = int(img_w * scale)
        new_h = int(img_h * scale)
        
        line_img = line_img.resize((new_w, new_h), Image.LANCZOS)
        self.preview_tk = ImageTk.PhotoImage(line_img)
        
        self.line_preview.delete('all')
        x_offset = (preview_w - new_w) // 2
        y_offset = (preview_h - new_h) // 2
        self.line_preview.create_image(x_offset, y_offset, anchor=tk.NW, image=self.preview_tk)
    
    def _on_text_change(self, event=None):
        """Handle text entry changes."""
        text = self.text_entry.get('1.0', 'end-1c')
        self.line_texts[self.current_line_idx] = text
        self._update_word_info()
    
    def _update_word_info(self):
        """Update word count information."""
        detected = len(self.line_words.get(self.current_line_idx, []))
        text = self.text_entry.get('1.0', 'end-1c').strip()
        transcribed = len(text.split()) if text else 0
        
        color = 'green' if detected == transcribed else 'orange'
        self.word_info_label.config(
            text=f"Words: {detected} detected, {transcribed} in transcription",
            fg=color
        )
    
    def _prev_line(self):
        """Go to previous line."""
        if self.current_line_idx > 0:
            self.current_line_idx -= 1
            self.line_listbox.selection_clear(0, tk.END)
            self.line_listbox.selection_set(self.current_line_idx)
            self.line_listbox.see(self.current_line_idx)
            self._on_line_select()
    
    def _next_line(self):
        """Go to next line."""
        if self.current_line_idx < len(self.lines) - 1:
            self.current_line_idx += 1
            self.line_listbox.selection_clear(0, tk.END)
            self.line_listbox.selection_set(self.current_line_idx)
            self.line_listbox.see(self.current_line_idx)
            self._on_line_select()
    
    def _apply_transcription(self):
        """Apply transcription to detected words."""
        text = self.text_entry.get('1.0', 'end-1c').strip()
        words = text.split()
        detected_words = self.line_words.get(self.current_line_idx, [])
        
        if len(words) != len(detected_words):
            result = messagebox.askyesno(
                "Word Count Mismatch",
                f"Detected {len(detected_words)} words but transcription has {len(words)} words.\n\n"
                "Apply anyway? (Words will be matched left-to-right)"
            )
            if not result:
                return
        
        self.line_texts[self.current_line_idx] = text
        
        # Update listbox to show completion status
        word_count = len(detected_words)
        self.line_listbox.delete(self.current_line_idx)
        y_start, y_end = self.lines[self.current_line_idx]
        self.line_listbox.insert(
            self.current_line_idx,
            f"Line {self.current_line_idx + 1}: y={y_start}-{y_end}, {word_count} words ✓"
        )
        self.line_listbox.selection_set(self.current_line_idx)
        
        messagebox.showinfo("Success", f"Applied transcription to line {self.current_line_idx + 1}")
    
    def _export_iam(self):
        """Export annotations in IAM format."""
        if not self.lines:
            messagebox.showwarning("Warning", "No lines detected. Run line detection first.")
            return
        
        # Get save path
        save_path = filedialog.asksaveasfilename(
            defaultextension='.txt',
            filetypes=[('Text files', '*.txt')],
            title="Export IAM Format"
        )
        
        if not save_path:
            return
        
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                word_idx = 0
                for line_idx, (y_start, y_end) in enumerate(self.lines):
                    text = self.line_texts.get(line_idx, '')
                    words = text.split() if text else []
                    word_boxes = self.line_words.get(line_idx, [])
                    
                    # Match words to boxes
                    for i, (x, y, w, h) in enumerate(word_boxes):
                        word = words[i] if i < len(words) else '-'
                        # IAM format: id ok X x y w h X word
                        f.write(f"{word_idx} ok X {x} {y} {w} {h} X {word}\n")
                        word_idx += 1
            
            messagebox.showinfo("Export Complete", f"Saved to: {save_path}")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export: {e}")
    
    def _export_json(self):
        """Export annotations in JSON format."""
        import json
        
        if not self.lines:
            messagebox.showwarning("Warning", "No lines detected. Run line detection first.")
            return
        
        save_path = filedialog.asksaveasfilename(
            defaultextension='.json',
            filetypes=[('JSON files', '*.json')],
            title="Export JSON"
        )
        
        if not save_path:
            return
        
        try:
            data = {
                'image': os.path.basename(self.image_path) if self.image_path else 'unknown',
                'image_size': list(self.original_img.size) if self.original_img else [0, 0],
                'lines': []
            }
            
            for line_idx, (y_start, y_end) in enumerate(self.lines):
                text = self.line_texts.get(line_idx, '')
                words = text.split() if text else []
                word_boxes = self.line_words.get(line_idx, [])
                
                line_data = {
                    'line_id': line_idx,
                    'bbox': [0, y_start, self.original_img.width if self.original_img else 0, y_end - y_start],
                    'text': text,
                    'words': []
                }
                
                for i, (x, y, w, h) in enumerate(word_boxes):
                    word_data = {
                        'bbox': [x, y, w, h],
                        'text': words[i] if i < len(words) else ''
                    }
                    line_data['words'].append(word_data)
                
                data['lines'].append(line_data)
            
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            messagebox.showinfo("Export Complete", f"Saved to: {save_path}")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export: {e}")


def line_annotate():
    """Entry point for line-based annotation."""
    # Check for available image sources
    image_path = None
    
    # Priority 1: Current loaded image from folder
    if S.list_of_files and len(S.list_of_files) > S.pos:
        image_path = S.list_of_files[S.pos]
    
    # Priority 2: GAN batch images (check the selected batch index)
    if not image_path:
        import glob
        batch_dir = os.path.join(os.path.dirname(__file__), '..', 'gan_output_data', 'batch')
        batch_dir = os.path.abspath(batch_dir)
        jpgs = sorted(glob.glob(os.path.join(batch_dir, '*.jpg')))
        if jpgs:
            # Use the currently selected batch image
            batch_idx = getattr(S, 'gan_batch_index', 0)
            if 0 <= batch_idx < len(jpgs):
                image_path = jpgs[batch_idx]
            else:
                image_path = jpgs[0]
            print(f"Line annotation using GAN batch image: {image_path}")
    
    # Priority 3: temp_handwriting.jpg fallback
    if not image_path:
        gan_jpg = os.path.join(os.path.dirname(__file__), '..', 'temp_handwriting.jpg')
        gan_jpg = os.path.abspath(gan_jpg)
        if os.path.exists(gan_jpg):
            image_path = gan_jpg
            print(f"Line annotation using temp image: {image_path}")
    
    # Open the annotation window
    window = LineAnnotationWindow(image_path)
    
    # Store reference in state
    S.line_annotate_window = window


def start_embedded_line_annotation(image_path, detected_lines, text_lines=None):
    """
    Start line-by-line annotation embedded in the main annotation panel.
    
    Args:
        image_path: Path to the image file
        detected_lines: List of (y_start, y_end) tuples for each detected line
        text_lines: Optional list of text strings to pre-fill each line
    """
    import tkinter as tk
    from tkinter import messagebox, filedialog
    from PIL import Image, ImageTk
    
    if not image_path or not os.path.exists(image_path):
        messagebox.showerror("Error", "Image not found for annotation.")
        return
    
    if not detected_lines:
        messagebox.showinfo("No Lines", "No lines detected to annotate.")
        return
    
    # Load the image
    try:
        original_img = Image.open(image_path)
        img_width, img_height = original_img.size
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load image: {e}")
        return
    
    # Get annotation container body
    if not hasattr(S, 'annotation_body') or not S.annotation_body:
        messagebox.showerror("Error", "Annotation panel not available.")
        return
    
    # Clear the annotation body
    for widget in S.annotation_body.winfo_children():
        widget.destroy()
    
    # Store annotation data
    line_entries = []
    line_images = []  # Keep references to prevent garbage collection
    current_line_idx = [0]  # Use list to allow modification in nested functions
    
    # Create scrollable frame for line annotations
    canvas = tk.Canvas(S.annotation_body, bg='#f4f7fb', highlightthickness=0)
    scrollbar = tk.Scrollbar(S.annotation_body, orient="vertical", command=canvas.yview)
    scroll_frame = tk.Frame(canvas, bg='#f4f7fb')
    
    scroll_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    # Enable mouse wheel scrolling
    def on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    canvas.bind_all("<MouseWheel>", on_mousewheel)
    
    # Header
    header = tk.Frame(scroll_frame, bg='#6cb6ff', padx=10, pady=8)
    header.pack(fill=tk.X, pady=(0, 10))
    tk.Label(header, text=f"📄 Line Annotation - {len(detected_lines)} lines detected",
             font=('Segoe UI', 12, 'bold'), bg='#6cb6ff', fg='white').pack(side=tk.LEFT)
    
    # Create annotation entry for each line
    for i, (y_start, y_end) in enumerate(detected_lines):
        line_frame = tk.Frame(scroll_frame, bg='white', relief=tk.RIDGE, bd=1)
        line_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Line number label
        tk.Label(line_frame, text=f"Line {i + 1}:", font=('Segoe UI', 10, 'bold'),
                 bg='white', fg='#333').pack(anchor='w', padx=10, pady=(8, 2))
        
        # Crop the line from image
        line_crop = original_img.crop((0, y_start, img_width, y_end))
        
        # Resize for display (max width 600px, preserve aspect ratio)
        crop_w, crop_h = line_crop.size
        max_width = 600
        if crop_w > max_width:
            scale = max_width / crop_w
            new_w = max_width
            new_h = int(crop_h * scale)
            line_crop = line_crop.resize((new_w, new_h), Image.LANCZOS)
        
        # Create PhotoImage and display
        photo = ImageTk.PhotoImage(line_crop)
        line_images.append(photo)  # Keep reference
        
        img_label = tk.Label(line_frame, image=photo, bg='white', relief=tk.SUNKEN, bd=1)
        img_label.pack(padx=10, pady=5)
        
        # Text entry for transcription
        tk.Label(line_frame, text="Transcription:", font=('Segoe UI', 9),
                 bg='white', fg='#666').pack(anchor='w', padx=10, pady=(5, 2))
        
        entry = tk.Entry(line_frame, font=('Segoe UI', 11), width=70)
        entry.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Pre-fill if text is provided
        if text_lines and i < len(text_lines):
            entry.insert(0, text_lines[i])
        
        line_entries.append({
            'entry': entry,
            'y_start': y_start,
            'y_end': y_end,
            'frame': line_frame
        })
    
    # Action buttons frame
    btn_frame = tk.Frame(scroll_frame, bg='#f4f7fb')
    btn_frame.pack(fill=tk.X, padx=10, pady=(15, 20))
    
    def save_annotations():
        """Save line annotations to JSON file."""
        annotations = []
        for i, line_data in enumerate(line_entries):
            text = line_data['entry'].get().strip()
            annotations.append({
                'line_id': i,
                'y_start': line_data['y_start'],
                'y_end': line_data['y_end'],
                'text': text,
                'bbox': [0, line_data['y_start'], img_width, line_data['y_end'] - line_data['y_start']]
            })
        
        save_path = filedialog.asksaveasfilename(
            defaultextension='.json',
            filetypes=[('JSON files', '*.json'), ('All files', '*.*')],
            title="Save Line Annotations"
        )
        
        if save_path:
            try:
                import json
                data = {
                    'image': os.path.basename(image_path),
                    'image_size': [img_width, img_height],
                    'lines': annotations
                }
                with open(save_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                messagebox.showinfo("Saved", f"Annotations saved to:\n{save_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {e}")
    
    def export_iam_format():
        """Export in IAM-like format (image_id text)."""
        save_path = filedialog.asksaveasfilename(
            defaultextension='.txt',
            filetypes=[('Text files', '*.txt'), ('All files', '*.*')],
            title="Export IAM Format"
        )
        
        if save_path:
            try:
                base_name = os.path.splitext(os.path.basename(image_path))[0]
                lines_out = []
                for i, line_data in enumerate(line_entries):
                    text = line_data['entry'].get().strip()
                    if text:
                        lines_out.append(f"{base_name}-line{i:03d} {text}")
                
                with open(save_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(lines_out))
                messagebox.showinfo("Exported", f"IAM format exported to:\n{save_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export: {e}")
    
    def clear_all_entries():
        """Clear all transcription entries."""
        for line_data in line_entries:
            line_data['entry'].delete(0, tk.END)
    
    # Buttons
    tk.Button(btn_frame, text="⬅ Back to Detection", command=lambda: S.back_to_detection_from_annotation() if hasattr(S, 'back_to_detection_from_annotation') else None,
              bg='#6c757d', fg='white', font=('Segoe UI', 10, 'bold'),
              padx=12, pady=5).pack(side=tk.LEFT, padx=5)
    
    tk.Button(btn_frame, text="💾 Save JSON", command=save_annotations,
              bg='#6cb6ff', fg='white', font=('Segoe UI', 10, 'bold'),
              padx=15, pady=5).pack(side=tk.LEFT, padx=5)
    
    tk.Button(btn_frame, text="📄 Export IAM", command=export_iam_format,
              bg='#5a9fd4', fg='white', font=('Segoe UI', 10, 'bold'),
              padx=15, pady=5).pack(side=tk.LEFT, padx=5)
    
    tk.Button(btn_frame, text="🗑 Clear All", command=clear_all_entries,
              bg='#dc3545', fg='white', font=('Segoe UI', 10, 'bold'),
              padx=15, pady=5).pack(side=tk.RIGHT, padx=5)
    
    # Store references in state to prevent garbage collection
    S.line_annotation_images = line_images
    S.line_annotation_entries = line_entries
    S.line_annotation_canvas = canvas
