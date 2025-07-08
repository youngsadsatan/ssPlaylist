#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import re
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

COMEDY_FILE = 'comedy.txt'
OUTPUT_FILE = 'playlist.m3u'
M3U_HEADER = '#EXTM3U\n'

def read_urls(fname):
    try:
        with open(fname, 'r', encoding='utf-8') as f:
            return [u.strip() for u in f if u.strip() and not u.startswith('#')]
    except FileNotFoundError:
        print(f"Arquivo {fname} nÃ£o encontrado.")
        sys.exit(1)

def fetch_video_urls_with_playwright(page_url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        # Navegar e aguardar a pÃ¡gina carregar seus scripts
        page.goto(page_url, wait_until='networkidle')
        # Esperar o iframe estar presente no DOM (mesmo que oculto)
        iframe = page.query_selector('iframe.iframe-fix')
        if not iframe:
            print(f"  Aviso: iframe nao encontrado em {page_url}")
            browser.close()
            return []
        src = iframe.get_attribute('src')
        url_iframe = src if src.startswith('http') else 'https:' + src
        browser.close()
        r2 = requests.get(url_iframe)
        r2.raise_for_status()
        # Encontrar links .mp4 no HTML do iframe
        return re.findall(r'https?://[^"\']+\.mp4', r2.text)

def extract_from_page(page_url):
    resp = requests.get(page_url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'lxml')

    # tÃ­tulo e ano
    t = soup.find('h1') or soup.find('title')
    full = t.get_text(strip=True) if t else page_url
    m = re.search(r'(\d{4})', full)
    year = m.group(1) if m else None
    title = re.sub(r'\s*\(\d{4}\)', '', full).strip()

    # capa
    img = soup.select_one('.card__cover img')
    poster = img.get('src') if img and img.has_attr('src') else None

    # extrair vÃ­deos via Playwright
    videos = fetch_video_urls_with_playwright(page_url)[:2]
    return title, year, poster, videos

def generate_m3u(urls):
    lines = [M3U_HEADER]
    for page in sorted(urls, key=lambda u: u.lower()):
        print(f'Processando: {page}')
        title, year, poster, vids = extract_from_page(page)
        if not vids:
            print(f'  Aviso: sem vÃ­deos em {page}')
            continue
        name = f"{title} ({year})" if year else title
        for i, v in enumerate(vids, start=1):
            tag = 'principal' if i == 1 else 'alternativa'
            logo = f' tvg-logo="{poster}"' if poster else ''
            lines.append(f'#EXTINF:-1 type="video"{logo}, {name} [{tag}]')
            lines.append(v)
    return '\n'.join(lines)

def main():
    urls = read_urls(COMEDY_FILE)
    m3u = generate_m3u(urls)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(m3u)
    print(f'Playlist gerada em {OUTPUT_FILE}')

if __name__ == '__main__':
    main()
