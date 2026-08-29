from urllib.parse import urlparse

def classify_source_domain(url: str) -> str:
    """
    Classifies a URL into a source category based on domain authority rules:
    - Government (.gov.in, .nic.in, national portals)
    - University / Education (.ac.in, .edu.in, .edu)
    - Corporate CSR (company portals, foundations)
    - Trust / NGO (.org, trusts)
    - Aggregator / Blog (commercial aggregators, news)
    """
    if not url:
        return "Unknown"
        
    parsed = urlparse(url.lower())
    domain = parsed.netloc or parsed.path

    if any(domain.endswith(ext) for ext in [".gov.in", ".nic.in", "gov.in", "scholarships.gov.in"]):
        return "Government"
    
    if any(domain.endswith(ext) for ext in [".ac.in", ".edu.in", ".edu"]):
        return "University"

    if any(keyword in domain for keyword in ["tata", "reliance", "hDFC", "infosis", "wipro", "aditya", "csr"]):
        return "Corporate CSR"

    if any(keyword in domain for keyword in ["trust", "foundation", "ngo", ".org"]):
        return "Trust / NGO"

    if any(agg in domain for agg in ["buddy4study", "sarkari", "shiksha", "jagran", "indiatoday"]):
        return "Aggregator"

    return "Aggregator / Commercial"

def is_official_domain(url: str) -> bool:
    """Returns True if the URL domain is an official provider (not an aggregator or blog)."""
    category = classify_source_domain(url)
    return category in ["Government", "University", "Corporate CSR", "Trust / NGO"]
