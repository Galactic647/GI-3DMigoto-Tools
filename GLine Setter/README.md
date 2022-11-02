# GLine Setter

This tool is a standalone version of [genshin_set_outlines.py](https://github.com/SilentNightSound/GI-Model-Importer/blob/main/Tools/genshin_set_outlines.py) made by silent.

I basically rewrite the script since there are a few optimization that can be done but the behaviour is still similar.

The changes that I made was the tool will check for `texcoord` and `ini` files automatically, since it doesn't look like it's necessary to put it in manually.

--------------------

## GLine

If you just want to simply changes the outline thickness of a mod, then you can use the `GLine` tool.

When running it you can simply put in the thickness that you want. Generally the normal thickness is around 80-100 but try what work best for you.

--------------------

## GColor

`GColor` is another tool that is similar to `GLine` but with more customization.

The original code was also made by silent [geshin_set_color.py](https://github.com/SilentNightSound/GI-Model-Importer/blob/main/Tools/genshin_set_color.py).

From the description of the script, this tool is used to forcibly sets the color of a texcoord output to a certain value in `RGBA`.

The `RGB` controls the color value and the `A` controls the outline thickness.
