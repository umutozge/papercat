Papercat
--------

A simple command-line tool to tag and manage reearch articles. Tested only on
MacOS.

The most important feature of the tool is its use of `xattr`s to store tags. Thereby,

* No external database needed;
* Nothing gets lost when moving files around.


Installation and usage:

You can use the tool as an executable script: 

```
papercat.py <folder-of-documents>
```

But you need to have the dependencies like `pandas`, `xattrs` etc. in your
runtime environment.

In order to break free from module requirements, I would recommend using `pyinstaller` to package the script for once in a virtual
environment where you have the dependencies. This way you can use the executable (find it under `dist` folder)
anywhere in your system. In my case the following command worked:

```
pyinstaller --hidden-import=_cffi_backend -F papercat.py                   
```

Of course, it is always harder to read papers than manage them.
