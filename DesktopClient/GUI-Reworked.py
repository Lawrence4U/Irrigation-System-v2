from ctypes import alignment
from pickle import TRUE
from time import sleep
import tkinter as tk
from tkinter.ttk import *
from xmlrpc.client import Boolean
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.pyplot import text
from matplotlib.sankey import RIGHT

def toggle():
    print(btnActivo['text'])
    
    if btnActivo['text'] == "Inactivo":
        print("opt1")
        btnActivo.state(["pressed"])
        btnActivo.configure(text='Activo')
        print(btnActivo.state())
    else:
        btnActivo.state(["!pressed"])
        btnActivo.configure(text='Inactivo')
        print(btnActivo.state())


def intVartoInt(lista):
    lista = [i.get() for i in lista]
    return lista
    
    
    
def cButtonSemanal():
    print(chLunes.state())
    global opcion
    valores = intVartoInt(opcion)
    print(valores)
    print(root.winfo_height())
    
def comboSeleccionado(*args):
    print(selPrograma.get())
    
def commandFreq():
    if varFrecuencia.get():
        print("Personalizado")
    else:
        print("Unico")
        
    return
    
    
if __name__ == "__main__":
    
    root = tk.Tk()
    root.title("Interfaz")
    root.geometry("400x500+600+300")
    
    #cargando estilos
    style = Style()
    
    style.theme_use('clam')
    style.configure('A.TButton', width = 10, foreground = 'white', borderwidth=0, focusthickness=0, focuscolor='none', takefocus=False)
    style.map("A.TButton", background=[('pressed', 'green4'), ('!pressed', 'grey27')])
    style.configure('TLabels', width = 10, foreground = 'white2')
    style.configure('TRadiobutton', indicatoron=0)
    style.configure('A.TCheckbutton', foreground = 'white', anchor='center', width=3, indicatorrelief=tk.FLAT, indicatormargin=-10, indicatordiameter=-10, heigth=3)
    style.map('A.TCheckbutton', background=[('!selected', 'grey27'), ('selected', 'green4')])
    style.configure('A.TSpinbox',)
    style.configure('B.TButton', width = 1, height = 1 ,foreground = 'white')
    style.map("B.TButton", background=[('pressed', 'green4'), ('!pressed', 'grey27')])
    
    #Cargando ventana
    tabGroup = Notebook(root)
    
    tab1 = Frame(tabGroup)
    tab2 = Frame(tabGroup)
    
    tabGroup.add(tab1, text='Pestaña 1')
    tabGroup.add(tab2, text='Pestaña 2')
    tabGroup.pack(expand=1, fill="both")
    
    ##Selector de programas
    selPrograma = Combobox(tab1, values=[1,2,3,4,5,6], width= 5, justify= 'center', state='readonly')
    selPrograma.current(0)
    selPrograma.bind("<<ComboboxSelected>>", comboSeleccionado)
    
    ##Activación/desactivación del programa
    btnActivo = Button(tab1, command=toggle, text='Inactivo', style='A.TButton')
    ##Etiqueta
    labFreq = Label(tab1, text='Frecuencia del programa')
    
    ##Selector de frecuencia
    varFrecuencia = tk.IntVar()
    radFreq1 = tk.Radiobutton(tab1, text='Único',indicatoron=0, variable=varFrecuencia, value =0, command=commandFreq)
    radFreq2 = tk.Radiobutton(tab1, text='Personalizado',indicatoron= 0,variable=varFrecuencia, value =1, command=commandFreq)

    ##Programacion semanal
    ###Primero habria que cargar la selección existente para este dia
    opcion= [tk.IntVar(value=0),tk.IntVar(value=0),tk.IntVar(value=0),tk.IntVar(value=0),tk.IntVar(value=0),tk.IntVar(value=0),tk.IntVar(value=0)]
    chLunes = Checkbutton(tab1, text="L", variable=opcion[0], command=cButtonSemanal, style='A.TCheckbutton')
    chMartes = Checkbutton(tab1, text="M", variable=opcion[1], command=cButtonSemanal, style='A.TCheckbutton')
    chMiercoles = Checkbutton(tab1, text="X", variable=opcion[2], command=cButtonSemanal, style='A.TCheckbutton')
    chJueves = Checkbutton(tab1, text="J", variable=opcion[3], command=cButtonSemanal, style='A.TCheckbutton')
    chViernes = Checkbutton(tab1, text="V", variable=opcion[4], command=cButtonSemanal, style='A.TCheckbutton')
    chSabado = Checkbutton(tab1, text="S", variable=opcion[5], command=cButtonSemanal, style='A.TCheckbutton')
    chDomingo = Checkbutton(tab1, text="D", variable=opcion[6], command=cButtonSemanal, style='A.TCheckbutton')
    
    ##configuración de los programas
    listaOpciones=[]
    for i in range(144):
        for j in range(6):
            listaOpciones.append(f'{i%24}:{(j*10):02d}')
    
    listaOpciones = tuple(listaOpciones)
    
    labStart = Label(tab1, text='Tiempos de arranque:')
    butAddHora = Button(tab1, text='+', style='B.TButton')
    labHora = Label(tab1, text='Hora: ')
    tHora = tk.StringVar(value='0:00')
    spinHora = Spinbox(tab1, textvariable=tHora, wrap=True, values=listaOpciones, style='A.TSpinbox', width=5)
    
    labDura = Label(tab1, text='Duracion: ')
    tDuracion = tk.StringVar(value='0:00')
    spinDuracion = Spinbox(tab1, textvariable=tDuracion, wrap=True, values=listaOpciones, style='A.TSpinbox', width=5)
    
    ##Valvulas a las que aplicar el programa
    optVal = [tk.IntVar(value=0),tk.IntVar(value=0),tk.IntVar(value=0),tk.IntVar(value=0)]
    labVal = Label(tab1, text='Valvulas a operar:')
    chVal1 = Checkbutton(tab1, text="Valvula 1", variable=optVal[0])
    chVal2 = Checkbutton(tab1, text="Valvula 2", variable=optVal[1])
    chVal3 = Checkbutton(tab1, text="Valvula 3", variable=optVal[2])
    chVal4 = Checkbutton(tab1, text="Valvula 4", variable=optVal[3])
    #chValAll = Checkbutton(tab1, text="Activar todas", variable=opcion[6], command=cButtonEvent)
    
    ##Guardado de configuración
    butSave = Button(tab1, text='Guardar Programa')
    
    
    
    root.update_idletasks() #hacemos update del root para que este todo listo
    #distribución
    selPrograma.place(x=20, y=20)
    btnActivo.place(x=20, y=50)
    labFreq.place(x=20, y=80)
    radFreq1.place(x=30, y=110)
    radFreq2.place(x=71, y=110)
    chLunes.place(x= 20, y=150)
    chMartes.place(x= 50, y=150)
    chMiercoles.place(x= 80, y=150)
    chJueves.place(x= 110, y=150)
    chViernes.place(x= 140, y=150)
    chSabado.place(x= 170, y=150)
    chDomingo.place(x= 200, y=150)
    
    labStart.place(x= 20,y=190)
    butAddHora.place(x= 150, y=185)
    labHora.place(x= 20,y=220)
    spinHora.place(x= 60,y=220)
    labDura.place(x= 140,y=220)
    spinDuracion.place(x= 200,y=220)
    
    labVal.place(x= 20, y= 260)
    chVal1.place(x= 40, y= 290)
    chVal2.place(x= 40, y= 320)
    chVal3.place(x= 40, y= 350)
    chVal4.place(x= 40, y= 380)
    butSave.place(x= 20, y= root.winfo_height()-80)
    
    

    root.mainloop()