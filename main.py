import paho.mqtt.client as mqtt
import sqlite3
import time

# Чтение списка топиков из базы
def get_topics():
    # Открытие соединения и курсора для чтения
    with sqlite3.connect('mqtt_data.db') as conn:
        conn.execute('PRAGMA journal_mode=WAL')
        cursor = conn.cursor()
        cursor.execute("SELECT ID_Topic, Path_Topic FROM Topics")
        return cursor.fetchall()

# Функция для обработки входящих сообщений
def on_message(client, userdata, message):
    topic_path = message.topic
    value = message.payload.decode()
    timestamp = int(time.time())
    print(f"Полученно сообщение: Топик {topic_path}, Значение {value}, Время {timestamp}")

    # Открытие соединения для записи данных в базу
    with sqlite3.connect('mqtt_data.db') as conn:
        conn.execute('PRAGMA journal_mode=WAL')
        cursor = conn.cursor()

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

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Успешное подключение к брокеру")
    else:
        print(f"Ошибка подключения: {rc}")

def on_subscribe(client, userdata, mid, granted_qos):
    print(f"Подписка выполнена: mid={mid}, QoS={granted_qos}")

def on_log(client, userdata, level, buf):
    print(f"MQTT лог: {buf}")

# Инициализация MQTT клиента
print("Запуск программы...")
client = mqtt.Client(protocol=mqtt.MQTTv311)
print("Задаем логин и пароль...")
client.username_pw_set("", "")
client.on_log = on_log
client.on_message = on_message
client.on_connect = on_connect
client.on_subscribe = on_subscribe
print("Подключение к брокеру...")
client.connect("localhost", 3121)

# Обновление подписок
def update_subscriptions():
    # Открытие соединения и курсора для чтения
    with sqlite3.connect('mqtt_data.db') as conn:
        conn.execute('PRAGMA journal_mode=WAL')
        cursor = conn.cursor()
        client.unsubscribe("#")  # Отписаться от всех топиков
        topics = get_topics()  # Получить список топиков
        print("Топики из базы:", topics)
        for id_topic, path_topic in topics:
            client.subscribe(path_topic)
            print(f"Подписка на {path_topic}")

# Основной цикл
client.loop_start()
try:
    while True:
        update_subscriptions()
        time.sleep(5)
except KeyboardInterrupt:
    print("Отключение клиента")
    client.loop_stop()
    client.disconnect()
