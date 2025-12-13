import os, shutil
from PIL import Image, ImageTk
import state as S
from tkinter import Toplevel, Button, messagebox


def annotation_file():
    # Determine the output file path
    if S.list_of_files and len(S.list_of_files) > S.pos:
        # Using loaded image from folder
        output_file_path = S.list_of_files[S.pos] + ".txt"
        use_gan_image = False
    else:
        # Using GAN-generated image
        gan_output_dir = os.path.join(os.path.dirname(__file__), '..', 'gan_output_data')
        gan_output_dir = os.path.abspath(gan_output_dir)
        os.makedirs(gan_output_dir, exist_ok=True)
        output_file_path = os.path.join(gan_output_dir, "annotation.txt")
        use_gan_image = True
    
    # write IAM text
    fff = open(output_file_path, "w")
    ind = 0
    for iii in S.entries:
        if (iii.get() != '-'):
            fff.write(str(S.ind2) + ' ok X ' + str(round(S.finalrowsbbx[ind][0])) + ' ' + str(round(S.finalrowsbbx[ind][1])) + ' ' + str(round(S.finalrowsbbx[ind][2])) + ' ' + str(round(S.finalrowsbbx[ind][3])) + ' X ' + iii.get() + '\n')
        ind = ind + 1
        S.ind2 = S.ind2 + 1
    fff.close()

    # close annotate window
    if S.r:
        S.r.destroy()

    if use_gan_image:
        # For GAN images, just save annotations and show confirmation
        messagebox.showinfo("Annotation Saved", f"Annotation saved to:\n{output_file_path}")
        
        # Reset UI state
        if S.btn_save:
            S.btn_save["state"] = "normal"
        if S.btn_annotate:
            S.btn_annotate["state"] = "disabled"
        if S.btn_char_annotate:
            S.btn_char_annotate["state"] = "normal"
        if S.btn_htr:
            S.btn_htr["state"] = "normal"
        if S.btn_open:
            S.btn_open["state"] = "normal"
        if S.scale_slider:
            S.scale_slider["state"] = "disabled"
        if S.padding_slider:
            S.padding_slider["state"] = "disabled"
        if S.btn_save:
            S.btn_save["state"] = "disabled"
    else:
        # move files to done (original behavior for loaded images)
        shutil.move(S.list_of_files[S.pos], S.directorydone)
        shutil.move(S.list_of_files[S.pos] + '.txt', S.directorydone)
        os.mkdir(S.directorydone + '/' + str(S.nbrout))
        for ff in os.listdir(S.directoryout + '/'):
            shutil.move(S.directoryout + '/' + ff, S.directorydone + '/' + str(S.nbrout))

        S.nbrout = S.nbrout + 1
        S.pos = S.pos + 1

        with open("log.txt", "w") as ffflog:
            ffflog.write(str(S.nbr) + ';' + str(S.ind2) + ';' + str(S.nbrout))

        if len(os.listdir(S.pathDirectory)) != 0:
            if S.btn_save:
                S.btn_save["state"] = "normal"
            if S.btn_annotate:
                S.btn_annotate["state"] = "disabled"
            if S.btn_char_annotate:
                S.btn_char_annotate["state"] = "normal"
            from PIL import Image, ImageTk
            img2 = ImageTk.PhotoImage(Image.open(S.list_of_files[S.pos]).resize((800, 800)))
            S.label.configure(image=img2)
            S.label.text = img2
        else:
            fInfos = Toplevel()
            fInfos.title('No image left')
            Button(fInfos, text='Exit', command=S.window.destroy).pack(padx=50, pady=10)
            fInfos.transient(S.window)
            fInfos.grab_set()
            S.window.wait_window(fInfos)
