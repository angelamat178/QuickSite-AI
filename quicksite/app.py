from __future__ import annotations
import json, re, hashlib, os
from datetime import datetime
from html import escape
from pathlib import Path
from urllib.parse import urlparse
import streamlit as st
import sys
import requests
from dotenv import load_dotenv

# Keep package imports and local data stable when Streamlit is launched from another cwd.
PROJECT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_DIR / ".env")
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))
from quicksite.seo.db import make_engine, init_db
from quicksite.seo.rules import seed_rules
from quicksite.seo.ui import render_seo_section

ROOT=Path(__file__).resolve().parent; DATA=ROOT/'data'; DATA.mkdir(exist_ok=True)
FILES={k:DATA/f'{k}.json' for k in ['articles','cards','templates','pages','bulk_jobs']}
def now(): return datetime.now().strftime('%Y-%m-%d %H:%M')
def uid(prefix, seed=''): return prefix+'_'+hashlib.sha1((seed+now()).encode()).hexdigest()[:8]
def load(key, default):
    if not FILES[key].exists(): save(key,default); return default
    try: return json.loads(FILES[key].read_text(encoding='utf-8'))
    except Exception: return default
def save(key, value): FILES[key].write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')

DEFAULT_CARDS=[
 {'id':'c1','name':'Datos fijos','category':'General','content':'Empresa de contenido digital. Público objetivo: pymes y profesionales del marketing. No inventar precios, plazos, estadísticas ni datos de empresa.','active':True,'updated':now()},
 {'id':'c2','name':'Estilo','category':'Estilo','content':'Tono cercano, claro y profesional. Evitar relleno, frases genéricas y repeticiones. Usar ejemplos concretos y subtítulos descriptivos.','active':True,'updated':now()},
 {'id':'c3','name':'Reglas SEO','category':'SEO','content':'Priorizar la intención de búsqueda y la utilidad para la persona. Usar encabezados descriptivos y enlaces internos relevantes; no forzar palabras clave.','active':True,'updated':now()}]
DEFAULT_TEMPLATES=[
 {'id':'t_guide','name':'Guía práctica','category':'Tutorial','description':'Proceso paso a paso con recomendaciones accionables.','layout':'guide','prompt':'Explica el proceso paso a paso. Incluye requisitos, errores habituales y una lista final.','blocks':[['intro','Introducción'],['heading','Antes de empezar'],['paragraph','Contexto'],['heading','Pasos principales'],['list','Pasos accionables'],['conclusion','Conclusión']]},
 {'id':'t_compare','name':'Comparativa','category':'Comparativa','description':'Compara alternativas con criterios transparentes.','layout':'comparison','prompt':'Compara alternativas con criterios explícitos. No inventes precios ni pruebas.','blocks':[['intro','Contexto y criterios'],['heading','Opciones'],['list','Ventajas y límites'],['heading','Cómo elegir'],['paragraph','Criterios de decisión'],['conclusion','Recomendación según el caso']]},
 {'id':'t_faq','name':'Preguntas frecuentes','category':'FAQ','description':'Respuestas concretas a preguntas de usuarios.','layout':'faq','prompt':'Responde preguntas específicas sin repetir una guía ya publicada.','blocks':[['intro','Respuesta breve'],['heading','Preguntas frecuentes'],['faq','Pregunta y respuesta'],['faq','Otra pregunta y respuesta'],['conclusion','Resumen']]},
 {'id':'t_case','name':'Caso práctico','category':'Caso práctico','description':'Escenario, decisiones, aprendizajes y límites.','layout':'case','prompt':'Usa un escenario concreto. No inventes testimonios ni resultados reales; indica si es hipotético.','blocks':[['intro','Escenario y reto'],['heading','Situación inicial'],['paragraph','Contexto'],['heading','Decisiones'],['list','Proceso'],['heading','Aprendizajes'],['conclusion','Conclusión']]}]
DEFAULT_ART={'id':'demo1','title':'Cómo crear una página web rápida y profesional con WordPress','keyword':'crear página web WordPress','meta':'Planifica y crea una web con WordPress con una estructura clara y consejos prácticos.','category':'Tecnología','template_id':'t_guide','status':'Borrador local','created':now(),'blocks':[
 {'type':'intro','text':'Crear una web útil empieza por definir qué necesita conseguir el proyecto y quién la va a utilizar. WordPress permite construir distintos tipos de sitios, pero el resultado depende de las decisiones de estructura, contenido y mantenimiento.'},
 {'type':'heading','text':'Define el objetivo y la estructura'},{'type':'paragraph','text':'Antes de elegir un diseño, concreta el público, las páginas necesarias y la acción principal que quieres facilitar.'},
 {'type':'heading','text':'Prepara la instalación'},{'type':'list','text':'Elegir un alojamiento adecuado.\nConfigurar el dominio.\nInstalar WordPress y mantenerlo actualizado.\nSeleccionar un tema accesible.'},
 {'type':'conclusion','text':'Empieza por una estructura pequeña, revisa el contenido y amplía la web cuando exista una necesidad concreta.'}]}
DEFAULT_PAGES=[{'title':'Guía de WordPress para principiantes','url':'https://ejemplo.com/guia-wordpress/','keywords':['wordpress','guía wordpress','principiantes']},{'title':'Cómo mejorar el SEO técnico','url':'https://ejemplo.com/seo-tecnico/','keywords':['seo técnico','rendimiento','indexación']},{'title':'Plugins esenciales para pequeñas empresas','url':'https://ejemplo.com/plugins-wordpress/','keywords':['plugins wordpress','pequeñas empresas','seguridad']}]
def navigate_to(label):
 st.session_state["quicksite_main_navigation_v2"] = label

def init():
 for key,default in [('articles',[DEFAULT_ART]),('cards',DEFAULT_CARDS),('templates',DEFAULT_TEMPLATES),('pages',DEFAULT_PAGES),('bulk_jobs',[])]:
  if key not in st.session_state: st.session_state[key]=load(key,default) or default

def template(tid): return next((x for x in st.session_state.templates if x['id']==tid),st.session_state.templates[0])
def article(aid): return next((x for x in st.session_state.articles if x['id']==aid),None)
def slug(s):
 import unicodedata
 s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode()
 return re.sub(r'[^a-z0-9]+','-',s.lower()).strip('-')
def make_demo(topic,tpl,prompt,keyword='',tone='Profesional',idx=0):
 # Plantillas con estructuras diferentes; contenido ilustrativo, no usa IA.
 layouts={
 'guide':[('intro',f'Esta guía aborda {topic} desde una perspectiva práctica. El objetivo es ayudarte a entender las decisiones principales y avanzar con un plan realista.'),('heading','Qué conviene tener claro antes de empezar'),('paragraph',f'Antes de actuar, define el objetivo, los recursos disponibles y cómo evaluarás el resultado de {topic}.'),('heading','Proceso recomendado'),('list',f'Define el objetivo relacionado con {topic}.\nRevisa requisitos y limitaciones.\nCompara alternativas con criterios claros.\nPrueba el enfoque y revisa el resultado.'),('heading','Errores que conviene evitar'),('paragraph','No des por ciertos datos sin verificar ni añadas pasos que no aporten valor. Adapta las recomendaciones al contexto real.'),('conclusion','Convierte estas ideas en una lista de acciones, verifica los datos específicos y revisa qué ha funcionado antes de ampliar el proceso.')],
 'comparison':[('intro',f'Elegir una solución para {topic} requiere más que comparar nombres. Conviene valorar el contexto, las limitaciones y el esfuerzo que implica cada alternativa.'),('heading','Criterios para comparar'),('list','Adecuación a la necesidad real.\nCoste total y mantenimiento, cuando se conozcan.\nFacilidad de uso y accesibilidad.\nPosibilidad de crecer sin complicaciones.'),('heading','Ventajas y límites'),('paragraph','Una opción sencilla puede cubrir necesidades básicas; otra más flexible quizá requiera configuración. Verifica las características actuales antes de decidir.'),('heading','Cómo tomar la decisión'),('paragraph',f'Prioriza el criterio más importante para tu caso de {topic}. Si hay dudas, compara alternativas con una prueba pequeña.'),('conclusion','No existe una opción universalmente mejor: elige la que resuelva tu necesidad concreta con límites asumibles.')],
 'faq':[('intro',f'Estas respuestas reúnen dudas habituales sobre {topic}. Úsalas como punto de partida y confirma los detalles específicos de tu situación.'),('heading','Preguntas frecuentes'),('faq',f'¿Por dónde empiezo con {topic}?\nDefine el objetivo y comprueba los requisitos antes de elegir herramientas.'),('faq','¿Qué errores son habituales?\nSaltar la planificación, asumir que todos los casos son iguales y no comprobar resultados.'),('faq','¿Cómo sé si funciona?\nDefine una señal de éxito antes de empezar y revísala con datos adecuados.'),('conclusion','Resume las decisiones clave y pasa a la acción con un alcance manejable.')],
 'case':[('intro',f'Imagina un equipo que necesita resolver una necesidad relacionada con {topic} con recursos limitados. Este caso hipotético muestra cómo ordenar el trabajo sin asumir una solución única.'),('heading','Situación y reto'),('paragraph','Separa los requisitos imprescindibles de las preferencias. Registra también qué información falta y quién puede validarla.'),('heading','Decisiones y ejecución'),('list','Acordar un objetivo verificable.\nComparar dos o tres enfoques.\nProbar la opción más sencilla que cumpla los requisitos.\nDocumentar resultados y límites.'),('heading','Aprendizajes'),('paragraph',f'En un proyecto de {topic}, las decisiones deben ajustarse al contexto real. Este ejemplo es ilustrativo, no un resultado medido.'),('conclusion','Aplica el método a pequeña escala, recoge evidencias y revisa el plan antes de invertir más recursos.')]} 
 blocks=[{'type':t,'text':v} for t,v in layouts.get(tpl.get('layout','guide'),layouts['guide'])]
 if prompt.strip(): blocks.insert(1,{'type':'paragraph','text':'Enfoque solicitado: '+prompt.strip()})
 prefixes={'guide':'Guía práctica: ','comparison':'Cómo elegir: ','case':'Caso práctico: '}
 title=('Preguntas frecuentes sobre '+topic) if tpl.get('layout')=='faq' else prefixes.get(tpl.get('layout'),'')+topic[:1].upper()+topic[1:]
 if idx%2 and len(blocks)>5: blocks[2],blocks[4]=blocks[4],blocks[2]
 return {'id':uid('art',topic+str(idx)),'title':title,'keyword':keyword.strip() or topic.lower(),'meta':f'Una visión práctica de {topic}: criterios, pasos y recomendaciones para decidir con contexto.'[:160],'category':'General','template_id':tpl['id'],'status':'Borrador local','created':now(),'tone':tone,'prompt':prompt,'blocks':blocks,'bulk_index':idx}
def markdown(a):
 out=['# '+a.get('title','Sin título')]
 for b in a.get('blocks',[]):
  t=b.get('text','').strip(); typ=b.get('type','paragraph')
  if not t: continue
  if typ=='heading': out.append('## '+t)
  elif typ=='list': out.append('\n'.join('- '+x.strip().lstrip('-• ') for x in t.splitlines() if x.strip()))
  elif typ=='faq':
   lines=t.splitlines(); out.append('### '+(lines[0] if lines else 'Pregunta frecuente')); out.extend(lines[1:])
  elif typ=='conclusion': out.append('## Conclusión\n'+t)
  else: out.append(t)
 return '\n\n'.join(out)
def find_links(text,pages,own_url=''):
 found=[]
 for p in pages:
  url=p.get('url','').strip()
  if not url or url==own_url: continue
  candidates=sorted(p.get('keywords',[])+[p.get('title','')],key=len,reverse=True)
  match=next((k for k in candidates if k and len(k.strip())>2 and k.lower() in text.lower()),None)
  if match and not any(x['url']==url for x in found): found.append({'anchor':match,'title':p.get('title',''),'url':url})
 return found
def link_text(text,item):
 pat=re.compile(re.escape(item['anchor']),re.I)
 if f"]({item['url']})" in text: return text
 return pat.sub(lambda m:f'[{m.group(0)}]({item["url"]})',text,count=1)



def render_legacy_interlinking():
 st.title('Páginas e interlinking'); st.write('Carga un inventario de URLs propias y revisa posibles enlaces contextuales.')
 st.info('TXT: una línea por página: Título | URL | palabra clave 1, palabra clave 2. CSV: title,url,keywords.')
 uploaded=st.file_uploader('Importar listado de URLs (CSV o TXT)',type=['csv','txt'],key='urlfile'); default='\n'.join(f"{p['title']} | {p['url']} | {', '.join(p.get('keywords',[]))}" for p in st.session_state.pages); text=st.text_area('Listado de páginas',default,height=170)
 x,y=st.columns(2)
 if x.button('Importar / actualizar páginas',type='primary'):
  raw=uploaded.getvalue().decode('utf-8-sig',errors='replace') if uploaded else text; parsed=[]
  if uploaded and uploaded.name.lower().endswith('.csv'):
   import csv,io
   for row in csv.DictReader(io.StringIO(raw)):
    url=(row.get('url') or row.get('URL') or '').strip(); title=(row.get('title') or row.get('titulo') or url).strip(); kws=(row.get('keywords') or row.get('palabras_clave') or '').replace(';',',')
    if urlparse(url).scheme in ('http','https') and urlparse(url).netloc: parsed.append({'title':title,'url':url,'keywords':[k.strip() for k in kws.split(',') if k.strip()]})
  else:
   for line in raw.splitlines():
    p=[v.strip() for v in line.split('|')]
    if len(p)>=2 and urlparse(p[1]).scheme in ('http','https') and urlparse(p[1]).netloc: parsed.append({'title':p[0] or p[1],'url':p[1],'keywords':[k.strip() for k in (p[2] if len(p)>2 else '').split(',') if k.strip()]})
  if parsed: st.session_state.pages=list({p['url']:p for p in parsed}.values()); save('pages',st.session_state.pages); st.success(f"Guardadas {len(st.session_state.pages)} páginas.")
  else: st.error('No se encontraron URLs http/https válidas.')
 y.download_button('Descargar CSV','title,url,keywords\n'+'\n'.join('"'+p['title'].replace('"','""')+'","'+p['url']+'","'+', '.join(p.get('keywords',[]))+'"' for p in st.session_state.pages),file_name='quicksite_urls.csv',mime='text/csv')
 st.markdown('### Inventario actual'); st.dataframe([{'Título':p['title'],'URL':p['url'],'Palabras clave':', '.join(p.get('keywords',[]))} for p in st.session_state.pages],use_container_width=True,hide_index=True)
 st.markdown('### Revisar interlinking de un artículo')
 if st.session_state.articles:
  amap={f"{a['title']} · {a.get('created','')}":a['id'] for a in st.session_state.articles}; pick=st.selectbox('Artículo que quieres revisar',list(amap),key='link_pick'); a=article(amap[pick]); own=st.text_input('URL de este artículo (opcional)',placeholder='https://tudominio.com/articulo/')
  if st.button('🔎 Revisar interlinking',type='primary'):
   combined=a['title']+'\n'+'\n'.join(b.get('text','') for b in a['blocks']); st.session_state.link_review={'article_id':a['id'],'found':find_links(combined,st.session_state.pages,own.strip())}
  review=st.session_state.get('link_review')
  if review and review.get('article_id')==a['id']:
   if review['found']:
    st.success(f"{len(review['found'])} oportunidades posibles. Revisa que cada enlace ayude al lector.")
    for i,item in enumerate(review['found']):
     with st.container(border=True):
      st.markdown(f"**Ancla sugerida:** `{item['anchor']}` · {item['title']}"); st.code(item['url'])
      if st.button('Insertar enlace',key=f"apply_{a['id']}_{i}"):
       done=False
       for b in a['blocks']:
        if item['anchor'].lower() in b.get('text','').lower(): b['text']=link_text(b['text'],item); done=True; break
       if done: save('articles',st.session_state.articles); st.success('Enlace insertado en el primer bloque coincidente.'); st.rerun()
       else: st.warning('No se encontró el texto ancla en un bloque.')
    if st.button('Insertar todas las sugerencias',key='apply_all_'+a['id']):
     n=0
     for item in review['found']:
      for b in a['blocks']:
       if item['anchor'].lower() in b.get('text','').lower(): b['text']=link_text(b['text'],item); n+=1; break
     save('articles',st.session_state.articles); st.success(f'Aplicados {n} enlaces. Comprueba el contexto.'); st.rerun()
   else: st.warning('No hay coincidencias literales. Añade sinónimos relevantes o revisa el texto.')
 else: st.info('Crea un artículo para revisar enlaces.')

st.set_page_config(page_title='QuickSite · Studio',page_icon='⚡',layout='wide')
st.markdown('''<style>
:root{--qs-bg:#090C12;--qs-panel:#111722;--qs-line:#263244;--qs-text:#EEF3FA;--qs-muted:#91A0B5;--qs-orange:#FF761A;--qs-green:#48D6A5;--qs-radius:18px}
html,body,[class*="css"]{font-family:Inter,"Segoe UI",system-ui,-apple-system,sans-serif}
.stApp{background:radial-gradient(ellipse at 72% -10%,rgba(39,53,76,.36),transparent 38%),linear-gradient(180deg,#0B0F16 0%,#090C12 100%);color:var(--qs-text)}
[data-testid="stHeader"]{background:rgba(9,12,18,.78);backdrop-filter:blur(12px)}
[data-testid="stMainBlockContainer"]{max-width:1720px;padding:1.55rem 2.5rem 3rem}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0B0F15,#090C12);border-right:1px solid #202938}
[data-testid="stSidebar"] [data-testid="stSidebarContent"]{padding:1.35rem .95rem 1.1rem}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p{color:#98A7BA}
[data-testid="stSidebar"] div[data-testid="stRadio"]>label{display:none}
[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"]{gap:.35rem}
[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] label{border:1px solid transparent;border-radius:11px;padding:.52rem .65rem;background:transparent;transition:all .15s}
[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] label p{font-size:.91rem;font-weight:550;color:#AAB5C5}
[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked){background:linear-gradient(90deg,rgba(255,118,26,.19),rgba(255,118,26,.07));border-color:rgba(255,118,26,.25);box-shadow:inset 3px 0 0 var(--qs-orange)}
[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) p{color:#FF9A50;font-weight:700}
[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] label>div:first-child{display:none}
[data-testid="stSidebar"] hr{border-color:#202938;margin:.85rem 0}
.stApp h1,.stApp h2,.stApp h3{letter-spacing:-.045em;color:#F1F5FB;font-weight:700}
h1{font-size:2.15rem!important;line-height:1.12!important}h2{font-size:1.45rem!important;line-height:1.2!important}h3{font-size:1.12rem!important;line-height:1.25!important}
p,.stMarkdown{color:#CBD5E3}.stCaption,small,[data-testid="stCaptionContainer"]{color:var(--qs-muted)!important}
hr{border-color:#263244!important;opacity:.75}
.stButton>button,.stDownloadButton>button,.stFormSubmitButton>button{border-radius:10px;border:1px solid #2B3748;background:linear-gradient(180deg,#1A2330,#151C27);color:#EAF0F8;font-weight:650;min-height:2.55rem;padding:.52rem .95rem;transition:transform .14s,border-color .14s,filter .14s;box-shadow:0 3px 10px rgba(0,0,0,.12)}
.stButton>button:hover,.stDownloadButton>button:hover,.stFormSubmitButton>button:hover{border-color:rgba(255,118,26,.75);color:#fff;transform:translateY(-1px);filter:brightness(1.06)}
.stButton>button[kind="primary"],.stFormSubmitButton>button[kind="primary"]{background:linear-gradient(135deg,#FF8A25,#FF6A00 70%,#F35B00);border-color:#FF8A25;color:#fff;box-shadow:0 6px 18px rgba(255,106,0,.17)}
div[data-baseweb="input"] input,div[data-baseweb="textarea"] textarea,div[data-baseweb="select"]>div{background:#0D131C!important;color:#EDF3FA!important;border-color:#2B3748!important;border-radius:10px!important;min-height:2.55rem}
div[data-baseweb="input"] input:focus,div[data-baseweb="textarea"] textarea:focus{border-color:#FF842B!important;box-shadow:0 0 0 1px rgba(255,132,43,.25)!important}
div[data-testid="stTextArea"] textarea{line-height:1.55}
div[data-testid="stMetric"]{background:linear-gradient(145deg,#151D29,#101620);border:1px solid #283447;padding:1.05rem 1.15rem;border-radius:15px;box-shadow:0 8px 22px rgba(0,0,0,.1);min-height:110px}
div[data-testid="stMetricLabel"] p{font-size:.84rem!important;font-weight:600;color:#9CAABD!important}div[data-testid="stMetricValue"]{font-size:1.75rem!important;font-weight:750;letter-spacing:-.04em;color:#F4F7FC}div[data-testid="stMetricDelta"]{font-size:.78rem}
div[data-testid="stVerticalBlockBorderWrapper"]{background:linear-gradient(145deg,rgba(20,28,40,.92),rgba(14,20,29,.96));border:1px solid #273346!important;border-radius:var(--qs-radius)!important;box-shadow:0 12px 28px rgba(0,0,0,.12);padding:1px}
div[data-testid="stVerticalBlockBorderWrapper"]>div{padding:1rem 1.05rem}
div[data-testid="stDataFrame"],div[data-testid="stTable"]{border:1px solid #293548;border-radius:12px;overflow:hidden}
div[data-testid="stExpander"]{border:1px solid #293548!important;border-radius:12px!important;background:rgba(17,23,34,.58)}div[data-testid="stExpander"] summary{font-weight:600;color:#DDE6F2}
div[data-testid="stAlert"]{border-radius:12px;border:1px solid #354357}
div[data-testid="stRadio"]>label{color:#AAB8CA;font-size:.85rem;font-weight:650}div[data-testid="stRadio"] div[role="radiogroup"]{gap:.25rem}
div[data-testid="stRadio"] div[role="radiogroup"] label{padding:.43rem .78rem;border:1px solid transparent;border-radius:10px;background:transparent;transition:all .15s}
div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked){background:rgba(255,118,26,.13);border-color:rgba(255,118,26,.35)}div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) p{color:#FF9A50;font-weight:700}
div[data-testid="stCheckbox"] label p{color:#C3CEDC}
.qs-kicker{color:#FF8A32;font-size:.71rem;font-weight:800;text-transform:uppercase;letter-spacing:.15em;margin:0 0 .45rem}
.qs-brand{display:flex;align-items:center;gap:.7rem;margin:0 0 1.6rem;padding:.3rem .4rem}.qs-brand-mark{display:flex;align-items:center;justify-content:center;width:38px;height:38px;border-radius:12px;color:#fff;background:linear-gradient(145deg,#FF8A25,#F65C00);font-size:1.25rem;box-shadow:0 6px 18px rgba(255,106,0,.18)}.qs-brand-name{font-size:1.48rem;font-weight:800;letter-spacing:-.06em;color:#F3F6FB;line-height:1.05}.qs-brand-name span{color:#FF7A1A}.qs-brand-mark svg{width:23px;height:23px;display:block}
.qs-side-label{color:#66768C;font-size:.67rem;letter-spacing:.14em;font-weight:800;margin:.7rem .45rem .45rem}.qs-side-status{display:flex;align-items:center;gap:.45rem;color:#92A2B7;font-size:.78rem}.qs-side-status i{display:inline-block;width:7px;height:7px;border-radius:50%;background:#45D7A0;box-shadow:0 0 0 4px rgba(69,215,160,.1)}
.qs-pill{display:inline-flex;align-items:center;background:rgba(72,214,165,.1);color:#55D9AD;border:1px solid rgba(72,214,165,.22);border-radius:99px;padding:4px 10px;font-size:.74rem;font-weight:750;letter-spacing:.02em}
.qs-seo-top-title{display:flex;align-items:center;justify-content:space-between;gap:1rem;margin:.15rem 0 1.1rem}.qs-seo-top-title h1{font-size:1.9rem!important;margin:0 0 .3rem!important}.qs-seo-top-title p{margin:0;color:#98A7BA;font-size:.92rem}
.qs-local-pill{display:inline-flex;align-items:center;gap:.5rem;padding:.55rem .8rem;border:1px solid #293548;border-radius:99px;background:#101722;color:#B6C2D2;font-size:.76rem;font-weight:650;white-space:nowrap}.qs-local-pill span{width:7px;height:7px;border-radius:50%;background:#4DD9A7;box-shadow:0 0 0 4px rgba(77,217,167,.1)}
.qs-seo-hero{display:flex;align-items:center;justify-content:space-between;gap:1.2rem;padding:1.55rem 1.65rem;margin:.15rem 0 1.1rem;border:1px solid rgba(255,118,26,.2);border-radius:18px;background:radial-gradient(ellipse at 78% 0%,rgba(255,118,26,.12),transparent 40%),linear-gradient(115deg,#171E29,#10151F 64%,#171D27);box-shadow:0 16px 34px rgba(0,0,0,.14)}
.qs-seo-hero .qs-eyebrow{font-size:.68rem;letter-spacing:.16em;color:#FF9A50;font-weight:800;margin-bottom:.55rem}.qs-seo-hero h1{margin:0 0 .52rem;font-size:2rem!important;letter-spacing:-.055em}.qs-seo-hero p{margin:0;color:#A7B4C6;max-width:660px;font-size:.94rem}
.qs-hero-side{display:flex;align-items:center;gap:.8rem;padding:.85rem 1rem;border-radius:14px;border:1px solid #2B3748;background:rgba(9,13,20,.45);min-width:240px}.qs-pulse{width:9px;height:9px;border-radius:100%;background:#45D7A0;box-shadow:0 0 0 5px rgba(69,215,160,.1)}.qs-hero-side strong,.qs-hero-side span{display:block}.qs-hero-side strong{font-size:.88rem;color:#EBF1F8;margin-bottom:.2rem}.qs-hero-side span{font-size:.73rem;color:#8FA0B5;max-width:245px;overflow-wrap:anywhere}
.qs-section-heading{display:flex;justify-content:space-between;align-items:end;margin:1.9rem 0 .9rem}.qs-section-heading h2{font-size:1.38rem!important;margin:0 0 .25rem}.qs-section-heading p{margin:0;color:#8F9FB4;font-size:.85rem}
.qs-chart-heading{display:flex;align-items:flex-start;justify-content:space-between;gap:.7rem;min-height:42px;margin-bottom:.35rem}.qs-chart-title{color:#EFF4FB;font-weight:750;font-size:1rem;letter-spacing:-.02em}.qs-chart-subtitle{font-size:.77rem;color:#8595AA;margin-top:.22rem}
.qs-demo-badge,.qs-data-badge{flex-shrink:0;display:inline-flex;align-items:center;padding:.28rem .48rem;border-radius:7px;font-size:.61rem;font-weight:850;letter-spacing:.08em;white-space:nowrap}.qs-demo-badge{color:#F4C16A;border:1px solid rgba(244,193,106,.23);background:rgba(244,193,106,.08)}.qs-data-badge{color:#56D7AC;border:1px solid rgba(86,215,172,.22);background:rgba(86,215,172,.08)}
.qs-inline-notice{display:flex;align-items:center;gap:.8rem;margin:.7rem 0 1rem;padding:.9rem 1rem;border:1px solid rgba(255,118,26,.24);border-radius:12px;background:rgba(255,118,26,.055)}.qs-inline-notice strong,.qs-inline-notice span{display:block}.qs-inline-notice strong{color:#F5F7FA;margin-bottom:.2rem}.qs-inline-notice span{font-size:.82rem;color:#A8B4C4}
.qs-action-number{font-size:.72rem;font-weight:850;letter-spacing:.12em;color:#FF8B34;margin-bottom:.8rem}.qs-action-title{font-size:1.02rem;font-weight:750;color:#F0F4FA;margin-bottom:.35rem}.qs-action-description{font-size:.82rem;color:#94A3B7;min-height:2.8rem;margin-bottom:.8rem;line-height:1.5}
.qs-footnote{margin-top:1rem;padding:.8rem 1rem;border-left:3px solid #43516A;background:rgba(26,35,49,.45);border-radius:0 10px 10px 0;color:#91A0B5;font-size:.78rem;line-height:1.55}.qs-footnote strong{color:#C1CDDC}
.qs-recent-row{display:flex;align-items:center;gap:.8rem;padding:.85rem .1rem;border-bottom:1px solid rgba(43,55,72,.72)}.qs-recent-row:last-child{border-bottom:0}.qs-recent-dot{width:8px;height:8px;flex:0 0 8px;border-radius:50%;background:#FF761A;box-shadow:0 0 0 4px rgba(255,118,26,.1)}.qs-recent-main{min-width:0;flex:1}.qs-recent-main strong,.qs-recent-main span{display:block}.qs-recent-main strong{color:#EAF0F8;font-size:.86rem;font-weight:650;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.qs-recent-main span{font-size:.74rem;color:#8393A8;margin-top:.2rem}.qs-recent-status{font-size:.69rem;color:#A8B6C9;border:1px solid #304056;border-radius:7px;padding:.28rem .45rem;white-space:nowrap}
[data-testid="stPlotlyChart"]{border-radius:12px}
@media(max-width:900px){[data-testid="stMainBlockContainer"]{padding-left:1rem;padding-right:1rem}.qs-seo-hero{align-items:flex-start;flex-direction:column}.qs-hero-side{min-width:0;width:100%}.qs-seo-top-title{align-items:flex-start;flex-direction:column}.qs-local-pill{margin-top:.2rem}}

</style>''',unsafe_allow_html=True)
# Shared local DB for SEO metadata; the editorial prototype retains its own JSON store for now.
(PROJECT_DIR / 'data').mkdir(parents=True, exist_ok=True)
engine = make_engine()
init_db(engine)
seed_rules(engine)
init()
with st.sidebar:
 st.markdown('<div class="qs-brand"><div class="qs-brand-mark"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M13.2 1.8 4.7 13.1h6.1l-.9 9.1 9.4-13.1h-6.1z" fill="currentColor"/></svg></div><div class="qs-brand-name">Quick<span>Site</span></div></div>', unsafe_allow_html=True)
 st.markdown('<div class="qs-side-label">WORKSPACE</div>', unsafe_allow_html=True)
 nav_map={
  '⌂  Inicio':'Inicio','✦  Generador':'Generador','◉  Chat':'Chat','▤  Editor por bloques':'Editor por bloques',
  '⌁  SEO y analítica':'SEO','▦  Generación en masa':'Generación en masa','▧  Plantillas':'Plantillas',
  '▣  Fichas de contexto':'Fichas de contexto','◷  Historial':'Historial','⚙  Ajustes':'Ajustes'}
 selected_nav=st.radio('Navegación',list(nav_map),format_func=lambda item:item,label_visibility='collapsed',key='quicksite_main_navigation_v2')
 page=nav_map[selected_nav]
 st.markdown('---')
 active=sum(bool(c.get('active')) for c in st.session_state.cards)
 st.markdown(f'<div class="qs-side-label">CONTEXTO ACTIVO</div><div class="qs-pill">{active} de {len(st.session_state.cards)} fichas</div>',unsafe_allow_html=True)
 for c in st.session_state.cards:
  if c.get('active'):
   st.caption('●  '+c['name'])
 st.markdown('---')
 st.markdown('<div class="qs-side-status"><i></i> Aplicación local · No publica</div>',unsafe_allow_html=True)
if page != 'SEO':
 st.markdown('<div class="qs-kicker">QUICKSITE / EDITORIAL STUDIO</div>',unsafe_allow_html=True)

if page=='Inicio':
 st.markdown('<section class="qs-seo-hero"><div><div class="qs-eyebrow">EDITORIAL WORKSPACE · LOCAL FIRST</div><h1>Tu estudio editorial</h1><p>Prepara contenido, cuida el SEO y organiza tus recursos desde un mismo espacio.</p></div><div class="qs-hero-side"><div class="qs-pulse"></div><div><strong>QuickSite listo</strong><span>Revisión humana antes de cualquier publicación</span></div></div></section>',unsafe_allow_html=True)
 cols=st.columns(4,gap='medium')
 for col,label,val in zip(cols,['Artículos guardados','Plantillas','Fichas activas','URLs editoriales'],[len(st.session_state.articles),len(st.session_state.templates),active,len(st.session_state.pages)]):
  with col:
   st.metric(label,val)
 st.markdown('<div class="qs-section-heading"><div><h2>Tu espacio de trabajo</h2><p>Accede directamente a las funciones habituales.</p></div></div>',unsafe_allow_html=True)
 quick=st.columns(3,gap='medium')
 quick_actions=[
  (quick[0],'✦','Generar contenido','Crea un nuevo borrador con una plantilla y fichas de contexto.','✦  Generador','Abrir generador'),
  (quick[1],'⌁','SEO y analítica','Audita páginas, revisa hallazgos y prioriza mejoras técnicas.','⌁  SEO y analítica','Abrir SEO'),
  (quick[2],'▣','Fichas de contexto','Mantén consistentes los datos, el estilo y las reglas editoriales.','▣  Fichas de contexto','Gestionar fichas'),
 ]
 for col,icon,title,desc,dest,button_text in quick_actions:
  with col:
   with st.container(border=True):
    st.markdown(f'<div class="qs-action-number">{icon} / QUICK ACTION</div><div class="qs-action-title">{title}</div><div class="qs-action-description">{desc}</div>',unsafe_allow_html=True)
    st.button(button_text,key='home_action_'+title.replace(' ','_'),on_click=navigate_to,args=(dest,),use_container_width=True)
 st.markdown('<div class="qs-section-heading"><div><h2>Biblioteca editorial</h2><p>Estado y actividad de los artículos guardados localmente.</p></div></div>',unsafe_allow_html=True)
 left,right=st.columns([.9,1.5],gap='large')
 with left:
  with st.container(border=True):
   st.markdown('**Estado de los artículos**')
   import plotly.graph_objects as go
   from collections import Counter
   status_counts=Counter(a.get('status','Sin estado') for a in st.session_state.articles)
   if status_counts:
    palette=['#FF761A','#7AA2FF','#48D6A5','#B49BFF','#8190A5']; status_colors=[palette[i%len(palette)] for i,_ in enumerate(status_counts)]
    fig=go.Figure(go.Pie(labels=list(status_counts),values=list(status_counts.values()),hole=.7,marker={'colors':status_colors,'line':{'color':'#10151E','width':3}},textinfo='percent',hovertemplate='%{label}<br>%{value} artículos<extra></extra>'))
    fig.update_layout(template='plotly_dark',height=270,paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',font={'family':'Inter, Segoe UI, sans-serif','color':'#EAF0F8','size':12},showlegend=True,legend={'orientation':'h','yanchor':'bottom','y':-0.03,'xanchor':'left','x':0},margin={'l':5,'r':5,'t':8,'b':16})
    st.plotly_chart(fig,use_container_width=True,config={'displayModeBar':False},key='home_article_status')
   else:
    st.info('Todavía no hay artículos guardados.')
 with right:
  with st.container(border=True):
   st.markdown('**Actividad reciente**')
   recent=sorted(st.session_state.articles,key=lambda x:x.get('created',''),reverse=True)[:5]
   if recent:
    for a in recent:
     title_html=escape(str(a.get("title","Sin título"))); keyword_html=escape(str(a.get("keyword", "Sin palabra clave"))); created_html=escape(str(a.get("created", ""))); status_html=escape(str(a.get("status","Borrador local")))
     st.markdown(f'<div class="qs-recent-row"><div class="qs-recent-dot"></div><div class="qs-recent-main"><strong>{title_html}</strong><span>{keyword_html} · {created_html}</span></div><span class="qs-recent-status">{status_html}</span></div>',unsafe_allow_html=True)
   else:
    st.info('Genera el primer artículo desde el menú lateral.')
 st.markdown('<div class="qs-footnote"><strong>Modo seguro:</strong> los artículos se mantienen como borradores locales hasta que se conecte el flujo de WordPress. QuickSite no publica automáticamente.</div>',unsafe_allow_html=True)

elif page=='Generador':
 st.title('Genera un artículo para tu blog')
 st.write('Prepara un borrador para WordPress, revisa el resultado y ajusta el contenido antes de enviarlo.')
 left,right=st.columns([1.08,1],gap='large')
 with left:
  st.markdown('### Construcción')
  with st.container(border=True):
   topic=st.text_input('Tema o idea del artículo',placeholder='Ej. Cómo elegir un hosting para una tienda online',max_chars=200,key='generator_topic')
   c1,c2=st.columns(2)
   with c1:
    tone=st.selectbox('Tono de voz',['Profesional','Conversacional','Informativo','Persuasivo','Creativo'],key='generator_tone'); tplmap={f"{t['name']} · {t['category']}":t['id'] for t in st.session_state.templates}; tpllabel=st.selectbox('Plantilla',list(tplmap),key='generator_template')
   with c2:
    keyword=st.text_input('Palabra clave principal',placeholder='Palabras clave separadas por comas',key='generator_keyword'); category=st.selectbox('Categoría',['General','WordPress','SEO','Marketing digital','Tecnología','Guías'],key='generator_category')
   prompt=st.text_area('Instrucciones adicionales',placeholder='Audiencia, enfoque, requisitos, elementos que debe incluir y qué evitar…',height=110,key='generator_prompt'); use_cards=st.checkbox('Aplicar fichas de contexto activas',True,key='generator_use_cards')
   if st.button('⚡ Generar borrador',type='primary',use_container_width=True,key='generator_create'):
    if not topic.strip(): st.error('Escribe un tema antes de generar.')
    else:
     context='\n'.join(c['name']+': '+c['content'] for c in st.session_state.cards if use_cards and c.get('active')); effective=(prompt+'\nContexto activo:\n'+context).strip(); a=make_demo(topic,template(tplmap[tpllabel]),effective,keyword,tone); a['category']=category; st.session_state.articles.insert(0,a); save('articles',st.session_state.articles); st.session_state.selected_article_id=a['id']; st.success('Borrador de demostración creado y guardado. El generador aún no usa Ollama; puedes editarlo antes de exportar.')
 with right:
  st.markdown('### Vista previa')
  selected=article(st.session_state.get('selected_article_id','')) or (st.session_state.articles[0] if st.session_state.articles else None)
  if selected:
   with st.container(border=True):
    st.caption(f"{selected.get('category','General')} · {selected.get('created','')} · BORRADOR LOCAL")
    st.markdown('## '+selected.get('title','Sin título'))
    st.caption('Palabra clave: '+selected.get('keyword','—'))
    if selected.get('meta'): st.write(selected['meta'])
    for b in selected.get('blocks',[]):
     text=b.get('text','').strip(); typ=b.get('type')
     if not text: continue
     if typ=='heading': st.markdown('### '+text)
     elif typ=='list':
      for line in text.splitlines():
       if line.strip(): st.markdown('- '+line.lstrip('-• '))
     elif typ=='faq':
      lines=text.splitlines()
      with st.expander(lines[0] if lines else 'Pregunta frecuente'): st.write('\n'.join(lines[1:]) if len(lines)>1 else '')
     elif typ=='conclusion': st.markdown('### Conclusión'); st.write(text)
     else: st.write(text)
   st.download_button('Descargar Markdown',markdown(selected),file_name=slug(selected['title'])+'.md',mime='text/markdown',use_container_width=True)
  else:
   st.info('Genera un artículo para mostrar la vista previa aquí.')

elif page=='Chat':
 st.title('Chat con QuickSite AI')
 st.caption('Conversación con Ollama local y fichas de contexto activas. Si Ollama no está disponible, no se simula una respuesta.')
 if 'chat_messages' not in st.session_state: st.session_state.chat_messages=[]
 col_a,col_b=st.columns([5,1])
 with col_b:
  if st.button('Limpiar chat',use_container_width=True):
   st.session_state.chat_messages=[]; st.rerun()
 for msg in st.session_state.chat_messages:
  with st.chat_message(msg['role']): st.markdown(msg['content'])
 prompt=st.chat_input('Escribe una pregunta o pide una mejora…')
 if prompt:
  st.session_state.chat_messages.append({'role':'user','content':prompt})
  with st.chat_message('user'): st.markdown(prompt)
  model=os.getenv('OLLAMA_MODEL','').strip(); base_url=os.getenv('OLLAMA_URL','http://localhost:11434').strip().rstrip('/')
  if not model:
   st.warning('Falta configurar OLLAMA_MODEL en el archivo .env. No se ha enviado la petición.')
  else:
   context='\n\n'.join(c['name']+':\n'+c['content'] for c in st.session_state.cards if c.get('active'))
   system=('Eres QuickSite AI, un asistente editorial. Responde en castellano. No inventes datos fijos, precios, plazos ni datos de empresa; señala lo que debe verificarse. No publiques ni modifiques WordPress.\n\nFICHAS DE CONTEXTO ACTIVAS:\n'+(context or 'No hay fichas activas.'))
   payload={'model':model,'stream':False,'messages':[{'role':'system','content':system}]+st.session_state.chat_messages[-20:]}
   try:
    with st.spinner('Consultando Ollama local…'):
     response=requests.post(base_url+'/api/chat',json=payload,timeout=180)
     response.raise_for_status()
     answer=response.json().get('message',{}).get('content','').strip()
    if not answer: raise ValueError('Ollama devolvió una respuesta vacía.')
    st.session_state.chat_messages.append({'role':'assistant','content':answer})
    with st.chat_message('assistant'): st.markdown(answer)
   except requests.RequestException as exc:
    st.error(f'No se pudo conectar con Ollama en {base_url}. Comprueba que el servicio esté iniciado, que OLLAMA_URL sea correcto y que el modelo exista. Detalle: {exc}')
   except (ValueError,KeyError) as exc:
    st.error(f'No se pudo interpretar la respuesta de Ollama: {exc}')
 st.caption('La conversación reside en la sesión actual. Las fichas activas se incluyen en el contexto de cada petición.')

elif page=='Editor por bloques':
 st.title('Editor por bloques'); st.write('Los botones y desplegables solo controlan acciones y tipos. Edita el contenido dentro de cada bloque de texto.')
 arts=st.session_state.articles
 if not arts: st.info('Crea primero un artículo desde Generador.')
 else:
  labels={f"{a['title']} · {a.get('created','')}":a['id'] for a in arts}; current=st.session_state.get('selected_article_id',arts[0]['id']); default=next((k for k,v in labels.items() if v==current),list(labels)[0]); chosen=st.selectbox('Artículo',list(labels),index=list(labels).index(default)); a=article(labels[chosen])
  if a:
   c1,c2,c3=st.columns([4,2,3]); a['title']=c1.text_input('Título',a.get('title',''),key='edit_title_'+a['id']); a['keyword']=c2.text_input('Palabra clave',a.get('keyword',''),key='edit_kw_'+a['id']); a['meta']=c3.text_input('Meta descripción',a.get('meta',''),key='edit_meta_'+a['id'])
   st.markdown('### Contenido editable')
   types=['intro','heading','paragraph','list','faq','conclusion']; names={'intro':'Introducción','heading':'Encabezado H2','paragraph':'Párrafo','list':'Lista (un elemento por línea)','faq':'Pregunta frecuente','conclusion':'Conclusión'}
   for i,b in enumerate(a.get('blocks',[])):
    with st.container(border=True):
     x,y,z=st.columns([2,6,1]); b['type']=x.selectbox('Tipo de bloque',types,index=types.index(b.get('type','paragraph')) if b.get('type','paragraph') in types else 2,format_func=lambda t:names[t],key=f"type_{a['id']}_{i}"); b['text']=y.text_area('Texto del bloque',b.get('text',''),height=100,key=f"text_{a['id']}_{i}")
     if z.button('↑',key=f"up_{a['id']}_{i}",disabled=i==0): a['blocks'][i-1],a['blocks'][i]=a['blocks'][i],a['blocks'][i-1]; save('articles',arts); st.rerun()
     if z.button('↓',key=f"down_{a['id']}_{i}",disabled=i==len(a['blocks'])-1): a['blocks'][i+1],a['blocks'][i]=a['blocks'][i],a['blocks'][i+1]; save('articles',arts); st.rerun()
     if z.button('✕',key=f"del_{a['id']}_{i}"): a['blocks'].pop(i); save('articles',arts); st.rerun()
   x,y=st.columns([3,2]); addtype=x.selectbox('Añadir bloque',types,format_func=lambda t:names[t],key='add_block_type')
   if y.button('＋ Añadir bloque'): a['blocks'].append({'type':addtype,'text':''}); save('articles',arts); st.rerun()
   x,y=st.columns(2)
   if x.button('Guardar cambios',type='primary',use_container_width=True): a['updated']=now(); save('articles',arts); st.success('Cambios guardados localmente.')
   y.download_button('Exportar Markdown',markdown(a),file_name=slug(a['title'])+'.md',mime='text/markdown',use_container_width=True)
   st.markdown('---'); st.markdown('### Previsualización'); st.markdown(f"<div style='border:1px solid #202c3a;border-radius:12px;padding:18px'><span class='qs-kicker'>{a.get('category','General')} · VISTA PREVIA</span><h1>{a['title']}</h1><p>Palabra clave: {a.get('keyword','')}</p></div>",unsafe_allow_html=True)
   for b in a['blocks']:
    text=b.get('text','').strip(); typ=b.get('type')
    if not text: continue
    if typ=='heading': st.subheader(text)
    elif typ=='list':
     for line in text.splitlines():
      if line.strip(): st.markdown('- '+line.lstrip('-• '))
    elif typ=='faq':
     lines=text.splitlines()
     with st.expander(lines[0] if lines else 'Pregunta frecuente'): st.write('\n'.join(lines[1:]) if len(lines)>1 else '')
    elif typ=='conclusion': st.markdown('### Conclusión'); st.write(text)
    else: st.write(text)
   st.warning('Vista previa local: no se envía a WordPress.')

elif page=='SEO':
 render_seo_section(engine, render_legacy_interlinking)

elif page=='Generación en masa':
 st.title('Generación en masa'); st.write('Crea borradores con plantilla y prompt comunes, personalizando variables por cada tema.')
 with st.container(border=True):
  tm={f"{t['name']} · {t['category']}":t['id'] for t in st.session_state.templates}; tl=st.selectbox('Seleccionar plantilla para el lote',list(tm),key='bulk_tpl'); prompt=st.text_area('Prompt común del lote',placeholder='Audiencia, requisitos, límites y valor original que debe aportar cada pieza…',height=100)
  st.caption('Un tema por línea o CSV simple separado por |: tema | palabra clave | público | enfoque único.')
  rawdefault='Guía para elegir un hosting | hosting web | pequeñas empresas | criterios de rendimiento y soporte\nCómo mejorar el SEO técnico | SEO técnico | responsables web | rastreo e indexación\nPlugins útiles para WordPress | plugins WordPress | autónomos | mantenimiento y seguridad'
  variables=st.text_area('Variables en masa',rawdefault,height=150); upload=st.file_uploader('O subir TXT/CSV de variables',type=['txt','csv'],key='bulkfile'); limit=st.slider('Máximo de borradores',1,30,5)
  if st.button('⚡ Preparar lote de borradores',type='primary',use_container_width=True):
   raw=upload.getvalue().decode('utf-8-sig',errors='replace') if upload else variables; rows=[]
   for line in raw.splitlines():
    if not line.strip() or line.strip().startswith('#') or line.lower().startswith('tema,'): continue
    p=[x.strip() for x in (line.split('|') if '|' in line else line.split(','))]
    if p[0]: rows.append({'topic':p[0],'keyword':p[1] if len(p)>1 else p[0],'audience':p[2] if len(p)>2 else 'lectores interesados','angle':p[3] if len(p)>3 else 'enfoque práctico'})
   rows=rows[:limit]
   if not rows: st.error('Añade al menos un tema.')
   else:
    tpl=template(tm[tl]); created=[]
    for i,r in enumerate(rows):
     specific=(prompt+'\nPúblico: '+r['audience']+'.\nEnfoque único: '+r['angle']+'. Evita repetir una estructura genérica.').strip(); a=make_demo(r['topic'],tpl,specific,r['keyword'],'Profesional',i); a['bulk_variables']=r; created.append(a)
    st.session_state.articles=created+st.session_state.articles; job={'id':uid('batch',str(len(rows))),'created':now(),'template':tpl['name'],'prompt':prompt,'count':len(rows),'variables':rows,'article_ids':[a['id'] for a in created]}; st.session_state.bulk_jobs.insert(0,job); save('articles',st.session_state.articles); save('bulk_jobs',st.session_state.bulk_jobs); st.success(f'Lote creado: {len(rows)} borradores locales.')
 if st.session_state.bulk_jobs:
  st.markdown('### Lotes recientes')
  for j in st.session_state.bulk_jobs[:10]:
   with st.container(border=True): st.markdown(f"**{j['template']}** · {j['created']} · {j['count']} artículos"); st.caption(j.get('prompt') or 'Sin prompt adicional'); st.write(', '.join(r['topic'] for r in j['variables']))

elif page=='Plantillas':
 st.title('Plantillas editoriales'); st.write('Las plantillas definen estructuras y enfoques diferentes, no solo títulos.')
 left,right=st.columns([2,3])
 with left:
  st.markdown('### Plantillas guardadas')
  for t in st.session_state.templates:
   with st.container(border=True):
    st.markdown('**'+t['name']+'**'); st.caption(f"{t['category']} · estructura: {t['layout']}"); st.write(t.get('description',''))
    if st.button('Editar',key='edit_'+t['id']): st.session_state.edit_tpl=t['id']; st.rerun()
  if st.button('＋ Crear plantilla nueva',type='primary'):
   t={'id':uid('tpl'),'name':'Nueva plantilla','category':'General','description':'Descripción de la plantilla','layout':'guide','prompt':'Define intención, audiencia y valor diferencial.','blocks':[['intro','Introducción'],['heading','Sección principal'],['paragraph','Desarrollo'],['conclusion','Conclusión']]}; st.session_state.templates.append(t); save('templates',st.session_state.templates); st.session_state.edit_tpl=t['id']; st.rerun()
 with right:
  selected=st.session_state.get('edit_tpl',st.session_state.templates[0]['id']); t=next((x for x in st.session_state.templates if x['id']==selected),st.session_state.templates[0]); st.markdown('### Editar plantilla')
  t['name']=st.text_input('Nombre',t['name'],key='tn_'+t['id']); t['category']=st.text_input('Categoría',t.get('category','General'),key='tc_'+t['id']); t['description']=st.text_input('Descripción',t.get('description',''),key='td_'+t['id']); layouts=['guide','comparison','faq','case']; t['layout']=st.selectbox('Tipo de estructura',layouts,index=layouts.index(t.get('layout','guide')) if t.get('layout','guide') in layouts else 0,key='tl_'+t['id']); t['prompt']=st.text_area('Instrucciones base',t.get('prompt',''),height=100,key='tp_'+t['id']); old='\n'.join(f'{b[0]} | {b[1]}' if isinstance(b,(list,tuple)) else f"{b.get('type','paragraph')} | {b.get('text','')}" for b in t.get('blocks',[])); blocks=st.text_area('Bloques de referencia: tipo | descripción',old,height=160,key='tb_'+t['id'])
  x,y=st.columns(2)
  if x.button('Guardar plantilla',type='primary',use_container_width=True):
   t['blocks']=[[line.split('|',1)[0].strip(),line.split('|',1)[1].strip()] for line in blocks.splitlines() if '|' in line]; save('templates',st.session_state.templates); st.success('Plantilla guardada.')
  if y.button('Eliminar plantilla',disabled=len(st.session_state.templates)<=1,use_container_width=True): st.session_state.templates=[z for z in st.session_state.templates if z['id']!=t['id']]; save('templates',st.session_state.templates); st.session_state.pop('edit_tpl',None); st.rerun()

elif page=='Fichas de contexto':
 st.title('Fichas de contexto'); st.write('Crea, edita y activa fichas. También puedes importar varias desde archivos TXT o MD.')
 with st.expander('＋ Crear ficha manual'):
  name=st.text_input('Nombre de ficha',key='newcardname'); cat=st.selectbox('Categoría',['General','Datos fijos','Estilo','SEO','Reglas','Temas','Público objetivo','Importada'],key='newcardcat'); content=st.text_area('Contenido',height=110,key='newcardcontent')
  if st.button('Crear ficha',type='primary'):
   if not name.strip() or not content.strip(): st.error('Nombre y contenido son obligatorios.')
   else: st.session_state.cards.append({'id':uid('card',name),'name':name.strip(),'category':cat,'content':content.strip(),'active':True,'updated':now()}); save('cards',st.session_state.cards); st.success('Ficha creada.')
 files=st.file_uploader('Subir fichas desde archivos de texto',type=['txt','md'],accept_multiple_files=True,key='cardfiles')
 if files and st.button('Importar archivos',type='primary'):
  added=0
  for f in files:
   body=f.getvalue().decode('utf-8-sig',errors='replace').strip()
   if body: st.session_state.cards.append({'id':uid('card',f.name),'name':Path(f.name).stem.replace('_',' ').replace('-',' ').title(),'category':'Importada','content':body[:20000],'active':True,'updated':now(),'source_file':f.name}); added+=1
  save('cards',st.session_state.cards); st.success(f'Importadas {added} fichas.')
 st.markdown('### Fichas guardadas')
 for c in st.session_state.cards:
  with st.container(border=True):
   x,y,z=st.columns([4,1,1]); c['name']=x.text_input('Nombre',c['name'],key='cn_'+c['id']); cats=['General','Datos fijos','Estilo','SEO','Reglas','Temas','Público objetivo','Importada']; c['category']=x.selectbox('Categoría',cats,index=cats.index(c['category']) if c.get('category') in cats else 0,key='cc_'+c['id']); c['content']=x.text_area('Contenido de la ficha',c['content'],height=120,key='ct_'+c['id']); c['active']=y.toggle('Activa',value=c.get('active',True),key='ca_'+c['id'])
   if z.button('Guardar',key='cs_'+c['id']): c['updated']=now(); save('cards',st.session_state.cards); st.success('Ficha guardada.')
   if z.button('Eliminar',key='cd_'+c['id']): st.session_state.cards=[v for v in st.session_state.cards if v['id']!=c['id']]; save('cards',st.session_state.cards); st.rerun()
   st.caption(f"Actualizada: {c.get('updated','—')} · {c.get('source_file','Edición manual')}")

elif page=='Historial':
 st.title('Historial de artículos'); search=st.text_input('Buscar por título o palabra clave'); status=st.selectbox('Estado',['Todos','Borrador local','En revisión','Listo para enviar','Enviado a WordPress (simulado)']); arts=[a for a in st.session_state.articles if (not search or search.lower() in (a.get('title','')+' '+a.get('keyword','')).lower()) and (status=='Todos' or a.get('status')==status)]; st.caption(f'{len(arts)} artículos')
 for a in arts:
  with st.container(border=True):
   x,y,z=st.columns([5,2,1]); x.markdown('**'+a['title']+'**'); x.caption(f"{a.get('keyword','')} · {a.get('created','')} · {a.get('status','')}")
   if y.button('Seleccionar',key='hist_'+a['id']): st.session_state.selected_article_id=a['id']; st.info('Seleccionado. Abre Editor por bloques en el menú.')
   if z.button('Eliminar',key='hdel_'+a['id']): st.session_state.articles=[q for q in st.session_state.articles if q['id']!=a['id']]; save('articles',st.session_state.articles); st.rerun()
   with st.expander('Vista previa'): st.markdown(markdown(a))

elif page=='Ajustes':
 st.title('Ajustes'); st.write('Configuración local. Integraciones desactivadas deliberadamente.')
 for name,desc in [('Ollama',f"Chat local · modelo: {os.getenv('OLLAMA_MODEL','no configurado')}"),('WordPress REST API','Prueba de lectura disponible; envío de artículos pendiente'),('Rank Math','No conectado en esta fase'),('Pexels','No conectado en esta fase')]:
  with st.container(border=True): x,y=st.columns([2,4]); x.markdown('**'+name+'**'); y.markdown(f"<span class='qs-pill'>DESACTIVADO</span>　{desc}",unsafe_allow_html=True)
 backup={k:st.session_state[k] for k in ['articles','cards','templates','pages','bulk_jobs']}; st.download_button('Exportar copia de seguridad JSON',json.dumps(backup,ensure_ascii=False,indent=2),file_name='quicksite_backup.json',mime='application/json')
 if st.button('Restaurar datos de ejemplo'):
  for k,v in [('articles',[DEFAULT_ART]),('cards',DEFAULT_CARDS),('templates',DEFAULT_TEMPLATES),('pages',DEFAULT_PAGES),('bulk_jobs',[])]: st.session_state[k]=v; save(k,v)
  st.success('Datos de ejemplo restaurados.'); st.rerun()

st.markdown('---'); st.caption('QuickSite · Studio integrado · Revisión humana obligatoria · No publica automáticamente. Las conexiones externas pendientes se identifican en SEO > Conexiones.')
