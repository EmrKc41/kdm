"""xlsx paketini ZIP arşivi olarak açan/yazan katman.

openpyxl bir dosyayı açıp kaydettiğinde çizim nesnelerini (text box), yazıcı
ayarlarını ve customXml parçalarını sessizce siler. Bu sınıf paketi ham bayt
seviyesinde tutar: dokunulmayan her parça baytı baytına korunur.
"""

from __future__ import annotations

import posixpath
import re
import shutil
import zipfile
from collections import OrderedDict
from pathlib import Path

from ..errors import SablonHatasi


class XlsxPackage:
    """Bir .xlsx dosyasının tüm parçalarını bellekte tutan düzenlenebilir paket."""

    def __init__(self, parts: "OrderedDict[str, bytes]"):
        self._parts = parts

    # --- Yükleme / kaydetme --------------------------------------------------

    @classmethod
    def open(cls, path: str | Path) -> "XlsxPackage":
        path = Path(path)
        if not path.is_file():
            raise SablonHatasi(f"Şablon dosyası bulunamadı: {path.name}")
        parts: OrderedDict[str, bytes] = OrderedDict()
        try:
            with zipfile.ZipFile(path) as zf:
                for info in zf.infolist():
                    parts[info.filename] = zf.read(info.filename)
        except zipfile.BadZipFile as exc:
            raise SablonHatasi(
                f"Şablon dosyası okunamadı, bozuk olabilir: {path.name}"
            ) from exc
        return cls(parts)

    def save(self, path: str | Path) -> None:
        """Paketi diske yazar. Parça sırası orijinaldeki gibi korunur."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zf:
            for name, data in self._parts.items():
                zf.writestr(name, data)
        shutil.move(str(tmp), str(path))

    # --- Parça erişimi -------------------------------------------------------

    def names(self) -> list[str]:
        return list(self._parts)

    def has(self, name: str) -> bool:
        return name in self._parts

    def read_bytes(self, name: str) -> bytes:
        if name not in self._parts:
            raise SablonHatasi(f"Şablonda beklenen parça yok: {name}")
        return self._parts[name]

    def read_text(self, name: str) -> str:
        return self.read_bytes(name).decode("utf-8")

    def write_bytes(self, name: str, data: bytes) -> None:
        self._parts[name] = data

    def write_text(self, name: str, text: str) -> None:
        self._parts[name] = text.encode("utf-8")

    def remove(self, name: str) -> None:
        self._parts.pop(name, None)

    # --- Yardımcılar ---------------------------------------------------------

    def next_media_name(self, extension: str) -> str:
        """Kullanılmayan bir xl/media/imageN.<ext> adı üretir."""
        used = {
            int(m.group(1))
            for n in self._parts
            if (m := re.fullmatch(r"xl/media/image(\d+)\.\w+", n))
        }
        n = 1
        while n in used:
            n += 1
        return f"xl/media/image{n}.{extension.lstrip('.').lower()}"

    def ensure_content_type_default(self, extension: str, content_type: str) -> None:
        """[Content_Types].xml içinde bir uzantı için Default kaydı olduğunu garanti eder."""
        ext = extension.lstrip(".").lower()
        name = "[Content_Types].xml"
        xml = self.read_text(name)
        if re.search(rf'<Default\s+Extension="{ext}"', xml, re.I):
            return
        entry = f'<Default Extension="{ext}" ContentType="{content_type}"/>'
        xml = xml.replace("<Types ", "<Types ", 1)
        idx = xml.find(">", xml.find("<Types ")) + 1
        self.write_text(name, xml[:idx] + entry + xml[idx:])

    def add_relationship(self, rels_part: str, target: str, rel_type: str) -> str:
        """İlişki dosyasına yeni kayıt ekler ve üretilen rId değerini döndürür.

        `target`, ilişki dosyasının bulunduğu klasöre göre göreli yazılır.
        """
        xml = self.read_text(rels_part)
        used = {int(m) for m in re.findall(r'Id="rId(\d+)"', xml)}
        n = 1
        while n in used:
            n += 1
        rid = f"rId{n}"

        base = posixpath.dirname(posixpath.dirname(rels_part))  # .../_rels/x -> ...
        rel_target = posixpath.relpath(target, base)

        entry = f'<Relationship Id="{rid}" Type="{rel_type}" Target="{rel_target}"/>'
        xml = xml.replace("</Relationships>", entry + "</Relationships>")
        self.write_text(rels_part, xml)
        return rid
