#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from syntaq import InlineMarkup


class InlineMarkupTester(unittest.TestCase):

    def test_no_content(self):
        line = InlineMarkup("")
        assert line.__html__() == ""

    def test_no_tags(self):
        line = InlineMarkup("foo bar")
        assert line.__html__() == "foo bar"

    def test_ampersand(self):
        line = InlineMarkup("foo & bar")
        assert line.__html__() == "foo &amp; bar"

    def test_entities(self):
        line = InlineMarkup("foo & ' \" < > bar")
        assert line.__html__() == "foo &amp; &apos; &quot; &lt; &gt; bar"

    def test_strong(self):
        line = InlineMarkup("foo **bar**")
        assert line.__html__() == "foo <strong>bar</strong>"

    def test_single_asterisks(self):
        line = InlineMarkup("foo *bar*")
        assert line.__html__() == "foo *bar*"

    def test_em(self):
        line = InlineMarkup("foo //bar//")
        assert line.__html__() == "foo <em>bar</em>"

    def test_single_slashes(self):
        line = InlineMarkup("7 / 10")
        assert line.__html__() == "7 / 10"

    def test_code(self):
        line = InlineMarkup("foo ``bar``")
        assert line.__html__() == "foo <code>bar</code>"

    def test_sup(self):
        line = InlineMarkup("foo ^^bar^^")
        assert line.__html__() == "foo <sup>bar</sup>"

    def test_sub(self):
        line = InlineMarkup("foo ,,bar,,")
        assert line.__html__() == "foo <sub>bar</sub>"

    def test_q(self):
        line = InlineMarkup('foo ""bar""')
        assert line.__html__() == "foo <q>bar</q>"

    def test_nested_tags(self):
        line = InlineMarkup("foo **//bar//**")
        assert line.__html__() == "foo <strong><em>bar</em></strong>"

    def test_oddly_nested_tags(self):
        line = InlineMarkup("foo **//**bar**//**")
        assert line.__html__() == "foo <strong><em></em></strong>bar<strong><em></em></strong>"

    def test_code_does_not_nest(self):
        line = InlineMarkup("foo ``bar ** baz // qux``")
        assert line.__html__() == "foo <code>bar ** baz // qux</code>"

    def test_code_can_contain_ampersand(self):
        line = InlineMarkup("foo ``bar & baz``")
        assert line.__html__() == "foo <code>bar &amp; baz</code>"

    def test_tag_without_explicit_end(self):
        line = InlineMarkup("foo **bar")
        assert line.__html__() == "foo <strong>bar</strong>"

    def test_nested_tags_without_explicit_end(self):
        line = InlineMarkup("foo **//bar**")
        assert line.__html__() == "foo <strong><em>bar</em></strong>"

    def test_image(self):
        line = InlineMarkup("foo {{bar.png}}")
        assert line.__html__() == 'foo <img src="bar.png">'

    def test_image_with_alt(self):
        line = InlineMarkup("foo {{bar.png|baz qux}}")
        assert line.__html__() == 'foo <img src="bar.png" alt="baz qux">'

    def test_link(self):
        line = InlineMarkup("foo [[bar]]")
        assert line.__html__() == 'foo <a href="bar">bar</a>'

    def test_external_link(self):
        line = InlineMarkup("foo [[http://www.example.com/stuff]]")
        assert line.__html__() == 'foo <a href="http://www.example.com/stuff">http://www.example.com/stuff</a>'

    def test_external_link_with_trailing_slash(self):
        line = InlineMarkup("foo [[http://www.example.com/stuff/]]")
        assert line.__html__() == 'foo <a href="http://www.example.com/stuff/">http://www.example.com/stuff/</a>'

    def test_unclosed_link(self):
        line = InlineMarkup("foo [[bar")
        assert line.__html__() == 'foo <a href="bar">bar</a>'

    def test_link_with_description(self):
        line = InlineMarkup("foo [[bar|description & things]]")
        assert line.__html__() == 'foo <a href="bar">description &amp; things</a>'

    def test_link_with_description_and_markup(self):
        line = InlineMarkup("foo [[bar|this is an **important** link]]")
        assert line.__html__() == 'foo <a href="bar">this is an <strong>important</strong> link</a>'

    def test_link_with_image_description(self):
        line = InlineMarkup("foo [[bar|{{image.jpg}}]]")
        assert line.__html__() == 'foo <a href="bar"><img src="image.jpg"></a>'

    def test_unclosed_link_with_image_description(self):
        line = InlineMarkup("foo [[bar|{{image.jpg")
        assert line.__html__() == 'foo <a href="bar"><img src="image.jpg"></a>'

    def test_link_with_complex_description(self):
        line = InlineMarkup("[[http://www.example.com/stuff|this is a //really// interesting link --> {{image.jpg}}]]")
        assert line.__html__() == '<a href="http://www.example.com/stuff">this is a <em>really</em> interesting link &rarr; <img src="image.jpg"></a>'

    def test_escaped_asterisks(self):
        line = InlineMarkup("foo ~** bar")
        assert line.__html__() == "foo ** bar"

    def test_trailing_tilde(self):
        line = InlineMarkup("foo bar ~")
        assert line.__html__() == "foo bar ~"

    def test_auto_link(self):
        line = InlineMarkup("foo http://example.com/ bar")
        assert line.__html__() == 'foo <a href="http://example.com/">http://example.com/</a> bar'

    def test_auto_link_with_trailing_dot(self):
        line = InlineMarkup("foo http://example.com/. bar")
        assert line.__html__() == 'foo <a href="http://example.com/">http://example.com/</a>. bar'

    def test_auto_link_in_angle_brackets(self):
        markup = "foo <http://example.com/> bar"
        expected_html = 'foo &lt;<a href="http://example.com/">http://example.com/</a>&gt; bar'
        actual_html = InlineMarkup(markup).__html__()
        try:
            assert actual_html == expected_html
        except AssertionError as err:
            print(markup + "\n" + actual_html + " != " + expected_html)
            raise err


if __name__ == "__main__":
    unittest.main()
