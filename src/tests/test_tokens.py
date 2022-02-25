import unittest
from pathlib import Path

from src.teletext import Teletext, TeletextPage


class TestTokens(unittest.TestCase):

    def load_teletext(self, filename: str):
        return Teletext.from_ndjson(
            Path(__file__).resolve().parent / "data" / f"{filename}.ndjson"
        )

    def test_tokens(self):
        tt = self.load_teletext("tokens01")

        self.assertEqual(
            ['tagesschau', 'Nachrichten', 'Russischer', 'Angriff', 'auf', 'Ukraine', 'Explosionen',
             'in', 'Kiew', 'Angriffe', 'mit', 'Panzern', 'im', 'Laufe', 'des', 'Tages', 'erwartet',
             'Generalmobilmachung', 'angeordnet', 'Selenskyj', 'sieht', 'sich', 'als', 'Ziel', 'USA',
             'und', 'Atomenergiebehörde', 'besorgt', 'über', 'Einnahme', 'Tschernobyls', 'Meldungen',
             'über', 'Kämpfe', 'landesweit', 'Hunderte', 'Festnahmen', 'bei', 'Protesten', 'gegen',
             'russischen', 'Angriff', 'in', 'Moskau', 'Bundesregierung', 'hebt', 'Hermes-Bürgschaften',
             'auf', 'Neue', 'EU-Sanktionen', 'Biden', 'kündigt', 'harte', 'Sanktionen',
             'an', 'US-Soldaten', 'nach', 'Deutschland', 'NATO-Staaten', 'wollen', 'über', 'stärkeren',
             'Schutz', 'der', 'östlichen', 'NATO-Länder', 'Laut', 'UNHCR', 'etwa', 'Menschen', 'auf',
             'der', 'Flucht', 'weitere', 'Schlagzeilen'],
            tt.get_page(101, 1).to_tokens()
        )

        self.assertEqual(
            ['tagesschau', 'Nachrichten', 'Sanktionen', 'gegen', 'Russland', 'Die', 'Bundesregierung',
             'hat', 'laut', 'Bundeswirtschaftsministerium', 'die', 'Hermes-Bürgschaften', 'für', 'Russland',
             'aufgehoben', 'Damit', 'werde', 'das', 'Geschäft', 'deutscher', 'Unternehmen', 'mit', 'Russland',
             'ab', 'sofort', 'erheblich', 'erschwert', 'schreibt', 'das', 'Handelsblatt', 'Gestern',
             'beschlossen', 'die', 'EU-Staaten', 'ein', 'umfangreiches', 'Sanktionspaket', 'Die', 'Maßnahmen',
             'betreffen', 'u.a', 'die', 'Bereiche', 'Energie', 'Finanzen', 'Transport', 'und', 'Export', 'Zum',
             'Beispiel', 'sollen', 'russische', 'Banken', 'von', 'den', 'EU-Finanzmärkten', 'sowie', 'die',
             'Luftverkehrsbranche', 'von', 'der', 'Versorgung', 'mit', 'Technik', 'abgeschnitten', 'werden',
             'Biden', 'kündigt', 'harte', 'Sanktionen', 'an'],
            tt.get_page(109, 1).to_tokens()
        )

        self.assertEqual(
            ['Wetter', 'Schifffahrt', 'VORHERSAGE', 'vom', 'Uhr', 'alles', 'gerundete', 'Prognosen', 'für',
             'Uhr', 'Angaben', 'in', 'cm', 'ELBE', 'Dresden', 'Torgau', 'Wittenberg', 'Dessau', 'Aken', 'Barby',
             'Magdeburg', 'S', 'Niegripp', 'Tangermünde', 'Wittenberge', 'Dömitz', 'Neu', 'Darchau', 'Boizenburg',
             'mehr'],
            tt.get_page(193, 1).to_tokens()
        )

        #page = tt.get_page(193, 1)
        #print(page.to_tokens())
