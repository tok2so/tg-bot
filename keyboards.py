from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup

main = ReplyKeyboardMarkup(resize_keyboard=True)
main.add('Каталог').add('Контакты')

main_admin = ReplyKeyboardMarkup(resize_keyboard=True)
main_admin.add('Админ-панель').add('Каталог').add('Контакты')

admin_panel = ReplyKeyboardMarkup(resize_keyboard=True)
admin_panel.add('Добавить товар').add('Удалить товар')

cancel = ReplyKeyboardMarkup(resize_keyboard=True)
cancel.add('Отмена')

# delete_confirmation = InlineKeyboardMarkup(row_width=2)
# delete_confirmation.add(InlineKeyboardButton(text='Да', callback_data='delete_yes'),
#                         InlineKeyboardButton(text='Нет', callback_data='delete_no'))
