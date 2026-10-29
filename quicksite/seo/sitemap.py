from __future__ import annotations
import requests
from defusedxml import ElementTree as ET
from urllib.parse import urlparse
SITEMAP_NS={"sm":"http://www.sitemaps.org/schemas/sitemap/0.9"}

def parse_sitemap(xml_text: str) -> list[dict]:
    root=ET.fromstring(xml_text)
    tag=root.tag.rsplit("}",1)[-1]
    out=[]
    if tag not in {"urlset","sitemapindex"}: raise ValueError("XML no parece un sitemap estándar.")
    child="sitemap" if tag=="sitemapindex" else "url"
    for node in root.findall(f"sm:{child}",SITEMAP_NS):
        loc=node.findtext("sm:loc",default="",namespaces=SITEMAP_NS).strip()
        lastmod=node.findtext("sm:lastmod",default="",namespaces=SITEMAP_NS).strip() or None
        if loc: out.append({"url":loc,"lastmod":lastmod,"kind":"sitemap" if tag=="sitemapindex" else "page"})
    return out

def fetch_sitemap(url: str, timeout=15, max_bytes=5_000_000) -> list[dict]:
    p=urlparse(url)
    if p.scheme!="https": raise ValueError("Por seguridad, el sitemap debe usar HTTPS.")
    r=requests.get(url,timeout=timeout,headers={"User-Agent":"QuickSiteSEO/0.1"},stream=True)
    r.raise_for_status()
    chunks=[]; size=0
    for chunk in r.iter_content(65536):
        size+=len(chunk)
        if size>max_bytes: raise ValueError("Sitemap supera el límite de tamaño configurado.")
        chunks.append(chunk)
    return parse_sitemap(b"".join(chunks).decode(r.encoding or "utf-8",errors="replace"))


def fetch_sitemap_tree(url: str, timeout=15, max_bytes=5_000_000, max_sitemaps=100) -> list[dict]:
    """Lee sitemap normal o índice, limita tamaño y evita bucles de índices."""
    pending=[url]; seen=set(); pages=[]
    while pending and len(seen)<max_sitemaps:
        current=pending.pop(0)
        if current in seen: continue
        seen.add(current)
        entries=fetch_sitemap(current,timeout=timeout,max_bytes=max_bytes)
        for entry in entries:
            if entry["kind"]=="sitemap": pending.append(entry["url"])
            else: pages.append(entry)
    if pending: raise ValueError("El índice contiene más sitemaps de los permitidos.")
    return pages
