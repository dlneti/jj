#!/usr/bin/env python
# -*- coding: utf-8 -*-

from telegram import Bot, TelegramError
from telegram.ext import Updater, CommandHandler, Filters
from modules import *


logger = logging.getLogger(__name__)
formatter = logging.Formatter(config["log_format"])

file_handler = logging.FileHandler('main.log')
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.setLevel(logging.INFO)

def start(bot, update):

    message = "Hi, my name is Marvin. Please, be nice to me."
    message += "\nAll I can do (for now) is tell you some basic info about a coin."
    message += "\n\nType: '/price (name/symbol of a coin)' and watch the magic happen!"
    message += "\nExample: /price bitcoin OR /price btc"
    message += "\n\nMore updates 'soon'"

    bot.send_message(chat_id=update.message.chat_id, text=message)
    logger.info("/start {0}:{1}:{2}:{3}-{4}".format(
        update.message.from_user['username'],
        update.message.from_user['id'],
        update.message.from_user['language_code'],
        update.message.chat_id,
        update.message.chat.type)
    )

def error(bot, update, error):
    logger.warn('Update {0} caused error {1}'.format(update, error))

def getPrice(bot, update, args):


    try:
        response = getCoinPrice(args[0])
    except IndexError:
        message = "I can't read your mind (yet). If you don't specify a coin"
        message += ", how do I know what coin to check?"
        bot.send_message(chat_id=update.message.chat_id, text=message)

        logger.info("/price [] {0}:{1}:{2}:{3}-{4}".format(
            ','.join(args),
            update.message.from_user['username'],
            update.message.from_user['id'],
            update.message.from_user['language_code'],
            update.message.chat_id,
            update.message.chat.type)
        )
    else:
        if not response:
            message = "'{}' is not in my database. Check your spelling.".format(args[0])
            bot.send_message(chat_id=update.message.chat_id, text=message)

            logger.info("/price {0}:NOT_FOUND {1}:{2}:{3}:{4}-{5}".format(
                ','.join(args),
                update.message.from_user['username'],
                update.message.from_user['id'],
                update.message.from_user['language_code'],
                update.message.chat_id,
                update.message.chat.type)
            )

        else:

            name = response['name']
            rank = response['rank']
            symbol = response['symbol']
            price_usd = thousandify(str(round(float(response['price_usd']), 3)))
            price_btc = response['price_btc']
            percent_change_24h = response['percent_change_24h']
            c_sign = '+' if float(percent_change_24h) >= 0 else ''
            volume_24_usd = thousandify(response['volume_24_usd'])
            market_cap_usd = thousandify(response['market_cap_usd'])
            b_price = response['binance_price']

            message = "<pre>{} ({})</pre>".format(name, symbol)
            message += "\n<pre>Rank   | {}</pre>".format(rank)
            message += "\n<pre>Price  | ${} - {}{}</pre>".format(
                price_usd, u"\u0243".encode('utf-8'), price_btc)
            message +="\n<pre>Change | {}{}%  (24H)</pre>".format(
                c_sign, str(percent_change_24h)
            )
            message += "\n<pre>Volume | ${}  (24H)</pre>".format(volume_24_usd)
            message += "\n<pre>MC     | ${}</pre>".format(market_cap_usd)

            bot.send_message(chat_id=update.message.chat_id,
                             parse_mode='HTML', text=message)

            if b_price:
                b_sign = '${}'.format(b_price[:-6]) if args[0].upper(
                    ) == 'BTC' else '{}{}'.format(
                        u"\u0243".encode('utf-8'), b_price)
                binance_message = "\n<pre>Binance price - {}</pre>".format(
                    b_sign)
                bot.send_message(chat_id=update.message.chat_id,
                                 parse_mode='HTML', text=binance_message)

            logger.info("/price {0} {1}:{2}:{3}:{4}-{5}".format(
                ','.join(args),
                update.message.from_user['username'],
                update.message.from_user['id'],
                update.message.from_user['language_code'],
                update.message.chat_id,
                update.message.chat.type)
            )

def ct(bot, update, args):

    if len(args) == 1 and args[0] == 'help':
        message = "\n/ct converts CURRENCY 1 --> CURRENCY 2\n\n"
        message += "Syntax:\n"
        message += "/ct <CURRENCY_1> <CURRENCY_2> [amount]\n\n"
        message += "Example:\n"
        message += "/ct tau eth 10000\n\n"

        message += "Supported fiat currencies:\n"
        message += "AUD, BRL, CAD, CHF, CLP, CNY, CZK, DKK,\n"
        message += "EUR, GBP, HKD, HUF, IDR, ILS, INR, JPY,\n"
        message += "KRW, MXN, MYR, NOK, NZD, PHP, PKR, PLN,\n"
        message += "RUB, SEK, SGD, THB, TRY, TWD, USD, ZAR\n\n"

        bot.send_message(chat_id=update.message.chat_id, text=message)

    elif len(args) != 3:
        message = "/ct command takes 3 arguments.\n\n"
        message += "Syntax:\n"
        message += "/ct <TOKEN_1> <TOKEN_2> [amount]"

        bot.send_message(chat_id=update.message.chat_id, text=message)

    elif not checkDigit(args[2]):
        message = "Amount must be a digit"

        bot.send_message(chat_id=update.message.chat_id, text=message)

    else:
        token_1 = CheckCoin(args[0])
        token_2 = CheckCoin(args[1])
        amount = checkDigit(args[2])
        cont = True

        if not token_1.symbol:
            if not token_1.name:
                message = "'{}' is not in my database. Check your spelling".format(
                    args[0])
                cont = False
                bot.send_message(chat_id=update.message.chat_id, text=message)
        elif not token_2.symbol:
            if not token_2.name:
                message = "'{}' is not in my database. Check your spelling".format(
                    args[1])
                cont = False
                bot.send_message(chat_id=update.message.chat_id, text=message)

        if cont:
            fiat_1 = token_1.name in config["supported_fiat"]
            fiat_2 = token_2.name in config["supported_fiat"]

            if fiat_1 or fiat_2:
                if fiat_1 and fiat_2:
                    message = "I do not concern myself with forex"
                elif fiat_1:
                    converted = convertToken(token_1.name, token_2.coin_id, amount)
                    if converted:
                        message = "{} <i>{}</i> = <b>{}</b> <i>{}</i>".format(
                            thousandify(amount),
                            token_1.name,
                            thousandify(converted),
                            token_2.symbol
                        )
                    else:
                        message = "something unexpected has happened ... maybe try again later?"
                else:
                    converted = convertToken(token_1.coin_id, token_2.name, amount)
                    if converted:
                        message = "{} <i>{}</i> = <b>{}</b> <i>{}</i>".format(
                            thousandify(amount),
                            token_1.symbol,
                            thousandify(converted),
                            token_2.name
                        )
                    else:
                        message = "something unexpected has happened ... maybe try again later?"
                bot.send_message(chat_id=update.message.chat_id,
                                 parse_mode='HTML',
                                 text=message)
            else:

                converted = convertToken(token_1.coin_id, token_2.coin_id, amount)
                if not converted:
                    message = "something unexpected has happened ... maybe try again later?"
                else:
                    message = "{} <i>{}</i> = <b>{}</b> <i>{}</i> ".format(
                        thousandify(amount),
                        token_1.symbol,
                        thousandify(converted[0]),
                        token_2.symbol
                    )
                    message += "| <b>${}</b>".format(thousandify(converted[1]))

                bot.send_message(chat_id=update.message.chat_id,
                                 parse_mode='HTML',
                                 text=message)

    logger.info("/ct {0} {1}:{2}:{3}:{4}-{5}".format(
        ','.join(args),
        update.message.from_user['username'],
        update.message.from_user['id'],
        update.message.from_user['language_code'],
        update.message.chat_id,
        update.message.chat.type)
    )

def newCoin(bot, job):

    binance = Binance()
    new_coin = binance.check_list()
    message = str()
    t_now = time.strftime('%H%M', time.localtime(time.time()))
    refresh = (t_now[:-2] in config["rt"]['hrs']) and (
        t_now[2:] in config["rt"]['mins'])

    if new_coin:
        for item in range(len(new_coin)):
            message += "\n<code>{} has been added to Binance</code>".format(
                new_coin[item])
        bot.send_message(chat_id=config["grp_id"], parse_mode='HTML', text=message)

    if refresh:
        try:
            getCmc()
            logger.info("CMC Data refreshed - {0}()".format(
                newCoin.__name__)
            )
        except Exception:
            logger.exception("Something went wrong. CMC not refreshed")

def refresh(bot, update):

    getCmc()
    bot.send_message(chat_id=update.message.chat_id, text="Done")

    logger.info("CMC Data refreshed by {0}:{1}".format(
        update.message.from_user['id'],
        update.message.from_user['username'])
    )


def main():

    try:
        logger.info("Start by {0}()".format(main.__name__))

        auth = config["wh_auth"]

        updater = Updater(token=auth["token"])
        dispatcher = updater.dispatcher
        j = updater.job_queue

        # REPEATING
        j.run_repeating(newCoin, interval=60, first=0)

        # NORMAL COMMANDS
        start_handler = CommandHandler('start', start)
        price_handler = CommandHandler('price', getPrice, pass_args=True)
        ct_handler = CommandHandler('ct', ct, pass_args=True)

        # ADMIN COMMANDS
        refresh_handler = CommandHandler(
            'refresh',
            refresh,
            filters=Filters.user(user_id=config["admin_id"])
        )

        dispatcher.add_handler(start_handler)
        dispatcher.add_handler(price_handler)
        dispatcher.add_handler(ct_handler)
        dispatcher.add_handler(refresh_handler)
        dispatcher.add_error_handler(error)


        updater.start_webhook(
            listen=auth["wh_listen_addr"],
            port=auth["wh_port"],
            url_path="TOKEN",
            key=auth["wh_key"],
            cert=auth["wh_cert"],
            webhook_url=auth["wh_url"]
        )

        updater.idle()
        logger.info("Shutdown")

    except Exception:
        logger.exception("Something went wrong")


if __name__ == '__main__':
    main()
