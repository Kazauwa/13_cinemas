import requests
from argparse import ArgumentParser
from bs4 import BeautifulSoup


def fetch_afisha_page():
    response = requests.get('http://www.afisha.ru/msk/schedule_cinema/')
    return response.content


def parse_afisha_list(raw_html):
    soup = BeautifulSoup(raw_html, 'html.parser')
    schedule = soup.find('div', id='schedule')
    raw_movie_list = schedule.find_all('div', class_='object s-votes-hover-area collapsed')
    movie_list = []

    for movie in raw_movie_list:
        movie = {
            'title': movie.find('h3', class_='usetags').text,
            'cinemas_count': len(movie.find('tbody'))
        }
        movie_list.append(movie)

    return movie_list


def fetch_movie_search_page(movie_title):
    params = {'text': movie_title}
    response = requests.get('https://plus.kinopoisk.ru/search/films/', params=params)
    return response.content


def parse_movie_search_page(raw_html, movie_title):
    soup = BeautifulSoup(raw_html, 'html.parser')
    movie = soup.find(attrs={'content': movie_title})

    if not movie:
        return

    movie = movie.parent
    movie_url = movie.find('a', attrs={'itemprop': 'url'})
    movie_url = movie_url['href']
    return movie_url


def fetch_movie_info(movie_url):
    if not movie_url:
        return

    movie_page = requests.get(movie_url)
    return movie_page.content


def parse_movie_info(raw_html):
    if not raw_html:
        return None, None

    soup = BeautifulSoup(raw_html, 'html.parser')
    rating = soup.find('div', class_='rating-button__rating').text
    voters = soup.find('div', class_='film-header__rating-comment').text
    return rating, voters


def output_movies_to_console(movies, top):
    for count, movie in enumerate(movies[:top + 1]):
        print('{0}. {1}'.format(count + 1, movie['title']))
        print('Рейтинг: {0} по результатам {1}'.format(movie['rating'], movie['voters']))
        print('Идёт в {0} кинотеатрах'.format(movie['cinemas_count']))


def sort_by_rating(movie):
    return movie.get('rating')


def sort_by_cinemas(movie):
    return movie.get('cinemas_count')


if __name__ == '__main__':
    parser = ArgumentParser(description='Узнай что в кино!')
    parser.add_argument('-c', action='store_const', const=sort_by_cinemas, default=sort_by_rating, dest='sort_key',
                        help='Сортировка по количеству кинотеатров, показывающих фильм')
    parser.add_argument('-t', '--top', type=int, nargs='?', default=10,
                        help='Размер результирующего списка')
    options = parser.parse_args()

    raw_afisha_page = fetch_afisha_page()
    movie_list = parse_afisha_list(raw_afisha_page)

    for count, movie in enumerate(movie_list):
        print('Обрабатываю фильмы с афиши {0}/{1}...'.format(count + 1, len(movie_list)), end='\r')
        raw_movie_search_page = fetch_movie_search_page(movie.get('title'))
        movie_url = parse_movie_search_page(raw_movie_search_page, movie.get('title'))
        raw_movie_info = fetch_movie_info(movie_url)
        movie['rating'], movie['voters'] = parse_movie_info(raw_movie_info)

    sorted_movie_list = sorted(movie_list, key=options.sort_key)
    output_movies_to_console(movie_list, options.top)
