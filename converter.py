"""Ekstrak PDF dari exe buatan Vaysoft "PDF to EXE" (exe tidak dijalankan)."""
import struct
from collections import Counter


class ConvertError(Exception):
    pass


def _overlay_start(d: bytes) -> int:
    if d[:2] != b"MZ":
        raise ConvertError("File ini bukan file .exe Windows.")
    try:
        pe = struct.unpack_from("<I", d, 0x3C)[0]
        n = struct.unpack_from("<H", d, pe + 6)[0]
        opt = struct.unpack_from("<H", d, pe + 20)[0]
        s = pe + 24 + opt
        end = 0
        for i in range(n):
            _, _, rs, rp = struct.unpack_from("<IIII", d, s + i * 40 + 8)
            end = max(end, rp + rs)
    except struct.error:
        raise ConvertError("Struktur exe tidak valid.")
    return end


def _printable(c: int) -> bool:
    return 32 <= c < 127 or c in (9, 10, 13)


def _decrypt(ov: bytes, key: list) -> bytes:
    p = len(key)
    out = bytearray(len(ov))
    for r in range(p):
        tbl = bytes(c ^ key[r] for c in range(256))
        out[r::p] = ov[r::p].translate(tbl)
    return bytes(out)


def _find_key(ov: bytes):
    head = b"%PDF-1."
    known = [ov[i] ^ head[i] for i in range(len(head))]
    if any(k > 15 for k in known):
        raise ConvertError("Bukan exe buatan Vaysoft PDF to EXE (format tidak dikenali).")
    pr = [_printable(c) for c in range(256)]
    results = []
    for p in range(1, 41):
        key = []
        for r in range(p):
            if r < len(known):
                key.append(known[r])
                continue
            h = Counter(ov[r::p])
            sc = [sum(n for c, n in h.items() if pr[c ^ k]) for k in range(16)]
            key.append(max(range(16), key=lambda k: sc[k]))
        dec = _decrypt(ov, key)
        results.append((dec.count(b"endobj") + dec.count(b"%%EOF"), p, key))
    top = max(r[0] for r in results)
    _, p, key = min((r for r in results if r[0] >= top * 0.9), key=lambda r: r[1])

    def score(k):
        d = _decrypt(ov, k)
        return (d.count(b"endobj") * 3 + d.count(b" obj") + d.count(b"%%EOF") * 5
                + d.count(b"/Type") + d.count(b"xref"))

    cur = score(key)
    for _ in range(3):
        changed = False
        for r in range(len(known), p):
            for k in range(16):
                if k == key[r]:
                    continue
                t = key[:]
                t[r] = k
                v = score(t)
                if v > cur:
                    key, cur, changed = t, v, True
        if not changed:
            break
    return key


def exe_to_pdf(data: bytes) -> bytes:
    ov = data[_overlay_start(data):]
    if len(ov) < 100:
        raise ConvertError("Tidak ada data PDF di dalam exe ini.")
    key = _find_key(ov)
    dec = _decrypt(ov, key)
    if not dec.startswith(b"%PDF-"):
        raise ConvertError("Gagal mendekripsi PDF.")
    end = dec.rfind(b"%%EOF")
    if end < 0:
        raise ConvertError("PDF hasil dekripsi tidak lengkap (kunci tidak ketemu).")
    return dec[: end + 5] + b"\n"
