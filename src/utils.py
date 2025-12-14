import cv2
import numpy as np


def match_template_in_image(image, template, threshold=0.8):
    """
    Find locations in 'image' that match the 'template' above a threshold.
    Returns a list of tuples (x1, y1, x2, y2, score).
    """
    img_gray = np.array(image.convert('L'))
    template_gray = np.array(template.convert('L'))
    # template_gray.shape -> (h, w)
    h, w = template_gray.shape
    # matchTemplate expects (w,h) in some uses; we use TM_CCOEFF_NORMED
    res = cv2.matchTemplate(img_gray, template_gray, cv2.TM_CCOEFF_NORMED)
    loc = np.where(res >= threshold)
    boxes = []
    for pt in zip(*loc[::-1]):
        x1, y1 = pt[0], pt[1]
        score = float(res[y1, x1])
        x2, y2 = x1 + w, y1 + h
        boxes.append((x1, y1, x2, y2, score))
    return boxes


def compute_scale_down(input_size, output_size):
    """compute scale down factor of neural network, given input and output size"""
    return output_size[0] / input_size[0]


def prob_true(p):
    """return True with probability p"""
    return np.random.random() < p
