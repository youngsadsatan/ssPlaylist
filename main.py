#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import re
import yt_dlp

MOVIES_FILE = 'comedy.txt'
OUTPUT_FILE = 'playlist.m3u'
M3U_HEADER = '#EXTM3U\n'

def read_urls(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return sorted([line.strip() for line in f if line.strip() and not line.startswith('#')])

def extract_with_ytdlp(url):
    ydl_opts = {
        'skip_download': True,
        'quiet': True,
        'no_warnings': True,
        'format': 'best[ext=mp4]/best'
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
    primary_url = info.get('url')
    fallback_url = None
    for fmt in info.get('formats', []):
        if fmt.get('ext') == 'mp4' and fmt.get('url') != primary_url:
            fallback_url = fmt.get('url')
            break
    title = info.get('title') or url
    year_match = re.search(r'', title)
    year = year_match.group(1) if year_match else None
    thumb = info.get('thumbnail')
    urls = [u for u in (primary_url, fallback_url) if u]
    return title, year, thumb, urls

def generate_m3u(entries):
    lines = [M3U_HEADER]
    for title, year, thumb, urls in entries:
        name = f"{title} ({year})" if year else title
        for idx, u in enumerate(urls, start=1):
            tag = 'principal' if idx == 1 else 'alternativa'
            logo = f' tvg-logo="{thumb}"' if thumb else ''
            lines.append(f'#EXTINF:-1 type="video"{logo}, {name} [{tag}]')
            lines.append(u)
    return "\n".join(lines)

def main():
    try:
        urls = read_urls(MOVIES_FILE)
    except FileNotFoundError:
        print(f"Arquivo {MOVIES_FILE} não encontrado.")
        sys.exit(1)

    entries = []
    for url in urls:
        print(f"Extraindo: {url}")
        try:
            data = extract_with_ytdlp(url)
            if data[3]:
                entries.append(data)
            else:
                print(f"  Aviso: sem URLs mp4 para {url}")
        except Exception as e:
            print(f"  Erro em {url}: {e}")

    playlist = generate_m3u(entries)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(playlist)
    print(f"Arquivo {OUTPUT_FILE} gerado.")

if __name__ == '__main__':
    main()
