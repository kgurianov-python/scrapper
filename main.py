import json
import logging

import requests as requests
from bs4 import BeautifulSoup, Tag, SoupStrainer

log_format = '%(name)s : %(levelname)s : %(asctime)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_format)
# logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('Scrapper')
logger.setLevel(logging.DEBUG)

BASE_URL = "https://carleton.ca/scs/our-people/school-of-computer-science-faculty/"
HEADER = {'Accept-Language': 'en-US',
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'}


def get_person_table_info(table_info: Tag):
    result = {}
    try:
        table = table_info.find('table', {"class": "people__table"}).select_one('tbody')
        for row in table.find_all('tr'):
            row_value_cell: Tag = row.find('td', {"class": "people__table-info"})
            if link := row_value_cell.find('a'):
                value = link['href']
            else:
                value = row_value_cell.text
            result.update({row.find('td', {"class": "people__table-title"}).text: value})
    except AttributeError:
        return None

    return result


def get_person_blob_info(person_article: Tag) -> []:
    result = {}
    try:
        titles = person_article.find_all('h3')
        for title in titles:
            big_data: Tag = title.next_sibling
            while big_data.name != 'p':
                big_data = big_data.next_sibling
            result.update({title.text: big_data.text})
    except AttributeError:
        return None

    return result


def get_person_info(url: str) -> {}:
    result = {}
    resp = requests.get(url, headers=HEADER)
    logger.debug(url)
    person_article = BeautifulSoup(resp.content, 'html.parser', parse_only=SoupStrainer('article'))

    person_detail = person_article.find("div", {"class": "people__details"})

    result.update({"name": person_detail.select_one('h2').text})
    result.update({"title": person_detail.select_one('p').text})

    result.update({"contacts": get_person_table_info(person_detail)})
    result.update({"research": get_person_blob_info(person_article)})
    return result


def get_faculty_people(faculty: Tag) -> []:
    people_cards = faculty.find_all('a')
    return [card['href'] for card in people_cards]


def get_faculties_list_with_links(soup: Tag) -> dict[str, Tag]:
    result: dict[str, []] = {}
    faculties: list[Tag] = soup.find_all("h2")
    for faculty in faculties:
        logger.info(f"{faculty.text}")
        faculty_data: Tag = faculty.next_element
        while faculty_data.name != 'section':
            faculty_data = faculty_data.next_element
        result.update({faculty.text: get_faculty_people(faculty_data)})
    return result


def main():
    resp = requests.get(BASE_URL, headers=HEADER)

    soup = BeautifulSoup(resp.content, 'html.parser', parse_only=SoupStrainer('article'))
    logger.info(f"{len(soup)=}")

    faculties_with_links = get_faculties_list_with_links(soup)

    for link in faculties_with_links['School Faculty']:
        print(json.dumps(get_person_info(link), indent=4))


if __name__ == '__main__':
    main()
