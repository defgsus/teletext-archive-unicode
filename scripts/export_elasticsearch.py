import os
import datetime
from pathlib import Path

from elastipy import Exporter
import dateutil.parser

from src.iterator import TeletextIterator


class TeletextExporter(Exporter):
    INDEX_NAME = "teletext-archive"

    MAPPINGS = {
        "properties": {
            "timestamp": {"type": "date"},
            "timestamp_hour": {"type": "integer"},
            "timestamp_weekday": {"type": "keyword"},
            "timestamp_week": {"type": "keyword"},

            "page_timestamp": {"type": "date"},
            "page_timestamp_hour": {"type": "integer"},
            "page_timestamp_weekday": {"type": "keyword"},
            "page_timestamp_week": {"type": "keyword"},

            "commit_hash": {"type": "keyword"},

            "channel": {"type": "keyword"},
            "category": {"type": "keyword"},
            "page": {"type": "keyword"},
            "main_page": {"type": "integer"},
            "sub_page": {"type": "integer"},
            "text": {
                "type": "text",
                "analyzer": "german",
                "term_vector": "with_positions_offsets_payloads",
                "store": True,
                "fielddata": True,
            },
        }
    }

    def get_document_id(self, data) -> str:
        return f'{data["timestamp"]}-{data["channel"]}-{data["page"]}'

    def transform_document(self, data: dict) -> dict:
        data = data.copy()
        self._add_timestamp(data, "timestamp")
        self._add_timestamp(data, "page_timestamp")
        return data
    
    @classmethod
    def _add_timestamp(cls, data: dict, key: str):
        if not isinstance(data[key], datetime.datetime):
            data[key] = dateutil.parser.parse(data[key])
        data[f"{key}_hour"] = data[key].hour
        data[f"{key}_weekday"] = data[key].strftime("%w %A")
        data[f"{key}_week"] = "%s-%s" % data[key].isocalendar()[:2]


def export_elasticsearch(tt_iterator: TeletextIterator):
    exporter = TeletextExporter()
    # exporter.delete_index()
    exporter.update_index()

    for tt in tt_iterator.iter_teletexts():
        export_items = []
        for index, page in tt.pages.items():
            export_items.append({
                "timestamp": tt.timestamp,
                "page_timestamp": page.timestamp,
                "commit_hash": tt.commit_hash,
                "channel": tt.channel,
                "category": page.category,
                "page": "%s-%s" % index,
                "main_page": index[0],
                "sub_page": index[1],
                "text": page.to_text(),
            })

        exporter.export_list(export_items)


def count_commits(tt_iterator: TeletextIterator):
    date_dict = {}
    for tt in tt_iterator.iter_teletexts():
        for index, page in tt.pages.items():
            key = page.timestamp[:10]
            if key not in date_dict:
                date_dict[key] = set()
            date_dict[key].add(tt.commit_hash)

        print("-------")
        for key, hashes in date_dict.items():
            print(key, len(hashes))


def main():
    tt_iterator = TeletextIterator(verbose=True)
    export_elasticsearch(tt_iterator)
    # count_commits(tt_iterator)


if __name__ == "__main__":
    main()
