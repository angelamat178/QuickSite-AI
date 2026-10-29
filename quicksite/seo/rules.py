from __future__ import annotations
from sqlalchemy import text
from .db import transaction
from .repository import add_recommendation

DEFAULT_RULES=[
 {"id":"missing_title","name":"Título ausente","description":"La auditoría comprobó que la página no contiene title.","severity":"high","config":{"enabled":True}},
 {"id":"missing_meta","name":"Meta descripción ausente","description":"La auditoría comprobó que no hay meta descripción.","severity":"medium","config":{"enabled":True}},
 {"id":"missing_h1","name":"H1 ausente","description":"La auditoría comprobó que la página no contiene H1.","severity":"medium","config":{"enabled":True}},
 {"id":"low_internal_links","name":"Página con pocos enlaces entrantes","description":"Señal estructural; requiere revisar importancia y arquitectura.","severity":"low","config":{"enabled":False,"max_inlinks":1}},
]

def seed_rules(engine):
    import json
    with transaction(engine) as c:
        for r in DEFAULT_RULES:
            c.execute(text("""INSERT INTO rules(id,name,description,enabled,severity,config_json)
            VALUES(:id,:name,:description,:enabled,:severity,:config)
            ON CONFLICT(id) DO NOTHING"""),{"id":r["id"],"name":r["name"],"description":r["description"],"enabled":int(r["config"].get("enabled",True)),"severity":r["severity"],"config":json.dumps(r["config"])})

def run_page_rules(engine, site_id, page_id, audit):
    seed_rules(engine); found=[]
    mapping={"missing_title":("title","Falta el título HTML"),"missing_meta":("meta_description","Falta la meta descripción"),"missing_h1":("h1","Falta el encabezado H1")}
    for rule_id,(field,title) in mapping.items():
        if not audit.get(field):
            evidence={"url":audit["url"],"field":field,"observed_value":audit.get(field),"source":"crawler","checked_at":audit.get("crawled_at")}
            add_recommendation(engine,site_id,page_id,rule_id,title,
             f"La auditoría HTTP observó que {field} está vacío. Revisa el contenido y la plantilla antes de modificar la página.",
             evidence,impact="potential",confidence="high",effort="low")
            found.append(rule_id)
    return found
