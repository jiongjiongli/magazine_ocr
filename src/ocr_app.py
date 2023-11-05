from pathlib import Path
from shutil import rmtree
import subprocess
import json
import logging
import yaml
import numpy as np
import re
import cv2
from PIL import Image
import xlsxwriter
from sklearn.feature_extraction.text import TfidfVectorizer
from paddleocr import PaddleOCR, draw_ocr


class OCRAPI:
    def __init__(self):
        print('Start read config...')
        self.config = self.read_config()
        self.images_dir_path = Path(self.config['images_dir_path'])
        self.ocr_output_images_dir = Path(self.config['ocr_output_images_dir'])
        self.image_file_prefix = self.config['image_file_prefix']

        print('Start ocr model init...')
        self.ocr_model = PaddleOCR(use_angle_cls=False, lang='en')
        print('Completed ocr model init!')

    def read_config(self):
        dir_path = Path(__file__).resolve().parent
        config_file_path = dir_path / 'config.yaml'

        with open(config_file_path, 'r') as file_stream:
            config_dict = yaml.safe_load(file_stream)

        return config_dict

    def reset_dir_path(self, dir_path):
        dir_path.mkdir(parents=True, exist_ok=True)

        for child_path in dir_path.glob("**/*"):
            if child_path.is_file():
                child_path.unlink()
            elif child_path.is_dir():
                rmtree(child_path)

    def ocr(self, input_pdf_file_path):
        print('Start reset_dir_path...')
        self.reset_dir_path(self.images_dir_path)
        self.reset_dir_path(self.ocr_output_images_dir)

        print('Start pdf to images...')
        output_images_dir_path = self.images_dir_path / self.image_file_prefix
        process_result = subprocess.run(['pdftoppm',
            '-png',
            input_pdf_file_path.as_posix(),
            output_images_dir_path.as_posix()],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)

        print('Completed pdftoppm with result:', process_result)

        image_file_paths = list(images_dir_path.glob(r'{}-*.png'.format(self.image_file_prefix)))
        image_file_paths.sort()

        for file_path in image_file_paths:
            print('Start ocr for file:', file_path)
            result = ocr_model.ocr(file_path.as_posix(), cls=False)
            img = Image.open(file_path.as_posix())
            img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            res = result[0]
            boxes = [line[0] for line in res]
            txts = [line[1][0] for line in res]
            scores = [line[1][1] for line in res]
            # im_show = draw_ocr(img, boxes, txts, scores, font_path='doc/fonts/simfang.ttf')
            im_show = draw_ocr(img, boxes, txts, scores, font_path='LiberationSans-Regular.ttf')
            im_show = Image.fromarray(im_show)
            match_results = re.match('(.*?)([0-9]+)', file_path.stem)
            image_index = match_results.group(2)
            ocr_output_image_path = self.ocr_output_images_dir / 'result_page_{}.jpg'.format(image_index)
            im_show.save(ocr_output_image_path.as_posix())

        print('Completed ocr!')
        workbook = xlsxwriter.Workbook('hello.xlsx')
        worksheet = workbook.add_worksheet()

        worksheet.write('A1', 'Hello world')

        workbook.close()
        print('OCR output images path:', self.ocr_output_images_dir)


def main():
    input_pdf_file_path = Path('/content/drive/MyDrive/data/cv/magazine/NT2023-0002RW Bi-Annual Publication 7 Spread v8 Digital FA.pdf')

    ocr_api = OCRAPI()
    ocr_api.ocr(input_pdf_file_path)


if __name__ == '__main__':
    main()
