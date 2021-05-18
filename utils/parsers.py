from abc import ABC, abstractmethod

import requests
from bs4 import BeautifulSoup

from .patterns import singleton


CURRENCIES_CONVERSION = {
    "₴": "UAH",
    "UAH": "UAH",
    "$": "USD",
    "USD": "USD",  # dollar
    "EUR": "EUR",  # euro
}


class CustomParser(ABC):
    @abstractmethod
    def parse(self, link: str):
        pass

    def return_empty_result(self, url: str):
        result = ParserResult(url=url, is_available=False)
        return result

    def return_wrong_url_result(self, url: str):
        result = ParserResult(url=url, is_available=False, is_wrong_url=True)
        return result

    def write_to_file(data):
        f = open("site.html", "wb")
        f.write(data)
        f.close()


class ParserResult:
    def __init__(
        self,
        url,
        title=None,
        price=0,
        currency="UAH",
        is_available=True,
        is_on_sale=False,
        price_before=0,
        is_wrong_url=False,
    ):
        self.url = url
        self.title = title
        self.price = price
        self.currency = CURRENCIES_CONVERSION[currency]
        self.is_available = is_available  # waiting / out of stock
        self.is_on_sale = is_on_sale
        self.price_before = price_before
        self.is_wrong_url = is_wrong_url

    def to_dict(self):
        result = {
            "url": self.url,
            "title": self.title,
            "price": self.price,
            "currency": self.currency,
            "is_available": self.is_available,
            "is_on_sale": self.is_on_sale,
            "price_before": self.price_before,
            "is_wrong_url": self.is_wrong_url,
        }
        return result

    def __str__(self):
        return str(self.to_dict())

    # TODO
    # Notes
    # - може бути на знижці, з ціною і не доступне
    # (https://www.citrus.ua/stiralnye-mashiny/stiralnaya-mashina-lg-f2r5ws0w-676002.html)


@singleton
class CitrusParser(CustomParser):
    def parse(self, link):
        page = requests.get(link)
        if not page.ok:
            return self.return_wrong_url_result(link)

        soup = BeautifulSoup(page.content, "html.parser")

        b_price = soup.find("b", class_="buy-section__new-price")
        if not b_price:
            return self.return_empty_result(link)

        raw_price, span_currency = b_price.children

        price = float("".join(raw_price.split()))
        currency = span_currency.text
        is_available = self.is_available(soup)
        is_on_sale, price_before = self.check_on_sale(soup)

        title = None
        h1_title = soup.find("h1", class_="product__title")
        if h1_title:
            title = h1_title.text.strip()

        result = ParserResult(
            url=link,
            title=title,
            price=price,
            currency=currency,
            is_available=is_available,
            is_on_sale=is_on_sale,
            price_before=price_before,
        )

        return result

    def is_available(self, soup):
        is_waiting = self.is_waiting(soup)
        return not bool(is_waiting)

    def is_waiting(self, soup):
        waiting = soup.find("p", class_="status--waiting")
        return bool(waiting)

    def check_on_sale(self, soup):
        span_price = soup.find("span", "buy-section__old-price")
        if not span_price:
            return False, 0

        price_raw = span_price.contents[0]
        price = float("".join(price_raw.split()))
        return True, price


@singleton
class AlloParser(CustomParser):
    def parse(self, link):
        page = requests.get(link)
        if not page.ok:
            return self.return_wrong_url_result(link)
        # TODO - think about it (зараз як ніби все правильно встановлюють)
        # if not page.ok:  # wrong url
        #     return None

        soup = BeautifulSoup(page.content, "html.parser")

        div_price = soup.find("div", class_="p-trade-price__current")
        if not div_price:
            return self.return_empty_result(link)
            # # чи це тільки кейс коли немає в наявності чи ще якісь
            # print("No price was found")
            # return

        price = float(div_price.find("meta", itemprop="price")["content"])
        currency = div_price.find("meta", itemprop="priceCurrency")["content"]
        is_available = self.is_available(soup)
        is_on_sale, price_before = self.check_on_sale(soup)

        title = None
        h1_title = soup.find("h1", itemprop="name")
        if h1_title:
            title = h1_title.text.strip()

        result = ParserResult(
            url=link,
            title=title,
            price=price,
            currency=currency,
            is_available=is_available,
            is_on_sale=is_on_sale,
            price_before=price_before,
        )

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


@singleton
class EpicentrParser(CustomParser):
    def parse(self, link):
        page = requests.get(link)
        if not page.ok:
            return self.return_wrong_url_result(link)

        soup = BeautifulSoup(page.content, "html.parser")

        div_price = soup.find("div", class_="p-price__main")
        if not div_price:
            return self.return_empty_result(link)

        raw_price = div_price.text.strip()
        price = float("".join(raw_price.split()))

        currency = div_price.get_attribute_list("data-text")[0][0]

        is_available = True
        is_on_sale, price_before = self.check_on_sale(soup)

        title = None
        h1_title = soup.find("h1")
        if h1_title:
            title = h1_title.text.strip()

        result = ParserResult(
            url=link,
            title=title,
            price=price,
            currency=currency,
            is_available=is_available,
            is_on_sale=is_on_sale,
            price_before=price_before,
        )

        return result

    def check_on_sale(self, soup):
        span_price = soup.find("span", "p-price__old-sum")
        if not span_price:
            return False, 0

        price = float(span_price.text.strip())
        return True, price


def test_citrus():
    parser = CitrusParser()

    links = [
        (
            "https://www.citrus.ua/aksessuary-dlya-gejminga/geympad-dualsense-"
            "dlya-sony-ps5-664502.html"
        ),
        (
            "https://www.citrus.ua/games/disk-xbox-star-wars-squadrons-blu-ray-"
            "english-version-674048.html"
        ),
        (
            "https://www.citrus.ua/aksessuary-dlya-naushnikov/chekhol-dlya-apple-"
            "airpods-star-wars-stormtrooper-654245.html"
        ),
        (
            "https://www.citrus.ua/games/disk-xbox-one-star-wars-fallen-order-blu-"
            "ray-russian-subtitles-657026.html"
        ),
        "https://www.citrus.ua/electroscooters/elektrosamokat-likebike-one-black-637102.html",
        # PS5 (предзаказ)
        "https://www.citrus.ua/igrovye-pristavki/igrovaya-konsol-sony-playstation-5-663700.html",
    ]
    for link in links:
        print(parser.parse(link))


def test_allo():
    parser = AlloParser()

    links = [
        "https://allo.ua/ua/jelektrosamokaty/xiaomi-mi-electric-scooter-lite-black.html",
        (
            "https://allo.ua/ru/igrovye-pristavki/microsoft-xbox-one-s-"
            "1tb-white-gta-5-rasshirennaja-garantija-18-mesjacev.html"
        ),
        "https://allo.ua/ru/igrovye-pristavki/konsol-playstation-5-digital-edition.html",
        "https://allo.ua/ru/igrovye-pristavki/igrovaya-konsol-playstation-5.html",
        "https://allo.ua/ru/products/mobile/xiaomi-redmi-note-9-pro-6-128gb-interstellar-grey.html",
        # 404 page
        # "https://allo.ua/ua/dasdasda222"
    ]
    for link in links:
        print(parser.parse(link))


def test_epicentr():
    parser = EpicentrParser()

    links = [
        # int price
        "https://epicentrk.ua/ua/shop/batut-maxxpro-tr48-b.html",
        # sale
        "https://epicentrk.ua/ua/shop/nabor-kastryul-6-predmetov-up-underprice.html",
        # float price
        "https://epicentrk.ua/ua/shop/gorka-doloni-bolshaya-golubovato-seraya-014550-15.html",
        # not available
        (
            "https://epicentrk.ua/ua/shop/mplc-mikrofon-sennheiser-xs-1-cordial-cim-5-fm"
            "-cable-1eb7cd65-1757-6b96-8667-97bf9c66ef6b.html"
        ),
        # 404 page
        "https://epicentrk.ua/32131/",
    ]
    for link in links:
        print(parser.parse(link))


if __name__ == "__main__":
    # test_citrus()
    # test_allo()
    test_epicentr()


# FOXTROT, ELDORADO
# - protected by incapsula technology (зайди на них через інкогніто і там буде опис)
