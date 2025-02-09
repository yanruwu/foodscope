from memory_profiler import profile

@profile
def funcion_pesada():
    # Ejemplo: Crear una lista grande
    lista = [i for i in range(10**6)]
    # Realiza alguna operación
    suma = sum(lista)
    return suma

if __name__ == "__main__":
    resultado = funcion_pesada()
    print("Resultado:", resultado)
