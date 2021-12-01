import psycopg2
import config
import datetime
from aiogram import types


def chek_user(info: types.User):
    """
    Вызывается во время ввода команды /start
    Проверяем нет ли пользователя в нашей Бд, в таблице user_tg
    В случае отсутствия записываем id пользователя и его nickname
    :param info: message.from_user из сообщения телеги
    """
    with psycopg2.connect(host=config.HOST, database=config.DBNAME, user=config.USER, password=config.PASSWORD) as conn:
        cur = conn.cursor()
        cur.execute("Select * from user_tg Where user_id = %s" % info.id)
        records = cur.fetchall()
        if len(records) == 0:
            cur.execute("INSERT INTO user_tg (date_in, user_id, mention) VALUES ('%s', %s, '%s')"
                        % (datetime.date.today().strftime('%Y.%m.%d'), info.id, info.mention))


def chek_paper(paper: str):
    """
    Проверяем была ли записана инфа о запрашиваемом тикере ранее.
    Если новая бумага, пишем в базу.
    Если бумага ранее имелась, увеличиваем ее счетчик просмотра
    :param paper: тикер бумаги, который мы проверяем
    :return:
    """
    with psycopg2.connect(host=config.HOST, database=config.DBNAME, user=config.USER, password=config.PASSWORD) as conn:
        cur = conn.cursor()
        cur.execute("select * from ask_paper where paper = '%s' and date_in = '%s'"
                    % ('#' + paper, datetime.date.today().strftime('%Y.%m.%d')))
        records = cur.fetchall()
        if len(records) == 0:
            cur.execute("insert into ask_paper (date_in, paper, value) values ('%s', '#%s', 1)"
                        % (datetime.date.today().strftime('%Y.%m.%d'), paper.lower()))
        else:
            cur.execute("""update ask_paper 
                            set 
                                value = value + 1
                            WHERE 
                                paper = '#%s' and
                                date_in = '%s'""" % (paper.lower(), datetime.date.today().strftime('%Y.%m.%d')))


def get_paper(interval: str):
    """
    Функция возвращает запрашиваемые бумаги за поселднюю неделю
    date: ожидаем д
    :return:
    """
    with psycopg2.connect(host=config.HOST, database=config.DBNAME, user=config.USER, password=config.PASSWORD) as conn:
        cur = conn.cursor()
        cur.execute("""
                    SELECT PAPER, 
                    SUM(VALUE) 
                    FROM ASK_PAPER
                    WHERE DATE_IN > (CURRENT_DATE - interval '%s')
                    GROUP BY PAPER""" % interval)
        records = cur.fetchall()
        return records


def get_count_user_bot():
    """
    Функция возвращает количестко пользователей подписанных на бот
    :return: 
    """
    with psycopg2.connect(host=config.HOST, database=config.DBNAME, user=config.USER, password=config.PASSWORD) as conn:
        cur = conn.cursor()
        cur.execute("""
                    select count(user_id) from user_tg
                    """)
        records = cur.fetchall()
        return records[0][0]


def get_id_user_bot():
    with psycopg2.connect(host=config.HOST, database=config.DBNAME, user=config.USER, password=config.PASSWORD) as conn:
        cur = conn.cursor()
        cur.execute("""
                    select user_id from user_tg
                    """)
        records = cur.fetchall()
        return records


def chek_paper_in_wl(id_user: int, paper: str):
    with psycopg2.connect(host=config.HOST, database=config.DBNAME, user=config.USER, password=config.PASSWORD) as conn:
        curr = conn.cursor()
        curr.execute("select paper from watch_list where id_user = %s and paper = '%s'"
                     % (id_user, paper))
        rec = curr.fetchall()
        return rec


def add_paper_in_wl(id_user, paper):
    with psycopg2.connect(host=config.HOST, database=config.DBNAME, user=config.USER, password=config.PASSWORD) as conn:
        curr = conn.cursor()
        curr.execute("insert into watch_list (id_user, paper) values (%s, '%s')"
                     % (id_user, paper))


def del_paper_in_wl(id_user, paper):
    """
    Скорректировать запрос
    :param id_user:
    :param paper:
    :return:
    """
    with psycopg2.connect(host=config.HOST, database=config.DBNAME, user=config.USER, password=config.PASSWORD) as conn:
        curr = conn.cursor()
        curr.execute("delete from watch_list where id_user = %s and paper = '%s'" % (id_user, paper))


def get_my_watch_list(id_user: int):
    with psycopg2.connect(host=config.HOST, database=config.DBNAME, user=config.USER, password=config.PASSWORD) as conn:
        curr = conn.cursor()
        curr.execute("select paper from watch_list where id_user = %s" % id_user)
        return curr.fetchall()