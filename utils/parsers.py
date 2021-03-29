import requests
from bs4 import BeautifulSoup

from abc import ABC, abstractmethod

from .patterns import singleton

# TODO
# - return object - з полями типу "price", "is_waiting", "is_on_sale"
# - dict to convert ("UAH" <-> "₴")


class CustomParser(ABC):
    @abstractmethod
    def get_price(self, link: str):
        pass

    def write_to_file(data):
        f = open("site.html", "wb")
        f.write(data)
        f.close()


# class ParserResult:
#     def __init__(
#         self, price, currency, is_on_sale=False, before_price=0, is_waiting=False
#     ):
#         self.price = price
#         self.currency = currency
#         self.is_on_sale = is_on_sale
#         self.before_price = before_price
#         self.is_waiting = is_waiting


@singleton
class CitrusParser(CustomParser):
    def get_price(self, link):
        page = requests.get(link)

        soup = BeautifulSoup(page.content, "html.parser")

        b_price = soup.find("b", class_="buy-section__new-price")
        if not b_price:
            print("No price was found")
            return

        price, span_currency = b_price.children

        result_price = float("".join(price.split()))
        result_currency = span_currency.text

        result = f"{result_price} {result_currency}"

        if self.is_waiting(soup):
            result += " - waiting"

        is_on_sale, before_price = self.check_on_sale(soup)
        if is_on_sale:
            result += f" - on sale (before - {before_price} {result_currency})"

        return result

    def is_waiting(self, soup):
        waiting = soup.find("p", class_="status--waiting")
        return bool(waiting)

    def check_on_sale(self, soup):
        span_price = soup.find("span", "buy-section__old-price")
        if not span_price:
            return False, None

        price_raw = span_price.contents[0]
        price = float("".join(price_raw.split()))
        return True, price


@singleton
class AlloParser(CustomParser):
    def get_price(self, link):
        page = requests.get(link)

        soup = BeautifulSoup(page.content, "html.parser")

        div_price = soup.find("div", class_="p-trade-price__current")
        if not div_price:
            # чи це тільки кейс коли немає в наявності чи ще якісь
            print("No price was found")
            return

        price = float(div_price.find("meta", itemprop="price")["content"])
        currency = div_price.find("meta", itemprop="priceCurrency")["content"]

        result = f"{price} {currency}"

        if not self.is_available(soup):
            result += " - doesn't available"

        is_on_sale, before_price = self.check_on_sale(soup)
        if is_on_sale:
            result += f" - on sale (before - {before_price} {currency})"

        return result

    def is_available(self, soup):
        is_out_of_stock = self.is_out_of_stock(soup)
        return not is_out_of_stock

    def is_out_of_stock(self, soup):
        button_out_of_stock = soup.find(class_="buy-button--out-stock")
        return bool(button_out_of_stock)

    def check_on_sale(self, soup):
        div_price = soup.find(class_="p-trade-price__old")
        if not div_price:
            return False, None

        *price_components, currency = div_price.find(class_="sum").text.split()

        price = float("".join(price_components))
        return True, price


def test_citrus():
    parser = CitrusParser()

    links = [
        "https://www.citrus.ua/aksessuary-dlya-gejminga/geympad-dualsense-dlya-sony-ps5-664502.html",
        "https://www.citrus.ua/games/disk-xbox-star-wars-squadrons-blu-ray-english-version-674048.html",
        "https://www.citrus.ua/aksessuary-dlya-naushnikov/chekhol-dlya-apple-airpods-star-wars-stormtrooper-654245.html",
        "https://www.citrus.ua/games/disk-xbox-one-star-wars-fallen-order-blu-ray-russian-subtitles-657026.html",
        "https://www.citrus.ua/electroscooters/elektrosamokat-likebike-one-black-637102.html",
        # PS5 (предзаказ)
        "https://www.citrus.ua/igrovye-pristavki/igrovaya-konsol-sony-playstation-5-663700.html",
    ]
    for link in links:
        print(parser.get_price(link))


def test_allo():
    parser = AlloParser()

    links = [
        "https://allo.ua/ru/igrovye-pristavki/microsoft-xbox-one-s-1tb-white-gta-5-rasshirennaja-garantija-18-mesjacev.html",
        "https://allo.ua/ru/igrovye-pristavki/konsol-playstation-5-digital-edition.html",
        "https://allo.ua/ru/igrovye-pristavki/igrovaya-konsol-playstation-5.html",
        "https://allo.ua/ru/products/mobile/xiaomi-redmi-note-9-pro-6-128gb-interstellar-grey.html",
    ]
    for link in links:
        print(parser.get_price(link))


if __name__ == "__main__":
    test_citrus()
    test_allo()


# FOXTROT, ELDORADO
# - protected by incapsula technology (зайди на них через інкогніто і там буде опис)
