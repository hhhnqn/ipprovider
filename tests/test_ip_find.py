"""Pruebas de detección de IPs en texto."""

from ipprovider.ip_find import find_ips_in_text


def test_ipv4_basic():
    t = "Servidor 203.0.113.10 y copia 192.168.1.1"
    ips = find_ips_in_text(t)
    assert ips == ["203.0.113.10", "192.168.1.1"]


def test_ipv4_glued_to_letters():
    """Algunos PDF unen la IP al texto previo (p. ej. Ip181.27.224.47)."""
    t = "on Ip181.27.224.47\nAccount End"
    assert find_ips_in_text(t) == ["181.27.224.47"]


def test_ipv4_dedupe_order():
    t = "A 10.0.0.1 B 10.0.0.1 C 198.51.100.2"
    assert find_ips_in_text(t) == ["10.0.0.1", "198.51.100.2"]


def test_ipv6_compressed():
    t = "IPv6: 2001:db8::1 y ::1"
    ips = find_ips_in_text(t)
    assert "2001:db8::1" in ips
    assert "::1" in ips


def test_ipv6_ipv4_mapped():
    t = "Mapeada ::ffff:192.0.2.1"
    ips = find_ips_in_text(t)
    assert any("192.0.2.1" in ip or "ffff" in ip for ip in ips)


def test_false_positive_not_octets():
    t = "999.999.999.999 no es válida"
    ips = find_ips_in_text(t)
    assert "999.999.999.999" not in ips


def test_ipv4_before_ipv6_order():
    t = "primero 198.51.100.5 luego 2001:db8::2"
    assert find_ips_in_text(t) == ["198.51.100.5", "2001:db8::2"]
