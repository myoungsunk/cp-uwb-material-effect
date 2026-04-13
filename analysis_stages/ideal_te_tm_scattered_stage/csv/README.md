# Ideal Scattered Stage CSV Layout

Use this folder for ideal-source / ideal-probe field exports generated with:

- `Field Type = Scattered from SBR+ Regions`

Recommended structure:

- `raw/pec`
- `raw/baseline`
- `raw/slab_concrete`
- `raw/slab_glass`
- `raw/slab_wood`
- `normalized`

`manifest.csv` should point at the actual raw CSV files.

Reflection/export interpretation in this stage:

- `z_m`: reflected scattered field
- `z_p`: transmitted scattered field
- total transmitted field is reconstructed later as `E_inc + E_scat`
