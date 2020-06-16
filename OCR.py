
# Import required packages
import cv2 as cv2
import pytesseract
import numpy as np
from detection import draw_contour
from unidecode import unidecode
import Levenshtein as lev
import sqlite3


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


# img = maintain_aspect_ratio_resize(img, 500, inter=cv2.INTER_CUBIC)

res = draw_contour("./Images/MTG/card2.jpg")

# Convert the image to gray scale
gray = cv2.cvtColor(res, cv2.COLOR_BGR2GRAY)


cv2.imshow("res", res)

th3 = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 27, 27)  # 27, 2


blur = cv2.GaussianBlur(th3, (5, 5), 0)


# cv2.imshow("blur", blur)

# cv2.imshow("th3", th3)
# cv2.waitKey(0)


custom_config = r'-l fra+eng --psm 12 -c tessedit_char_blacklist=<>#!{}‘\\\|'
text = (pytesseract.image_to_string(blur, config=custom_config))
final_text = [line for line in text.splitlines() if len(line) > 2 and not line.isupper()]
final_text = ' '.join(final_text)


try:
    sqliteConnection = sqlite3.connect('AllPrintings.sqlite')

    cursor = sqliteConnection.cursor()
    print("Successfully Connected to SQLite DataBase")

    sqlite_select_Query = "select name, originalText,flavorText, uuid from cards"
    rows = cursor.execute(sqlite_select_Query)
    min_dist = 99999999
    min_text = ""
    min_uuid = None
    for row in rows:
        if row is not None:
            text = ' '.join(x for x in row[:-1] if x is not None)
            # print(text)
            dist = lev.distance(final_text, text)
            if dist < min_dist:
                min_dist = dist
                min_text = text
                min_uuid = row[-1]
            # print(unidecode(row[0]))

    sqlite_select_Query = "select name, text, uuid from foreign_data"
    rows = cursor.execute(sqlite_select_Query)
    for row in rows:
        if row is not None:
            text = ' '.join(x for x in row[:-1] if x is not None)
            # print(text)
            dist = lev.distance(final_text, text)
            if dist < min_dist:
                min_dist = dist
                min_text = text
                min_uuid = row[-1]
            # print(unidecode(row[0]))

    uu = (min_uuid,)

    rows = cursor.execute("select price, type from prices where uuid=?", uu)
    prices = {}
    for row in rows:
        if row is not None:
            prices[row[1]] = row[0]

    cursor.close()

except sqlite3.Error as error:
    print("Error while connecting to sqlite", error)
finally:
    if (sqliteConnection):
        sqliteConnection.close()
        print("The SQLite connection is closed")


print("OCR = ", final_text)
print("Card found =", min_text)
print("Card UUID = ", min_uuid)
print("Card prices = ", prices)
