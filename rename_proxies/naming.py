import base64
import io
from collections import defaultdict
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont


@lru_cache(maxsize=256)
def generate_number_image_base64(number: int, image_size=(100, 100), font_size=50):
    img = Image.new("RGB", image_size, "white")
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default(size=font_size)
    text = str(number)
    text_size = draw.textbbox((0, 0), text, font=font)
    text_width = text_size[2] - text_size[0]
    text_height = text_size[3] - text_size[1]
    position = ((image_size[0] - text_width) // 2, (image_size[1] - text_height) // 3)
    draw.text(position, text, fill="black", font=font)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode()


def apply_nation_names(proxies, nation_cache):
    """按 GeoIP 重命名节点，并生成扩展脚本分组所需的 entries。"""
    nation_counter = defaultdict(int)
    new_proxies = []
    entries = []
    for proxy in proxies:
        orig = (proxy.get("name") or "").strip()
        p = dict(proxy)
        server = p.get("server")
        if server:
            nation, _, _ = nation_cache.get(server, ("未知", "cn", 0))
            nation_counter[nation] += 1
            p["name"] = f"{nation} {nation_counter[nation]}"
        new_proxies.append(p)
        entries.append({"name": (p.get("name") or "").strip(), "orig": orig})
    return new_proxies, entries, nation_counter
