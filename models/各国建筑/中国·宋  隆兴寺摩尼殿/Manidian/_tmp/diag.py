import bpy, bmesh
rows = []
for ob in bpy.data.objects:
    if ob.type != 'MESH':
        continue
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    be = sum(1 for e in bm.edges if len(e.link_faces) < 2)
    nm = sum(1 for e in bm.edges if len(e.link_faces) > 2)
    if be or nm:
        rows.append((be, nm, ob.name, len(bm.verts)))
    bm.free()
rows.sort(reverse=True)
print("OPEN_EDGES total_objects=%d" % len(rows))
for be, nm, n, v in rows[:14]:
    print("  %5d open %4d nonmanifold  %-26s v=%d" % (be, nm, n, v))
