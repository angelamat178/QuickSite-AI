"""Funciones de análisis puras, fáciles de probar y sin llamadas de red."""
from __future__ import annotations

def ctr(clicks: float, impressions: float) -> float | None:
    return clicks / impressions if impressions > 0 else None

def conversion_rate(conversions: float, sessions: float, measurement_status="measured") -> float | None:
    if measurement_status != "measured" or sessions <= 0: return None
    return conversions / sessions

def classify_conversion_state(conversions, measurement_status):
    if measurement_status in {"not_instrumented","unknown","unavailable"}: return "not_measured"
    if conversions == 0: return "zero_measured"
    if conversions is None: return "not_measured"
    return "conversions_observed"

def page_opportunity(clicks, impressions, position, min_impressions=100, min_position=8, max_position=20):
    if impressions < min_impressions: return None
    if not min_position <= position <= max_position: return None
    return {"rule":"position_opportunity","evidence":{"clicks":clicks,"impressions":impressions,"position":position},
            "explanation":f"La página tiene {impressions} impresiones y posición media {position:.1f}; revisar intención y enlaces internos.",
            "confidence":"medium","impact":"potential"}
