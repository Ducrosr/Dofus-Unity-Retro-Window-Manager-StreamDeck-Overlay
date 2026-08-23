# Dofus Window Manager

[Français](README.md) · [English](README.en.md) · **Español**

> [!NOTE]
> Esta traducción fue generada con ayuda de IA y puede contener errores. Puedes proponer correcciones mediante Issues o Pull Requests en el repositorio oficial.

Gestor local de ventanas para Windows compatible con **Dofus Unity** y **Dofus Retro**, diseñado para facilitar y agilizar el juego multicuenta. Detecta las ventanas abiertas, conserva su orden y permite cambiar entre ellas mediante atajos globales, un overlay o un Stream Deck.

> [!WARNING]
> **Este repositorio es la única fuente oficial:**
> <https://github.com/Ducrosr/Dofus-Unity-Retro-Window-Manager-StreamDeck-Overlay>
>
> No descargues Dofus Window Manager desde sitios de terceros, mensajes privados o espejos. Una copia modificada podría intentar robar credenciales de Ankama, tokens de sesión o datos personales. La aplicación oficial nunca solicita tu contraseña de Ankama, código de doble autenticación ni acceso a tu cuenta.
>
> Consulta también la guía oficial de Ankama: **[Reconocer el phishing y protegerse](https://support.ankama.com/hc/fr/articles/201376953-Reconna%C3%AEtre-le-phishing-et-s-en-prot%C3%A9ger)**.

La versión 2.20.0 es la beta pública actual. Reúne la interfaz multilingüe, los overlays, las solicitudes de atención, los retratos, los iconos oficiales y los temas Unity/Retro. El ejecutable de Windows correspondiente está disponible en la [Release oficial v2.20.0-beta.1](https://github.com/Ducrosr/Dofus-Unity-Retro-Window-Manager-StreamDeck-Overlay/releases/tag/v2.20.0-beta.1).

## Funciones principales

- detección nativa de ventanas Dofus Unity y Retro;
- atajos globales para el personaje siguiente y anterior;
- orden por botones o arrastrar y soltar;
- alias, retrato personalizado o de clase incluido, 39 iconos oficiales de características y 20 iconos oficiales de oficios por personaje;
- las ventanas ignoradas conservan su tecla de Stream Deck, pero salen de la rotación automática;
- perfiles JSON y copia completa de la configuración;
- cambio instantáneo entre Unity y Retro;
- modo compacto siempre visible;
- notificación de cambio personalizable: contenido, posición, duración y opacidad;
- overlay de rotación transparente, desplazable y redimensionable;
- indicador naranja `!` de solicitud de atención, con parpadeo suave opcional, en la aplicación, el overlay y Stream Deck;
- doce temas disponibles en ambos modos: Standard, Bonta, Brakmar, Tribute, Gold and Steel, Belladone, Unicorn, Emerald Mine, Sufokia, Pandala, Wabbit y Retro;
- francés por defecto, además de inglés y español seleccionables con un clic;
- restablecimiento independiente de la visualización que conserva perfiles y personalizaciones de personajes;
- comprobación opcional de Releases oficiales, sin descarga automática.

Standard es el tema predeterminado de Unity y Retro el de Dofus Retro. Todos los temas pueden utilizarse en ambos modos y la aplicación recuerda una preferencia distinta para cada versión del juego.

## Stream Deck 0.6.1

El plugin incluye ocho teclas de personaje y acciones Anterior, Siguiente, Subir, Bajar, Ignorar/restaurar, Actualizar y Abrir/mostrar. En cada tecla se puede colocar el número, nombre, clase y alias de forma independiente en cuatro líneas. Los retratos, iconos, solicitudes de atención, tema activo e idioma se sincronizan automáticamente.

El perfil incluido está preparado para el Stream Deck estándar de 15 teclas. Una ventana excluida de la rotación sigue siendo accesible desde su tecla asignada.

## Instalación rápida

### Ejecutable para Windows

Descarga el ejecutable únicamente desde una Release oficial de este repositorio, verifica su huella SHA-256 cuando esté disponible, colócalo en una carpeta permanente y ejecútalo. El ejecutable estándar no incluye la detección visual experimental de invitaciones en Retro.

Windows SmartScreen puede mostrar una alerta para versiones beta sin firma. No ignores esa alerta si el archivo procede de otra fuente.

### Desde el código fuente

Requisitos: Windows 10/11 de 64 bits y Python 3.12 o posterior.

```powershell
git clone https://github.com/Ducrosr/Dofus-Unity-Retro-Window-Manager-StreamDeck-Overlay.git
cd Dofus-Unity-Retro-Window-Manager-StreamDeck-Overlay
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

Instala el plugin desde **Aplicación → Instalar plugin de Stream Deck** y acepta el perfil propuesto.

## Primeros pasos

1. Inicia el gestor y elige Unity o Retro.
2. Abre los clientes de Dofus y pulsa **Actualizar**.
3. Comprueba los nombres y las clases detectados.
4. Arrastra los personajes al orden deseado.
5. Añade opcionalmente un alias, retrato e icono mediante **Personalizar…**.
6. Prueba F5, F6, F7 y Ctrl+Alt+R.
7. Guarda un perfil.
8. Configura el overlay y la notificación en **Ajustes → Visualización en el juego**.

Atajos predeterminados:

| Acción | Atajo |
|---|---|
| Personaje siguiente | F5 |
| Personaje anterior | F6 |
| Ignorar/restaurar ventana actual | F7 |
| Actualizar ventanas | Ctrl+Alt+R |

## Seguridad y privacidad

Dofus Window Manager no lee la memoria ni los paquetes de red de Dofus, no inyecta código, no envía comandos al juego, no solicita credenciales de Ankama y no sube retratos. El puente de Stream Deck escucha únicamente en `127.0.0.1:32145`. Los ajustes, perfiles y registros permanecen en `%APPDATA%\DofusUnityWindowManager\`.

Ejecuta el gestor y Dofus con el mismo nivel de privilegios de Windows. Lee [SECURITY.md](SECURITY.md) y la guía [anti-phishing de Ankama](https://support.ankama.com/hc/fr/articles/201376953-Reconna%C3%AEtre-le-phishing-et-s-en-prot%C3%A9ger) antes de instalar un binario obtenido fuera del repositorio oficial.

## Compilación y pruebas

```powershell
py -3.14 -m unittest discover -s tests -v
py -3.14 -m pip install -r requirements-dev.txt
py -3.14 -m ruff check .
py -3.14 build_exe.py
```

PyInstaller crea `dist\DofusWindowManager.exe`. Las fuentes y los comandos del plugin se encuentran en [`streamdeck-plugin`](streamdeck-plugin/README.md).

## Estado del proyecto

Solo Windows. Este proyecto comunitario no está afiliado, aprobado ni patrocinado por Ankama. Dofus, Dofus Retro, Ankama, así como los retratos e iconos del juego incluidos en `assets/ankama`, pertenecen a sus respectivos propietarios. Esos recursos visuales no están cubiertos por la licencia GPL-3.0 del código; consulta el [aviso de recursos](assets/ankama/NOTICE.md) antes de redistribuirlos.
