# Study-Annotation-Tool
Study annotation tool is a tool to annotate handwriting text images with respect to IAM format Database. 

## Install Dependencies
* Use Python 3.8.5+ and venv

```python
  python3 -m venv StudyAnnotationTool
  source StudyAnnotationTool/bin/activate
  pip3 install -r requirements.txt
  https://www.dropbox.com/s/mqhco2q67ovpfjq/model.zip?dl=1  
 ```

## Run Study Annotation Tool
* Download [trained model](https://drive.google.com/file/d/1utQgvQusucEl9kxnkwI_X-FOshrs2mL9/view), and place the unzipped files into the model directory
* Go to src folder and run this command

```python
 python3 annotationgui.py
```

---

## 5-Step Workflow Wizard

The tool now includes an integrated **Workflow Wizard** (🔄 button in the sidebar) that guides you through a structured dataset analysis pipeline:

### Step 1 — Dataset Ingestion
- **Option A:** Upload raw images (scanner/camera)
- **Option B:** Load synthetic/GAN‑generated images
- **Option C:** Upload a pre-annotated dataset
- **Option D:** Load images with external annotation files (JSON, COCO, TXT, CSV, JSONL)
- Automatic metadata extraction, integrity checks, and thumbnail previews

### Step 2 — Annotation-Driven Statistical Analysis
- Label distribution (bar charts & tables)
- Character frequency analysis
- Writer/style diversity metrics
- Gap detection: rare characters, class imbalance, missing labels

### Step 3 — Dataset Splitting & Optimization
- Configurable train/val/test ratios with sliders
- 4 presets (70/15/15, 80/10/10, 60/20/20, 90/5/5)
- Constraints: stratified split, writer-independent, shuffle, seed
- Auto-recommendation based on dataset size
- Quality validation and JSON export

### Step 4 — Model Recommendation & Dataset Guidance
- Automatic mapping of dataset characteristics → suitable architectures
- 20+ models across 5 categories (Character Detection, Word-Level, Line-Level, Page-Level, Synthetic Data)
- Paper & GitHub links for each architecture
- Augmentation strategy recommendations with impact ratings
- Dataset quality score (0–100)

### Step 5 — Collaborative & Extensible Usage
- Export to 7 formats: IAM, COCO, YOLO, VOC, CSV, JSONL, Full Pipeline JSON
- Version history with manual checkpoints
- Integration hooks for Hugging Face Hub, Label Studio, W&B
- Full pipeline summary dashboard

---

## Legacy Annotation Flow

![screen1](/images/screen1.png)

* Then, follow enabled buttons
1. By clicking on Open button, select folder containing images for annotation and the first image will appear in the canvas
2. By clicking on Words Detection button, words will be detected and annotated around boxes
3. By clicking on Annotate button, new window will open and all words will be presented with input field for transcription 
4. By clicking on generateAnnotation button, IAM annotation text file will be generated and saved with the current image and word crops. 
5. If there are images remaining in the folder, the same process will be repeated for next image ...

![screen1](/images/screen2.png)
![screen1](/images/screen3.png)
![screen1](/images/screen4.png)
![screen1](/images/screen5.png)


## References
* [Handwritten Word Detector](https://github.com/githubharald/WordDetectorNN) 
* [IAM Handwriting Database](https://fki.tic.heia-fr.ch/databases/iam-handwriting-database)
