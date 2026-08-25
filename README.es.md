<h1 align="center">Dofus Window Manager</h1>

<p align="center"><strong>Gestor multicuenta para Dofus Unity y Retro — con o sin Stream Deck</strong></p>

<p align="center">
  Cambia de personaje con <strong>atajos de teclado globales</strong>, mantén tu equipo visible en un <strong>overlay</strong> y añade el plugin de <strong>Stream Deck</strong> solo si lo deseas.
</p>

<p align="center">
  <a href="https://github.com/Ducrosr/Dofus-Unity-Retro-Window-Manager-StreamDeck-Overlay/releases/tag/v2.20.0-beta.4"><strong>⬇ Descargar para Windows</strong></a>
  ·
  <a href="docs/INSTALLATION.md">Guía de instalación</a>
  ·
  <a href="docs/UTILISATION.md">Guía de uso</a>
</p>

<p align="center">
  <img src=".github/social-preview.png" alt="Dofus Window Manager — Gestión multicuenta Unity y Retro con atajos, overlay y Stream Deck opcional" width="100%">
</p>

[Français](README.md) · [English](README.en.md) · **Español**

> [!NOTE]
> Esta traducción fue generada con ayuda de IA y puede contener errores. Puedes proponer correcciones mediante Issues o Pull Requests en el repositorio oficial.

Gestor local de ventanas para Windows compatible con **Dofus Unity** y **Dofus Retro**, diseñado para facilitar y agilizar el juego multicuenta. Detecta las ventanas abiertas, conserva su orden y permite cambiar entre ellas mediante los atajos **F5/F6**, el overlay o el modo compacto. **Stream Deck no es necesario**: el plugin incluido es una integración opcional para quien disponga del dispositivo.

> [!WARNING]
> **Este repositorio es la única fuente oficial:**
> <https://github.com/Ducrosr/Dofus-Unity-Retro-Window-Manager-StreamDeck-Overlay>
>
> No descargues Dofus Window Manager desde sitios de terceros, mensajes privados o espejos. Una copia modificada podría intentar robar credenciales de Ankama, tokens de sesión o datos personales. La aplicación oficial nunca solicita tu contraseña de Ankama, código de doble autenticación ni acceso a tu cuenta.
>
> Consulta también la guía oficial de Ankama: **[Reconocer el phishing y protegerse](https://support.ankama.com/hc/fr/articles/201376953-Reconna%C3%AEtre-le-phishing-et-s-en-prot%C3%A9ger)**.

La versión 2.20.0 es la beta pública actual. Reúne la interfaz multilingüe, los overlays, las solicitudes de atención, los retratos, los iconos oficiales y los temas Unity/Retro. El ejecutable de Windows correspondiente está disponible en la [Release oficial v2.20.0-beta.4](https://github.com/Ducrosr/Dofus-Unity-Retro-Window-Manager-StreamDeck-Overlay/releases/tag/v2.20.0-beta.4).

## Funciones principales

- detección nativa de ventanas Dofus Unity y Retro;
- atajos globales para el personaje siguiente y anterior, además de ocho atajos directos opcionales para las posiciones 1 a 8;
- captura guiada de combinaciones, detección inmediata de duplicados y etiquetas explícitas para los atajos rechazados o ya utilizados por Windows;
- orden por botones o arrastrar y soltar;
- alias, retrato personalizado o de clase incluido, 39 iconos oficiales de características y 20 iconos oficiales de oficios por personaje;
- las ventanas ignoradas conservan su tecla de Stream Deck, pero salen de la rotación automática;
- perfiles JSON por servidor con orden, alias, retratos e iconos independientes, además de una copia completa de la configuración;
- historial local de los doce últimos puntos de restauración completos, con creación manual y protección automática antes de operaciones de riesgo;
- reconocimiento opcional del perfil del servidor mediante una coincidencia exacta de personajes y del modo Unity/Retro, sin elección automática cuando coinciden varios perfiles;
- escritura atómica de ajustes y perfiles, con copia automática de los últimos ajustes válidos;
- cambio instantáneo entre Unity y Retro con preferencias de visualización separadas para cada versión;
- modo de rendimiento adaptativo que espacia los escaneos de recuperación mientras los eventos de Windows funcionan y restaura automáticamente el intervalo normal cuando es necesario;
- modo compacto siempre visible;
- recuperación automática del modo compacto y del overlay tras un cambio de monitores;
- notificación de cambio personalizable con anchura automática según el contenido, posición, duración y opacidad;
- overlay de rotación transparente vertical u horizontal, desplazable y redimensionable, con anchura automática opcional;
- título y flechas de reordenación del overlay opcionales; arrastrar y soltar sigue disponible cuando se ocultan las flechas;
- retratos e iconos visibles u ocultables de forma independiente en la notificación, el overlay y Stream Deck;
- indicador naranja `!` de solicitud de atención, con parpadeo suave opcional, en la aplicación, el overlay y Stream Deck;
- cola cronológica `!1`, `!2`… con acción **Siguiente alerta** en la aplicación, el overlay, el atajo F8 y Stream Deck;
- perfiles editables incluidos para Stream Deck Standard de 15 teclas, Mini, XL, Plus y Neo, disponibles también en la vista previa integrada;
- comprobación del estado del plugin instalado con reparación explícita mediante el paquete oficial incluido;
- doce temas disponibles en ambos modos: Standard, Bonta, Brakmar, Tribute, Gold and Steel, Belladone, Unicorn, Emerald Mine, Sufokia, Pandala, Wabbit y Retro;
- francés por defecto, además de inglés y español seleccionables mediante botones con banderas gráficas;
- ajustes organizados en las pestañas General, Apariencia y Atajos;
- opciones de accesibilidad para contraste alto, escala de interfaz del 80 al 160 % y reducción de movimiento/parpadeo;
- aviso de seguridad obligatorio en el primer inicio, antes de activar los atajos globales;
- configuración inicial guiada para idioma, modo Unity/Retro, detección, prueba de enfoque, overlay e instalación opcional de Stream Deck;
- simulación del overlay y la notificación con personajes ficticios, sin Dofus abierto ni acción de enfoque;
- preajustes Minimal, Equilibrado y Completo para cambiar rápidamente la densidad visual;
- restablecimiento independiente de la visualización que conserva perfiles y personalizaciones de personajes;
- comprobación opcional de Releases oficiales, sin descarga automática;
- métricas locales de duración de escaneos y latencia de enfoque en el diagnóstico;
- paquete ZIP de soporte anonimizado opcional, sin retratos ni configuración restaurable.

Standard es el tema predeterminado tanto para Unity como para Retro. Todos los temas pueden utilizarse en ambos modos y la aplicación recuerda un tema y un conjunto de preferencias de visualización distintos para cada versión del juego.

## Stream Deck 0.8.0

El plugin incluye ocho teclas de personaje y acciones Anterior, Siguiente, Siguiente alerta, Subir, Bajar, Ignorar/restaurar, Actualizar y Abrir/mostrar. La tecla Siguiente alerta muestra el número pendiente y activa la solicitud más antigua. En cada tecla se puede colocar el número, nombre, clase y alias de forma independiente en cuatro líneas. Los retratos, iconos, orden de alertas, tema activo e idioma se sincronizan automáticamente.

Stream Deck sigue siendo opcional. El paquete proporciona automáticamente un diseño editable para los modelos Standard de 15 teclas, Mini, XL, Plus y Neo. Los dispositivos compactos priorizan las teclas de personaje y Anterior/Siguiente, mientras que el diseño XL muestra los ocho personajes y todos los comandos en sus dos primeras filas. Una ventana excluida de la rotación sigue siendo accesible desde su tecla asignada.

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
2. Lee el aviso de seguridad, confirma que tu copia procede del repositorio oficial, abre los clientes de Dofus y pulsa **Actualizar**.
3. Comprueba los nombres y las clases detectados.
4. Arrastra los personajes al orden deseado.
5. Crea o carga un perfil por servidor y añade opcionalmente un alias, retrato e icono mediante **Personalizar…**.
6. Prueba F5, F6, F7, F8 y Ctrl+Alt+R; los accesos directos a las ventanas 1 a 8 se configuran en Ajustes.
7. Guarda el perfil.
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

Ejecuta el gestor y Dofus con el mismo nivel de privilegios de Windows. En el primer inicio, la aplicación exige leer un aviso y confirmar que la copia procede del repositorio oficial. Si ya ejecutaste una copia no oficial, ciérrala, desconecta el equipo si es necesario, cambia inmediatamente las contraseñas de Ankama y del correo asociado desde otro dispositivo de confianza, activa la doble autenticación y ejecuta un análisis antivirus completo o sin conexión. Lee [SECURITY.md](SECURITY.md) y la guía [anti-phishing de Ankama](https://support.ankama.com/hc/fr/articles/201376953-Reconna%C3%AEtre-le-phishing-et-s-en-prot%C3%A9ger).

## Compilación y pruebas

```powershell
py -3.14 -m unittest discover -s tests -v
py -3.14 -m pip install -r requirements-dev.txt
py -3.14 -m ruff check .
py -3.14 build_exe.py
```

PyInstaller crea `dist\DofusWindowManager.exe`; el repositorio también contiene una definición de Inno Setup para `DofusWindowManager-Setup.exe`. Las fuentes y los comandos del plugin se encuentran en [`streamdeck-plugin`](streamdeck-plugin/README.md).

## Estado del proyecto

Solo Windows. Este proyecto comunitario no está afiliado, aprobado ni patrocinado por Ankama. Dofus, Dofus Retro, Ankama, así como los retratos e iconos del juego incluidos en `assets/ankama`, pertenecen a sus respectivos propietarios. Esos recursos visuales no están cubiertos por la licencia GPL-3.0 del código; consulta el [aviso de recursos](assets/ankama/NOTICE.md) antes de redistribuirlos.
