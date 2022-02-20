import unittest

from src.teletext import Teletext, TeletextPage


class TestTeletex(unittest.TestCase):

    def test_comparison(self):
        page1 = TeletextPage()
        page1.new_line()
        page1.add_block(TeletextPage.Block("hello", "w", "b"))

        page2 = TeletextPage()
        page2.new_line()
        page2.add_block(TeletextPage.Block("hello", "w", "b"))

        page3 = TeletextPage()
        page3.new_line()
        page3.add_block(TeletextPage.Block("hello", "w", "b", link=200))

        self.assertEqual(page1, page2)
        self.assertNotEqual(page1, page3)

    def test_json(self):
        block = TeletextPage.Block("text", "r", "g", 1, [1, 23])
        self.assertEqual(
            block,
            TeletextPage.Block.from_json(block.to_json())
        )