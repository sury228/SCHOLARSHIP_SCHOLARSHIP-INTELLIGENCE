import streamlit as st

def get_confidence_badge_html(score: float, status: str) -> str:
    """Returns HTML for a sleek luxury gold/dark badge for status and confidence score."""
    if status == "VERIFIED" or score >= 95.0:
        badge_bg = "linear-gradient(135deg, #BF953F 0%, #FCF6BA 50%, #B38728 100%)"
        text_color = "#0B0C10"
        border = "1px solid #FFD700"
    elif status == "EXPIRING_SOON":
        badge_bg = "linear-gradient(135deg, #D4AF37 0%, #AA771C 100%)"
        text_color = "#FFFFFF"
        border = "1px solid #D4AF37"
    elif status in ["EXPIRED", "NO_LONGER_VERIFIABLE"]:
        badge_bg = "rgba(220, 38, 38, 0.2)"
        text_color = "#F87171"
        border = "1px solid rgba(220, 38, 38, 0.4)"
    else:
        badge_bg = "rgba(212, 175, 55, 0.15)"
        text_color = "#F3E5AB"
        border = "1px solid rgba(212, 175, 55, 0.3)"

    return f"""<span style="background: {badge_bg}; color: {text_color}; border: {border}; padding: 3px 12px; border-radius: 20px; font-weight: 700; font-size: 12px; letter-spacing: 0.5px; box-shadow: 0 2px 8px rgba(0,0,0,0.5); display: inline-block;">{status} — {score:.1f}%</span>"""

def render_confidence_badge(score: float, status: str):
    """Renders a sleek luxury gold/dark badge for status and confidence score."""
    badge_html = get_confidence_badge_html(score, status)
    st.markdown(
        f"""
        <div style="display: inline-block; margin-top: 4px; margin-bottom: 8px;">
            {badge_html}
        </div>
        """,
        unsafe_allow_html=True
    )

def render_evidence_card(evidence_list: list):
    """Renders evidence traceability quotes in a black & gold luxury card theme."""
    st.markdown("<h4 style='color: #D4AF37; font-family: \"Playfair Display\", serif; margin-top: 15px;'>Verification Evidence Traceability</h4>", unsafe_allow_html=True)
    if not evidence_list:
        st.info("No evidence records available for inspection.")
        return

    for item in evidence_list:
        is_valid = bool(item.get("is_verified_substring"))
        status_tag = "<span style='color: #34D399; font-size: 11px; font-weight: 700; background: rgba(52,211,153,0.1); border: 1px solid #34D399; padding: 2px 6px; border-radius: 4px; margin-right: 6px;'>EXACT MATCH</span>" if is_valid else "<span style='color: #F87171; font-size: 11px; font-weight: 700; background: rgba(248,113,113,0.1); border: 1px solid #F87171; padding: 2px 6px; border-radius: 4px; margin-right: 6px;'>UNVERIFIED</span>"
        border_color = "#D4AF37" if is_valid else "#EF4444"
        bg_color = "rgba(20, 20, 24, 0.8)"
        quote_color = "#F3E5AB" if is_valid else "#F87171"

        st.markdown(
            f"""
            <div style="border-left: 3px solid {border_color}; background: {bg_color}; border-top: 1px solid rgba(212,175,55,0.15); border-right: 1px solid rgba(212,175,55,0.15); border-bottom: 1px solid rgba(212,175,55,0.15); padding: 14px 18px; margin-bottom: 12px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.4);">
                <div style="color: #D4AF37; font-weight: 600; font-size: 14px;">{status_tag} Field: <code style="color: #FCF6BA; background: rgba(212,175,55,0.1); padding: 2px 6px; border-radius: 4px;">{item.get('field_name')}</code></div>
                <div style="color: #E5E7EB; margin-top: 4px; font-size: 14px;">Extracted Value: <strong style="color: #FFFFFF;">{item.get('extracted_value')}</strong></div>
                <div style="margin-top: 6px; font-size: 13px; color: {quote_color}; font-style: italic;">
                    Source Quote: "{item.get('source_quote')}"
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

def render_change_timeline(history_records: list):
    """Renders historical change audit timeline with gold accents."""
    st.markdown("<h4 style='color: #D4AF37; font-family: \"Playfair Display\", serif; margin-top: 15px;'>Historical Audit Trail</h4>", unsafe_allow_html=True)
    if not history_records:
        st.info("No historical alterations logged for this scholarship.")
        return

    for rec in history_records:
        st.markdown(
            f"""
            <div style="border-left: 3px solid #D4AF37; background: rgba(18, 18, 22, 0.7); padding: 12px 16px; margin-bottom: 12px; border-radius: 6px; border-top: 1px solid rgba(212,175,55,0.1);">
                <span style="font-size: 12px; color: #AA771C; font-weight: 600;">{rec.get('change_detected_date')}</span><br/>
                <strong style="color: #F3E5AB; font-size: 14px;">Field Updated: <code style="color: #FFD700; background: rgba(212,175,55,0.1); padding: 1px 5px;">{rec.get('field_name')}</code></strong><br/>
                <div style="margin-top: 4px; font-size: 13.5px;">
                    <span style="color: #F87171; text-decoration: line-through;">Old: {rec.get('old_value')}</span>
                    <span style="color: #D4AF37; margin: 0 6px;">➔</span>
                    <span style="color: #34D399; font-weight: 600;">New: {rec.get('new_value')}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
