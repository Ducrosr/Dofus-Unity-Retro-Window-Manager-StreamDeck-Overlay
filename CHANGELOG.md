# Historique

## 2.20.0-beta.2 — préversion Windows

- écritures atomiques des réglages, des profils et des exports JSON afin qu’une interruption ne laisse jamais un fichier partiellement remplacé ;
- conservation automatique de la dernière version valide des réglages dans `settings.json.bak` et restauration transparente depuis cette copie si le fichier principal est illisible ;
- récupération automatique du mode compact et de l’overlay lorsqu’un changement d’écran ou de disposition les place hors de toute zone visible, tout en conservant les coordonnées négatives valides des configurations multi-écrans ;
- adaptation automatique de la largeur de l’overlay et de la notification à leur contenu, avec conservation d’un mode manuel pour l’overlay ;
- réglages indépendants, activés par défaut, pour afficher ou masquer les portraits et les icônes dans la notification, l’overlay et le Stream Deck ;
- mise à jour en place du focus dans l’application, le mode compact et l’overlay afin d’éviter leur reconstruction et le clignotement visible à chaque changement de personnage ;
- regroupement des rafales de navigation vers leur destination finale et remplacement des notifications en attente par la plus récente, sans accumulation retardée ;
- ajout d’une file chronologique des demandes d’attention : `!1` désigne la plus ancienne, les signaux répétés ne modifient pas l’ordre et un focus échoué conserve l’alerte ;
- ajout de l’action **Prochaine alerte** dans l’application, le mode compact, l’overlay déverrouillé, le raccourci global F8 et le plugin Stream Deck 0.7.0 ;
- publication du rang et du nombre d’alertes sur le pont local afin de synchroniser l’application, l’overlay et les touches Stream Deck ;

## 2.20.0-beta.1 — bêta source

- synchronisation immédiate de chaque changement d’ordre depuis l’application vers l’overlay et le Stream Deck, indépendamment de la reconstruction du tableau principal ;
- correction de la mise en page sans fenêtre détectée : la vignette vide est désormais contrainte en pixels et ne peut plus étirer l’interface ;
- rééquilibrage des largeurs entre les tableaux et les commandes, avec défilement horizontal propre à chaque tableau et défilement vertical global amélioré ;
- ajout d’états explicites **Aucune fenêtre détectée**, **Aucune fenêtre ignorée** et **Aucun résultat** ;
- mise à disposition des douze thèmes dans les deux modes : les palettes Unity peuvent être utilisées en Retro et le thème Retro en Unity ; Standard reste le défaut Unity et Retro le défaut Dofus Retro ;
- déplacement du réglage de clignotement dans une section **Demandes d’attention** immédiatement visible ;
- ajout d’un bouton **Réinitialiser l’affichage…** dans l’interface principale et dans le pied fixe des paramètres, sans suppression des profils, alias, portraits, icônes ou raccourcis ;
- ajout d’un léger clignotement pour les demandes d’attention, désactivable sans retirer la couleur orange ni le repère `!` ;
- mise à l’échelle dynamique du texte de l’overlay selon sa largeur, sa hauteur et le nombre de personnages ;
- réglages indépendants pour afficher les portraits dans la notification, l’overlay et le Stream Deck ;
- ajout de 38 portraits de classes, 39 icônes officielles de caractéristiques et 20 icônes officielles de métiers fournies par l’utilisateur, sélectionnables depuis la personnalisation des personnages ;
- suppression du catalogue de symboles génériques créé pour le projet : seules les icônes officielles intégrées sont désormais proposées ;
- ajout dans l’application et la documentation d’une attribution explicite à Ankama Games pour les illustrations et icônes de jeu intégrées ;
- ajout d’un réglage d’opacité indépendant pour la notification de changement de fenêtre ;
- ajout des langues français, anglais et espagnol avec sélection directe par drapeaux ;
- avertissement explicite indiquant que les traductions anglaise et espagnole ont été réalisées avec l’aide d’une IA et peuvent contenir des erreurs ;
- ajout de onze palettes Unity : Standard, Bonta, Brakmar, Tribute, Gold and Steel, Belladone, Unicorn, Emerald Mine, Sufokia, Pandala et Wabbit ;
- suppression des anciens thèmes externes ; Standard devient le défaut Unity et Retro le défaut Retro, avec une préférence mémorisée séparément pour chaque version du jeu ;
- transmission du thème et de la langue au plugin Stream Deck 0.6.1 ; les touches Personnage et les actions dynamiques reprennent automatiquement la palette active ;
- ajout dans l’application de liens directs vers le dépôt GitHub officiel et la page anti-phishing du support Ankama ;
- renommage du dépôt en **Dofus-Unity-Retro-Window-Manager-StreamDeck-Overlay** afin de refléter les deux versions du jeu, le plugin Stream Deck et les overlays ;
- mise à jour des README français, anglais et espagnol avec les fonctions 2.20, les thèmes, les visuels et les recommandations de sécurité ;

- refonte du thème **Retro — parchemin et orange** d’après la palette historique : fonds crème/kaki, en-têtes brun-charbon et actions orange, sans reprendre d’élément graphique du jeu ;
- ajout d’un **mode compact** toujours au premier plan, limité aux personnages inclus dans la rotation et directement cliquable ;
- ajout d’un bouton **Quitter le mode compact** restaurant immédiatement l’interface complète ;
- ajout d’une notification non interactive après chaque changement de fenêtre, affichant la position, le nom ou alias et la classe du personnage ;
- choix de la position de la notification dans la fenêtre Dofus ciblée et de sa durée d’affichage ;
- ajout d’un overlay transparent permanent présentant la rotation et mettant en évidence le personnage actif ;
- déplacement de l’overlay par glisser-déposer, coordonnées et opacité personnalisables, ainsi qu’un verrouillage permettant aux clics de traverser l’overlay ;
- contenu de l’overlay personnalisable sur quatre emplacements ; par défaut : numéro à gauche, nom ligne 1, classe et alias ligne 2 ;
- suivi du premier plan lorsque le mode compact ou l’overlay est visible afin de refléter aussi un changement manuel de fenêtre ;
- ajout d’un défilement vertical dans les paramètres pour conserver l’accès aux nouvelles options sur les écrans courts ou avec une mise à l’échelle élevée ;
- ajout d’un vérificateur de mise à jour facultatif, limité aux Releases du dépôt GitHub officiel ;
- vérification automatique différée et silencieuse, au maximum une fois toutes les 24 heures ;
- ajout d’une recherche manuelle dans le panneau Application et de préférences pour désactiver le contrôle automatique ou exclure les versions bêta ;
- aucun téléchargement ni aucune installation automatique : l’utilisateur choisit explicitement s’il souhaite ouvrir la Release officielle ;
- validation stricte des numéros de version et reconstruction locale de l’adresse officielle afin de ne jamais suivre un lien arbitraire reçu du réseau ;
- ajout de la version de publication et de l’état du vérificateur dans le diagnostic.
- détection au mieux des demandes d’attention Windows par événement d’accessibilité et clignotement de la barre des tâches ; l’état reste actif jusqu’au focus réel de la fenêtre ;
- signalement orange avec repère `!` dans l’application, le mode compact, l’overlay et le plugin Stream Deck ;
- ajout d’un portrait local par personnage, recadré et stocké dans les réglages, sans envoi réseau ;
- remplacement de l’ancien catalogue de symboles génériques par les icônes officielles intégrées ;
- affichage facultatif des portraits et icônes dans l’application, la notification, l’overlay et le Stream Deck ;
- personnalisation du contenu de la notification avec les mêmes quatre emplacements que l’overlay ;
- réorganisation des personnages directement dans l’overlay par flèches ou glisser-déposer avec aperçu de destination ;
- redimensionnement direct de l’overlay par une poignée et mémorisation des dimensions ;
- plugin Stream Deck 0.6.1.

## 2.19.0

- ajout d'un exécutable Windows 64 bits standard, sans détection visuelle Retro facultative, pour les utilisateurs ne souhaitant pas installer Python ;
- publication de l'empreinte SHA-256 du binaire et ajout des instructions de vérification ;

- ajout d’un défilement vertical global pour conserver l’accès à tous les boutons lorsque la fenêtre est réduite ou que l’affichage Windows utilise une mise à l’échelle élevée ;
- la molette fait défiler l’interface sauf lorsqu’elle se trouve au-dessus d’un tableau ou du journal, qui conservent leur propre défilement ;
- ajout d’un aperçu interactif du profil Stream Deck 15 touches depuis le panneau Application ;
- l’aperçu reprend l’ordre courant des huit personnages, les quatre lignes de texte par défaut et les états actif, ignoré ou indisponible ;
- les touches de l’aperçu permettent de tester directement le focus, la rotation, le changement d’ordre, l’actualisation et l’exclusion temporaire ;
- migration du dépôt public vers l’architecture modulaire actuelle, avec guides d’installation, d’utilisation et de compilation ;
- ajout d’une politique de sécurité, de formulaires de bug et d’amélioration, d’un guide de contribution et d’une intégration continue Windows/Python/Stream Deck ;
- aucun changement du plugin Stream Deck n’est requis : il reste en version 0.4.1.

## 2.18.3

- remplacement du dernier recours `SW_MINIMIZE` par `SW_FORCEMINIMIZE`, prévu par Windows pour minimiser une fenêtre appartenant à un autre thread ;
- la réduction de Stream Deck n’est plus annulée lorsque la préparation préalable de l’ordre Z est refusée ;
- ajout de deux replis successifs : message système `WM_SYSCOMMAND/SC_MINIMIZE`, puis appel synchrone `ShowWindow/SW_FORCEMINIMIZE` ;
- reconnaissance de Stream Deck par le nom du processus ou par le titre exact de sa fenêtre ;
- nouvelle promotion temporaire au premier plan de Dofus après la réduction effective de Stream Deck ;
- erreurs de focus enrichies avec la fenêtre bloquante et le résultat de chaque méthode de réduction ;
- ajout d’un secours côté plugin lorsque Stream Deck et son plugin fonctionnent à un niveau de privilèges supérieur au manager : le plugin réduit sa propre application puis répète la commande une fois ;
- plugin Stream Deck 0.4.1, à réinstaller depuis le bouton intégré de l’application.

## 2.18.2

- ajout d’un dernier recours ciblé lorsque l’application Stream Deck garde le premier plan : Dofus est préparé juste derrière elle puis seule la fenêtre Stream Deck est réduite afin que Windows active le client demandé ;
- détection stricte du processus `StreamDeck.exe` pour ne jamais réduire une autre application au premier plan ;
- ajout du sélecteur **Version de Dofus** dans le panneau Application pour basculer immédiatement entre Unity et Retro sans redémarrer ;
- arrêt et redémarrage du bon WinEventHook, arrêt de la capture visuelle hors Retro, nettoyage des anciens handles et nouveau scan automatique au changement de mode ;
- exclusion des résultats tardifs provenant d’un scan lancé dans le mode précédent ;
- conservation des profils, alias et préférences pendant la bascule ;
- aucun changement du plugin Stream Deck n’est requis : il reste en version 0.4.0.

## 2.18.1

- correction de la mise au premier plan d’une fenêtre Dofus lorsque l’application Stream Deck est active ;
- rattachement temporaire du thread de Dofus Window Manager aux files d’entrée de la fenêtre au premier plan et de la fenêtre Dofus ciblée ;
- ajout de signatures Win32 64 bits explicites pour éviter la troncature des identifiants de fenêtre ;
- vérification effective de la fenêtre au premier plan avant de confirmer une commande Stream Deck ;
- conservation du personnage réellement actif lorsque Windows refuse malgré tout le changement de fenêtre, afin d’éviter un faux changement visuel sur les touches ;
- ajout de deux solutions de repli ciblées pour les fenêtres Unity refusant l’activation Windows standard ;
- aucun changement du plugin Stream Deck n’est requis : la correction se situe entièrement dans l’application.

## 2.18.0

- ajout d’une icône dans la zone de notification avec les commandes Afficher, Actualiser et Quitter ;
- réduction dans la zone de notification à la fermeture, désactivable dans les paramètres ;
- ajout du démarrage automatique facultatif avec Windows, directement dans la zone de notification et sans redemander le mode Unity/Retro ;
- ajout d’une page de diagnostic copiable indiquant les versions, l’état du pont local, la dernière activité Stream Deck, les fenêtres détectées et les dossiers de journaux ;
- ajout d’un export/import complet pour les réglages, profils, alias et l’ordre courant, sans supprimer les autres profils locaux lors d’une restauration ;
- ajout d’une réinitialisation sûre des réglages, sans suppression des profils ;
- ajout de couleurs de bordure persistantes par personnage dans le plugin Stream Deck : automatique, Terre, Feu, Eau, Air, Neutre et Violet ;
- mise à jour du profil Stream Deck fourni avec la nouvelle préférence de couleur ;
- plugin Stream Deck 0.4.0.

## 2.17.1

- correction de la suppression d’un alias : l’application publie immédiatement un alias vide et le bouton Stream Deck affiche désormais `—` au lieu de conserver l’ancienne valeur ;
- séparation stricte du nom et de l’alias dans l’état transmis au plugin ;
- alias vierge par défaut et suppression des entrées vides lors de l’enregistrement ou du chargement d’un profil ;
- ajout de conseils dans l’application et dans les propriétés Stream Deck pour utiliser un élément ou un métier comme alias distinctif ;
- ajout du thème intégré **Sombre moderne**, désormais sélectionné par défaut et appliqué aux installations existantes qui utilisaient l’ancien thème par défaut Equilux ;
- plugin Stream Deck 0.3.5.

## 2.17.0

- réorganisation de l’interface principale en quatre groupes : navigation, fenêtre sélectionnée, profils et application ;
- déplacement de l’import, de l’export JSON et de la suppression dans une fenêtre **Gérer les profils** ;
- clarification de la différence entre l’enregistrement interne d’un profil et son export portable ;
- confirmation avant le remplacement d’un profil existant ;
- journal masqué par défaut et affichable à la demande afin d’alléger la fenêtre ;
- nouvelle présentation des paramètres par sections ;
- suppression complète de l’option de rotation sur les popups lorsque le mode Unity est utilisé ;
- ajout du bouton **Installer le plugin Stream Deck**, compatible avec les sources et l’exécutable PyInstaller ;
- inclusion automatique du paquet Stream Deck dans la construction de l’exécutable.

## 2.16.4

- ajout de la touche Stream Deck **Lancer / afficher** dans le dernier emplacement vacant du profil 15 touches ;
- enregistrement automatique de la commande de lancement réelle, compatible avec l’exécutable et le projet Python ;
- restauration au premier plan de l’instance déjà ouverte sans lancer de doublon ;
- aperçu visuel du glisser-déposer des personnages avec surbrillance de la destination et indication avant/après ;
- aperçu visuel du déplacement des colonnes directement dans leurs en-têtes.

## 2.16.3

- correction de la structure interne du profil Stream Deck préconfiguré ;
- association correcte entre les identifiants de pages et leurs dossiers internes afin que le profil soit réellement importé après confirmation ;
- ajout d’un test de cohérence du format `.streamDeckProfile`.

## 2.16.2

- ajout d’un profil Stream Deck 15 touches proposé automatiquement lors de la première installation du plugin ;
- préconfiguration des huit touches Personnage et des actions **Monter**, **Descendre**, **Ignorer / réintégrer**, **Actualiser**, **Précédent** et **Suivant** ;
- le profil installé reste entièrement modifiable par l’utilisateur ;
- nouvelle mise en page par défaut des touches Personnage : numéro ligne 1, nom ligne 2, classe ligne 3 et alias ligne 4 ;
- conservation de la mise en page des anciennes touches déjà configurées.

## 2.16.1

- ajout des actions Stream Deck **Monter le personnage** et **Descendre le personnage** ;
- ciblage prioritaire de la fenêtre Dofus au premier plan, avec repli sur le personnage actif du gestionnaire ;
- synchronisation immédiate du nouvel ordre dans l’application et sur les touches Stream Deck ;
- arrêt à la première et à la dernière place, sans boucle automatique ;
- refus explicite du déplacement d’une fenêtre ignorée, qui doit d’abord être réintégrée.

## 2.16.0

- remplacement des listes textuelles par des tableaux avec quatre colonnes indépendantes : **Classe**, **Nom**, **Alias** et **ID fenêtre** ;
- l’alias ne remplace plus la classe dans l’interface ;
- réorganisation des colonnes par glisser-déposer de leurs en-têtes, avec mémorisation dans les paramètres ;
- réorganisation des personnages par glisser-déposer dans **Fenêtres gérées** ;
- conservation des boutons **Haut** et **Bas** comme alternative au glisser-déposer ;
- synchronisation de l’ordre des personnages avec les positions des touches Stream Deck ;
- les préférences de texte restent liées aux personnages lorsqu’ils changent de touche ;
- les fenêtres ignorées restent ancrées à leur touche et exclues de la rotation.

## 2.15.1

- correction du rendu des textes personnalisés sur les touches Stream Deck : le SVG dynamique est désormais transmis sous forme d’URL d’image encodée ;
- association des touches à l’identité stable du personnage au lieu de sa seule position ;
- conservation des fenêtres ignorées dans l’état publié au Stream Deck et dans sa liste de personnages ;
- une fenêtre ignorée reste activable directement par sa touche, mais est exclue des actions **Suivant** et **Précédent** ;
- migration automatique des anciennes associations enregistrées par numéro de case ;
- ajout d’un repère rouge sur la touche d’un personnage ignoré et affichage de « — » pour sa position de rotation.

## 2.15.0

- ajout de l’action Stream Deck **Ignorer / réintégrer** pour basculer la fenêtre Dofus actuellement au premier plan ;
- repli sur le personnage actif du gestionnaire lorsqu’aucune fenêtre Dofus n’est au premier plan ;
- correction de l’action **Actualiser**, qui attend désormais la fin effective du scan avant de confirmer ;
- mise en file d’un nouveau scan lorsqu’une actualisation forcée est demandée pendant un scan déjà actif ;
- ajout d’un compteur de scans terminés au pont local afin de synchroniser correctement le plugin ;
- mise en page personnalisable par personnage pour le numéro de position, le nom, l’alias et la classe ;
- chaque texte peut être masqué ou placé sur l’une des quatre lignes du bouton ;
- regroupement automatique des éléments affectés à la même ligne et rendu dynamique adapté à l’état actif.

## 2.14.5

- séparation stricte du pseudo détecté et de l’alias dans le plugin Stream Deck ;
- correction du cas où un ancien alias, par exemple `Pandala`, remplaçait le véritable nom `Nealla` dans la liste ;
- ajout d’**Alias** comme troisième mode d’affichage persistant par personnage ;
- repli automatique sur le nom du personnage lorsqu’aucun alias n’est défini ;
- ajout de l’alias dans la liste de sélection lorsqu’il existe, sans masquer le pseudo ni la classe.

## 2.14.4

- stockage persistant du choix **Nom / Classe** par personnage dans les réglages globaux du plugin ;
- la préférence suit désormais le pseudo lorsque l’ordre des fenêtres Dofus est modifié ;
- migration automatique des choix déjà configurés sur les touches Stream Deck ;
- synchronisation du sélecteur **Affichage** avec la préférence du personnage actuellement associé à la case.

## 2.14.3

- correction de la détection du nom lorsque Dofus Unity place la classe avant le personnage dans le titre ;
- prise en charge des deux ordres `Nom - Classe - version` et `Classe - Nom - version` ;
- ajout d’un secours côté Stream Deck lorsque un ancien alias ou un ancien scan confond le nom et la classe.

## 2.14.2

- extraction explicite de la classe du personnage depuis le titre des fenêtres Dofus ;
- ajout du réglage Stream Deck **Affichage**, configurable indépendamment sur chaque touche ;
- choix entre le nom ou la classe, avec repli automatique sur le nom lorsque la classe est indisponible ;
- affichage du nom et de la classe dans la liste déroulante des personnages.

## 2.14.1

- remplacement du curseur de sélection Stream Deck par une liste déroulante affichant les personnages détectés ;
- mise à jour automatique de cette liste lorsque des fenêtres apparaissent, disparaissent ou changent d’alias ;
- ajout d’un état explicite lorsque Dofus Window Manager est fermé ou qu’aucune fenêtre n’est détectée.

## 2.14.0

- ajout d’un pont HTTP local limité à `127.0.0.1:32145`, sans nouvelle dépendance Python ;
- ajout d’un plugin Stream Deck officiel en TypeScript avec une touche configurable par case/personnage ;
- affichage automatique du pseudo ou de l’alias et indication visuelle du personnage actif ;
- ajout des actions Stream Deck suivant, précédent et actualiser ;
- traitement des commandes Stream Deck sur le thread de l’interface afin de préserver la sûreté de Tkinter ;
- validation des requêtes JSON, refus des origines navigateur et arrêt propre du serveur local ;
- ajout de tests unitaires du pont local et d’un paquet `.streamDeckPlugin` prêt à installer.

## 2.13.1

- correction du type de callback natif passé à `EnumWindows` : il doit être créé avec `ctypes.WINFUNCTYPE`, et non lu depuis `ctypes.wintypes` ;
- le scanner remonte désormais l’erreur Win32 dans l’interface au lieu de transformer silencieusement toute panne en liste vide ;
- ajout de tests de régression sur le callback et l’énumération filtrée des fenêtres.

## 2.13.0

- correction du gestionnaire d’événements de popup Retro, auparavant imbriqué dans une autre méthode et inutilisable ;
- correction de la lecture de `PopupEvent` et du ciblage de la liste `_managed_order` ;
- arrêt propre de la capture visuelle à la fermeture ;
- arrêt propre du thread WinEventHook et libération des captures quand l’option popup est désactivée ;
- suppression du journal de diagnostic périodique et d’anciens fragments inutilisés ;
- suppression du secours `pywinauto/comtypes` au profit de l’énumération Win32 native déjà utilisée ;
- séparation des dépendances essentielles, visuelles facultatives et de développement ;
- construction PyInstaller isolée et reproductible, avec une variante légère ou une variante popup ;
- ajout de tests unitaires, d’une configuration Ruff et d’un `.gitignore` ;
- migration des anciens pickles limitée aux données primitives, sans chargement de classes arbitraires ;
- archive nettoyée des environnements, builds, caches, icônes inutilisées et données personnelles.
