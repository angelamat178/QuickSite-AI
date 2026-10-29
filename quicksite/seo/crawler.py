from __future__ import annotations
import re
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

def audit_url(url: str, allowed_host: str, timeout=12) -> dict:
    p=urlparse(url)
    if p.scheme!="https" or p.hostname!=allowed_host:
        raise ValueError("El rastreador solo admite HTTPS en el dominio del perfil.")
    r=requests.get(url,timeout=timeout,allow_redirects=True,headers={"User-Agent":"QuickSiteSEO/0.1"})
    if urlparse(r.url).hostname!=allowed_host: raise ValueError("Redirección fuera del dominio; bloqueada.")
    soup=BeautifulSoup(r.text[:2_000_000],"html.parser")
    title=soup.title.get_text(" ",strip=True) if soup.title else ""
    desc=soup.find("meta",attrs={"name":re.compile("^description$",re.I)})
    canonical=soup.find("link",attrs={"rel":lambda v:v and "canonical" in v})
    robots=soup.find("meta",attrs={"name":re.compile("^robots$",re.I)})
    h1=soup.find("h1")
    text_content=soup.get_text(" ",strip=True)
    links=[]
    for a in soup.find_all("a",href=True):
        target=urljoin(r.url,a["href"]).split("#",1)[0]
        if urlparse(target).hostname==allowed_host and urlparse(target).scheme in ("http","https"):
            links.append({"url":target,"anchor":a.get_text(" ",strip=True)[:300]})
    return {"url":url,"final_url":r.url,"http_status":r.status_code,"title":title,
      "meta_description":desc.get("content","").strip() if desc else "",
      "canonical":canonical.get("href","").strip() if canonical else "",
      "robots":robots.get("content","").strip() if robots else "",
      "h1":h1.get_text(" ",strip=True) if h1 else "",
      "word_count":len(text_content.split()),"links":links,
      "crawled_at":datetime.now(timezone.utc).isoformat(),
      "findings":[x for x,ok in [
       ("missing_title",bool(title)),("missing_meta_description",bool(desc and desc.get("content","").strip())),
       ("missing_h1",bool(h1)),("multiple_h1",len(soup.find_all("h1"))<=1)] if not ok]}
