from bs4 import BeautifulSoup
import re
import requests
from aiogram import types


def chek_leng(split_msg: str):
    """
    проверяем сообщение на анг язык
    :param split_msg:
    :return:
    """
    msg = split_msg.strip()
    i = 0
    while i in range(len(msg)):
        if re.search(r'[a-zA-Z]', msg[i]):
            i += 1
        else:
            return False
    if msg == '':
        return False
    else:
        return True


class subs:

    def __init__(self, message: types.Message):
        self.message = message
        self.headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,'
                      '*/*;q=0.8, application/signed-exchange;v=b3;q=0.9',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/91.0.4472.106 Safari/537.36 '
        }
        self.ticket = ''
        self.week = 0
        self.final_short = []
        self.final_options = []
        self.date_options = ''

    def get_query(self) -> object:
        """
        Проверяем что написал пользовать
        :return: тикер и, если есть, количество недель для запроса на опционы
        """
        split_msg = self.message.split('+')
        if len(split_msg) == 1:  # если написан просто тикер
            flag = chek_leng(split_msg[0])
            if flag:  # если тикер написан не на английском
                self.ticket = split_msg[0].lower().strip()
        elif len(split_msg) == 2:  # если формат тикер + неделя (int)
            flag = chek_leng(split_msg[0])
            if flag and split_msg[1].strip().isdigit():  # если неделя указана как число
                self.ticket = split_msg[0].lower().strip()
                self.week = int(split_msg[1])

    def get_parser_finviz(self):
        req = requests.get('https://finviz.com/quote.ashx?t=' + self.ticket, headers=self.headers)
        soup = BeautifulSoup(req.text, 'html.parser')
        items = soup.find_all('tr', class_='table-dark-row')
        if len(items) != 0:
            cards = [{
                'tiker': self.ticket,
                'title': items[2].contents[13].text,
                'volume': items[2].contents[14].text
            }]
            self.final_short = cards[0]

    def get_parser_yahoo(self):
        call_options = []
        put_options = []
        call = 'call-in-the-money'
        put = 'put-in-the-money'
        undefined = 'undefined'
        url = f'https://finance.yahoo.com/quote/{self.ticket}/options?p={self.ticket}&straddle=true'
        if self.ticket != '':
            req = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(req.content, 'html.parser')
            date_react = soup.findAll('select', {'class': 'Fz(s) H(25px) Bd Bdc($seperatorColor)'})
            self.date_options = date_react[0].contents[0].string
            if 1 <= self.week:
                if self.week <= len(date_react[0].contents):
                    url = f'https://finance.yahoo.com/quote/{self.ticket}/options?date=' \
                          f'{date_react[0].contents[self.week].nextSibling.attrs["value"]}&p={self.ticket}&straddle=true'
                    self.date_options = date_react[0].contents[self.week].string
                else:
                    return None
            req = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(req.content, 'html.parser')
            content = soup.findAll('table', {'class': 'straddles W(100%) Pos(r) straddle-options'})
        else:
            return None
        records = content[0].contents[1].contents
        for row in records:
            if call in row.attrs['class']:
                call_options.append({
                    'volume_call': row.contents[3].text,
                    'strike': row.contents[5].text,
                    'volume_put': row.contents[9].text,
                })
            elif put in row.attrs['class'] or undefined in row.attrs['class']:
                put_options.append({
                    'volume_call': row.contents[3].text,
                    'strike': row.contents[5].text,
                    'volume_put': row.contents[9].text,
                })

        self.final_options = call_options[-3:] + put_options[:3]

    @property
    def get_message(self):
        if not self.final_options:
            self.message = '#' + str(self.final_short['tiker']) + ' ' + str(self.final_short['title']) + \
                           ' ' + str(self.final_short['volume']) + '\n'
        else:
            temp_msg = ''
            for option in self.final_options:
                temp_msg += "Strike: " + option['strike'] + ' ' + option['volume_call'] + ' 🔼 ' \
                            + option['volume_put'] + ' 🔽 \n'
            self.message = '#' + str(self.final_short['tiker']) + ' ' + str(self.final_short['title']) + \
                           ' ' + str(self.final_short['volume']) + '\n' + \
                           self.date_options + '\n' + temp_msg



