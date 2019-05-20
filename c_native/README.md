To create the C-native format tree, check the make instructions in the README file in the root directory ($ make, or $ make cnative).
However, before doing that the library cnativenodelib.so must be built by going to the tools/cnative directory and execute:

$ gcc -shared -o cnativenodelib.so -fPIC cnativenodelib.c

And in the tools directory, compile vspec.py.
$ python -m compileall vspec.py

The created cnative tree file can then be tried out using the testparser found in the cnative directory.
To build it, execute:

cc vsstestparser.c vssparserutilities.c -o vsstestparser

When starting it, the path to the cnative file must be provided. If started from the cnative directory:
$ ./vsstestparser ../../vss_rel_<current version>.cnative

In the tesparser you can traverse the tree from the keyboard keys r/l/u/d as shown in the simple UI. 
You can also search the tree by first enter the key g, and a path possibly including wildcars, e.g. "Root.Signal.Cabin.Door.*.*.IsOpen".
The UI will then display the path to all nodes found matching the search path. 
