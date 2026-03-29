import argparse

class MyParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage()
        print(f"Try '{self.prog} --help' for more information.")
        raise SystemExit(2)

p = MyParser(prog='test')
sp = p.add_subparsers(dest='cmd')
sub = sp.add_parser('foo')
print(f'sub type: {type(sub).__name__}')
print(f'main type: {type(p).__name__}')
