import tkinter as tk
from tkinter import messagebox, scrolledtext
import state as S
import sys
import os
import tempfile
from PIL import Image, ImageTk, ImageDraw, ImageFont
import io
import xml.etree.ElementTree as ET
import re

def parse_and_render_svg(svg_file_path, canvas, canvas_width=600, canvas_height=300):
    """Parse SVG file and render handwriting paths to tkinter canvas"""
    try:
        # Read and parse SVG file
        with open(svg_file_path, 'r', encoding='utf-8') as f:
            svg_content = f.read()
        
        # Parse XML
        root = ET.fromstring(svg_content)
        
        # Extract SVG namespace and viewBox
        viewbox = root.get('viewBox', '0 0 1000 400')
        viewbox_parts = viewbox.split()
        svg_width = float(viewbox_parts[2])
        svg_height = float(viewbox_parts[3])
        
        # Calculate scaling to fit canvas
        scale_x = canvas_width / svg_width
        scale_y = canvas_height / svg_height
        scale = min(scale_x, scale_y) * 0.9  # Leave some padding
        
        # Calculate offset to center the drawing
        offset_x = (canvas_width - svg_width * scale) / 2
        offset_y = (canvas_height - svg_height * scale) / 2
        
        # Find all path elements (handwriting strokes)
        paths = []
        for elem in root.iter():
            if elem.tag.endswith('path'):
                d = elem.get('d', '')
                stroke = elem.get('stroke', 'black')
                stroke_width = float(elem.get('stroke-width', '2'))
                paths.append((d, stroke, stroke_width))
        
        # Clear canvas
        canvas.delete("all")
        
        # Add background
        canvas.create_rectangle(0, 0, canvas_width, canvas_height, fill='white', outline='')
        
        # Parse and render each path
        for path_data, stroke_color, stroke_width in paths:
            if not path_data:
                continue
                
            # Parse path data (simplified parser for M and L commands)
            coords = []
            current_pos = [0, 0]
            
            # Split path data into commands
            commands = re.findall(r'[ML][^ML]*', path_data)
            
            for cmd in commands:
                if cmd.startswith('M'):  # Move to
                    # Extract coordinates
                    coords_str = cmd[1:].strip()
                    if coords_str:
                        try:
                            x, y = map(float, coords_str.split(','))
                            current_pos = [x * scale + offset_x, y * scale + offset_y]
                            coords.append(('M', current_pos[0], current_pos[1]))
                        except:
                            continue
                elif cmd.startswith('L'):  # Line to
                    coords_str = cmd[1:].strip()
                    if coords_str:
                        try:
                            x, y = map(float, coords_str.split(','))
                            new_pos = [x * scale + offset_x, y * scale + offset_y]
                            coords.append(('L', new_pos[0], new_pos[1]))
                            current_pos = new_pos
                        except:
                            continue
            
            # Convert to tkinter canvas lines
            if len(coords) > 1:
                line_coords = []
                for i, (cmd_type, x, y) in enumerate(coords):
                    if cmd_type == 'M':
                        # Start new line segment
                        if line_coords and len(line_coords) >= 4:
                            canvas.create_line(line_coords, fill=stroke_color, width=max(1, int(stroke_width * scale)), capstyle=tk.ROUND, smooth=True)
                        line_coords = [x, y]
                    elif cmd_type == 'L' and line_coords:
                        line_coords.extend([x, y])
                
                # Draw final line segment
                if line_coords and len(line_coords) >= 4:
                    canvas.create_line(line_coords, fill=stroke_color, width=max(1, int(stroke_width * scale)), capstyle=tk.ROUND, smooth=True)
        
        return True
        
    except Exception as e:
        print(f"SVG parsing error: {e}")
        return False
# Add gan folder to path to import Hand class
current_script_dir = os.path.dirname(os.path.abspath(__file__))
gan_folder = os.path.join(current_script_dir, '..', 'gan')
gan_folder = os.path.abspath(gan_folder)

if gan_folder not in sys.path:
    sys.path.insert(0, gan_folder)

# Import Hand class with detailed error handling
Hand = None
try:
    # Change to gan directory temporarily for import
    original_cwd = os.getcwd()
    os.chdir(gan_folder)
    
    from demo import Hand
    print(f"Successfully imported Hand class from {gan_folder}")
    
except ImportError as e:
    print(f"ImportError: Could not import Hand class: {e}")
    Hand = None
except Exception as e:
    print(f"Unexpected error importing Hand class: {e}")
    Hand = None
finally:
    # Restore original working directory
    if 'original_cwd' in locals():
        os.chdir(original_cwd)


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

    # Style controls
    tk.Label(form, text="Style ID:").grid(row=3, column=0, sticky="w", pady=(10, 0))
    style_var = tk.IntVar(value=9)
    
    # Check available styles in gan directory
    gan_dir = os.path.join(os.path.dirname(__file__), '..', 'gan')
    max_style = 12  # Default safe maximum
    styles_dir = os.path.join(gan_dir, 'styles')
    if os.path.exists(styles_dir):
        available = []
        for i in range(21):
            if (os.path.exists(os.path.join(styles_dir, f'style-{i}-strokes.npy')) and 
                os.path.exists(os.path.join(styles_dir, f'style-{i}-chars.npy'))):
                available.append(i)
        if available:
            max_style = max(available)
    
    style_scale = tk.Scale(form, from_=0, to=max_style, orient=tk.HORIZONTAL, variable=style_var)
    style_scale.grid(row=3, column=1, sticky="w", padx=(5, 20))
    style_label = tk.Label(form, text="9")
    style_label.grid(row=3, column=2, sticky="w")

    # Update label when slider changes
    def update_style_label(value):
        style_label.config(text=str(int(float(value))))
    
    style_scale.config(command=update_style_label)

    # Generate action (placed before preview)
    def on_generate():
        content = text_area.get("1.0", "end-1c").strip()
        model = model_var.get()
        lang = lang_var.get()
        style_val = style_var.get()
        
        if not content:
            messagebox.showinfo("Generate HTR", "Please enter some text in the textarea.")
            return
            
        if Hand is None:
            current_script_dir = os.path.dirname(os.path.abspath(__file__))
            gan_folder_path = os.path.abspath(os.path.join(current_script_dir, '..', 'gan'))
            
            error_msg = "GAN model not available. Please check:\\n\\n"
            error_msg += f"1. GAN folder exists at: {gan_folder_path}\\n"
            error_msg += "2. Required files (demo.py, checkpoints/) are present\\n"
            error_msg += "3. TensorFlow and other dependencies are installed\\n\\n"
            error_msg += "Check the console for detailed import errors."
            messagebox.showerror("GAN Model Error", error_msg)
            return
            
        try:
            # Show progress in info textbox
            info_text.config(state=tk.NORMAL)
            info_text.delete(1.0, tk.END)
            info_text.insert(tk.END, "🔄 Starting handwriting generation...\n\nPlease wait while processing your text...")
            info_text.config(state=tk.DISABLED)
            
            # Clear preview canvas
            preview.delete("all")
            preview.create_text(300, 150, text="Generating...", fill="#666")
            preview.update()
            
            # Initialize Hand model with proper paths
            current_dir = os.path.dirname(os.path.abspath(__file__))
            gan_dir = os.path.abspath(os.path.join(current_dir, '..', 'gan'))
            
            # Ensure we're in the correct directory for model loading
            old_cwd = os.getcwd()
            try:
                os.chdir(gan_dir)
                print(f"Initializing Hand model from directory: {gan_dir}")
                hand = Hand()
                print("Hand model initialized successfully")
                
                # Check for required model files
                checkpoints_dir = os.path.join(gan_dir, 'checkpoints')
                if not os.path.exists(checkpoints_dir):
                    raise FileNotFoundError(f"Checkpoints directory not found at {checkpoints_dir}")
            
            except Exception as model_error:
                os.chdir(old_cwd)  # Restore directory even if model init fails
                error_msg = f"Failed to initialize GAN model:\\n{str(model_error)}\\n\\n"
                error_msg += f"Working directory: {gan_dir}\\n"
                error_msg += "Please check:\\n"
                error_msg += "1. Checkpoints folder exists and contains model files\\n"
                error_msg += "2. TensorFlow is properly installed\\n"
                error_msg += "3. All GAN dependencies are available"
                
                preview.delete("all")
                preview.create_text(300, 150, text=f"Model initialization failed:\\n{str(model_error)}", fill="red", justify=tk.CENTER)
                
                info_text.config(state=tk.NORMAL)
                info_text.delete(1.0, tk.END)
                info_text.insert(tk.END, f"❌ GAN Model Error\\n\\n{error_msg}")
                info_text.config(state=tk.DISABLED)
                
                messagebox.showerror("Model Initialization Error", error_msg)
                return
            
            # Split content into lines (max 75 chars each) FIRST
            lines = []
            words = content.split()
            current_line = ""
            
            for word in words:
                if len(current_line + " " + word) <= 75:
                    current_line = current_line + " " + word if current_line else word
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            
            if current_line:
                lines.append(current_line)
            
            # Change to gan directory for model loading
            old_cwd = os.getcwd()
            try:
                os.chdir(gan_dir)
                hand = Hand()
                
                # Check available styles
                available_styles = []
                styles_dir = 'styles'
                if os.path.exists(styles_dir):
                    for i in range(21):  # Check styles 0-20
                        stroke_file = f'{styles_dir}/style-{i}-strokes.npy'
                        chars_file = f'{styles_dir}/style-{i}-chars.npy'
                        if os.path.exists(stroke_file) and os.path.exists(chars_file):
                            available_styles.append(i)
                
                # Use available style or fallback to no style
                if style_val in available_styles:
                    styles = [style_val] * len(lines)
                else:
                    # Fallback: use no style (None) if requested style not available
                    styles = None
                    if available_styles:
                        # Or use the first available style
                        styles = [available_styles[0]] * len(lines)
                        messagebox.showinfo("Style Note", f"Style {style_val} not available. Using style {available_styles[0]} instead.")
                    else:
                        messagebox.showinfo("Style Note", f"No style files found. Generating without style conditioning.")
                
            finally:
                os.chdir(old_cwd)
            
            # Generate handwriting with fixed black color and stroke width 1
            output_path = os.path.join(os.path.dirname(__file__), '..', 'temp_handwriting.svg')
            biases = [0.75] * len(lines)  # Fixed bias value
            # styles variable already set above based on availability
            stroke_colors = ['black'] * len(lines)
            stroke_widths = [1] * len(lines)
            
            # Change back to gan directory for generation
            os.chdir(gan_dir)
            try:
                hand.write(
                    filename=output_path,
                    lines=lines,
                    biases=biases,
                    styles=styles,
                    stroke_colors=stroke_colors,
                    stroke_widths=stroke_widths
                )
            finally:
                os.chdir(old_cwd)
            
            # Display the actual SVG handwriting in canvas
            try:
                # Try to parse and render SVG directly
                if parse_and_render_svg(output_path, preview, 600, 300):
                    conversion_method = "Direct SVG Rendering"
                    
                    # Also try to save a JPG version using fallback methods
                    jpg_path = output_path.replace('.svg', '.jpg')
                    try:
                        # Try Wand for JPG conversion
                        from wand.image import Image as WandImage
                        with WandImage(filename=output_path) as wand_img:
                            wand_img.format = 'jpeg'
                            wand_img.background_color = 'white'
                            wand_img.save(filename=jpg_path)
                    except Exception:
                        # Create a simple JPG using PIL as fallback
                        img = Image.new('RGB', (800, 400), 'white')
                        draw = ImageDraw.Draw(img)
                        try:
                            font = ImageFont.truetype("arial.ttf", 14)
                        except:
                            font = ImageFont.load_default()
                        
                        y_pos = 30
                        for i, line in enumerate(lines):
                            if y_pos > 350:
                                break
                            draw.text((20, y_pos), f"{i+1}. {line}", fill='black', font=font)
                            y_pos += 30
                        img.save(jpg_path, 'JPEG', quality=95)
                    
                    # Update info textbox
                    info_text.config(state=tk.NORMAL)
                    info_text.delete(1.0, tk.END)
                    
                    actual_style = styles[0] if styles else "No style"
                    info_content = f"""✅ Handwriting Generated and Displayed!

📝 Text Lines: {len(lines)}
🎨 Style Used: {actual_style}
📁 SVG File: {output_path}
🖼️ JPG File: {jpg_path}
📊 Character Count: {len(content)}
⚙️ Bias Setting: 0.75 (fixed)
🖥️ Display: {conversion_method}
🎨 Handwriting: Rendered directly from SVG

Generated Lines:
"""
                    
                    for i, line in enumerate(lines, 1):
                        info_content += f"{i}. {line}\n"
                    
                    info_content += f"\n✅ Files saved and handwriting displayed\n💡 Both SVG and JPG versions available"
                    
                    info_text.insert(tk.END, info_content)
                    info_text.config(state=tk.DISABLED)
                    
                    messagebox.showinfo("Generate HTR", f"Handwriting generated and displayed!\nLines: {len(lines)}\nStyle: {actual_style}\nDisplay: SVG Rendered")
                    
                else:
                    raise Exception("SVG parsing failed")
                
            except Exception as display_error:
                # Fallback: show enhanced text-based preview
                preview.delete("all")
                
                # Create a nice background
                preview.create_rectangle(0, 0, 600, 300, fill='#f8f9fa', outline='#dee2e6')
                
                # Title
                preview.create_text(300, 20, text="Generated Handwriting Content", 
                                  fill="#495057", justify=tk.CENTER, font=("Arial", 14, "bold"))
                
                # Show the text lines in a handwriting-like layout
                y_start = 50
                line_height = 25
                
                for i, line in enumerate(lines[:8]):  # Show max 8 lines
                    y_pos = y_start + (i * line_height)
                    if y_pos > 270:
                        break
                    
                    # Line number
                    preview.create_text(20, y_pos, text=f"{i+1}.", 
                                      anchor=tk.W, fill="#6c757d", font=("Arial", 9))
                    
                    # Text content
                    display_line = line[:70] + '...' if len(line) > 70 else line
                    preview.create_text(40, y_pos, text=display_line, 
                                      anchor=tk.W, fill="#212529", font=("Courier", 10))
                
                if len(lines) > 8:
                    preview.create_text(40, 270, text=f"... and {len(lines)-8} more lines in SVG file", 
                                      anchor=tk.W, fill="#6c757d", font=("Arial", 8, "italic"))
                
                # Footer note
                preview.create_text(300, 285, text=f"SVG file: {os.path.basename(output_path)}", 
                                  fill="#6c757d", justify=tk.CENTER, font=("Arial", 8))
                
                # Update info textbox with error details
                info_text.config(state=tk.NORMAL)
                info_text.delete(1.0, tk.END)
                actual_style = styles[0] if styles else "No style"
                info_content = f"""⚠️ Generation completed - Text preview shown

📝 Text Lines: {len(lines)}
🎨 Style Used: {actual_style}
📁 SVG File: {output_path}
❌ Display Note: Showing text preview (SVG contains actual handwriting)

Generated Lines:
"""
                for i, line in enumerate(lines, 1):
                    info_content += f"{i}. {line}\n"
                info_content += f"\n✅ SVG file saved successfully\n💡 Open the SVG file to view the actual handwriting\n🔧 Display error: {str(display_error)[:100]}..."
                
                info_text.insert(tk.END, info_content)
                info_text.config(state=tk.DISABLED)
                
                messagebox.showinfo("Generate HTR", f"Handwriting generated!\nLines: {len(lines)}\nStyle: {actual_style}\nFile: {output_path}\nNote: Text preview shown")
            
        except Exception as e:
            preview.delete("all")
            preview.create_text(300, 150, text=f"Generation failed:\n{str(e)}", fill="red", justify=tk.CENTER)
            
            # Update info textbox with error details
            info_text.config(state=tk.NORMAL)
            info_text.delete(1.0, tk.END)
            info_text.insert(tk.END, f"❌ Generation Failed\n\nError Details:\n{str(e)}\n\nPlease check your input and try again.")
            info_text.config(state=tk.DISABLED)
            
            messagebox.showerror("Generation Error", f"Failed to generate handwriting:\n{str(e)}")

    generate_btn = tk.Button(form, text="Generate", command=on_generate)
    generate_btn.grid(row=4, column=0, sticky="w", pady=(10, 0))

    # Preview canvas (placed after generate)
    tk.Label(form, text="Preview:").grid(row=5, column=0, sticky="w", pady=(10, 0))
    preview = tk.Canvas(form, width=600, height=300, bg="white", highlightthickness=1, highlightbackground="#ccc")
    preview.grid(row=6, column=0, columnspan=4, sticky="w", pady=(2, 5))

    # Information textbox below canvas
    tk.Label(form, text="Generation Info:").grid(row=7, column=0, sticky="w", pady=(5, 0))
    info_text = scrolledtext.ScrolledText(form, width=75, height=6, wrap=tk.WORD)
    info_text.grid(row=8, column=0, columnspan=4, sticky="w", pady=(2, 10))
    info_text.insert(tk.END, "Generation information will appear here...")
    info_text.config(state=tk.DISABLED)

    # Draw a simple placeholder in preview
    preview.create_text(300, 150, text="Preview Area", fill="#999")

    # Expand right panel if needed
    S.txt_edit.rowconfigure(0, weight=1)
    S.txt_edit.columnconfigure(0, weight=1)
