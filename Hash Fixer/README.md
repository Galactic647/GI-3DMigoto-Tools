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

For `ShaderOverride` sections it's slightly different because the option added was `allow_duplicate_hash = true` instead of match_priority.  
![image](https://user-images.githubusercontent.com/44773161/210266603-3c051109-2c97-4ce3-aa7f-c60d47a6118d.png)

---

## Troubleshooting

If some warnings still persist after running the tool, that means the section of the mod config file is not on the list of sections that the tool scan.

Here's an example of 2 sections that doesn't get scanned
![image](https://user-images.githubusercontent.com/44773161/227728531-593ea4c4-76b9-4dc6-9b9d-73d9e7d7411d.png)

To solve this issue you can add the hash manually by looking at the warning message and add it to `common_hash.txt`

Here's an example of a warning that presist
![image](https://user-images.githubusercontent.com/44773161/199424717-57bc3d27-990a-47e4-922b-b9eacaeeeef9.png)
In this example you can add `4e3376db` to `common_hash.txt` and then run the tool again and everything should be fixed.
