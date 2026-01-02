# Shared application state for GUI callbacks
# Simple module of globals to avoid circular imports

# indices and counters
pos = 0
nbr = 0
nbrout = 0
ind2 = 0

# paths
pathDirectory = ''
directoryout = ''
directorytmp = ''
directorydone = ''

# file list
list_of_files = []

# UI refs (set at runtime by annotationgui)
window = None
txt_edit = None
fr_buttons = None
btn_open = None
btn_save = None
btn_annotate = None
btn_line_annotate = None
btn_line_detect = None
btn_next = None
btn_prev = None
btn_htr = None
btn_char_annotate = None
label = None

# Main content area
input_text_area = None
input_text = ""
preview_canvas = None
current_preview_image = None
current_image_path = None
update_preview_image = None
image_info_var = None
btn_prev_img = None
btn_next_img = None

# Annotation window state
r = None
entries = []
entryText = []
text_box = None

# GAN input text for autofill
gan_input_text = None

# GAN batch images state
gan_batch_images = []  # List of paths to generated batch images
gan_batch_index = 0    # Currently selected batch image index

# Full image path for character annotation
full_image_path = None

# Processing state
finalrowsbbx = []

# Image scale for word detection
image_scale = 1.0
scale_slider = None
bbox_padding = 0
padding_slider = None
# RTL/Text direction support
text_direction = 'ltr'  # 'ltr' or 'rtl'

# Auto-save configuration
auto_save_enabled = True
auto_save_interval = 60000  # milliseconds (60 seconds)
auto_save_path = None
last_save_time = None

# Progress indicator
progress_var = None
progress_label = None

# Keyboard shortcut state
shortcuts_enabled = True

# Export format preference
export_format = 'iam'  # Default export format

# Update status callback (set by GUI)
update_status = None

# Show progress callback
show_progress = None
reset_progress = None