import os


class PDF2TXT:
    def __init__(self):
        pass

    def pdf2txt(self, file_path: str, raise_errors=True) -> str:
        if not file_path.endswith('.pdf'):
            if raise_errors:
                raise Exception('Failed to LOAD file. Must be PDF')
            else:
                return None

        file_out_path = file_path[:-4] + '.txt'

        # main command
        cmd = 'pdftotext "%s" "%s"' % (file_path, file_out_path)
        os.system(cmd)

        if not os.path.isfile(file_out_path) or os.path.getsize(file_out_path) == 0:
            if raise_errors:
                raise Exception('pdf2txt: Failed to generate TXT (No .txt file))')
            else:
                return None

        try:
            with open(file_out_path, 'r', encoding='unicode_escape') as f:
                text = ' '.join(f.readlines())
                if '\x00' in text:
                    text = text.replace('\x00', ' ')
                text = text.encode('utf-8', 'replace').decode('utf-8')
        except Exception as e:
            if raise_errors:
                raise Exception('Decode problem. No .txt file. ' + str(e))
            else:
                return None

        return text
