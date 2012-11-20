#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import re
import string


HEADING = re.compile(r"^(={1,6})\s*(.*[^=\s])\s*=*")
HORIZONTAL_RULE = re.compile(r"^(-{4})")
ORDERED_LIST = re.compile(r"^(#+)\s*(.*)")
PREFORMATTED = re.compile(r"^(\{\{\{)\s*([-:\s\w]*)", re.UNICODE)
BLOCK_CODE = re.compile(r"^(```)\s*([-:\s\w]*)", re.UNICODE)
UNORDERED_LIST = re.compile(r"^(\*+)\s*(.*)")
TABLE = re.compile(r"^(\|.*)")

END_OF_PREFORMATTED = re.compile(r"^\s*(\}\}\})")
END_OF_BLOCK_CODE = re.compile(r"^\s*(```)")

URL = re.compile(r"""(?i)\b((?:[a-z][\w-]+:(?:/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’]))""")

class HTML(object):

    @staticmethod
    def entities(text):
        chars = list(text)
        for i, ch in enumerate(chars):
            if ch == "&":
                chars[i] = "&amp;"
            elif ch == "'":
                chars[i] = "&apos;"
            elif ch == "\"":
                chars[i] = "&quot;"
            elif ch == "<":
                chars[i] = "&lt;"
            elif ch == ">":
                chars[i] = "&gt;"
        return "".join(chars)


class HTMLOutputStream(object):

    def __init__(self, processors=None):
        self.tokens = []
        self.stack = []
        self.token_buffer = []
        self.processors = processors or []

    def __html__(self):
        return "".join(self.tokens)

    def __repr__(self):
        return self.__html__()

    def _flush(self):
        if self.token_buffer:
            buffer = "".join(self.token_buffer)
            self.token_buffer = []
            for processor in self.processors:
                buffer = processor[0].sub(processor[1], buffer)
            self.tokens.append(buffer)

    def write_html(self, html):
        self._flush()
        self.tokens.append(html)

    def write_text(self, text, post_process=False):
        if post_process:
            self.token_buffer.extend(HTML.entities(text))
        else:
            self._flush()
            self.tokens.extend(HTML.entities(text))

    def tag(self, tag, attributes=None):
        if attributes:
            self.write_html("<{0} {1}>".format(
                tag,
                " ".join(
                    '{0}="{1}"'.format(key, HTML.entities(str(value)))
                    for key, value in attributes.items()
                    if value is not None
                )
            ))
        else:
            self.write_html("<{0}>".format(tag))

    def start_tag(self, tag, attributes=None, void=False):
        self.tag(tag, attributes)
        if not void:
            self.stack.append(tag)

    def end_tag(self, tag=None):
        if not self.stack:
            raise ValueError("No tags to close")
        if not tag:
            tag = self.stack[-1]
        if tag not in self.stack:
            raise ValueError("End tag </{0}> should have corresponding start tag <{0}>".format(tag))
        while True:
            t = self.stack.pop()
            self.write_html("</{0}>".format(t))
            if t == tag:
                break

    def element(self, tag, attributes=None, text=None, html=None):
        if text and html:
            raise ValueError("Cannot specify both text and html content")
        self.start_tag(tag, attributes)
        if text:
            self.write_text(text)
        if html:
            self.write_html(html)
        self.end_tag()

    def close(self):
        self._flush()
        while self.stack:
            t = self.stack.pop()
            self.write_html("</{0}>".format(t))


class Partitioner(object):

    def __init__(self, escape, *markers):
        self.escape = escape
        if escape:
            self.markers = [self.escape]
        else:
            self.markers = []
        self.markers.extend(markers)
        self.marker_chars = list(set(marker[0] for marker in self.markers))

    def partition(self, markup):
        self.tokens = []
        p, q = 0, 0
        while q < len(markup):
            if markup[q] in self.marker_chars:
                if self.escape and markup[q] == self.escape:
                    start = q + len(self.escape)
                else:
                    start = q
                for seq in self.markers:
                    end = start + len(seq)
                    if markup[start:end] == seq:
                        if q > p:
                            yield markup[p:q]
                        yield markup[q:end]
                        p, q = end, end
                        break
                else:
                    q += 1
            else:
                q += 1
        if q > p:
            yield markup[p:q]


class InlineMarkup(object):

    def __init__(self, markup=None):
        partitioner = Partitioner("~",
            "http://", "https://", "ftp://", "mailto:",
            '"""', "{{{", "}}}", "<--", "-->",
            "\\\\", "{{", "}}", "``", '""',
            "**", "//", "^^", ",,", "[[", "]]", "|"
        )
        self.tokens = list(partitioner.partition(markup))

    def __html__(self):

        def image(out, markup):
            src, alt = markup.partition("|")[0::2]
            out.tag("img", {"src": src, "alt": alt or None})

        def link(match):
            url = match.group(1)
            if ":" in url:
                href = url
            else:
                href = "http://" + url
            return '<a href="{0}">{1}</a>'.format(href, url)

        simple_tokens = {
            "\\\\": "<br>",
            "-->": "&rarr;",
            "<--": "&larr;",
        }
        toggle_tokens = {
            "//": "em",
            '""': "q",
            "**": "strong",
            ",,": "sub",
            "^^": "sup",
        }
        bracket_tokens = {
            "``" : ("``", lambda out, markup: out.element("code", text=markup)),
            "{{" : ("}}", image),
            "{{{": ("}}}", lambda out, markup: out.write_text(markup)),
        }

        out = HTMLOutputStream(processors=[(URL, link)])
        tokens = self.tokens[:]
        while tokens:
            token = tokens.pop(0)
            if token[0] == "~":
                out.write_text(token[1:])
            elif token in simple_tokens:
                out.write_html(simple_tokens[token])
            elif token in toggle_tokens:
                tag = toggle_tokens[token]
                if tag in out.stack:
                    out.end_tag(tag)
                else:
                    out.start_tag(tag)
            elif token in bracket_tokens:
                end_token, writer = bracket_tokens[token]
                markup = []
                while tokens:
                    token = tokens.pop(0)
                    if token == end_token:
                        break
                    elif token[0] == "~":
                        markup.append(token[1:])
                    else:
                        markup.append(token)
                writer(out, "".join(markup))
            elif token == "[[":
                href = []
                while tokens:
                    token = tokens.pop(0)
                    if token in ("|", "]]"):
                        break
                    elif token[0] == "~":
                        href.append(token[1:])
                    else:
                        href.append(token)
                href = "".join(href)
                out.start_tag("a", {"href": href})
                if token != "|":
                    out.write_text(href)
                    out.end_tag("a")
            elif token == "]]":
                try:
                    out.end_tag("a")
                except ValueError:
                    out.write_text(token)
            else:
                out.write_text(token, post_process=True)
        out.close()
        return out.__html__()


class HeadingMarkup(object):

    def __init__(self, markup):
        if not markup.startswith("="):
            raise ValueError("Heading must start with '='")
        chars = list(markup.rstrip().rstrip("="))
        self.level = 0
        while chars and chars[0] == "=":
            chars.pop(0)
            self.level += 1
        self.text = "".join(chars).strip()
        if self.level > 6:
            self.level = 6

    def __html__(self):
        out = HTMLOutputStream()
        out.element("h" + str(self.level), text=self.text)
        return out.__html__()


class TableRowMarkup(object):

    def __init__(self, markup):
        if not markup.startswith("|"):
            raise ValueError("Table row must start with '|'")
        bracket_tokens = {
            "``" : "``",
            "[[" : "]]",
            "{{" : "}}",
            "{{{": "}}}",
            }
        partitioner = Partitioner("~", "|", "``", "[[", "]]", "{{", "}}", "{{{", "}}}")
        markup = markup.rstrip()
        if markup.endswith("|"):
            tokens = list(partitioner.partition(markup[:-1]))
        else:
            tokens = list(partitioner.partition(markup))
        self.cells = []
        while tokens:
            token = tokens.pop(0)
            if token == "|":
                self.cells.append([])
            elif token in bracket_tokens:
                end = bracket_tokens[token]
                self.cells[-1].append(token)
                while tokens:
                    token = tokens.pop(0)
                    self.cells[-1].append(token)
                    if token == end:
                        break
            else:
                self.cells[-1].append(token)
        self.cells = ["".join(cell) for cell in self.cells]

    def __html__(self):
        out = HTMLOutputStream()
        out.start_tag("tr")
        for cell in self.cells:
            if cell.startswith("="):
                tag = "th"
                content = cell[1:]
            else:
                tag = "td"
                content = cell
            align = None
            if content:
                left_padded = content[0] in string.whitespace
                right_padded = content[-1] in string.whitespace
                if left_padded and right_padded:
                    align = "center"
                elif right_padded:
                    align = "left"
                elif left_padded:
                    align = "right"
            if align:
                content = content.strip()
                out.element(tag, {"style": "text-align:" + align}, html=InlineMarkup(content).__html__())
            else:
                out.element(tag, html=InlineMarkup(content).__html__())
        out.end_tag("tr")
        return out.__html__()


class Markup(object):

    def __init__(self, markup):
        self.blocks = []
        block, params, lines = None, None, []
        for line in markup.splitlines(True):
            if block is PREFORMATTED:
                at_end = END_OF_PREFORMATTED.match(line)
                if at_end:
                    self._append_block(block, params, lines)
                    block, params, lines = None, None, []
                else:
                    lines.append(line)
            elif block is BLOCK_CODE:
                at_end = END_OF_BLOCK_CODE.match(line)
                if at_end:
                    self._append_block(block, params, lines)
                    block, params, lines = None, None, []
                else:
                    lines.append(line)
            else:
                line = line.rstrip()
                #heading = HEADING.match(line)
                horizontal_rule = HORIZONTAL_RULE.match(line)
                ordered_list = ORDERED_LIST.match(line)
                preformatted = PREFORMATTED.match(line)
                block_code = BLOCK_CODE.match(line)
                unordered_list = UNORDERED_LIST.match(line)
                #table = TABLE.match(line)
                if line.startswith("="):
                    self._append_block(block, params, lines)
                    block, params, lines = None, None, []
                    self.blocks.append((HEADING, None, [HeadingMarkup(line)]))
                elif horizontal_rule:
                    self._append_block(block, params, lines)
                    block, params, lines = None, None, []
                    self.blocks.append((HORIZONTAL_RULE, None, None))
                elif ordered_list:
                    if block is ORDERED_LIST:
                        params.append(len(ordered_list.group(1)))
                        lines.append(ordered_list.group(2))
                    else:
                        self._append_block(block, params, lines)
                        block, params, lines = ORDERED_LIST, [len(ordered_list.group(1))], [ordered_list.group(2)]
                elif preformatted:
                    self._append_block(block, params, lines)
                    block, params, lines = PREFORMATTED, preformatted.group(2).split(), []
                elif block_code:
                    self._append_block(block, params, lines)
                    block, params, lines = BLOCK_CODE, block_code.group(2).split(), []
                elif unordered_list:
                    if block is UNORDERED_LIST:
                        params.append(len(unordered_list.group(1)))
                        lines.append(unordered_list.group(2))
                    else:
                        self._append_block(block, params, lines)
                        block, params, lines = UNORDERED_LIST, [len(unordered_list.group(1))], [unordered_list.group(2)]
                elif line.startswith("|"):
                    if block is not TABLE:
                        self._append_block(block, params, lines)
                        block, params, lines = TABLE, None, []
                    lines.append(TableRowMarkup(line))
                else:
                    if block:
                        self._append_block(block, params, lines)
                        block, params, lines = None, None, []
                    if line:
                        lines.append(line)
                    else:
                        if lines:
                            self.blocks.append((block, params, lines))
                            lines = []
        self._append_block(block, params, lines)

    def _append_block(self, block, params, lines):
        if block or lines:
            self.blocks.append((block, params, lines))

    def __html__(self):
        out = HTMLOutputStream()
        for i, (block, params, lines) in enumerate(self.blocks):
            if block is None:
                out.element("p", html=InlineMarkup(" ".join(lines)).__html__())
            elif block is HEADING:
                for line in lines:
                    out.write_html(line.__html__())
            elif block is HORIZONTAL_RULE:
                out.tag("hr")
            elif block is PREFORMATTED:
                if params:
                    out.start_tag("pre", {"class": " ".join(params)})
                else:
                    out.start_tag("pre")
                for line in lines:
                    out.write_text(line)
                out.end_tag("pre")
            elif block is BLOCK_CODE:
                if params:
                    out.start_tag("pre", {"class": " ".join(params)})
                else:
                    out.start_tag("pre")
                out.start_tag("ol")
                for line in lines:
                    out.start_tag("li")
                    out.element("code", text=line)
                    out.end_tag("li")
                out.end_tag("pre")
            elif block in (ORDERED_LIST, UNORDERED_LIST):
                if block is ORDERED_LIST:
                    tag = "ol"
                else:
                    tag = "ul"
                level = 0
                for i, line in enumerate(lines):
                    while level > params[i]:
                        out.end_tag(tag)
                        level -= 1
                    while level < params[i]:
                        out.start_tag(tag)
                        level += 1
                    out.element("li", html=InlineMarkup(line).__html__())
                for i in range(level):
                    out.end_tag(tag)
            elif block is TABLE:
                out.start_tag("table", {"cellspacing": 0})
                for line in lines:
                    out.write_html(line.__html__())
                out.end_tag("table")
        return out.__html__()


if __name__ == "__main__":
    import codecs
    import sys
    import os
    if len(sys.argv) > 1:
        markup = codecs.open(sys.argv[1], "r", "UTF-8").read()
        css = open(os.path.join(os.path.dirname(__file__), "..", "syntaq.css")).read()
        print("<!doctype html>\n<html>\n<head>")
        print("<style type=\"text/css\">" + css + "</style>")
        print("</head>\n<body>\n")
        print(Markup(markup).__html__())
        print("</body>\n</html>")
