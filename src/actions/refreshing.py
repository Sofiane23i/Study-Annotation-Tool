import state as S


def refreshing():
    message = S.text_box.get(1.0, "end-1c")
    jj = 0
    for ii in message.split('\n'):
        S.entryText[jj].set(ii)
        jj = jj + 1
