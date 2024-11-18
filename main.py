import paho.mqtt.client as mqtt
import sqlite3
import time

# Подключение к базе данных
conn = sqlite3.connect('mqtt_data.db')
cursor = conn.cursor()


# Чтение списка топиков из базы
def get_topics():
    cursor.execute("SELECT ID_Topic, Path_Topic FROM Topics")
    return cursor.fetchall()


# Функция для обработки входящих сообщений
def on_message(client, userdata, message):
    topic_path = message.topic
    value = message.payload.decode()
    timestamp = int(time.time())

    # Найти ID_Topic по Path_Topic
    cursor.execute("SELECT ID_Topic FROM Topics WHERE Path_Topic = ?", (topic_path,))
    topic_row = cursor.fetchone()

    if topic_row:
        id_topic = topic_row[0]
        # Сохранить данные в таблицу Data
        cursor.execute("INSERT INTO Data (ID_Topic, Value_Data, Time_Data) VALUES (?, ?, ?)",
                       (id_topic, value, timestamp))
        conn.commit()
        print(f"Сохранены данные: Топик {topic_path}, Значение {value}, Время {timestamp}")


# Инициализация MQTT клиента
client = mqtt.Client(protocol=mqtt.MQTTv311)
client.on_message = on_message
client.connect("localhost", 3121)


# Обновление подписок
def update_subscriptions():
    client.unsubscribe("#")  # Отписаться от всех топиков
    topics = get_topics()
    for id_topic, path_topic in topics:
        client.subscribe(path_topic)
        print(f"Подписка на {path_topic}")


# Основной цикл
try:
    while True:
        update_subscriptions()
        client.loop(timeout=1.0)  # Постоянно проверяем входящие сообщения
        time.sleep(5)  # Обновлять список топиков каждые 5 секунд
except KeyboardInterrupt:
    print("Отключение клиента")
    client.disconnect()
    conn.close()
