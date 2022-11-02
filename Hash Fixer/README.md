# Hash Fixer

Tool for fixing hash warnings upon loading multiple mods

--------------------

## Running
First add your `Mods` folder path to the `config.ini`.  
Example:  
`C:\Users\User\3DMigoto\Mods`

Run the exe and a prompt will ask for a mode choice  
`Mode (fix, restore):`

Type the mode that you want
* Fix  
  For fixing the hash warnings

* Restore  
  For reverting the changes

The way this tool fix the warnings was by adding `match_priority = 0` for sections in the ini file that have a common hash.  

## Troubleshooting
If some warnings still persist after running the tool, that means the hash that the mod use is not in `common_hash.txt`.

You can add these hashes yourself by looking at the warning messages.

After you got all the hashes that persist, add them to `common_hash.txt` and run the tool again.

## Problems

For now the tool will skip mods that have multiple textures or in other words, merged mods.

If you have more than one merged mods like these then it is possible that you will still get the hash warnings.