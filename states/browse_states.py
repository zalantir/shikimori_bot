from telebot.handler_backends import State, StatesGroup


class MenuStates(StatesGroup):
    default = State()  # базовое меню, доступное по умолчанию
