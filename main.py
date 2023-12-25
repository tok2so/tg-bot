from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
import keyboards as kb
import database as db
from config import TOKEN, ADMIN_ID
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, \
    InlineKeyboardButton

storage = MemoryStorage()
bot = Bot(TOKEN)
dp = Dispatcher(bot=bot, storage=storage)


async def on_startup(_):
    await db.db_start()
    print('Бот запущен!')


class NewOrderDelivery(StatesGroup):
    waiting_for_name = State()
    waiting_for_desc = State()
    waiting_for_photo = State()
    waiting_for_price = State()
    waiting_for_name_for_deletion = State()


@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await db.cmd_start_db(message.from_user.id)
    await message.answer('Добро пожаловать в Tokiso Shop', reply_markup=kb.main)
    if message.from_user.id == int(ADMIN_ID):
        await message.answer('Ты авторизовался как админ!', reply_markup=kb.main_admin)


@dp.message_handler(text='Каталог')
async def catalog_menu(message: types.Message):
    products = await db.get_all_products()

    if products:
        for product in products:
            product_info = f"{product['name']}\n{product['desc']}\nЦена: {product['price']} тг"

            pay_button = InlineKeyboardButton(text=f'Оплатить {product["price"]} тг',
                                              callback_data=f'payment_{product["i_id"]}')

            inline_keyboard = InlineKeyboardMarkup(row_width=1)
            inline_keyboard.add(pay_button)

            # Проверяем наличие фото перед отправкой
            if 'photo' in product and product['photo']:
                await bot.send_photo(message.from_user.id, photo=product['photo'], caption=product_info,
                                     reply_markup=inline_keyboard)
            else:
                await bot.send_message(message.from_user.id, product_info, reply_markup=inline_keyboard)
    else:
        await bot.send_message(message.from_user.id, 'В каталоге нет товаров')


@dp.callback_query_handler(lambda query: query.data.startswith('pay'), state='*')
async def pay_callback(query: types.CallbackQuery, state: FSMContext):
    # Получаем информацию о товаре
    item_id = int(query.data.split('_')[1])
    product = await db.get_product_by_id(item_id)

    # Отправляем информацию об оплате админу
    await bot.send_message(ADMIN_ID, f"Пользователь (@{query.from_user.username}) Хочет оплатить товар:\n"
                                     f"{product['name']}\n{product['desc']}\nЦена: {product['price']} тг."
                           "Так же, вы можете перевести деньги на каспи. Номер: +7(775)587-00-02.")

    admin_contact_button = InlineKeyboardButton(text='Связаться с администратором',
                                                url='https://t.me/TokisoShopSupport')
    admin_contact_keyboard = InlineKeyboardMarkup().add(admin_contact_button)
    await bot.send_message(query.from_user.id, "Ожидайте, администратор свяжется с вами для завершения оплаты.",
                           reply_markup=admin_contact_keyboard)

    await query.answer('Администратору отправлен запрос на оплату. Пожалуйста, ожидайте.')


@dp.message_handler(text='Контакты')
async def contacts(message: types.Message):
    await message.answer('По всем вопросам и предложениям --> @TokisoShopSupport')


@dp.message_handler(text='Админ-панель')
async def admin_panel(message: types.Message):
    if message.from_user.id == int(ADMIN_ID):
        await message.answer('Ты вошел в админ-панель', reply_markup=kb.admin_panel)
    else:
        await message.reply('Ты не админ')


@dp.callback_query_handler(lambda query: query.data.startswith('delete_item'), state='*')
async def delete_item_callback(query: types.CallbackQuery, state: FSMContext):
    if query.from_user.id == int(ADMIN_ID):
        item_id = int(query.data.split('_')[2])
        await db.delete_item(item_id)
        await query.answer('Товар удален')
    else:
        await query.answer('У вас нет прав на удаление товаров')


@dp.message_handler(text='Удалить товар')
async def delete_items_by_name(message: types.Message):
    if message.from_user.id == int(ADMIN_ID):
        await message.answer('Введите название товара для удаления:')
        await NewOrderDelivery.waiting_for_name_for_deletion.set()
    else:
        await message.reply('Вы не администратор.')


@dp.message_handler(text='Добавить товар')
async def add_item_admin(message: types.Message):
    if message.from_user.id == int(ADMIN_ID):
        await message.answer('Название товара:')
        await NewOrderDelivery.waiting_for_name.set()
    else:
        await message.reply('Я тебя не понимаю.')


@dp.message_handler(state=NewOrderDelivery.waiting_for_name, content_types=types.ContentType.TEXT)
async def process_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:  # Получаем данные из состояния
        data['name'] = message.text

    await message.answer('Описание товара:')
    await NewOrderDelivery.waiting_for_desc.set()


@dp.message_handler(state=NewOrderDelivery.waiting_for_desc, content_types=types.ContentType.TEXT)
async def process_desc(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['desc'] = message.text

    await message.answer('Фото товара:')
    await NewOrderDelivery.waiting_for_photo.set()


@dp.message_handler(state=NewOrderDelivery.waiting_for_photo, content_types=types.ContentType.PHOTO)
async def process_photo(message: types.Message, state: FSMContext):
    photo = message.photo[-1]  # используем последнее фото из отправленных
    photo_file_id = photo.file_id

    async with state.proxy() as data:
        data['photo'] = photo_file_id

    await message.answer('Цена товара:')
    await NewOrderDelivery.waiting_for_price.set()


@dp.message_handler(state=NewOrderDelivery.waiting_for_price, content_types=types.ContentType.TEXT)
async def process_price(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['price'] = message.text

    await db.add_item(data['name'], data['desc'], data['price'], data['photo'])

    await state.finish()
    await message.answer(f'Товар "{data["name"]}" успешно добавлен в каталог.')


@dp.message_handler(state=NewOrderDelivery.waiting_for_name_for_deletion, content_types=types.ContentType.TEXT)
async def process_name_for_deletion(message: types.Message, state: FSMContext):
    await db.delete_items_by_name(message.text)
    await state.finish()
    await message.answer(f'Товары с названием "{message.text}" удалены')


if __name__ == '__main__':
    from aiogram import executor

    executor.start_polling(dp, on_startup=on_startup)