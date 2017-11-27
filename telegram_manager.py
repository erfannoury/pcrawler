import subprocess
from telegram.ext import Updater, CommandHandler, MessageHandler, \
    Filters, ConversationHandler


# Telegram API
# access  bot via token
updater = Updater(token='HTTP API')
dispatcher = updater.dispatcher

admins = [55555555, 55555556]
BAN = 1


def filewrite(filename, mode, string):
    f = open(filename, mode)
    f.write(str(string))
    f.close()


def start(bot, update):
    if update.message.from_user.id in admins:
        update.message.reply_text('Hi , Command my lord \n /ban')


def ban(bot, update):
    if update.message.from_user.id in admins:
        update.message.reply_text('give me user profile url for ban')
        return BAN


def ban_user(bot, update):
    if update.message.from_user.id in admins:
        userurl = update.message.text
        id = userurl.split('/')[-1]
        try:
            filewrite('users_blacklist.txt', 'a', id + '\n')
            update.message.reply_text(id + ' added to blacklist!')
            subprocess.run(
                'sudo systemctl restart service',
                shell=False,
                stdout=subprocess.PIPE)
        except Exception as e:
            update.message.reply_text('sorry,we have some trouble')


def cancel(bot, update):
    update.message.reply_text('canceled')


def main():
    # handlers
    # start_handler = CommandHandler('start', start)
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            CommandHandler('ban', ban)],

        states={
            BAN: [MessageHandler(Filters.text, ban_user)],
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )
    #
    dispatcher.add_handler(conv_handler)
    # handle dispatcher
    # dispatcher.add_handler(start_handler)

    # run
    updater.start_polling()
    updater.idle()
    updater.stop()


if __name__ == '__main__':
    main()
