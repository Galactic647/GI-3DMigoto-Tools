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

--------------------

## Usage

### **Single mods**

The usage of both `GLine` and `GColor` is the same. Put them on the mod folder that you want to edit and run it.
![image](https://user-images.githubusercontent.com/44773161/199425538-f2eb1df6-22f0-409c-9c0e-2b6410261d5d.png)

### **Merged mods**

Same as the first one, the usage of both `GLine` and `GColor` is the same. But this time put the tool in the parent folder instead (where `merged.ini` is).

![image](https://user-images.githubusercontent.com/44773161/201698385-bf9d150f-d932-47ed-bebc-ab31d38f1d0c.png)

After that run it like usual.
