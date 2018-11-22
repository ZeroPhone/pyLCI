# -*- coding: utf-8 -*-

#TODO: export into ui.funcs?
import string
printable_characters = set(string.printable)

from ui import Menu, TextReader
from helpers import setup_logger

i = None
o = None
git_if = None

logger = setup_logger(__name__, "warning")

about_text = """ZPUI (beta)
git {}
{} branch

A user interface for small non-touch displays. \n
Developed for ZeroPhone, works for other stuff. \n
Docs: zpui.rtfd.org \n
Github: https://github.com/ZeroPhone/ZPUI \n
License: Apache 2.0, with MIT components."""

def about():
    mc = [["About ZPUI", about_zpui],
          ["Contributors", about_contributors]]
    Menu(mc, i, o, name="Settings-About menu").activate()

def about_zpui():
    try:
        branch = git_if.get_current_branch()
        head = git_if.get_head_for_branch(branch)[:10]
    except:
        logger.exception("Can't get git information!")
        branch = "unknown"
        head = "unknown"
    text = about_text.format(head, branch)
    TextReader(text, i, o, name="About ZPUI TextReader", h_scroll=False).activate()

def about_contributors():
    with open("CONTRIBUTORS.md", 'r') as f:
        contributors_md = f.read()
    lines = contributors_md.split('\n')[2:]
    contributor_names = "\n".join([line[3:] for line in lines])
    text = "ZPUI contributors:\n\n"+contributor_names
    filtered_characters = {"ö":"o"}
    for character, replacement in filtered_characters.items():
        text = text.replace(character, replacement)
    text = filter(lambda x: x in printable_characters, text).strip('\n')
    TextReader(text, i, o, name="About contributors TextReader").activate()
