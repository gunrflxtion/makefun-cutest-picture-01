#!/usr/bin/env python3
"""
Make.fun Cutest Picture Entry - Baby Otter Hugging Pink Heart
Pure Python 3.13 PNG renderer with stdlib only (os, struct, zlib, math, sys).
Deterministic: fixed layout, no random, no time, no network.
"""

import os
import struct
import zlib
import math
import sys

# Canvas size - read from env or use default
CANVAS_SIZE = int(os.environ.get('MAKEFUN_PREVIEW_PX', 1024))

# Colors
COLORS = {
    'BG_TOP': (255, 233, 214),
    'BG_MIDDLE': (255, 205, 233),
    'BG_BOTTOM': (255, 243, 226),
    'TAIL': (122, 74, 46),
    'BODY_TOP': (169, 116, 79),
    'BODY_BOTTOM': (138, 90, 59),
    'BELLY': (246, 221, 190),
    'HEAD_TOP': (176, 123, 82),
    'HEAD_BOTTOM': (138, 90, 59),
    'EAR_OUTER': (122, 74, 46),
    'EAR_INNER': (232, 160, 168),
    'EYE': (42, 26, 18),
    'EYE_HIGHLIGHT_1': (255, 255, 255),
    'EYE_HIGHLIGHT_2': (255, 255, 255),
    'EYEBROW': (107, 66, 38),
    'NOSE': (232, 122, 144),
    'MOUTH_OUTER': (122, 46, 53),
    'TONGUE': (242, 140, 160),
    'BLUSH': (255, 120, 150),
    'PAW': (169, 116, 79),
    'PAW_PAD': (200, 155, 114),
    'HEART_TOP': (255, 143, 176),
    'HEART_BOTTOM': (255, 92, 138),
}


def clamp255(v):
    """Clamp a channel value to a valid 0-255 int."""
    v = int(v)
    if v < 0:
        return 0
    if v > 255:
        return 255
    return v


def smoothstep(t):
    """Smoothstep, clamped to 0..1."""
    if t <= 0.0:
        return 0.0
    if t >= 1.0:
        return 1.0
    return t * t * (3.0 - 2.0 * t)


def blend(a, b, alpha):
    """Linear scalar blend: alpha=1 gives a, alpha=0 gives b."""
    return a * alpha + b * (1.0 - alpha)


def blend_color(a, b, alpha):
    """Blend two RGB tuples per channel, return an int RGB tuple.

    alpha is the weight of the NEW color b: 0 returns a unchanged,
    1 returns b.
    """
    if alpha <= 0.0:
        return a
    if alpha >= 1.0:
        return (clamp255(b[0]), clamp255(b[1]), clamp255(b[2]))
    inv = 1.0 - alpha
    return (
        clamp255(b[0] * alpha + a[0] * inv),
        clamp255(b[1] * alpha + a[1] * inv),
        clamp255(b[2] * alpha + a[2] * inv),
    )


def edge_alpha(sd, feather):
    """Coverage 0..1 from a signed distance (negative inside, 0 at edge).

    sd is in PIXELS, and feather is the soft-edge width in pixels.
    feather<=0 means a hard edge.
    """
    if feather <= 0:
        return 1.0 if sd <= 0.0 else 0.0
    t = (feather - sd) / (2.0 * feather)
    if t <= 0.0:
        return 0.0
    if t >= 1.0:
        return 1.0
    return smoothstep(t)


def ellipse_sd(dx, dy, rx, ry):
    """Signed distance in pixels from the ellipse edge (negative inside).

    Returns (q, pixel_sd) where q is the normalized squared radius.
    """
    q = dx * dx / (rx * rx) + dy * dy / (ry * ry)
    if q <= 0.0:
        return q, -min(rx, ry)
    s = math.sqrt(q)
    length = math.sqrt(dx * dx + dy * dy)
    radius = length / s
    return q, (s - 1.0) * radius


def create_pixels(canvas_size):
    """Create a 2D list of RGB rows for the canvas."""
    return [[(0, 0, 0) for _ in range(canvas_size)]
            for _ in range(canvas_size)]


def fill_ellipse(pixels, x, y, rx, ry, color, feather=0, alpha=1.0):
    """Fill an ellipse with a soft edge and solid interior."""
    h = len(pixels)
    w = len(pixels[0])
    col = (color[0], color[1], color[2])
    for dy in range(-ry, ry + 1):
        py = y + dy
        if py < 0 or py >= h:
            continue
        for dx in range(-rx, rx + 1):
            px = x + dx
            if px < 0 or px >= w:
                continue
            q, sd = ellipse_sd(dx, dy, rx, ry)
            if q > 4.0:
                continue
            a = edge_alpha(sd, feather) * alpha
            if a <= 0.0:
                continue
            pixels[py][px] = blend_color(pixels[py][px], col, a)


def fill_ellipse_gradient(pixels, x, y, rx, ry, color_top, color_bottom, feather=0):
    """Fill an ellipse with a vertical gradient (top color to bottom color)."""
    h = len(pixels)
    w = len(pixels[0])
    for dy in range(-ry, ry + 1):
        py = y + dy
        if py < 0 or py >= h:
            continue
        t = (dy + ry) / (2.0 * ry)
        if t < 0.0:
            t = 0.0
        elif t > 1.0:
            t = 1.0
        # blend(a, b, alpha) weights a by alpha, so use 1-t to get
        # color_top at the top (t=0) and color_bottom at the bottom.
        col = (
            clamp255(blend(color_top[0], color_bottom[0], 1.0 - t)),
            clamp255(blend(color_top[1], color_bottom[1], 1.0 - t)),
            clamp255(blend(color_top[2], color_bottom[2], 1.0 - t)),
        )
        for dx in range(-rx, rx + 1):
            px = x + dx
            if px < 0 or px >= w:
                continue
            q, sd = ellipse_sd(dx, dy, rx, ry)
            if q > 4.0:
                continue
            a = edge_alpha(sd, feather)
            if a <= 0.0:
                continue
            pixels[py][px] = blend_color(pixels[py][px], col, a)


def fill_ellipse_radial_gradient(pixels, x, y, rx, ry, color, highlight, feather=0):
    """Fill an ellipse with a radial gradient: color at center, highlight at edge."""
    h = len(pixels)
    w = len(pixels[0])
    for dy in range(-ry, ry + 1):
        py = y + dy
        if py < 0 or py >= h:
            continue
        for dx in range(-rx, rx + 1):
            px = x + dx
            if px < 0 or px >= w:
                continue
            q, sd = ellipse_sd(dx, dy, rx, ry)
            if q > 4.0:
                continue
            a = edge_alpha(sd, feather)
            if a <= 0.0:
                continue
            d = math.sqrt(q)
            if d > 1.0:
                d = 1.0
            wgt = 1.0 - d
            col = (
                clamp255(blend(color[0], highlight[0], wgt)),
                clamp255(blend(color[1], highlight[1], wgt)),
                clamp255(blend(color[2], highlight[2], wgt)),
            )
            pixels[py][px] = blend_color(pixels[py][px], col, a)


def fill_heart(pixels, x, y, r, rotation=0, color_top=COLORS['HEART_TOP'],
              color_bottom=COLORS['HEART_BOTTOM'], feather=0):
    """Fill a heart shape (classic implicit heart, solid interior)."""
    h = len(pixels)
    w = len(pixels[0])
    rad = math.radians(rotation)
    co = math.cos(rad)
    si = math.sin(rad)
    span = int(r * 1.2) + 2
    inv_r = 1.0 / r
    for dy in range(-span, span + 1):
        py = y + dy
        if py < 0 or py >= h:
            continue
        for dx in range(-span, span + 1):
            px = x + dx
            if px < 0 or px >= w:
                continue
            # Rotate the offset into the heart's local frame.
            lx = dx * co + dy * si
            ly = -dx * si + dy * co
            u = lx * inv_r
            v = -ly * inv_r
            f = (u * u + v * v - 1.0) ** 3 - u * u * (v ** 3)
            # f <= 0 inside, f = 0 at the edge; soften over a small band.
            a = 0.5 - f / 0.24
            if a <= 0.0:
                continue
            if a > 1.0:
                a = 1.0
            a = smoothstep(a)
            t = (dy + r) / (2.0 * r)
            if t < 0.0:
                t = 0.0
            elif t > 1.0:
                t = 1.0
            # blend(a, b, alpha) weights a by alpha, so use 1-t to get
            # color_top at the top (t=0) and color_bottom at the bottom.
            col = (
                clamp255(blend(color_top[0], color_bottom[0], 1.0 - t)),
                clamp255(blend(color_top[1], color_bottom[1], 1.0 - t)),
                clamp255(blend(color_top[2], color_bottom[2], 1.0 - t)),
            )
            pixels[py][px] = blend_color(pixels[py][px], col, a)
    # Soft glossy highlight on the upper-left lobe.
    fill_ellipse(pixels, x - int(0.36 * r), y - int(0.34 * r),
                 int(0.30 * r), int(0.20 * r),
                 (255, 255, 255), feather=1, alpha=0.35)


def draw_background(pixels, canvas_size):
    """Draw a vertical gradient background: cream, pink, cream."""
    for yy in range(canvas_size):
        t = yy / canvas_size
        if t < 0.5:
            alpha = 1.0 - 2.0 * t
            top_color = COLORS['BG_TOP']
            bot_color = COLORS['BG_MIDDLE']
        else:
            alpha = 2.0 - 2.0 * t
            top_color = COLORS['BG_MIDDLE']
            bot_color = COLORS['BG_BOTTOM']
        r = clamp255(blend(top_color[0], bot_color[0], alpha))
        g = clamp255(blend(top_color[1], bot_color[1], alpha))
        b = clamp255(blend(top_color[2], bot_color[2], alpha))
        pixels[yy] = [(r, g, b)] * canvas_size


def draw_glow(pixels, center_x, center_y, radius, max_radius, color, feather):
    """Draw a soft radial glow, strongest at the inner radius, fading out."""
    h = len(pixels)
    w = len(pixels[0])
    col = (color[0], color[1], color[2])
    for dy in range(-max_radius, max_radius + 1):
        py = center_y + dy
        if py < 0 or py >= h:
            continue
        for dx in range(-max_radius, max_radius + 1):
            px = center_x + dx
            if px < 0 or px >= w:
                continue
            dist = math.sqrt(dx * dx + dy * dy)
            if dist <= radius or dist > max_radius:
                continue
            t = (dist - radius) / (max_radius - radius)
            alpha = 0.3 * (1.0 - smoothstep(t))
            if alpha <= 0.02:
                continue
            pixels[py][px] = blend_color(pixels[py][px], col, alpha)


def draw_bokeh(pixels, positions, color, max_radius, max_alpha, feather):
    """Draw soft bokeh circles, bright at the center, fading to the edge."""
    h = len(pixels)
    w = len(pixels[0])
    col = (color[0], color[1], color[2])
    for (bx, by) in positions:
        for dy in range(-max_radius, max_radius + 1):
            py = by + dy
            if py < 0 or py >= h:
                continue
            for dx in range(-max_radius, max_radius + 1):
                px = bx + dx
                if px < 0 or px >= w:
                    continue
                dist = math.sqrt(dx * dx + dy * dy)
                if dist > max_radius:
                    continue
                alpha = max_alpha * (1.0 - smoothstep(dist / max_radius))
                if alpha <= 0.02:
                    continue
                pixels[py][px] = blend_color(pixels[py][px], col, alpha)


def draw_ellipse(pixels, cx, cy, rx, ry, color, rotation=0, feather=0):
    """Draw a filled ellipse with optional rotation and a soft edge.

    Uses inverse mapping (screen pixel to local coordinates) so a
    rotated ellipse has no gaps.
    """
    h = len(pixels)
    w = len(pixels[0])
    col = (color[0], color[1], color[2])
    rad = math.radians(rotation)
    co = math.cos(rad)
    si = math.sin(rad)
    hx = int(abs(rx * co) + abs(ry * si)) + 2
    hy = int(abs(rx * si) + abs(ry * co)) + 2
    for py in range(cy - hy, cy + hy + 1):
        if py < 0 or py >= h:
            continue
        for px in range(cx - hx, cx + hx + 1):
            if px < 0 or px >= w:
                continue
            ox = px - cx
            oy = py - cy
            dx = ox * co + oy * si
            dy = -ox * si + oy * co
            q, sd = ellipse_sd(dx, dy, rx, ry)
            if q > 4.0:
                continue
            a = edge_alpha(sd, feather)
            if a <= 0.0:
                continue
            pixels[py][px] = blend_color(pixels[py][px], col, a)


def draw_ellipse_arc(pixels, cx, cy, rx, color, feather=0):
    """Draw the top arc of a circle (a soft 3px stroke)."""
    h = len(pixels)
    w = len(pixels[0])
    col = (color[0], color[1], color[2])
    for dx in range(-rx, rx + 1):
        frac = 1.0 - (dx / rx) ** 2
        if frac < 0.0:
            frac = 0.0
        dy = -int(rx * math.sqrt(frac))
        for k in range(3):
            px = cx + dx
            py = cy + dy + k
            if px < 0 or px >= w or py < 0 or py >= h:
                continue
            pixels[py][px] = blend_color(pixels[py][px], col, 0.9)


def draw_line(pixels, x1, y1, x2, y2, color, width=1):
    """Draw a line with Bresenham stepping and a square brush of width."""
    h = len(pixels)
    w = len(pixels[0])
    col = (color[0], color[1], color[2])
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx - dy
    x, y = x1, y1
    half = width // 2
    while True:
        for oy in range(-half, half + 1):
            for ox in range(-half, half + 1):
                px = x + ox
                py = y + oy
                if px < 0 or px >= w or py < 0 or py >= h:
                    continue
                pixels[py][px] = col
        if x == x2 and y == y2:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy


def _png_chunk(chunk_type, data):
    """Build one PNG chunk: length + type + data + CRC32."""
    out = struct.pack('>I', len(data))
    out += chunk_type
    out += data
    out += struct.pack('>I', zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
    return out


def encode_png(pixels, width, height):
    """Encode pixels to a valid PNG (filter 0, single IDAT)."""
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        for (r, g, b) in pixels[y]:
            raw.append(r)
            raw.append(g)
            raw.append(b)
    compressed = zlib.compress(bytes(raw), 9)
    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    png_data = b'\x89PNG\r\n\x1a\n'
    png_data += _png_chunk(b'IHDR', ihdr_data)
    png_data += _png_chunk(b'IDAT', compressed)
    png_data += _png_chunk(b'IEND', b'')
    return png_data


def main():
    # Create pixel buffer
    pixels = create_pixels(CANVAS_SIZE)

    # Draw scene
    draw_background(pixels, CANVAS_SIZE)

    # Bokeh positions (fixed for determinism)
    bokeh_positions = [
        (10, 80), (15, 150), (20, 220), (25, 290), (30, 360),
        (50, 100), (50, 400), (50, 700),
        (900, 100), (900, 400), (900, 700), (990, 100), (990, 400)
    ]
    draw_bokeh(pixels, bokeh_positions, (255, 255, 255), 55, 0.25, 0)

    # Ground shadow
    draw_glow(pixels, 512, 885, 180, 290, (80, 60, 40), 0)

    # Tail
    draw_ellipse(pixels, 795, 775, 95, 48, COLORS['TAIL'], -30, 1)

    # Body
    fill_ellipse_gradient(pixels, 512, 640, 260, 280,
                          COLORS['BODY_TOP'], COLORS['BODY_BOTTOM'], 1)

    # Belly
    fill_ellipse(pixels, 512, 705, 165, 190, COLORS['BELLY'], 1)

    # Head
    fill_ellipse_radial_gradient(pixels, 500, 400, 235, 235,
                                 COLORS['HEAD_TOP'], COLORS['HEAD_BOTTOM'], 1)

    # Ears
    fill_ellipse(pixels, 320, 210, 42, 42, COLORS['EAR_OUTER'], 1)
    fill_ellipse(pixels, 320, 210, 24, 24, COLORS['EAR_INNER'], 1)
    fill_ellipse(pixels, 690, 195, 42, 42, COLORS['EAR_OUTER'], 1)
    fill_ellipse(pixels, 690, 195, 24, 24, COLORS['EAR_INNER'], 1)

    # Eyes (big, glossy; highlights offset to the upper left)
    fill_ellipse(pixels, 415, 400, 62, 62, COLORS['EYE'], 1)
    fill_ellipse(pixels, 396, 380, 18, 18, COLORS['EYE_HIGHLIGHT_1'], 1)
    fill_ellipse(pixels, 430, 414, 7, 7, COLORS['EYE_HIGHLIGHT_2'], 1)

    fill_ellipse(pixels, 600, 388, 62, 62, COLORS['EYE'], 1)
    fill_ellipse(pixels, 581, 368, 18, 18, COLORS['EYE_HIGHLIGHT_1'], 1)
    fill_ellipse(pixels, 615, 402, 7, 7, COLORS['EYE_HIGHLIGHT_2'], 1)

    # Nose
    fill_ellipse(pixels, 505, 490, 26, 26, COLORS['NOSE'], 1)
    fill_ellipse(pixels, 497, 482, 9, 9, COLORS['EYE_HIGHLIGHT_1'], 1)
    draw_line(pixels, 505, 502, 505, 514, COLORS['NOSE'], 2)

    # Mouth
    fill_ellipse(pixels, 505, 528, 22, 22, COLORS['MOUTH_OUTER'], 1)
    fill_ellipse(pixels, 505, 530, 12, 12, COLORS['TONGUE'], 1)

    # Blush (soft tint)
    fill_ellipse(pixels, 330, 500, 48, 48, COLORS['BLUSH'], 1, alpha=0.55)
    fill_ellipse(pixels, 685, 490, 48, 48, COLORS['BLUSH'], 1, alpha=0.55)

    # Heart
    fill_heart(pixels, 512, 645, 75, -8,
               COLORS['HEART_TOP'], COLORS['HEART_BOTTOM'], 1)

    # Paws (hugging the heart)
    fill_ellipse(pixels, 400, 695, 78, 78, COLORS['PAW'], 1)
    fill_ellipse(pixels, 400, 695, 35, 35, COLORS['PAW_PAD'], 1)
    draw_ellipse_arc(pixels, 400, 695, 78, COLORS['EYEBROW'], 1)
    fill_ellipse(pixels, 625, 695, 78, 78, COLORS['PAW'], 1)
    fill_ellipse(pixels, 625, 695, 35, 35, COLORS['PAW_PAD'], 1)
    draw_ellipse_arc(pixels, 625, 695, 78, COLORS['EYEBROW'], 1)

    # Encode and save PNG
    png_data = encode_png(pixels, CANVAS_SIZE, CANVAS_SIZE)

    output_dir = os.environ.get('MAKEFUN_OUTPUT_DIR', '/output')
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, 'entry.png')
    with open(output_path, 'wb') as f:
        f.write(png_data)

    print(f"Written {output_path} ({len(png_data)} bytes)")


if __name__ == '__main__':
    main()
