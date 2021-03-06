# Study-Annotation-Tool
Study annotation tool is a tool to annotate handwriting text images with respect to IAM format Database. 

## Install Dependencies
* Use Python 3.8.5 and venv

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

![screen1](/images/screen1.png)

* Then, follow enabled buttons
1. By clicking on Open button, select folder containing images for annotation and the frst image will appear in the canvas
2. By clicking on Words Detection button, words will be detected and annotated arround boxes
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
