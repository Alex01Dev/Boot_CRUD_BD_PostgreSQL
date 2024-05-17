import psycopg2
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import wget

def init_chrome():
    ruta_chromedriver = ChromeDriverManager().install()
    s = Service(ruta_chromedriver)
    options = Options()
    user_agent = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Ubuntu Chromium/71.0.3578.80 Chrome/71.0.3578.80 Safari/537.36")
    options.add_argument(f"user-agent={user_agent}")
    options.add_argument("--window-size=970,1080")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-extensions")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--no-sandbox")
    options.add_argument("--allow-running-insecure-content")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--no-first-run")
    options.add_argument("--no-proxy-server")
    options.add_argument("--disable-blink-features=AutomationControlled")

    exp_opt = [
        'enable-automation',
        'ignore-certificate-errors',
        'enable-logging'
    ]
    options.add_experimental_option("excludeSwitches", exp_opt)

    driver = webdriver.Chrome(service=s, options=options)
    driver.set_window_position(0, 0)

    return driver

def mostrar_datos_tabla(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM pokemons")
        rows = cursor.fetchall()
        for row in rows:
            print(row)
        cursor.close()
    except psycopg2.Error as e:
        print(f"Error al obtener los datos de la tabla: {e}")

def conectar_bd():
    DB_NAME = "db_pokemon"
    DB_USER = "postgres"
    DB_PASSWORD = "alexfango04"
    DB_HOST = "localhost"
    DB_PORT = "5432"

    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            client_encoding="UTF8"
        )
        print("Conexión exitosa a la base de datos PostgreSQL")
        return conn
    except psycopg2.Error as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None



def crear_tabla(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pokemons (
                id SERIAL PRIMARY KEY,
                nombre VARCHAR(250),
                descripcion TEXT,
                imagen_url TEXT
            )
        """)
        conn.commit()
        cursor.close()
        print("Tabla creada exitosamente (si no existía)")
    except psycopg2.Error as e:
        print(f"Error al crear la tabla: {e}")

def insertar_pokemon(conn, nombre, descripcion, imagen_url):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO pokemons (nombre, descripcion, imagen_url) VALUES (%s, %s, %s)
        """, (nombre, descripcion, imagen_url))
        conn.commit()
        cursor.close()
        print("Datos insertados exitosamente")
    except psycopg2.Error as e:
        print(f"Error al insertar datos: {e}")

def descargar_info_pokemon(pokemon, conn):
    driver = init_chrome()
    try:
        driver.get(f"https://www.wikidex.net/wiki/{pokemon}")
        wait = WebDriverWait(driver, 10)

        nombre = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1.firstHeading"))).text

        descripcion_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.cuadro_pokemon")))
        descripcion = descripcion_element.text

        imagen_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.imagen")))
        imagen_url = imagen_element.find_element(By.TAG_NAME, "img").get_attribute("src")

        insertar_pokemon(conn, nombre, descripcion, imagen_url)

        print(f"Información de {pokemon} descargada y almacenada exitosamente en la base de datos.")
    
    except TimeoutException:
        print(f"Error: No se pudo encontrar un elemento en la página para el Pokémon {pokemon}.")
    except NoSuchElementException:
        print(f"Error: No se encontró un elemento en la página para el Pokémon {pokemon}.")
    except Exception as e:
        print(f"Error inesperado: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    pokemon = input("Ingrese el nombre del Pokémon: ")
    conn = conectar_bd()
    if conn:
        crear_tabla(conn)
        descargar_info_pokemon(pokemon, conn)
        mostrar_datos_tabla(conn)
        conn.close()
