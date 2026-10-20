"""Reproduce the approved object-image preparation, separate from stack blending."""
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageOps

HERE = Path(__file__).resolve().parent
SIZE = 512


def load_rgb(name):
    with Image.open(HERE/'input'/name) as original:
        rgba = ImageOps.exif_transpose(original).convert('RGBA')
        background = Image.new('RGBA', rgba.size, 'white')
        background.alpha_composite(rgba)
    return np.asarray(background.convert('RGB'), dtype=float)/255


def prepare_object(name, background):
    image = load_rgb(name)
    hsv = cv2.cvtColor(np.round(image*255).astype('uint8'), cv2.COLOR_RGB2HSV)
    if background == 'black':
        foreground = (image.max(2) > .06).astype('uint8') if name == 'mars.jpeg' else ((hsv[...,1] > 40) & (hsv[...,2] > 40)).astype('uint8')
    else:
        foreground = ((hsv[...,1] > 65) & (hsv[...,2] > 45)).astype('uint8')
    contours, _ = cv2.findContours(foreground, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contour = max(contours, key=cv2.contourArea)
    silhouette = np.zeros(foreground.shape, dtype='uint8')
    cv2.drawContours(silhouette, [contour], -1, 1, cv2.FILLED)
    if background == 'black':
        x,y,w,h = cv2.boundingRect(contour)
        silhouette = cv2.erode(silhouette, np.ones((3,3), 'uint8'))
        alpha = cv2.GaussianBlur(silhouette.astype(float), (0,0), .7)[...,None]
        prepared = image*alpha
    else:
        _,_,stats,_ = cv2.connectedComponentsWithStats(foreground)
        k = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
        x,y,w,h = map(int, stats[k,:4])
        alpha = cv2.GaussianBlur(silhouette.astype(float), (0,0), .8)[...,None]
        prepared = image*alpha + (1-alpha)
    scale = 384/max(w,h)
    matrix = np.array([[scale,0,256-scale*(x+w/2)], [0,scale,256-scale*(y+h/2)]])
    border = (0,0,0) if background == 'black' else (1,1,1)
    result = cv2.warpAffine(prepared, matrix, (SIZE,SIZE), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=border)
    return result, {'file':name, 'foreground_bbox':[x,y,w,h], 'matrix':matrix.tolist(), 'background':background,
                    'preparation':'Filled external foreground contour; black backdrop uses one source-pixel erosion and sigma .7 edge softness; white backdrop uses sigma .8. Uniform scale and bilinear translation.'}


def prepare_face(name, source, target, crop_left=None):
    image = load_rgb(name)
    if crop_left is not None:
        image[:,:crop_left] = 1
    matrix = cv2.getAffineTransform(np.float32(source), np.float32(target))
    result = cv2.warpAffine(image, matrix, (SIZE,SIZE), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(1,1,1))
    return result, {'file':name, 'source_points':source, 'target_points':target, 'crop_left':crop_left,
                    'matrix':matrix.tolist(), 'preparation':'Manual three-point affine alignment of visible cut face; bilinear resampling and white outside the source. crop_left removes the neighboring whole lime.'}


def match_chroma(image, reference, region):
    lab = cv2.cvtColor(image.astype('float32'), cv2.COLOR_RGB2LAB)
    reference_lab = cv2.cvtColor(reference.astype('float32'), cv2.COLOR_RGB2LAB)
    shift = np.median(reference_lab[region,1:], axis=0) - np.median(lab[region,1:], axis=0)
    lab[...,1:] += shift
    return cv2.cvtColor(lab, cv2.COLOR_LAB2RGB).astype(float), shift.tolist()


def prepare_cases():
    mars,mi = prepare_object('mars.jpeg','black')
    cookie,ci = prepare_object('cookie.jpg','black')
    ball,bi = prepare_object('basketball.png','white')
    orange,oi = prepare_object('orange.jpg','white')
    kiwi,ki = prepare_face('kiwi-whole.jpg', [[710,490],[910,480],[710,320]], [[260,235],[424,235],[260,90]])
    lime,li = prepare_face('lime.jpg', [[2350,720],[2910,700],[2350,190]], [[260,235],[424,235],[260,90]], crop_left=1600)
    return [
        {'id':'mars-cookie','title':'Mars Cookie: an edible planet','mask':'vertical','a':mars,'b':cookie,'source_a':mi,'source_b':ci,'vertices':None},
        {'id':'orange-basketball','title':'Basketball texture in an orange','mask':'irregular','a':ball,'b':orange,'source_a':bi,'source_b':oi,
         'vertices':[[273,87],[344,106],[401,157],[422,222],[407,296],[354,366],[286,411],[250,363],[259,302],[233,248],[253,187]]},
        {'id':'kiwi-lime','title':'Kiwi seeds in a lime','mask':'irregular','a':kiwi,'b':lime,'source_a':ki,'source_b':li,
         'vertices':[[150,170],[200,120],[275,112],[337,150],[374,218],[362,289],[302,341],[227,338],[158,296],[133,232]]},
    ]
