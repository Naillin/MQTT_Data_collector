import paho.mqtt.client as mqtt
import sqlite3
import time
import logging
import platform
from logging.handlers import SysLogHandler

# Чтение списка топиков из базы
def get_topics():
    """
    Retrieves a list of topics from the SQLite database.

    Returns:
        list: A list of tuples containing the ID and path of each topic.
    """
    # Открытие соединения и курсора для чтения
    with sqlite3.connect('mqtt_data.db') as conn:
        conn.execute('PRAGMA journal_mode=WAL')
        cursor = conn.cursor()
        cursor.execute("SELECT ID_Topic, Path_Topic FROM Topics")
        return cursor.fetchall()

# Функция для обработки входящих сообщений
def on_message(client, userdata, message):
    """
    Handles incoming MQTT messages by processing the topic path, payload value, and timestamp.

    Parameters:
        client (object): The MQTT client instance.
        userdata (object): The user data associated with the MQTT client.
        message (object): The incoming MQTT message.

    Returns:
        None
    """
    topic_path = message.topic
    raw_value = message.payload.decode()
    timestamp = int(time.time())
    log_string = f"Полученно сообщение: Топик {topic_path}, Значение {raw_value}, Время {timestamp}"
    logger.info(log_string)
    print(log_string)

    value = 0.0
    # Проверяем, является ли значение числом (целым или дробным)
    try:
        value = float(raw_value)  # Пробуем преобразовать в число
    except ValueError:
        error_msg = f"Ошибка: Некорректное числовое значение '{raw_value}' в топике {topic_path}"
        logger.warning(error_msg)
        print(error_msg)
        return  # Прекращаем выполнение функции

    # Открытие соединения для записи данных в базу
    with sqlite3.connect('mqtt_data.db') as conn:
        conn.execute('PRAGMA journal_mode=WAL')
        cursor = conn.cursor()

        # Найти ID_Topic по Path_Topic
        cursor.execute("SELECT ID_Topic, AltitudeSensor_Topic FROM Topics WHERE Path_Topic = ?", (topic_path,))
        topic_row = cursor.fetchone()

        if topic_row:
            id_topic = topic_row[0]
            level = topic_row[1] - value
            # Сохранить данные в таблицу Data
            cursor.execute("INSERT INTO Data (ID_Topic, Value_Data, Time_Data) VALUES (?, ?, ?)",
                           (id_topic, level, timestamp))
            conn.commit()
            log_string = f"Сохранены данные: Топик {topic_path}, Значение {level}, Время {timestamp}"
            logger.info(log_string)
            print(log_string)

def on_connect(client, userdata, flags, rc):
    """
    Handles the connection event of the MQTT client.

    Parameters:
        client (object): The MQTT client instance.
        userdata (object): The user data associated with the MQTT client.
        flags (int): The connection flags.
        rc (int): The connection result code.

    Returns:
        None
    """
    log_string = f"on_connect вызван с кодом: {rc}"
    logger.info(log_string)
    print(log_string)
    if rc == 0:
        log_string = "Успешное подключение к брокеру"
        logger.info(log_string)
        print(log_string)
    else:
        log_string = f"Ошибка подключения: {rc}"
        logger.info(log_string)
        print(log_string)

def on_subscribe(client, userdata, mid, granted_qos):
    """
    Handles the subscription event of the MQTT client.

    Parameters:
        client (object): The MQTT client instance.
        userdata (object): The user data associated with the MQTT client.
        mid (int): The message ID.
        granted_qos (int): The granted Quality of Service.

    Returns:
        None
    """
    log_string = f"Подписка выполнена: mid={mid}, QoS={granted_qos}"
    logger.info(log_string)
    print(log_string)

def on_log(client, userdata, level, buf):
    """
    Handles the logging event of the MQTT client.

    Parameters:
        client (object): The MQTT client instance.
        userdata (object): The user data associated with the MQTT client.
        level (int): The logging level.
        buf (str): The log message buffer.

    Returns:
        None
    """
    log_string = f"MQTT лог: {buf}"
    logger.info(log_string)
    print(log_string)

# Настройка логгера
logger = logging.getLogger('mqtt-data-collector')
logger.setLevel(logging.INFO)

if platform.system() == 'Windows':
    # Логгер для Windows (в файл)
    file_handler = logging.FileHandler('mqtt-data-collector-logs.log')
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(message)s'))
    logger.addHandler(file_handler)
else:
    # Логгер для Linux (в syslog через systemd)
    syslog_handler = SysLogHandler(address='/dev/log')
    syslog_handler.setFormatter(logging.Formatter('%(name)s: %(message)s'))
    logger.addHandler(syslog_handler)

# Инициализация MQTT клиента
logger.info("Запуск программы...")
print("Запуск программы...")
client = mqtt.Client(client_id="DataCollector", protocol=mqtt.MQTTv311)
logger.info("Задаем логин и пароль...")
print("Задаем логин и пароль...")
client.username_pw_set("", "")
client.on_log = on_log
client.on_message = on_message
client.on_connect = on_connect
client.on_subscribe = on_subscribe
logger.info("Подключение к брокеру...")
print("Подключение к брокеру...")
client.connect("127.0.0.1", 3121)

# Обновление подписок
def update_subscriptions():
    """
    Updates the MQTT client subscriptions by unsubscribing from all topics,
    retrieving the list of topics from the database, and then subscribing to each topic.

    Parameters:
        None

    Returns:
        None
    """
    # Открытие соединения и курсора для чтения
    with sqlite3.connect('mqtt_data.db') as conn:
        conn.execute('PRAGMA journal_mode=WAL')
        cursor = conn.cursor()
        client.unsubscribe("#")  # Отписаться от всех топиков
        topics = get_topics()  # Получить список топиков
        log_string = f"Топики из базы:, {topics}"
        logger.info(log_string)
        print(log_string)
        for id_topic, path_topic in topics:
            client.subscribe(path_topic)
            log_string = f"Подписка на {path_topic}"
            logger.info(log_string)
            print(log_string)

# Основной цикл
client.loop_start()
try:
    while True:
        update_subscriptions()
        time.sleep(5)
except KeyboardInterrupt:
    logger.info("Отключение клиента")
    print("Отключение клиента")
    client.loop_stop()
    client.disconnect()
