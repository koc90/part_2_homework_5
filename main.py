# Publiczne API Narodowy Bank Polski pozwala uzyskać informacje o kursach wymiany gotówki Narodowy Bank Polski w wybranym dniu. Archiwum przechowuje dane z ostatnich 4 lat.

# Napisz narzędzie konsolowe, które zwraca kursy wymiany EUR i USD Narodowy Bank Polski z ostatnich kilku dni. Ustaw ograniczenie, aby narzędzie mogło wyświetlać tylko kursy wymiany z ostatnich 10 dni. Użyj klienta Aiohttp, aby wysłać żądanie do API. Postępuj zgodnie z zasadami SOLID podczas pisania zadania. Poprawnie obsługuj błędy zapytań sieciowych.

# Opis parametrów odpowiedzi dot. kursów walut
# Table – typ tabeli
# No – numer tabeli
# TradingDate – data notowania (dotyczy tabeli C)
# EffectiveDate – data publikacji
# Rates – lista kursów poszczególnych walut w tabeli
# Country – nazwa kraju
# Symbol – symbol waluty (numeryczny, dotyczy kursów archiwalnych)
# Currency – nazwa waluty
# Code – kod waluty
# Bid – przeliczony kurs kupna waluty (dotyczy tabeli C) - purchase
# Ask – przeliczony kurs sprzedaży waluty (dotyczy tabeli C) - sale
# Mid – przeliczony kurs średni waluty (dotyczy tabel A oraz B)

import aiohttp
import asyncio
import requests
from datetime import datetime, timedelta
import logging
import sys


CURRENCIES = ["USD", "EUR"]

logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(process)s - %(thread)s - %(message)s",
)


# IO-bound tasks


def get_data_from_api_sync(date: str) -> list:
    print(f"get_data_from_api_sync called for date: {date}")
    start = datetime.now()
    url = create_url(date)
    response = requests.get(url)

    if response.status_code == 200:
        end = datetime.now()
        elapsed = end - start
        print(f"Data has been received. Elapsed time: {elapsed}")
        data = response.json()

    else:
        logging.error(
            f"Data for date {date} has not been received. Status code: {response.status_code}"
        )
        data = "Data unavailable"

    return {date: data}


async def get_data_from_api_async(date: str) -> list:
    print(f"get_data_from_api_async called for date: {date}")
    start = datetime.now()
    url = create_url(date)
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                end = datetime.now()
                elapsed = end - start
                print(f"Data has been received. Elapsed time: {elapsed}")

            else:
                logging.error(
                    f"Data for date {date} has not been received. Status code: {response.status}"
                )
                data = "Data unavailable"

    return {date: data}


# CPU-bound tasks


def create_url(date):
    url = f"https://api.nbp.pl/api/exchangerates/tables/c/{date}?format=json"
    return url


def remove_dates_with_no_data(datadict: dict) -> dict:
    list_of_dates_to_remove = []
    for date, data in datadict.items():
        if not isinstance(data, list):
            list_of_dates_to_remove.append(date)

    for date_to_remove in list_of_dates_to_remove:
        datadict.pop(date_to_remove)

    return (datadict, list_of_dates_to_remove)


def create_past_date_as_string(days_ago: int) -> str:
    logging.debug(
        f"We are in create_past_date_as_string function\n Arguments:\n days_ago = {days_ago}"
    )
    today_date = datetime.today().date()
    days = timedelta(days=days_ago)
    new_date = today_date - days
    new_date_str = str(new_date)

    logging.debug(f"Date has been created: {new_date_str}")
    return new_date_str


def get_rates_from_data(data: list) -> list:
    rates = data[0]["rates"]
    # logging.debug(f"Rates: {rates}")
    return rates


def create_sale_dict(rates: list) -> dict:
    # logging.debug(f"We are in create_sale_dict function,\nArguments: \nrates = {rates}")
    sale_dict = dict()
    for rate in rates:
        # logging.debug(f"Current element of list: {rate}")
        key = rate["code"]
        value = rate["ask"]
        sale_dict[key] = value

    # logging.debug(f"sale_dict has been created: {sale_dict}")
    return sale_dict


def create_purchase_dict(rates: list) -> dict:
    # logging.debug(
    #     f"We are in create_purchase_dict function,\nArguments: \nrates = {rates}"
    # )
    purchase_dict = dict()
    for rate in rates:
        # logging.debug(f"Current element of list: {rate}")
        key = rate["code"]
        value = rate["bid"]
        purchase_dict[key] = value

    # logging.debug(f"purchase_dict has been created: {purchase_dict}")
    return purchase_dict


def create_dict_of_rates_of_day(currencies: list, rates: list, date: str) -> dict:
    sale_dict = create_sale_dict(rates)
    purchase_dict = create_purchase_dict(rates)

    logging.debug(
        f"We are in create_of_rates_of_day function,\ncurrencies = {currencies}\nsale_dict = {sale_dict}\npurchase_dict = {purchase_dict}"
    )

    inner_dict_of_rates = dict()

    for currency in currencies:
        inner_dict_of_rates[currency] = {
            "sale": sale_dict[currency],
            "purchase": purchase_dict[currency],
        }

    dict_of_rates = {date: inner_dict_of_rates}

    # logging.debug(f"Dictionary has been created: {dict_of_rates}")
    return dict_of_rates


def create_list_of_wanted_dates(n: int) -> list:
    wanted_dates = []
    for i in range(n + 1):
        wanted_date = create_past_date_as_string(i)
        wanted_dates.append(wanted_date)

    return wanted_dates


def create_datadict_sync(dates: list[str]) -> dict:
    datadict = dict()
    for date in dates:
        datadict.update(get_data_from_api_sync(date))
    return datadict


async def gather_all_get_data_from_api_tasks(dates: list[str]) -> list:
    tasks = []
    for date in dates:
        tasks.append(get_data_from_api_async(date))

    logging.debug(f"tasks gathered: {tasks}")

    result = asyncio.gather(*tasks)
    return await result


def create_datadict_async(dates: list[str]) -> dict:
    gather_tasks_to_run = gather_all_get_data_from_api_tasks(dates)
    logging.debug(f"gather_tasks = {gather_tasks_to_run}")

    results = asyncio.run(gather_tasks_to_run)

    is_results_list = isinstance(results, list)
    logging.debug(
        f"Tasks done, results should be a list. Is results a list: {is_results_list}"
    )

    datadict = dict()
    for result in results:
        datadict.update(result)
    return datadict


def create_list_of_rates_for_n_last_days(
    n: int, if_async=True, if_possible_choice=False
) -> list[dict]:
    dates = create_list_of_wanted_dates(n)

    if if_async:
        datadict = create_datadict_async(dates)
    else:
        datadict = create_datadict_sync(dates)

    (datadict, dates_with_no_data) = remove_dates_with_no_data(datadict)

    all_rates = dict()
    for key, value in datadict.items():
        all_rates[key] = get_rates_from_data(value)

    if if_possible_choice:
        currencies = create_list_of_wanted_currencies(all_rates)
    else:
        currencies = CURRENCIES

    result = [
        create_dict_of_rates_of_day(currencies, rates, date)
        for date, rates in all_rates.items()
    ]
    print(f"\n\n Result:\n{result}\n")

    if len(dates_with_no_data) > 0:
        print(f"Failed to download data for the following dates: {dates_with_no_data}")

    return result


def display_prettier_result(result: list) -> None:
    print("\n\nResult in prettier form:")
    for item in result:
        date_s = item.keys()
        currencies_dicts = item.values()
        for date in date_s:
            print(f"\n{date}:")
        for currency_dict in currencies_dicts:
            for currency, rates in currency_dict.items():
                print(f"    {currency}: {rates}")


def create_list_of_available_currencies(
    rates: dict,
) -> list:  # do części nieobowiązkowej
    logging.debug(
        f"We are in create_list_of_available_currencies\n Arguments:\nrates = {rates}"
    )
    list_of_available_currencies = []
    for currency_dict in list(rates.values())[0]:
        logging.debug(f"\n\n\n\ncurrency_dict = {currency_dict}\n\n\n\n")

        list_of_available_currencies.append(currency_dict["code"])

    logging.debug(f"list_of_available_currencies: {list_of_available_currencies}")

    return list_of_available_currencies


def create_list_of_wanted_currencies(rates: dict) -> list:  # do części nieobowiązkowej
    list_of_currencies = []
    available_currencies = create_list_of_available_currencies(rates)
    while True:
        print(f"\nCodes of available currencies: {available_currencies}")
        wanted_currency = input(
            "Input a code (only one) of currnency. You can also write 'all' to add all available currencies or write 'exit' to finish this action:\n"
        )
        if wanted_currency.lower() == "exit":
            break
        elif wanted_currency.lower() == "all":
            list_of_currencies = available_currencies
            break
        elif wanted_currency.upper() in available_currencies:
            list_of_currencies.append(wanted_currency)
            print(
                "\nCode has been added to list, you can add more codes or finish this action and go to the next step\n"
            )
        else:
            print("There is no such code. Try again")

    # logging.debug(f"List of codes: {list_of_currencies}")
    return list_of_currencies


async def fun1():  # Próby - niepotrzebne
    date1 = create_past_date_as_string(1)
    date2 = create_past_date_as_string(0)
    f1 = get_data_from_api_async(date=date1)
    f2 = get_data_from_api_async(date=date2)
    print(f1)
    print(f2)
    return await asyncio.gather(f1, f2)


def start_with_user_currencies(days_ago):
    print("\n\nAsynchronic\n")
    start = datetime.now()
    result_async = create_list_of_rates_for_n_last_days(
        days_ago, if_async=True, if_possible_choice=True
    )
    end = datetime.now()
    elapsed_async = end - start
    print(f"Task has been completed. Elapsed time: {elapsed_async}\n")

    display_prettier_result(result_async)


def test_fun1(days_ago: int):
    print("\n\nSynchronic\n")
    start = datetime.now()
    result_sync = create_list_of_rates_for_n_last_days(days_ago, if_async=False)
    end = datetime.now()
    elapsed_sync = end - start
    print(f"Task has been completed. Elapsed time: {elapsed_sync}\n")

    print("\n\nAsynchronic\n")
    start = datetime.now()
    result_async = create_list_of_rates_for_n_last_days(days_ago)
    end = datetime.now()
    elapsed_async = end - start
    print(f"Task has been completed. Elapsed time: {elapsed_async}\n")

    display_prettier_result(result_async)


def main():
    days_ago = int(sys.argv[1])
    if days_ago > 10:
        print("Rates older than 10 days are not available")
        days_ago = 10

    test_fun1(days_ago)
    # start_with_user_currencies(days_ago)


if __name__ == "__main__":
    main()
