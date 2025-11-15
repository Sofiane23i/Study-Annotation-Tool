from tkinter import filedialog as fd
import state as S


def import_annotaion():
    filetypes = (
        ('text files', '*.txt'),
        ('All files', '*.*')
    )

    filename = fd.askopenfilename(
        title='Open a file',
        initialdir='/',
        filetypes=filetypes)

    if not filename:
        return

    message = ''
    with open(filename, 'r') as file1:
        Lines = file1.readlines()
        for line in Lines:
            linee = line.split('\n')
            linee = linee[0].split(' ')
            for ii in linee:
                message = message + ii + '\n'
    message = message[:-1]

    S.text_box.insert('end', message)

    jj = 0
    for ii in message.split('\n'):
        S.entryText[jj].set(ii)
        jj = jj + 1
