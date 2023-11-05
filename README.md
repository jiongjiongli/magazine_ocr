# magazine_ocr

# 1 Requirements

- Ubuntu 
- GPU



# 2 Deployment

```
bash install.sh
```



# 3 Run

```
cd magazine_ocr
python src/ocr_app.py "/content/NT2023-0002RW Bi-Annual Publication 7 Spread v8 Digital FA.pdf"
```



# 4 Input 

A pdf file.



# 5 Output

One PDF file for visualization.

One excel file to record OCR result of each page.

# 6 Workflow

1. Convert each page in PDF to images.
2. Run OCR model to recognize each image.
3. Visualization: 
    1. Draw recognized texts together with it's location in the original images.
    2. Convert all Images to PDF.
4. Generate an excel to record OCR result of each page.