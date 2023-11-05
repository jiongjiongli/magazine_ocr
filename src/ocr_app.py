from pathlib import Path
import argparse
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
from paddleocr import PaddleOCR, draw_ocr, logger as ocr_logger
from ppocr.utils.logging import get_logger


class OCRAPI:
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.logger.info('Start read config...')
        self.config = self.read_config()
        self.output_root_dir_path = Path(self.config['output_root_dir_path'])
        self.images_dir_path = self.output_root_dir_path / self.config['images_dir_name']
        self.ocr_output_images_dir = self.output_root_dir_path / self.config['ocr_output_images_dir_name']
        self.image_file_prefix = self.config['image_file_prefix']

        self.logger.info('Start ocr model init...')
        self.ocr_model = PaddleOCR(use_angle_cls=False, lang='en')
        self.logger.info('Completed ocr model init!')

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
        self.logger.info(r'Start reset dir path {}...'.format(self.images_dir_path))
        self.reset_dir_path(self.images_dir_path)
        self.logger.info(r'Start reset dir path {}...'.format(self.ocr_output_images_dir))
        self.reset_dir_path(self.ocr_output_images_dir)

        self.logger.info(r'Input pdf file path: {}'.format(input_pdf_file_path))
        self.logger.info('Start pdf to images...')
        output_images_dir_path = self.images_dir_path / self.image_file_prefix
        process_result = subprocess.run(
            ['pdftoppm',
                '-png',
                input_pdf_file_path.as_posix(),
                output_images_dir_path.as_posix()],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)

        self.logger.info(r'Completed pdftoppm with result: {}'.format(process_result))

        output_excel_file_path = self.output_root_dir_path / r'{}.xlsx'.format(input_pdf_file_path.stem)
        workbook = xlsxwriter.Workbook(output_excel_file_path.as_posix())
        image_file_paths = list(self.images_dir_path.glob(r'{}-*.png'.format(self.image_file_prefix)))
        image_file_paths.sort()

        for file_path in image_file_paths:
            self.logger.info(r'Start ocr for file: {}'.format(file_path))
            result = self.ocr_model.ocr(file_path.as_posix(), cls=False)

            match_results = re.match('(.*?)([0-9]+)', file_path.stem)
            image_index = match_results.group(2)
            worksheet = workbook.add_worksheet(str(image_index))
            worksheet.set_column(0, 0, 60)

            img = Image.open(file_path.as_posix())
            img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            res = result[0]

            output_head = [[
                    ['x1', 'y1'],
                    ['x2', 'y2'],
                    ['x3', 'y3'],
                    ['x4', 'y4']
                ],
                ('text', 'confidence_score')]
            row = 0

            for line in [output_head] + res:
                column = 0

                box = line[0]
                text = line[1][0]
                score = line[1][1]

                worksheet.write(row, column, text)
                column += 1

                for point in box:
                    for coordinate in point:
                        worksheet.write(row, column, coordinate)
                        column += 1

                worksheet.write(row, column, score)
                column += 1

                row += 1

            boxes = [line[0] for line in res]
            txts = [line[1][0] for line in res]
            scores = [line[1][1] for line in res]
            # im_show = draw_ocr(img, boxes, txts, scores, font_path='doc/fonts/simfang.ttf')
            im_show = draw_ocr(img, boxes, txts, scores, font_path='LiberationSans-Regular.ttf')
            im_show = Image.fromarray(im_show)

            ocr_output_image_path = self.ocr_output_images_dir / 'result_page_{}.jpg'.format(image_index)
            im_show.save(ocr_output_image_path.as_posix())

        workbook.close()

        self.logger.info('Start images to pdf...')
        input_files_path = self.ocr_output_images_dir / '*.jpg'
        output_file_path = self.output_root_dir_path / r'{}_ocr.pdf'.format(input_pdf_file_path.stem)

        process_result = subprocess.run(
            ['convert',
                input_files_path.as_posix(),
                output_file_path.as_posix()],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)

        self.logger.info(r'Completed images to pdf with result: {}'.format(process_result))

        self.logger.info('OCR output images path: {}'.format(self.ocr_output_images_dir))
        self.logger.info('OCR output pdf path: {}'.format(output_file_path))
        self.logger.info('OCR output excel path: {}'.format(output_excel_file_path))
        self.logger.info('Completed ocr!')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input_pdf_file_path')
    args = parser.parse_args()
    # /content/drive/MyDrive/data/cv/magazine/NT2023-0002RW Bi-Annual Publication 7 Spread v8 Digital FA.pdf
    input_pdf_file_path = Path(args.input_pdf_file_path)

    ocr_logger.setLevel(logging.ERROR)

    ocr_api = OCRAPI()
    ocr_api.ocr(input_pdf_file_path)


if __name__ == '__main__':
    main()
