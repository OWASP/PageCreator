import sys


def build_csv():
    newlines = []
    with open('redirects.conf') as f:
        for line in f.readlines():
            if line.startswith('#') or len(line.strip()) == 0:
                continue
            newlines.append(line)
    
    with open('redirects.csv', 'w') as f:
        f.writelines(newlines)



build_csv()