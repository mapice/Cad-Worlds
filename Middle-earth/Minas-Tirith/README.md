# Minas Tirith

A first editable Blender interpretation of the White City, beginning the Middle-earth project in Cad Worlds. Created on 29 October 2026 with Blender 5.2 LTS.

![Overview](outputs/Minas-Tirith-overview.png)

## Open the model

Open [Minas-Tirith.blend](outputs/Minas-Tirith.blend) in Blender. Materials are procedural and included in the file; no external textures or add-ons are required. The file uses Git LFS when versioned.

Press **Numpad 0** to switch between the main camera and free navigation. Collections separate the landscape, each circle's fortifications and houses, connecting ramps, the stone prow, citadel, fountain court, banners, and lighting. Houses are individual mesh objects; repeated details of walls and landmarks are grouped into editable meshes.

Five cameras are included: overview, front, citadel, plan, and main gate. Their rendered views are in `outputs/`.

## This first version

- Seven stepped circles with walls, battlements, towers, and gates.
- 400 houses with varied heights and roofs, plus the ceremonial hall.
- Six curved ramps with landings and supports.
- The great rock, summit promenade, Tower of Ecthelion, arcades, White Tree, fountain, and Gondor banners.
- An interpreted foothill of Mindolluin and the approach from the Pelennor.

This is an exterior study, not an exact reconstruction of the film miniature or a canonical survey. Dimensions, house layouts, terrain, and circulation are interpreted. Interiors are not modelled. Complete pedestrian routing, tunnels through the great rock, detailed street-to-ramp connections, and further architectural variety remain future work. The model is not prepared or certified for 3D printing.

## Rebuild and verify

The scripts use Blender's bundled Python and no external dependencies. Paths are resolved relative to this folder, and seed `1437` makes the procedural layout repeatable.

```sh
blender --background --python scripts/build.py -- --no-render
blender --background --python scripts/render_and_verify.py
```

Use `--preview` with `build.py` for a smaller initial render. Running the scripts replaces generated files in `outputs/`; preserve any manual edits before rebuilding. Temporary reports go in the ignored `work/` folder.

The [verification report](outputs/verification.json) checks the saved file for empty geometry, non-finite coordinates, missing external images, seven wall groups, six ramps, and unobstructed radial centreline probes through the seven gates. These limited checks do not establish full walkability, collision-free geometry, manifold solids, or canonical accuracy.

## References

The overall silhouette and principal landmarks are informed by [Wētā Workshop's Minas Tirith environment](https://www.wetanz.com/us/minas-tirith) and [photographs of the Wētā model](https://www.thewetamuseum.com/lotr/environments/lotrenviro_minast.html). The geometry in this project was generated independently; reference photographs are not included.

This is an unofficial fan project. Minas Tirith, Middle-earth, and the associated fictional setting belong to their respective rights holders.
