# Strategy

The judge picks the cuter picture at one glance, weighing: a clear cute
subject first, then the subject's own cuteness, charm, craft, and
readability at small size. This entry is built to win on those, in order.

1. **Clear cute subject.** One baby otter, centered, filling the frame.
   Nothing else competes with it: the background is a soft gradient with
   faint bokeh, so the otter is unmistakable even at 300 pixels across.

2. **Cute subject.** A baby otter is round, chubby, and soft by nature.
   The drawing leans into that: a big round head and belly, small round
   ears, and oversized dark eyes with two white highlights each. The eyes
   are the single most important feature, so they are the largest and
   glossiest shapes on the face.

3. **Charm.** The otter hugs a glossy pink heart with two big clumsy
   paws, paws in front of the heart the way a child hugs a toy. A small
   head tilt, pink blush cheeks, and a tiny open smiling mouth add
   personality without clutter.

4. **Craft.** The picture is drawn, not pasted: every shape is a filled
   ellipse, gradient, or heart curve with a soft 1-pixel edge, so there
   are no hard outlines, smears, or artefacts. The otter has exactly two
   ears, two eyes, one nose, one mouth, two paws, and one tail. No text.

5. **Reads small.** One subject, high contrast between the dark eyes and
   the light face, and the pink heart as a single bright accent. Nothing
   crowds the otter.

## Implementation

Pure Python 3.13, standard library only (`os`, `struct`, `zlib`, `math`,
`sys`). The renderer is a small software rasterizer: per-pixel signed
distance fills with soft edges, vertical and radial gradients, an implicit
heart curve, Bresenham lines, and a hand-written PNG encoder (filter 0,
single IDAT, correct CRC32 on every chunk). All layout values are fixed
constants, so the output is deterministic and reproducible byte for byte.
The result is 1024x1024 and about 124 KB, well under the 1 MiB limit.
