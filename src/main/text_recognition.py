import numpy as np
import cv2 as cv
import pytesseract
from imutils.object_detection import non_max_suppression
from utils.utils import box_extractor, forward_passer
import argparse


def get_arguments():
    ap = argparse.ArgumentParser()
    ap.add_argument('-i', '--image', type=str, help='path to image')
    ap.add_argument('-east', '--east', type=str, help='path to Text Detection model')
    ap.add_argument('-c', '--min_confidence', type=float, default=0.5, help='minium confidence to process a region')
    ap.add_argument('-w', '--with', type=int, default=320, help='resized image width (multiple of 32)')
    ap.add_argument('-e', '--height', type=int, default=320, help='reized image height (multiple of 32)')

    arguments = vars(ap.parse_args())

    return arguments


def resize_image(image, width, height):
    h, w = image.shape[:2]
    ratio_h = h / height
    ratio_w = w / width

    image = cv.resize(image, (width, height))
    return image, ratio_w, ratio_h


def main(image, width, height, detector, min_confidence):
    image = cv.imread(image)
    # image = cv.resize(image, (image.shape[0]//5, image.shape[1]//5))
    origin_image = np.copy(image)

    # Reisze image
    image, ratio_h, ratio_w = resize_image(image, width, height)

    # Layer used for ROI Regression
    layer_names = ['feature_fusion/Conv_7/Sigmoid',
                   'feature_fusion/concat_3']

    # Load model
    net = cv.dnn.readNet(detector)

    # Getting result from model
    scores, geometry = forward_passer(net, image, layer_names)

    # Decoding results from the model
    rectangles, confidences = box_extractor(scores, geometry, min_confidence)

    # Applying non-max superession to get boxes depicting text region
    boxes = non_max_suppression(np.array(rectangles), probs=confidences)

    results = []
    # drawing rectangle on the Image
    for (start_x, start_y, end_x, end_y) in boxes:
        start_x = int(start_x * ratio_h)
        start_y = int(start_y * ratio_w)
        end_x = int(end_x * ratio_h)
        end_y = int(end_y * ratio_w)
        # print('({},{}) - ({},{})'.format(start_x, start_y, end_x, end_y))

        roi = origin_image[start_y:end_y, start_x:end_x]

        # recognition Text
        config = '-1 eng --oem 1 --psm 7'
        text = pytesseract.image_to_string(roi, config = config)

        results.append(((start_x, start_y, end_x, end_y), text))

        results.sort(key=lambda r:r[0][1])

        # cv.rectangle(origin_image, (start_x, start_y), (end_x, end_y), (0, 255, 0), 2)

    # Drawing image
    for (start_x, start_y, end_x, end_y), text in results:
        cv.rectangle(origin_image, (start_x, start_y), (end_x, end_y), (0, 255, 0), 1)
        print(text)
        cv.putText(origin_image, text, (start_x, start_y), cv.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 1)

    cv.imshow('Detection !', origin_image)
    cv.waitKey(0)


if __name__ == '__main__':
    args = get_arguments()

    # Setting path pytesseract
    pytesseract.pytesseract.tesseract_cmd = '/usr/share/tesseract-ocr/4.00/tessdata'

    # main(image=args['image'], width=args['width'], height=args['height'],detector=args['east'], min_confidence=args['min_confidence'])
    image_path = '../data/The-architecture-of-CRNN-1-convolutional-layers-extracting-feature-from-the-original.png'
    model = '../model/frozen_east_text_detection.pb'
    height = 320
    width = 320
    min_confidence = 0.65
    main(image_path, width, height, model, min_confidence)