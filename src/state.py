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
btn_next = None
btn_prev = None
btn_htr = None
btn_char_annotate = None
label = None

# Annotation window state
r = None
entries = []
entryText = []
text_box = None

# Processing state
finalrowsbbx = []

# Image scale for word detection
image_scale = 1.0
scale_slider = None
bbox_padding = 0
padding_slider = None
