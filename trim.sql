drop table rulings;
drop table set_translations;
drop table sets;
drop table tokens;
drop table legalities;

-- Filter cards table
BEGIN TRANSACTION;
CREATE TEMPORARY TABLE t1_backup(name, Text, flavorText, type, uuid, id);
INSERT INTO t1_backup SELECT name, Text, flavorText, type, uuid, id FROM cards;
DROP TABLE cards;
CREATE TABLE cards(name, Text, flavorText, type, uuid, id);
INSERT INTO cards SELECT name, Text, flavorText, type, uuid, id FROM t1_backup;
DROP TABLE t1_backup;
COMMIT;


-- Remove non-french data
delete from foreign_data where language != "French";

-- Remove non-physical data
delete from prices where type = "mtgo";
delete from prices where type = "mtgoFoil";

-- Filter foreign_data 
BEGIN TRANSACTION;
CREATE TEMPORARY TABLE t2_backup(name, text, flavorText, type, uuid, id);
INSERT INTO t2_backup SELECT name, text, flavorText, type, uuid, id FROM foreign_data;
DROP TABLE foreign_data;
CREATE TABLE foreign_data(name, text, flavorText, type, uuid, id);
INSERT INTO foreign_data SELECT name, text, flavorText, type, uuid, id FROM t2_backup;
DROP TABLE t2_backup;
COMMIT;


-- Filter prices
BEGIN TRANSACTION;
CREATE TEMPORARY TABLE t3_backup(price, type, uuid, id);
INSERT INTO t3_backup SELECT price, type, uuid, id FROM prices;
DROP TABLE prices;
CREATE TABLE prices(price, type, uuid, id);
INSERT INTO prices SELECT price, type, uuid, id FROM t3_backup;
DROP TABLE t3_backup;
COMMIT;

-- Reduce DB file size
vacuum;