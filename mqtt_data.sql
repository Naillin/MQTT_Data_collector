-- Создаем таблицу Topics
CREATE TABLE Topics (
    ID_Topic INTEGER PRIMARY KEY,
    Name_Topic TEXT NOT NULL,
    Path_Topic TEXT NOT NULL,
    Latitude_Topic REAL,
    Longitude_Topic REAL
);

-- Создаем таблицу Data с каскадным удалением
CREATE TABLE Data (
    ID_Data INTEGER PRIMARY KEY,
    ID_Topic INTEGER NOT NULL,
    Value_Data TEXT,
    Time_Data DATETIME NOT NULL,
    FOREIGN KEY (ID_Topic) REFERENCES Topics(ID_Topic) ON DELETE CASCADE
);
