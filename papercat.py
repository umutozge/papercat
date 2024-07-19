#!/usr/bin/python3

import os
import xattr
import sys
import cmd
import re
import pandas as pd
from tabulate import tabulate
from functools import reduce

class PCShell(cmd.Cmd):

    def __init__(self, datapath):
        super().__init__()
        self.datapath = datapath
        self.holder = Holder(self.datapath)
        self.prompt = 'papercat> '
        self.intro = 'Welcome to PaperCat!\n\n? for help.\n'
        self.line = "? for help"

    def do_list(self, arg):
        """List entries according to a criterion.
Usage:

    list <criterion>

if no <criterion> is provided, all the items are listed.

<criterion> is either
    - a list of tags like [<t_1>,<t_2>,...,<t_n>] (no quotes, no spaces).
    - a possibly partial name
"""

        df = self.holder.papers
        if not arg:
            print(df[['name','tags']].to_string())
        elif arg[0] == '[' and  arg[-1] == ']' and ' ' not in arg:
            tag_list = arg[1:-1].split(',')
            print(df.loc[df['tags'].map(lambda tags: all([x in tags for x in
                                                          tag_list]))][['name','tags']].to_string())
        elif ' ' not in arg:
            print(df.loc[df['name'].map(lambda name: arg in
                                        name)][['name','tags']].to_string())
        else:
            self.default(self.line)

    def do_ls(self, arg):
        'short for list'
        self.do_list(arg)

    def do_tag(self, arg):
        """Usage:

    tag <item-index> <tag>

<item-index> is the integer in the first column in what you get by list command. To apply the
tag to all items provide 'all' as <item-index>"""

        try:
            index, tag = arg.split()
        except ValueError:
            self.default(self.line)

        if index == 'all':
            self.holder.tag_all(tag)
        else:
            try:
                self.holder.papers.iat[int(index),2].tag(tag)
            except ValueError:
                self.default(self.line)

    def do_tag_if(self, arg):
        """Tag items that satisfy a condition.

Usage 1:

    tag_if <string> <tag>

adds <tag> to all entries whose name contains <string>.

Usage 2:

    tag_if [<tag_1>,<tag_2>,...,<tag_n>] <tag>

adds <tag> to all entries whose tags include the list of tags given as the
first argument. DO NOT leave space between tags.
        """
        try:
            condition, tag = arg.split()
        except ValueError:
            self.default(self.line)
            return None

        if condition[0] == '[' and condition[-1] == ']':
            condition = condition[1:-1].split(',')
            self.holder.apply_by_tags(lambda x: x.tag(tag), condition)
        else:
            self.holder.apply_by_name(lambda x: x.tag(tag), condition)

    def do_untag(self, arg):
        """Usage:

    untag <item-index> tag

<item-index> is the first column in what you get by list command."""
        try:
            index, tag  = arg.split()
        except ValueError:
            self.default(self.line)

        try:
            self.holder.papers.at[int(index),'object'].remove_tag(tag)
        except ValueError:
            self.default(self.line)

    def do_untag_if(self, arg):
        'see tag_if'
        condition, tag = arg.split()
        if condition[0] == '[' and condition[-1] == ']':
            condition = condition[1:-1].split(',')
            self.holder.apply_by_tags(lambda x: x.remove_tag(tag), condition)
        else:
            self.holder.apply_by_name(lambda x: x.remove_tag(tag), condition)

    def do_open(self, arg):
        'open the document with the provided index'

        try:
            index = int(arg)
        except ValueError:
            self.default(self.line)
        else:
            file = self.holder.papers.iat[index, 2].get_file_name()
            os.system(f'open {file}')

    def do_tags(self, arg):
        'print the list of tags'

        tags=self.holder.get_tags()
        acc=[]
        for i in range(0, len(tags), 8):
            acc+=[tags[i:i+8]]
        print()
        print(tabulate(acc,tablefmt="plain"))
        print()

    def do_refresh(self, arg):
        self.holder = Holder(self.datapath)

    def do_bye(self, arg):
        'leave PaperCat'
        print('come again.')
        return True

class Holder():

    def __init__(self, datapath):

        self.papers = []
        with os.scandir(os.path.join(os.getcwd(),datapath)) as entries:
            for entry in entries:
                if not entry.name.startswith('.'):
                    self.papers.append(Paper(entry))

        self.papers = pd.DataFrame([{'name':x.name,'tags':x.tags, 'object':x}
                                                for x in self.papers])

    def get_papers(self):
        return self.papers

    def get_tags(self):
        return reduce(lambda acc, current: acc + [current] if current not in acc else acc,
                      sorted(
                          reduce(lambda x,y:x+y,
                              self.papers['tags'])),
                      []
                     )

    def apply_by_name(self, func, name):
        self.papers =\
        self.papers.assign(object = lambda df: df.apply(lambda row: func(row['object'])
                                                                    if name in row['name']
                                                                    else row['object'],
                                                       axis='columns'))

    def apply_by_tags(self, func, tags):
        self.papers =\
        self.papers.assign(object = lambda df:
                                    df.apply(lambda row:
                                             func(row['object'])
                                             if all([tag in row['tags']
                                                     for tag in tags])
                                             else row['object'],
                                             axis='columns'))

    def tag_all(self, tag):
        self.papers.assign(object = lambda df: df.apply(lambda df: df['object'].tag(tag), axis='columns'))

    def tag_by_name(self, name, tag):
        self.papers =\
        self.papers.assign(object = lambda df: df.apply(lambda row: row['object'].tag(tag)
                                                                    if name in row['name']
                                                                    else row['object'],
                                                       axis='columns'))

    def tag_by_tags(self, tags, tag):
        self.papers =\
        self.papers.assign(object = lambda df:
                                    df.apply(lambda row:
                                             row['object'].tag(tag)
                                             if all([tag in row['tags']
                                                     for tag in tags])
                                             else row['object'],
                                             axis='columns'))

    def untag_by_name(self, name, tag):
        self.papers =\
        self.papers.assign(object = lambda df: df.apply(lambda row: row['object'].remove_tag(tag)
                                                                    if name in row['name']
                                                                    else row['object'],
                                                       axis='columns'))

    def untag_by_tags(self, tags, tag):
        self.papers =\
        self.papers.assign(object = lambda df:
                                    df.apply(lambda row:
                                             row['object'].remove_tag(tag)
                                             if all([tag in row['tags']
                                                     for tag in tags])
                                             else row['object'],
                                             axis='columns'))

class Paper():

    def __init__(self, entry):
        self.path = entry.path
        self.name = re.sub(r'^(.*)\..*$',r'\1',entry.name)
        self.file_name = self.path.replace(' ','\\ ')
        xattr_tag = self._get_xattr_tag()
        self.tags = xattr_tag.decode('utf-8').split(':') if xattr_tag else []

    def _get_xattr_tag(self):
        try:
            tag = xattr.getxattr(self.path, 'papercat.tags')
        except AttributeError:
            tag = None
        except OSError:
            tag = None
        return tag

    def _set_xattr_tag(self):
        xattr.setxattr(self.path, 'papercat.tags', bytes(':'.join(self.tags), 'utf-8'))
        return self._get_xattr_tag()

    def remove_tag(self, tag):
        try:
            self.tags.remove(tag)
            self._set_xattr_tag()
        except ValueError:
            pass
        return self

    def tag(self, tag, append=True):
        if tag not in self.tags:
            self.tags += [tag]
            self._set_xattr_tag()
        return self

    def get_name(self):
        return self.name

    def get_file_name(self):
        return self.file_name

    def __str__(self):
        return f'Paper({self.name}, {self.get_tags()})'

    def __repr__(self):
        return {'name':self.name, 'tags':self.tags}

if __name__=='__main__':

    shell = PCShell(sys.argv[1])
    shell.cmdloop()
    sys.exit()
