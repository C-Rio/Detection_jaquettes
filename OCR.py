# Import required packages
import cv2 as cv2
import pytesseract
from detection import draw_contour
import Levenshtein as lev
import sqlite3
from langdetect import detect


# img = maintain_aspect_ratio_resize(img, 500, inter=cv2.INTER_CUBIC)

res = draw_contour("./Images/MTG/card.jpg")

# Convert the image to gray scale
gray = cv2.cvtColor(res, cv2.COLOR_BGR2GRAY)
th3 = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 27, 27)  # 27, 2
blur = cv2.GaussianBlur(th3, (5, 5), 0)

custom_config = r'-l fra+eng -c tessedit_char_blacklist=<>#![]‘\\\|'
text = (pytesseract.image_to_string(blur, config=custom_config))
final_text = [line for line in text.splitlines() if len(line) > 2 and not line.isupper()]
final_text = ' '.join(final_text)

lang = detect(final_text)
print(lang)

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
        rows = cursor.execute("select name, text, uuid from foreign_data where language=:lang", {"lang": lang})

    for row in rows:
        if row is not None:
            text = ' '.join(x for x in row[:-1] if x is not None)
            dist = lev.distance(final_text, text)
            if dist < min_dist:
                min_dist = dist
                min_text = text
                min_uuid = row[-1]

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


print("OCR = ", final_text)
print("Card found =", min_text)
print("Card prices = ", prices)
