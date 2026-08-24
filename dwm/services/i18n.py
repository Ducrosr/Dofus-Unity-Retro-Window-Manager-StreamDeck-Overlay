from __future__ import annotations

from collections.abc import Mapping
from typing import Any


LANGUAGES = ("fr", "en", "es")
LANGUAGE_FLAGS = {"fr": "🇫🇷", "en": "🇬🇧", "es": "🇪🇸"}
LANGUAGE_NAMES = {"fr": "Français", "en": "English", "es": "Español"}

_language = "fr"


def normalize_language(language: str | None) -> str:
    value = (language or "fr").strip().lower().split("-", 1)[0]
    return value if value in LANGUAGES else "fr"


def set_language(language: str | None) -> str:
    global _language
    _language = normalize_language(language)
    return _language


def get_language() -> str:
    return _language


_EN: dict[str, str] = {
    "Choisir le jeu": "Choose game",
    "Sélectionne la version de Dofus :": "Select the Dofus version:",
    "Mémoriser ce choix (pré-sélection au prochain lancement)": "Remember this choice (preselected on next launch)",
    "Rechercher": "Search",
    "Actualisation automatique": "Automatic refresh",
    "Aperçu interactif du profil par défaut": "Interactive preview of the default profile",
    "Ce rapport peut être copié pour faciliter le dépannage.": "This report can be copied to help troubleshooting.",
    "Choisir un portrait…": "Choose a portrait…",
    "Configuration de l’application": "Application configuration",
    "Copier le rapport": "Copy report",
    "Exporter une copie…": "Export a copy…",
    "Exporter une sauvegarde complète…": "Export a full backup…",
    "Fermer": "Close",
    "Icône": "Icon",
    "Importer un JSON…": "Import JSON…",
    "Importer une sauvegarde…": "Import a backup…",
    "Ouvrir les journaux": "Open logs",
    "Profil sélectionné": "Selected profile",
    "Quitter": "Quit",
    "Recherche en cours…": "Checking…",
    "Retirer": "Remove",
    "Réinitialiser les réglages…": "Reset settings…",
    "Réinitialiser l’affichage…": "Reset display…",
    "Réinitialiser l’affichage": "Reset display",
    "Affichage réinitialisé": "Display reset",
    "Rétablir le thème, les colonnes, la notification et l’overlay par défaut ?\n\nLes profils, alias, portraits, icônes et raccourcis seront conservés.": "Restore the default theme, columns, notification and overlay?\n\nProfiles, aliases, portraits, icons and shortcuts will be kept.",
    "L’affichage par défaut est restauré et l’overlay est activé à sa position initiale.": "The default display has been restored and the overlay is enabled at its initial position.",
    "Supprimer le profil": "Delete profile",
    "État de Dofus Window Manager": "Dofus Window Manager status",
    "Aperçu Stream Deck — profil 15 touches": "Stream Deck preview — 15-key profile",
    "Diagnostic": "Diagnostics",
    "Gérer les profils": "Manage profiles",
    "Sauvegarde et restauration": "Backup and restore",
    "Dofus Window Manager — Mode compact": "Dofus Window Manager — Compact mode",
    "Confirmer": "Confirm",
    "Erreur": "Error",
    "Installation impossible": "Installation failed",
    "Portrait incompatible": "Unsupported portrait",
    "Sauvegarde invalide": "Invalid backup",
    "Journaux": "Logs",
    "Mise à jour": "Update",
    "Charger profil": "Load profile",
    "Exporter": "Export",
    "Démarrage Windows": "Windows startup",
    "Rafraîchir": "Refresh",
    "Fenêtres gérées": "Managed windows",
    "Fenêtres ignorées": "Ignored windows",
    "Glissez un personnage pour modifier l’ordre ; glissez un en-tête pour déplacer une colonne.": "Drag a character to change its order; drag a header to move a column.",
    "Navigation": "Navigation",
    "← Précédent": "← Previous",
    "Suivant →": "Next →",
    "↑ Monter": "↑ Move up",
    "↓ Descendre": "↓ Move down",
    "⚠ Prochaine alerte ({count})": "⚠ Next alert ({count})",
    "Fenêtre sélectionnée": "Selected window",
    "Sélectionnez un personnage": "Select a character",
    "Personnaliser…": "Customize…",
    "Astuce : un élément (Terre, Feu, Eau, Air) ou un métier peut servir d’alias pour distinguer des pseudos proches ou deux personnages de même classe.": "Tip: an element (Earth, Fire, Water, Air) or a profession can be used as an alias to distinguish similar names or duplicate classes.",
    "Ignorer": "Ignore",
    "Réintégrer": "Restore",
    "Profils": "Profiles",
    "Charger": "Load",
    "Enregistrer…": "Save…",
    "Gérer les profils…": "Manage profiles…",
    "Application": "Application",
    "Version de Dofus": "Dofus version",
    "Paramètres…": "Settings…",
    "Mode compact": "Compact mode",
    "Afficher l’overlay": "Show overlay",
    "Masquer l’overlay": "Hide overlay",
    "Aperçu Stream Deck…": "Stream Deck preview…",
    "Diagnostic…": "Diagnostics…",
    "Sauvegarder / restaurer…": "Back up / restore…",
    "Installer le plugin Stream Deck": "Install Stream Deck plugin",
    "Dépôt GitHub officiel": "Official GitHub repository",
    "Conseils anti-phishing Ankama": "Ankama anti-phishing guidance",
    "Lien externe": "External link",
    "Le navigateur n’a pas pu être ouvert.\n\nAdresse à consulter :\n{url}": "The browser could not be opened.\n\nOpen this address manually:\n{url}",
    "Rechercher une mise à jour…": "Check for updates…",
    "Activité": "Activity",
    "Afficher le journal": "Show log",
    "Masquer le journal": "Hide log",
    "Paramètres": "Settings",
    "Général": "General",
    "Apparence": "Appearance",
    "Raccourcis": "Shortcuts",
    "Général · mode {game}": "General · {game} mode",
    "Thème · mode {game}": "Theme · {game} mode",
    "Thème": "Theme",
    "Intervalle d’actualisation": "Refresh interval",
    " secondes": " seconds",
    "Réduire dans la zone de notification à la fermeture": "Minimize to the notification area when closing",
    "Lancer avec Windows, directement dans la zone de notification": "Start with Windows directly in the notification area",
    "Rechercher automatiquement les mises à jour officielles": "Automatically check for official updates",
    "Inclure les versions bêta": "Include beta releases",
    "Vérification quotidienne au maximum ; aucun téléchargement automatique.": "Checked at most once a day; no automatic download.",
    "Affichage en jeu": "In-game display",
    "Affichage en jeu · {game}": "In-game display · {game}",
    "Demandes d’attention": "Attention requests",
    "Clignotement léger sur l’application, l’overlay et le Stream Deck": "Subtle blinking in the app, overlay and Stream Deck",
    "Désactivez le clignotement pour conserver uniquement la couleur orange et le repère !.": "Turn blinking off to keep only the orange color and ! marker.",
    "Afficher le personnage après chaque changement de fenêtre": "Show the character after each window switch",
    "Position de la notification": "Notification position",
    "Durée": "Duration",
    "   Opacité": "   Opacity",
    "Contenu de la notification": "Notification content",
    "Afficher en permanence la rotation": "Always show the rotation",
    "Opacité": "Opacity",
    "   Orientation": "   Orientation",
    "Vertical": "Vertical",
    "Horizontal": "Horizontal",
    "Position X / Y": "X / Y position",
    "Largeur / hauteur": "Width / height",
    "Largeur manuelle / hauteur": "Manual width / height",
    " px · hauteur 0 = automatique": " px · height 0 = automatic",
    "Adapter automatiquement la largeur de l’overlay au contenu": "Automatically fit the overlay width to its content",
    "Contenu de l’overlay": "Overlay content",
    "Par défaut : numéro à gauche, nom ligne 1, puis classe · alias ligne 2.": "Default: number on the left, name on line 1, then class · alias on line 2.",
    "Verrouiller et ignorer les clics": "Lock and ignore clicks",
    "Déverrouillé : glissez l’en-tête pour déplacer l’overlay, une ligne pour la réordonner, ou la poignée ◢ pour le redimensionner.": "Unlocked: drag the header to move the overlay, a row to reorder it, or the ◢ handle to resize it.",
    "Afficher les portraits dans la notification, l’overlay et le Stream Deck": "Show portraits in the notification, overlay and Stream Deck",
    "Faire légèrement clignoter les fenêtres demandant l’attention": "Gently blink windows that need attention",
    "Faire légèrement clignoter les fenêtres demandant l’attention (désactivé : orange et ! conservés)": "Gently blink windows that need attention (off: orange and ! remain)",
    "Afficher les portraits dans la notification": "Show portraits in the notification",
    "Afficher les icônes dans la notification": "Show icons in the notification",
    "Afficher les portraits dans l’overlay": "Show portraits in the overlay",
    "Afficher les icônes dans l’overlay": "Show icons in the overlay",
    "Afficher les portraits sur le Stream Deck": "Show portraits on the Stream Deck",
    "Portrait de classe…": "Class portrait…",
    "Féminin": "Female",
    "Masculin": "Male",
    "Illustrations et icônes Dofus © Ankama Games. Projet communautaire non affilié.": "Dofus artwork and icons © Ankama Games. Unaffiliated community project.",
    "Le portrait personnel est recadré et enregistré localement. Les illustrations et icônes de jeu intégrées sont la propriété d’Ankama Games. Dofus Window Manager est un projet communautaire non affilié à Ankama.": "Personal portraits are cropped and stored locally. The bundled game artwork and icons are the property of Ankama Games. Dofus Window Manager is an unaffiliated community project.",
    "Afficher les icônes officielles de caractéristiques ou de métiers sur ces mêmes affichages": "Show official stat or profession icons on the same displays",
    "Afficher les icônes officielles de caractéristiques ou de métiers sur le Stream Deck": "Show official stat or profession icons on the Stream Deck",
    "Raccourcis clavier": "Keyboard shortcuts",
    "Personnage suivant": "Next character",
    "Personnage précédent": "Previous character",
    "Ignorer la fenêtre": "Ignore window",
    "Prochaine fenêtre en attente": "Next pending window",
    "Actualiser la liste": "Refresh list",
    "Exemples : F5, Ctrl+Alt+R, Shift+F6 ou Win+F7": "Examples: F5, Ctrl+Alt+R, Shift+F6 or Win+F7",
    "Accès direct par position (facultatif)": "Direct access by position (optional)",
    "Fenêtre {position}": "Window {position}",
    "Raccourcis globaux. Laissez vide pour désactiver. Exemple : 1 → première fenêtre.": "Global shortcuts. Leave blank to disable. Example: 1 → first window.",
    "Détection des fenêtres": "Window detection",
    "Synchronisation en temps réel et détection des demandes d’attention Windows": "Real-time synchronization and Windows attention request detection",
    "Rotation automatique sur les invitations de groupe ou d’échange": "Automatic rotation for group or trade invitations",
    " — module optionnel absent": " — optional module missing",
    "Annuler": "Cancel",
    "Appliquer": "Apply",
    "Classe": "Class",
    "Nom": "Name",
    "Alias": "Alias",
    "ID fenêtre": "Window ID",
    "Masqué": "Hidden",
    "Numéro": "Number",
    "À gauche": "Left",
    "Ligne 1": "Line 1",
    "Ligne 2 · gauche": "Line 2 · left",
    "Ligne 2 · droite": "Line 2 · right",
    "En haut à gauche": "Top left",
    "En haut au centre": "Top center",
    "En haut à droite": "Top right",
    "En bas à gauche": "Bottom left",
    "En bas au centre": "Bottom center",
    "En bas à droite": "Bottom right",
    "Quitter le mode compact": "Exit compact mode",
    "ROTATION  ·  déplacer ici  ·  glisser une ligne = ordre": "ROTATION  ·  drag here  ·  drag a row = order",
    "Aucune fenêtre en rotation": "No window in rotation",
    "Aucune fenêtre détectée": "No window detected",
    "Aucun résultat": "No result",
    "Aucune fenêtre ignorée": "No ignored window",
    "Avertissement de traduction": "Translation notice",
    "Cette traduction a été réalisée par une IA et peut contenir des erreurs. Vous pouvez signaler toute correction sur le dépôt GitHub officiel.": "This translation was generated by AI and may contain errors. You can report corrections on the official GitHub repository.",
    "Mode {game} · gestion locale des fenêtres": "{game} mode · local window management",
    "Avertissement de sécurité": "Security warning",
    "Avant d’utiliser Dofus Window Manager": "Before using Dofus Window Manager",
    (
        "Téléchargez l’exécutable uniquement depuis les Releases du dépôt GitHub officiel. "
        "Une copie reçue ailleurs peut avoir été modifiée pour contenir un virus, voler vos "
        "identifiants Ankama ou compromettre votre ordinateur."
    ): (
        "Download the executable only from the official GitHub repository Releases. "
        "A copy obtained elsewhere may have been modified to contain malware, steal your "
        "Ankama credentials, or compromise your computer."
    ),
    "Ouvrir le dépôt GitHub officiel": "Open the official GitHub repository",
    "Si le fichier provient d’une source non officielle ou vous paraît suspect :": "If the file comes from an unofficial source or appears suspicious:",
    (
        "• Ne l’exécutez pas, ou fermez-le immédiatement et déconnectez le PC du réseau.\n"
        "• Depuis un autre appareil de confiance, changez immédiatement les mots de passe "
        "Ankama et de l’adresse e-mail associée, puis activez la double authentification.\n"
        "• Lancez une analyse complète, idéalement hors ligne, avec Sécurité Windows ou un "
        "antivirus à jour, puis supprimez ou mettez le fichier en quarantaine.\n"
        "• Vérifiez les connexions et activités inhabituelles de vos comptes et contactez le "
        "support concerné en cas de doute."
    ): (
        "• Do not run it, or close it immediately and disconnect the PC from the network.\n"
        "• From another trusted device, immediately change the Ankama password and the "
        "associated email password, then enable two-factor authentication.\n"
        "• Run a full scan, preferably an offline scan, with Windows Security or an up-to-date "
        "antivirus, then delete or quarantine the file.\n"
        "• Review your accounts for unusual sign-ins or activity and contact the relevant "
        "support team if in doubt."
    ),
    "J’ai lu cet avertissement et je confirme utiliser une copie provenant du dépôt officiel.": "I have read this warning and confirm that I am using a copy from the official repository.",
    "Continuer": "Continue",
    "Enregistrement impossible": "Unable to save",
}

_ES: dict[str, str] = {
    "Choisir le jeu": "Elegir juego",
    "Sélectionne la version de Dofus :": "Selecciona la versión de Dofus:",
    "Mémoriser ce choix (pré-sélection au prochain lancement)": "Recordar esta opción (preseleccionada en el próximo inicio)",
    "Rechercher": "Buscar",
    "Actualisation automatique": "Actualización automática",
    "Aperçu interactif du profil par défaut": "Vista previa interactiva del perfil predeterminado",
    "Ce rapport peut être copié pour faciliter le dépannage.": "Este informe se puede copiar para facilitar el diagnóstico.",
    "Choisir un portrait…": "Elegir un retrato…",
    "Configuration de l’application": "Configuración de la aplicación",
    "Copier le rapport": "Copiar informe",
    "Exporter une copie…": "Exportar una copia…",
    "Exporter une sauvegarde complète…": "Exportar una copia de seguridad completa…",
    "Fermer": "Cerrar",
    "Icône": "Icono",
    "Importer un JSON…": "Importar JSON…",
    "Importer une sauvegarde…": "Importar una copia de seguridad…",
    "Ouvrir les journaux": "Abrir registros",
    "Profil sélectionné": "Perfil seleccionado",
    "Quitter": "Salir",
    "Recherche en cours…": "Buscando…",
    "Retirer": "Quitar",
    "Réinitialiser les réglages…": "Restablecer ajustes…",
    "Réinitialiser l’affichage…": "Restablecer visualización…",
    "Réinitialiser l’affichage": "Restablecer visualización",
    "Affichage réinitialisé": "Visualización restablecida",
    "Rétablir le thème, les colonnes, la notification et l’overlay par défaut ?\n\nLes profils, alias, portraits, icônes et raccourcis seront conservés.": "¿Restablecer el tema, las columnas, la notificación y el overlay predeterminados?\n\nSe conservarán los perfiles, alias, retratos, iconos y atajos.",
    "L’affichage par défaut est restauré et l’overlay est activé à sa position initiale.": "Se ha restaurado la visualización predeterminada y el overlay está activado en su posición inicial.",
    "Supprimer le profil": "Eliminar perfil",
    "État de Dofus Window Manager": "Estado de Dofus Window Manager",
    "Aperçu Stream Deck — profil 15 touches": "Vista previa de Stream Deck — perfil de 15 teclas",
    "Diagnostic": "Diagnóstico",
    "Gérer les profils": "Gestionar perfiles",
    "Sauvegarde et restauration": "Copia de seguridad y restauración",
    "Dofus Window Manager — Mode compact": "Dofus Window Manager — Modo compacto",
    "Confirmer": "Confirmar",
    "Erreur": "Error",
    "Installation impossible": "No se pudo instalar",
    "Portrait incompatible": "Retrato incompatible",
    "Sauvegarde invalide": "Copia de seguridad no válida",
    "Journaux": "Registros",
    "Mise à jour": "Actualización",
    "Charger profil": "Cargar perfil",
    "Exporter": "Exportar",
    "Démarrage Windows": "Inicio de Windows",
    "Rafraîchir": "Actualizar",
    "Fenêtres gérées": "Ventanas gestionadas",
    "Fenêtres ignorées": "Ventanas ignoradas",
    "Glissez un personnage pour modifier l’ordre ; glissez un en-tête pour déplacer une colonne.": "Arrastra un personaje para cambiar el orden; arrastra un encabezado para mover una columna.",
    "Navigation": "Navegación",
    "← Précédent": "← Anterior",
    "Suivant →": "Siguiente →",
    "↑ Monter": "↑ Subir",
    "↓ Descendre": "↓ Bajar",
    "⚠ Prochaine alerte ({count})": "⚠ Siguiente alerta ({count})",
    "Fenêtre sélectionnée": "Ventana seleccionada",
    "Sélectionnez un personnage": "Selecciona un personaje",
    "Personnaliser…": "Personalizar…",
    "Astuce : un élément (Terre, Feu, Eau, Air) ou un métier peut servir d’alias pour distinguer des pseudos proches ou deux personnages de même classe.": "Consejo: un elemento (Tierra, Fuego, Agua, Aire) o un oficio puede servir de alias para distinguir nombres parecidos o clases duplicadas.",
    "Ignorer": "Ignorar",
    "Réintégrer": "Restaurar",
    "Profils": "Perfiles",
    "Charger": "Cargar",
    "Enregistrer…": "Guardar…",
    "Gérer les profils…": "Gestionar perfiles…",
    "Application": "Aplicación",
    "Version de Dofus": "Versión de Dofus",
    "Paramètres…": "Ajustes…",
    "Mode compact": "Modo compacto",
    "Afficher l’overlay": "Mostrar overlay",
    "Masquer l’overlay": "Ocultar overlay",
    "Aperçu Stream Deck…": "Vista previa de Stream Deck…",
    "Diagnostic…": "Diagnóstico…",
    "Sauvegarder / restaurer…": "Guardar / restaurar…",
    "Installer le plugin Stream Deck": "Instalar plugin de Stream Deck",
    "Dépôt GitHub officiel": "Repositorio oficial de GitHub",
    "Conseils anti-phishing Ankama": "Consejos anti-phishing de Ankama",
    "Lien externe": "Enlace externo",
    "Le navigateur n’a pas pu être ouvert.\n\nAdresse à consulter :\n{url}": "No se pudo abrir el navegador.\n\nAbre manualmente esta dirección:\n{url}",
    "Rechercher une mise à jour…": "Buscar actualizaciones…",
    "Activité": "Actividad",
    "Afficher le journal": "Mostrar registro",
    "Masquer le journal": "Ocultar registro",
    "Paramètres": "Ajustes",
    "Général": "General",
    "Apparence": "Apariencia",
    "Raccourcis": "Atajos",
    "Général · mode {game}": "General · modo {game}",
    "Thème · mode {game}": "Tema · modo {game}",
    "Thème": "Tema",
    "Intervalle d’actualisation": "Intervalo de actualización",
    " secondes": " segundos",
    "Réduire dans la zone de notification à la fermeture": "Minimizar al área de notificación al cerrar",
    "Lancer avec Windows, directement dans la zone de notification": "Iniciar con Windows directamente en el área de notificación",
    "Rechercher automatiquement les mises à jour officielles": "Buscar automáticamente actualizaciones oficiales",
    "Inclure les versions bêta": "Incluir versiones beta",
    "Vérification quotidienne au maximum ; aucun téléchargement automatique.": "Comprobación diaria como máximo; sin descarga automática.",
    "Affichage en jeu": "Visualización en el juego",
    "Affichage en jeu · {game}": "Visualización en el juego · {game}",
    "Demandes d’attention": "Solicitudes de atención",
    "Clignotement léger sur l’application, l’overlay et le Stream Deck": "Parpadeo suave en la aplicación, el overlay y Stream Deck",
    "Désactivez le clignotement pour conserver uniquement la couleur orange et le repère !.": "Desactiva el parpadeo para conservar solo el color naranja y el indicador !.",
    "Afficher le personnage après chaque changement de fenêtre": "Mostrar el personaje después de cada cambio de ventana",
    "Position de la notification": "Posición de la notificación",
    "Durée": "Duración",
    "   Opacité": "   Opacidad",
    "Contenu de la notification": "Contenido de la notificación",
    "Afficher en permanence la rotation": "Mostrar siempre la rotación",
    "Opacité": "Opacidad",
    "   Orientation": "   Orientación",
    "Vertical": "Vertical",
    "Horizontal": "Horizontal",
    "Position X / Y": "Posición X / Y",
    "Largeur / hauteur": "Anchura / altura",
    "Largeur manuelle / hauteur": "Anchura manual / altura",
    " px · hauteur 0 = automatique": " px · altura 0 = automática",
    "Adapter automatiquement la largeur de l’overlay au contenu": "Adaptar automáticamente la anchura del overlay al contenido",
    "Contenu de l’overlay": "Contenido del overlay",
    "Par défaut : numéro à gauche, nom ligne 1, puis classe · alias ligne 2.": "Por defecto: número a la izquierda, nombre en la línea 1 y clase · alias en la línea 2.",
    "Verrouiller et ignorer les clics": "Bloquear e ignorar clics",
    "Déverrouillé : glissez l’en-tête pour déplacer l’overlay, une ligne pour la réordonner, ou la poignée ◢ pour le redimensionner.": "Desbloqueado: arrastra el encabezado para mover el overlay, una fila para reordenarla o el control ◢ para cambiar su tamaño.",
    "Afficher les portraits dans la notification, l’overlay et le Stream Deck": "Mostrar retratos en la notificación, el overlay y Stream Deck",
    "Faire légèrement clignoter les fenêtres demandant l’attention": "Hacer parpadear suavemente las ventanas que requieren atención",
    "Faire légèrement clignoter les fenêtres demandant l’attention (désactivé : orange et ! conservés)": "Hacer parpadear suavemente las ventanas que requieren atención (desactivado: se mantienen el naranja y !)",
    "Afficher les portraits dans la notification": "Mostrar retratos en la notificación",
    "Afficher les icônes dans la notification": "Mostrar iconos en la notificación",
    "Afficher les portraits dans l’overlay": "Mostrar retratos en el overlay",
    "Afficher les icônes dans l’overlay": "Mostrar iconos en el overlay",
    "Afficher les portraits sur le Stream Deck": "Mostrar retratos en Stream Deck",
    "Portrait de classe…": "Retrato de clase…",
    "Féminin": "Femenino",
    "Masculin": "Masculino",
    "Illustrations et icônes Dofus © Ankama Games. Projet communautaire non affilié.": "Ilustraciones e iconos de Dofus © Ankama Games. Proyecto comunitario no afiliado.",
    "Le portrait personnel est recadré et enregistré localement. Les illustrations et icônes de jeu intégrées sont la propriété d’Ankama Games. Dofus Window Manager est un projet communautaire non affilié à Ankama.": "Los retratos personales se recortan y guardan localmente. Las ilustraciones y los iconos del juego incluidos son propiedad de Ankama Games. Dofus Window Manager es un proyecto comunitario no afiliado a Ankama.",
    "Afficher les icônes officielles de caractéristiques ou de métiers sur ces mêmes affichages": "Mostrar iconos oficiales de características u oficios en esas vistas",
    "Afficher les icônes officielles de caractéristiques ou de métiers sur le Stream Deck": "Mostrar iconos oficiales de características u oficios en Stream Deck",
    "Raccourcis clavier": "Atajos de teclado",
    "Personnage suivant": "Personaje siguiente",
    "Personnage précédent": "Personaje anterior",
    "Ignorer la fenêtre": "Ignorar ventana",
    "Prochaine fenêtre en attente": "Siguiente ventana pendiente",
    "Actualiser la liste": "Actualizar lista",
    "Exemples : F5, Ctrl+Alt+R, Shift+F6 ou Win+F7": "Ejemplos: F5, Ctrl+Alt+R, Shift+F6 o Win+F7",
    "Accès direct par position (facultatif)": "Acceso directo por posición (opcional)",
    "Fenêtre {position}": "Ventana {position}",
    "Raccourcis globaux. Laissez vide pour désactiver. Exemple : 1 → première fenêtre.": "Atajos globales. Déjalo vacío para desactivar. Ejemplo: 1 → primera ventana.",
    "Détection des fenêtres": "Detección de ventanas",
    "Synchronisation en temps réel et détection des demandes d’attention Windows": "Sincronización en tiempo real y detección de solicitudes de atención de Windows",
    "Rotation automatique sur les invitations de groupe ou d’échange": "Rotación automática para invitaciones de grupo o intercambio",
    " — module optionnel absent": " — falta el módulo opcional",
    "Annuler": "Cancelar",
    "Appliquer": "Aplicar",
    "Classe": "Clase",
    "Nom": "Nombre",
    "Alias": "Alias",
    "ID fenêtre": "ID de ventana",
    "Masqué": "Oculto",
    "Numéro": "Número",
    "À gauche": "Izquierda",
    "Ligne 1": "Línea 1",
    "Ligne 2 · gauche": "Línea 2 · izquierda",
    "Ligne 2 · droite": "Línea 2 · derecha",
    "En haut à gauche": "Arriba a la izquierda",
    "En haut au centre": "Arriba al centro",
    "En haut à droite": "Arriba a la derecha",
    "En bas à gauche": "Abajo a la izquierda",
    "En bas au centre": "Abajo al centro",
    "En bas à droite": "Abajo a la derecha",
    "Quitter le mode compact": "Salir del modo compacto",
    "ROTATION  ·  déplacer ici  ·  glisser une ligne = ordre": "ROTACIÓN  ·  arrastrar aquí  ·  arrastrar fila = orden",
    "Aucune fenêtre en rotation": "No hay ventanas en la rotación",
    "Aucune fenêtre détectée": "No se detectaron ventanas",
    "Aucun résultat": "Sin resultados",
    "Aucune fenêtre ignorée": "No hay ventanas ignoradas",
    "Avertissement de traduction": "Aviso de traducción",
    "Cette traduction a été réalisée par une IA et peut contenir des erreurs. Vous pouvez signaler toute correction sur le dépôt GitHub officiel.": "Esta traducción fue generada por IA y puede contener errores. Puedes comunicar correcciones en el repositorio oficial de GitHub.",
    "Mode {game} · gestion locale des fenêtres": "Modo {game} · gestión local de ventanas",
    "Avertissement de sécurité": "Advertencia de seguridad",
    "Avant d’utiliser Dofus Window Manager": "Antes de usar Dofus Window Manager",
    (
        "Téléchargez l’exécutable uniquement depuis les Releases du dépôt GitHub officiel. "
        "Une copie reçue ailleurs peut avoir été modifiée pour contenir un virus, voler vos "
        "identifiants Ankama ou compromettre votre ordinateur."
    ): (
        "Descarga el ejecutable únicamente desde las Releases del repositorio oficial de GitHub. "
        "Una copia obtenida en otro lugar podría haber sido modificada para contener malware, "
        "robar tus credenciales de Ankama o comprometer tu ordenador."
    ),
    "Ouvrir le dépôt GitHub officiel": "Abrir el repositorio oficial de GitHub",
    "Si le fichier provient d’une source non officielle ou vous paraît suspect :": "Si el archivo procede de una fuente no oficial o parece sospechoso:",
    (
        "• Ne l’exécutez pas, ou fermez-le immédiatement et déconnectez le PC du réseau.\n"
        "• Depuis un autre appareil de confiance, changez immédiatement les mots de passe "
        "Ankama et de l’adresse e-mail associée, puis activez la double authentification.\n"
        "• Lancez une analyse complète, idéalement hors ligne, avec Sécurité Windows ou un "
        "antivirus à jour, puis supprimez ou mettez le fichier en quarantaine.\n"
        "• Vérifiez les connexions et activités inhabituelles de vos comptes et contactez le "
        "support concerné en cas de doute."
    ): (
        "• No lo ejecutes, o ciérralo inmediatamente y desconecta el PC de la red.\n"
        "• Desde otro dispositivo de confianza, cambia inmediatamente la contraseña de Ankama "
        "y la del correo electrónico asociado, y activa la autenticación de dos factores.\n"
        "• Ejecuta un análisis completo, preferiblemente sin conexión, con Seguridad de Windows "
        "o un antivirus actualizado, y elimina o pon el archivo en cuarentena.\n"
        "• Revisa si hay inicios de sesión o actividad inusual en tus cuentas y contacta con el "
        "soporte correspondiente si tienes dudas."
    ),
    "J’ai lu cet avertissement et je confirme utiliser une copie provenant du dépôt officiel.": "He leído esta advertencia y confirmo que utilizo una copia del repositorio oficial.",
    "Continuer": "Continuar",
    "Enregistrement impossible": "No se pudo guardar",
}

CATALOGS: Mapping[str, Mapping[str, str]] = {"en": _EN, "es": _ES}
TRANSLATABLE_TEXTS = frozenset({key for catalog in CATALOGS.values() for key in catalog})
_REVERSE_TRANSLATIONS = {
    translated: source
    for catalog in CATALOGS.values()
    for source, translated in catalog.items()
}


def tr(text: str, *, language: str | None = None, **values: Any) -> str:
    source = str(text)
    lang = normalize_language(language or _language)
    translated = CATALOGS.get(lang, {}).get(source, source)
    if values:
        try:
            return translated.format(**values)
        except (KeyError, ValueError):
            return translated
    return translated


def translated_variants(source: str) -> set[str]:
    return {source, *[str(catalog.get(source, source)) for catalog in CATALOGS.values()]}


def translation_source(text: str) -> str | None:
    value = str(text)
    if value in TRANSLATABLE_TEXTS:
        return value
    return _REVERSE_TRANSLATIONS.get(value)


def translation_notice(language: str) -> tuple[str, str]:
    lang = normalize_language(language)
    return (
        tr("Avertissement de traduction", language=lang),
        tr(
            "Cette traduction a été réalisée par une IA et peut contenir des erreurs. Vous pouvez signaler toute correction sur le dépôt GitHub officiel.",
            language=lang,
        ),
    )


def install_messagebox_translation(messagebox_module) -> None:
    if getattr(messagebox_module, "_dwm_i18n_installed", False):
        return
    for method_name in ("showinfo", "showwarning", "showerror", "askyesno", "askokcancel", "askretrycancel"):
        original = getattr(messagebox_module, method_name, None)
        if original is None:
            continue

        def localized(*args, _original=original, **kwargs):
            translated_args = list(args)
            for index in range(min(2, len(translated_args))):
                source = translation_source(str(translated_args[index]))
                if source:
                    translated_args[index] = tr(source)
            return _original(*translated_args, **kwargs)

        setattr(messagebox_module, method_name, localized)
    messagebox_module._dwm_i18n_installed = True
