from src.iterator import TeletextIterator


def main():
    tt_iterator = TeletextIterator()

    for tt in tt_iterator.iter_teletexts():
        print(tt)



if __name__ == "__main__":
    main()
