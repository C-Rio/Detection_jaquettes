# Import required packages
from langdetect import detect
import sqlite3
from Levenshtein import distance
from detection import draw_contour
from pytesseract import image_to_string
import cv2 as cv2

# img = maintain_aspect_ratio_resize(img, 500, inter=cv2.INTER_CUBIC)

res = draw_contour("./Images/MTG/card3.jpg")

# Convert the image to gray scale
gray = cv2.cvtColor(res, cv2.COLOR_BGR2GRAY)
th3 = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 27, 27)
blur = cv2.GaussianBlur(th3, (5, 5), 0)

custom_config = r'-l fra+eng -c tessedit_char_blacklist=<>#![]‘\\\|'
text = (image_to_string(blur, config=custom_config))
final_text = [line for line in text.splitlines() if len(line) > 2 and not line.isupper()]
final_text = ' '.join(final_text)

lang = detect(final_text)

min_dist = 99999999
min_text = ""
min_uuid = None

try:
    sqliteConnection = sqlite3.connect('AllPrintings.sqlite')

    cursor = sqliteConnection.cursor()

    if lang == "en":
        rows = cursor.execute("select name, originalText,flavorText, uuid from cards")
    else:
        lang = "French"
        rows = cursor.execute("select name, text, flavorText, uuid from foreign_data where language=:lang", {"lang": lang})
    for row in rows:
        if row is not None:
            text = ' '.join(x for x in row[:-1] if x is not None)
            dist = distance(final_text, text)
            if dist < min_dist:
                min_dist = dist
                min_text = text
                min_uuid = row[-1]

    rows = cursor.execute("select price, type from prices where uuid=:uuid", {"uuid": min_uuid})

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


print("OCR = ", final_text)
print("Card found =", min_text)
print("Card prices = ", prices)
