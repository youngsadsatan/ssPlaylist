import requests
from bs4 import BeautifulSoup
import re
import sys

M3U_HEADER = '#EXTM3U\n'
MOVIES_FILE = 'comedy.txt'
OUTPUT_FILE = 'playlist.m3u'


def extract_video_urls(page_url):
    '''
    Retorna título, data e até duas URLs de vídeo (principal e alternativa).
    '''
    resp = requests.get(page_url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'lxml')

    # Extrair título e data
    title_tag = soup.find('h1') or soup.find('title')
    full_title = title_tag.get_text(strip=True) if title_tag else page_url
    date_match = re.search(r'(\d{4})', full_title)
    year = date_match.group(1) if date_match else None
    title = re.sub(r'\s*\d{4}', '', full_title)

    # Buscar até dois vídeos
    video_urls = []
    for iframe in soup.find_all('iframe'):
        src = iframe.get('src')
        if not src:
            continue
        if src.endswith('.mp4') or 'mediafire.com' in src:
            video_urls.append(src)
        if len(video_urls) >= 2:
            break

    return title.strip(), year, video_urls


def gerar_m3u(entries):
    lines = [M3U_HEADER]
    for title, year, urls in sorted(entries, key=lambda e: e[0].lower()):
        display = f"{title} ({year})" if year else title
        for idx, url in enumerate(urls, 1):
            tag = 'principal' if idx == 1 else 'alternativa'
            lines.append(f"#EXTINF:-1 type='video', {display} [{tag}]")
            lines.append(url)
    return '\n'.join(lines)


def main():
    try:
        with open(MOVIES_FILE, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except FileNotFoundError:
        print(f"Arquivo {MOVIES_FILE} não encontrado.")
        sys.exit(1)

    entries = []
    for page in urls:
        print(f"Processando: {page}")
        try:
            title, year, vids = extract_video_urls(page)
            if vids:
                entries.append((title, year, vids))
            else:
                print(f"  Aviso: não encontrou vídeos em {page}")
        except Exception as e:
            print(f"  Erro ao processar {page}: {e}")

    m3u_content = gerar_m3u(entries)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as out:
        out.write(m3u_content)
    print(f"Playlist gerada em {OUTPUT_FILE}")


if __name__ == '__main__':
    main()
