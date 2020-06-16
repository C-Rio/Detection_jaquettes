import sqlite3
from unidecode import unidecode

try:
    sqliteConnection = sqlite3.connect('AllPrintings.sqlite')

    cursor = sqliteConnection.cursor()
    print("Successfully Connected to SQLite DataBase")

    sqlite_select_Query = "select originalText from cards"
    rows = cursor.execute(sqlite_select_Query)
    for row in rows:
        if row is not None:
            print(row[0])
            # print(unidecode(row[0]))
    cursor.close()

except sqlite3.Error as error:
    print("Error while connecting to sqlite", error)
finally:
    if (sqliteConnection):
        sqliteConnection.close()
        print("The SQLite connection is closed")
