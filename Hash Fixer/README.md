# Hash Fixer

Tool for fixing hash warnings upon loading multiple mods

Here's a tutorial (kinda) on how to run it.  
https://youtu.be/hFbvOeCE09Y

---

## Running

First add your `Mods` folder path to the `config.ini`.  
![image](https://user-images.githubusercontent.com/44773161/209852749-f7b3488e-521c-4f69-9748-e807bea24069.png)

Run the exe and a prompt will ask for a mode choice  
![image](https://user-images.githubusercontent.com/44773161/199424090-2349ea51-2451-4047-adc6-743c8d0a3399.png)

Type the mode that you want

* Fix  
  For fixing the hash warnings

* Restore  
  For reverting the changes

The way this tool fix the warnings was by adding `match_priority = 0` for sections in the ini file that have a common hash.  
![image](https://user-images.githubusercontent.com/44773161/209852627-cb0fb585-e41c-49f3-8c48-126aa0276063.png)

---

## Troubleshooting

If some warnings still persist after running the tool, that means the hash that the mod use is not in `common_hash.txt`.

You can add these hashes yourself by looking at the warning messages.
![image](https://user-images.githubusercontent.com/44773161/199424717-57bc3d27-990a-47e4-922b-b9eacaeeeef9.png)

After you got all the hashes that persist, add them to `common_hash.txt` and run the tool again.
