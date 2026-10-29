from __future__ import annotations
import json, re
from urllib.parse import urlsplit, urlunsplit
from sqlalchemy import text
from .db import transaction

def normalize_url(url: str) -> str:
    p=urlsplit(url.strip())
    if p.scheme.lower() not in ("http","https") or not p.netloc:
        raise ValueError("La URL debe ser absoluta y usar HTTP o HTTPS.")
    path=re.sub(r"/{2,}","/",p.path or "/")
    if path != "/" and path.endswith("/"): path=path.rstrip("/")
    return urlunsplit((p.scheme.lower(),p.netloc.lower(),path,p.query,""))

def create_site(engine, name, base_url, gsc_property="", ga4_property_id="", wp_api_url="", sitemap_url=""):
    base=normalize_url(base_url)
    with transaction(engine) as c:
        existing=c.execute(text("SELECT id FROM site_profiles WHERE base_url=:u"),{"u":base}).first()
        if existing: raise ValueError("Ya existe un perfil con esa URL base.")
        r=c.execute(text("""INSERT INTO site_profiles(name,base_url,gsc_property,ga4_property_id,wp_api_url,sitemap_url)
        VALUES(:n,:u,:g,:ga,:wp,:sm) RETURNING id"""),dict(n=name.strip(),u=base,g=gsc_property.strip(),ga=ga4_property_id.strip(),wp=wp_api_url.strip(),sm=sitemap_url.strip()))
        return r.scalar_one()

def list_sites(engine):
    with engine.connect() as c:
        return [dict(r._mapping) for r in c.execute(text("SELECT * FROM site_profiles ORDER BY id DESC"))]

def upsert_page(engine, site_id, url, **fields):
    normalized=normalize_url(url)
    allowed={"title","wp_id","wp_type","wp_status","canonical_url","meta_description","robots","http_status","h1","word_count","source","last_crawled_at"}
    data={k:v for k,v in fields.items() if k in allowed}
    data.update(site_id=site_id,url=url,normalized=normalized)
    cols=["site_id","url","normalized"]+list(k for k in data if k not in {"site_id","url","normalized"})
    extra_cols=cols[3:]
    if extra_cols:
        assignments=", ".join(f"{k}=:{k}" for k in cols if k not in {"site_id","normalized"})
        assignments += ", updated_at=CURRENT_TIMESTAMP"
        sql=f"INSERT INTO pages(site_profile_id,url,normalized_url,{','.join(extra_cols)}) VALUES(:site_id,:url,:normalized,{','.join(':'+k for k in extra_cols)}) ON CONFLICT(site_profile_id,normalized_url) DO UPDATE SET {assignments}"
    else:
        sql="INSERT INTO pages(site_profile_id,url,normalized_url) VALUES(:site_id,:url,:normalized) ON CONFLICT(site_profile_id,normalized_url) DO UPDATE SET url=excluded.url,updated_at=CURRENT_TIMESTAMP"
    with transaction(engine) as c:
        c.execute(text(sql),data)
        return c.execute(text("SELECT id FROM pages WHERE site_profile_id=:s AND normalized_url=:u"),{"s":site_id,"u":normalized}).scalar_one()

def list_pages(engine, site_id):
    with engine.connect() as c:
        return [dict(r._mapping) for r in c.execute(text("SELECT * FROM pages WHERE site_profile_id=:s ORDER BY url"),{"s":site_id})]

def save_metrics(engine, site_id, page_id, source, metric_date, metrics, dimensions=None, period_start=None, period_end=None, coverage="complete"):
    with transaction(engine) as c:
        c.execute(text("""INSERT INTO metric_snapshots(site_profile_id,page_id,source,metric_date,period_start,period_end,dimensions_json,metrics_json,coverage)
        VALUES(:s,:p,:src,:d,:ps,:pe,:dims,:metrics,:cov)"""),
        {"s":site_id,"p":page_id,"src":source,"d":metric_date,"ps":period_start,"pe":period_end,
         "dims":json.dumps(dimensions or {},ensure_ascii=False),"metrics":json.dumps(metrics,ensure_ascii=False),"cov":coverage})

def add_conversion(engine, site_id, event_date, source, event_name, count, page_id=None, qualified_count=None, customer_count=None, attribution=None, measurement_status="measured"):
    if count < 0 or (qualified_count is not None and qualified_count < 0) or (customer_count is not None and customer_count < 0):
        raise ValueError("Los recuentos no pueden ser negativos.")
    with transaction(engine) as c:
        c.execute(text("""INSERT INTO conversions(site_profile_id,page_id,event_date,source,event_name,count,qualified_count,customer_count,attribution_json,measurement_status)
        VALUES(:s,:p,:d,:src,:e,:n,:q,:cust,:a,:m)"""),
        {"s":site_id,"p":page_id,"d":event_date,"src":source,"e":event_name,"n":count,"q":qualified_count,"cust":customer_count,"a":json.dumps(attribution or {},ensure_ascii=False),"m":measurement_status})

def add_recommendation(engine, site_id, page_id, rule_id, title, explanation, evidence, impact="unknown", confidence="medium", effort="medium"):
    with transaction(engine) as c:
        existing = c.execute(text("SELECT id FROM recommendations WHERE site_profile_id=:s AND page_id=:p AND rule_id=:r AND status IN ('pending','accepted') ORDER BY id DESC LIMIT 1"), {"s":site_id,"p":page_id,"r":rule_id}).scalar()
        if existing:
            c.execute(text("UPDATE recommendations SET title=:t,explanation=:x,evidence_json=:e,impact=:i,confidence=:c,effort=:f,updated_at=CURRENT_TIMESTAMP WHERE id=:id"), {"t":title,"x":explanation,"e":json.dumps(evidence,ensure_ascii=False),"i":impact,"c":confidence,"f":effort,"id":existing})
            return existing
        result=c.execute(text("""INSERT INTO recommendations(site_profile_id,page_id,rule_id,title,explanation,evidence_json,impact,confidence,effort)
        VALUES(:s,:p,:r,:t,:x,:e,:i,:c,:f) RETURNING id"""),{"s":site_id,"p":page_id,"r":rule_id,"t":title,"x":explanation,"e":json.dumps(evidence,ensure_ascii=False),"i":impact,"c":confidence,"f":effort})
        return result.scalar_one()

def set_recommendation_status(engine, rec_id, status):
    if status not in {"pending","accepted","dismissed","completed"}: raise ValueError("Estado no válido.")
    with transaction(engine) as c:
        c.execute(text("UPDATE recommendations SET status=:s,updated_at=CURRENT_TIMESTAMP WHERE id=:i"),{"s":status,"i":rec_id})

def list_recommendations(engine, site_id):
    with engine.connect() as c:
        rows=c.execute(text("""SELECT r.*,p.url FROM recommendations r LEFT JOIN pages p ON p.id=r.page_id
        WHERE r.site_profile_id=:s ORDER BY r.created_at DESC"""),{"s":site_id})
        out=[]
        for row in rows:
            d=dict(row._mapping); d["evidence"]=json.loads(d.pop("evidence_json")); out.append(d)
        return out
