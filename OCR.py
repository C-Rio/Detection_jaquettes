
# Import required packages
from cv2 import cv2
import pytesseract
import numpy as np
from detection import draw_contour
from unidecode import unidecode


def maintain_aspect_ratio_resize(image, width=None, height=None, inter=cv2.INTER_AREA):
    # Grab the image size and initialize dimensions
    dim = None
    (h, w) = image.shape[:2]

    # Return original image if no need to resize
    if width is None and height is None:
        return image

    # We are resizing height if width is none
    if width is None:
        # Calculate the ratio of the height and construct the dimensions
        r = height / float(h)
        dim = (int(w * r), height)
    # We are resizing width if height is none
    else:
        # Calculate the ratio of the width and construct the dimensions
        r = width / float(w)
        dim = (width, int(h * r))

    # Return the resized image
    return cv2.resize(image, dim, interpolation=inter)


# Read image from which text needs to be extracted
img = cv2.imread("./Images/MTG/card2.jpg")
img = maintain_aspect_ratio_resize(img, 500, inter=cv2.INTER_CUBIC)

img_dim = np.delete(img.shape, 2)

res = draw_contour("./Images/MTG/card2.jpg")

# Convert the image to gray scale
gray = cv2.cvtColor(res, cv2.COLOR_BGR2GRAY)


cv2.imshow("res", res)

th3 = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 27, 27)  # 27, 2


blur = cv2.GaussianBlur(th3, (5, 5), 0)


cv2.imshow("blur", blur)

cv2.imshow("th3", th3)
cv2.waitKey(0)


# contours, hierarchy = cv2.findContours(th3, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
# th4 = cv2.drawContours(th3, contours, -1, color=0, thickness=3)


# lines = np.squeeze(cv2.HoughLinesP(cv2.bitwise_not(th3), 1, np.pi / 180, threshold=250, minLineLength=50, maxLineGap=20))
# print(lines)
# for line in lines:
#     cv2.line(th3, (line[0], line[1]), (line[2], line[3]), (128), 3)


# cv2.imshow("th4", th4)
# cv2.waitKey(0)

custom_config = r'-l fra --psm 12 -c tessedit_char_blacklist=<>#{}|'
text = unidecode(pytesseract.image_to_string(blur, config=custom_config))
final_text = [line for line in text.splitlines() if len(line) > 2 and not line.isupper()]


print(final_text)
