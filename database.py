import sqlite3 as sq

db = sq.connect('Tokiso_Shop.db')
cur = db.cursor()


async def db_start():
    cur.execute("CREATE TABLE IF NOT EXISTS accounts("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "tg_id INTEGER, "
                "cart_id TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS items("
                "i_id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "name TEXT,"
                "desc TEXT, "
                "price TEXT, "
                "photo TEXT, "
                "brand TEXT)")
    db.commit()


async def cmd_start_db(user_id):
    user = cur.execute("SELECT * FROM accounts WHERE tg_id == {key}".format(key=user_id)).fetchone()
    if not user:
        cur.execute("INSERT INTO accounts (tg_id) VALUES ({key})".format(key=user_id))
        db.commit()


async def add_item(name, desc, price, photo):
    cur.execute("INSERT INTO items (name, desc, price, photo) VALUES (?, ?, ?, ?)",
                (name, desc, price, photo))
    db.commit()


async def get_all_products():
    # sql-запрос на выбор всех товаров из таблицы items
    cur.execute('SELECT * FROM items')

    # узнаем названия столбцов из описания (метаданных) результата запроса
    columns = [column[0] for column in cur.description]

    # извлекаем все строки результата запроса и преобразуем в список словарей
    products = [dict(zip(columns, row)) for row in cur.fetchall()]
    return products


async def delete_items_by_name(name):
    cur.execute("DELETE FROM items WHERE name=?", (name,))
    db.commit()


async def get_product_by_id(item_id):
    cur.execute("SELECT * FROM items WHERE i_id=?", (item_id,))
    columns = [column[0] for column in cur.description]
    product = dict(zip(columns, cur.fetchone()))
    return product