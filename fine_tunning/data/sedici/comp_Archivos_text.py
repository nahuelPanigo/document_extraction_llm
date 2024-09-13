import os
import filecmp
import shutil

# Configura las rutas a las carpetas
carpeta1 = 'texts'
carpeta2 = 'texts2'


archivos_diferentes = []
archivos_eliminados = []


# Obtén los nombres de los archivos en la primera carpeta
archivos_carpeta1 = set(os.listdir(carpeta1))

# Recorre todos los archivos en la primera carpeta
for archivo in archivos_carpeta1:
    archivo1 = os.path.join(carpeta1, archivo)
    archivo2 = os.path.join(carpeta2, archivo)

    # Verifica si el archivo existe en la segunda carpeta
    if os.path.isfile(archivo2):
        # Compara los archivos
        if not filecmp.cmp(archivo1, archivo2, shallow=False):
            archivos_diferentes.append(archivo)
            print("archivo es diferente",archivo)
        else:
            print("archivo igual")
    else:
        print(f"El archivo '{archivo}' no se encuentra en la segunda carpeta")
        archivos_eliminados.append(archivo)
print("Comparación completa.")


print(archivos_diferentes)
print(archivos_eliminados)