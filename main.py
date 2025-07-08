import requests
from bs4 import BeautifulSoup
import re

def read_urls(filename):
    with open(filename, 'r') as f:
        return sorted([line.strip() for line in f if line.strip()])

def extract_video_urls(page_url):
    resp = requests.get(page_url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'lxml')

    # Extrair tÃ­tulo e ano
    title_tag = soup.find('h1') or soup.find('title')
    full_title = title_tag.get_text(strip=True) if title_tag else page_url
    date_match = re.search(r'(\d{4})', full_title)
    year = date_match.group(1) if date_match else None
    title = re.sub(r'\s*\(\d{4}\)', '', full_title).strip()

    # Extrair URL da capa
    cover = soup.select_one('.card__cover img')
    poster_url = cover['src'] if cover and cover.get('src') else None

    # Buscar vÃ­deos em iframes
    video_urls = []
    for iframe in soup.select('.iframe-fix'):
        src = iframe.get('src', '')
        if not src:
            continue
        iframe_url = src if src.startswith('http') else 'https:' + src

        try:
            r2 = requests.get(iframe_url)
            r2.raise_for_status()
            html_iframe = r2.text

            for link in re.findall(r'https?://[^"\']+\.mp4', html_iframe):
                if link not in video_urls:
                    video_urls.append(link)
                if len(video_urls) >= 2:
                    break
        except Exception as e:
            print(f'Erro ao acessar iframe: {iframe_url} - {e}')
        if len(video_urls) >= 2:
            break

    return title, year, poster_url, video_urls

def generate_m3u(urls):
    lines = ['#EXTM3U']
    for url in urls:
        print(f'Processando: {url}')
        try:
            title, year, poster_url, video_urls = extract_video_urls(url)
            if not video_urls:
                print(f'  Aviso: nao encontrou videos em {url}')
                continue
            name = f'{title} ({year})' if year else title
            for i, video_url in enumerate(video_urls):
                tag = 'principal' if i == 0 else 'alternativa'
                logo = f' tvg-logo="{poster_url}"' if poster_url else ''
                lines.append(f'#EXTINF:-1 type="video"{logo}, {name} [{tag}]')
                lines.append(video_url)
        except Exception as e:
            print(f'  Erro ao processar {url}: {e}')
    return '\n'.join(lines)

if __name__ == '__main__':
    urls = read_urls('comedy.txt')
    playlist = generate_m3u(urls)
    with open('playlist.m3u', 'w', encoding='utf-8') as f:
        f.write(playlist)
