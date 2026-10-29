"""Conectores de lectura. No ejecutan escrituras en WordPress."""
from __future__ import annotations
from urllib.parse import urljoin, urlparse
import requests

def test_wordpress_readonly(base_url: str, username: str, application_password: str, timeout=12) -> dict:
    base=base_url.strip().rstrip("/")
    p=urlparse(base)
    if p.scheme!="https" or not p.netloc: raise ValueError("WordPress debe usar una URL HTTPS válida.")
    api=urljoin(base+"/","wp-json/wp/v2/users/me?context=edit")
    r=requests.get(api,auth=(username,application_password.replace(" ","")),timeout=timeout,
                   headers={"User-Agent":"QuickSiteSEO/0.1"})
    if r.status_code==401: raise ValueError("WordPress rechazó las credenciales (401).")
    if r.status_code==403: raise ValueError("Credenciales válidas o endpoint encontrado, pero sin permiso suficiente (403).")
    r.raise_for_status()
    data=r.json()
    return {"id":data.get("id"),"name":data.get("name"),"roles":data.get("roles",[]),"endpoint":api}

def fetch_wordpress_content(base_url: str, username: str, application_password: str, per_page=100, max_pages=10) -> list[dict]:
    base=base_url.strip().rstrip("/")
    p=urlparse(base)
    if p.scheme!="https" or not p.netloc: raise ValueError("WordPress debe usar HTTPS.")
    results=[]
    for endpoint,kind in (("posts","post"),("pages","page")):
        for page in range(1,max_pages+1):
            r=requests.get(urljoin(base+"/",f"wp-json/wp/v2/{endpoint}"),
              params={"context":"edit","per_page":min(per_page,100),"page":page,"_fields":"id,link,slug,status,date,modified,title,content,excerpt"},
              auth=(username,application_password.replace(" ","")),timeout=15)
            if r.status_code in (401,403): raise ValueError(f"Sin permisos para leer {endpoint} (HTTP {r.status_code}).")
            if r.status_code==400 and page>1: break
            r.raise_for_status()
            batch=r.json()
            for item in batch:
                results.append({"wp_id":item["id"],"wp_type":kind,"url":item["link"],"title":item.get("title",{}).get("rendered",""),
                  "wp_status":item.get("status"),"modified":item.get("modified"),"slug":item.get("slug")})
            if len(batch)<min(per_page,100): break
    return results
