"""Presentation helpers for Symptom Buddy.

These helpers return HTML strings for use with Streamlit markdown.
They contain no Streamlit imports and no medical logic, so they can be
tested and reused without Streamlit installed. The Streamlit app is
responsible for rendering the returned HTML.
"""

import html


def _escape(value):
    return html.escape(str(value), quote=True)


def card_html(title, body, icon="", variant="default"):
    """Return a card div. Variant: default, mint, warning, urgent."""
    icon_part = ""
    if icon:
        icon_part = '<span class="sb-card-icon">{}</span> '.format(_escape(icon))
    return (
        '<div class="sb-card sb-card-{}"><h3>{}{}</h3><div>{}</div></div>'.format(
            _escape(variant), icon_part, _escape(title), body
        )
    )


def badge_html(text, variant="default"):
    """Return a small pill badge span."""
    return '<span class="sb-badge sb-badge-{}">{}</span>'.format(
        _escape(variant), _escape(text)
    )


def section_header_html(step, title, subtitle=""):
    """Return a step header, e.g. step 1, title, optional subtitle."""
    subtitle_part = ""
    if subtitle:
        subtitle_part = '<p class="sb-subtitle">{}</p>'.format(_escape(subtitle))
    return (
        '<div class="sb-step"><span class="sb-step-number">{}</span>'
        "<h2>{}</h2>{}</div>".format(_escape(step), _escape(title), subtitle_part)
    )


def pharmacy_card_html(pharmacy):
    """Return a card for one pharmacy, with honest stock labelling."""
    name = _escape(pharmacy.get("name", "Pharmacy"))
    address = _escape(pharmacy.get("address", ""))
    hours = _escape(pharmacy.get("hours", "Hours not listed"))
    phone = _escape(pharmacy.get("phone", ""))
    distance = pharmacy.get("distance_km")
    distance_part = ""
    if distance is not None:
        distance_part = badge_html("{} km away".format(distance), "mint")
    stock = _escape(pharmacy.get("stock_status", "Stock not verified - call to confirm"))
    city = _escape(pharmacy.get("city", ""))
    postcode = _escape(pharmacy.get("postcode", ""))
    return (
        '<div class="sb-card"><h3>📍 {}</h3>'
        "<p>{} {} {}, {}</p><p>Hours: {}</p><p>Phone: {}</p>"
        '<p><span class="sb-badge sb-badge-warning">{}</span></p></div>'.format(
            name, distance_part, address, city, postcode, hours, phone, stock
        )
    )


def urgent_care_card_html(entry):
    """Return a card for one urgent-care or clinic entry."""
    name = _escape(entry.get("name", "Urgent care"))
    address = _escape(entry.get("address", ""))
    hours = _escape(entry.get("hours", "Hours not listed"))
    phone = _escape(entry.get("phone", ""))
    distance = entry.get("distance_km")
    distance_part = ""
    if distance is not None:
        distance_part = badge_html("{} km away".format(distance), "mint")
    return (
        '<div class="sb-card"><h3>🏥 {}</h3>'
        "<p>{} {}</p><p>Hours: {}</p><p>Phone: {}</p></div>".format(
            name, distance_part, address, hours, phone
        )
    )
