# Guide d’utilisation

## Vue d’ensemble

L’interface principale comporte deux tableaux et quatre groupes de commandes :

- **Fenêtres gérées** : personnages inclus dans la rotation ;
- **Fenêtres ignorées** : personnages toujours détectés mais exclus de Suivant/Précédent ;
- **Navigation** : rotation et changement d’ordre ;
- **Fenêtre sélectionnée** : alias, portrait, icône et statut ignoré ;
- **Profils** : enregistrement et restauration d’une formation ;
- **Application** : mode Unity/Retro, mode compact, overlay, paramètres, aperçu Stream Deck, diagnostic, sauvegarde, installation du plugin et mises à jour.

La barre verticale à droite conserve l’accès aux commandes lorsque la fenêtre est courte ou que Windows utilise une mise à l’échelle élevée. La molette garde la priorité au tableau ou au journal lorsqu’elle se trouve au-dessus.

Chaque tableau possède aussi une barre horizontale lorsque ses colonnes dépassent la largeur disponible. Si un tableau vide ne peut pas défiler, la molette reprend automatiquement le défilement vertical de l’interface complète.

## Détecter les personnages

1. Ouvrez les clients Dofus.
2. Sélectionnez Unity ou Retro dans **Version de Dofus**.
3. Cliquez sur **Rafraîchir**.
4. Contrôlez le nom et la classe dans le tableau.

Le mode Unity cible les fenêtres Unity. Le mode Retro combine la classe de fenêtre Chromium et le marqueur Dofus Retro du titre afin d’éviter les faux positifs provenant d’autres applications Chromium.

## Passer d’un personnage à l’autre

- **F5** ou **Suivant** active le personnage suivant ;
- **F6** ou **Précédent** active le personnage précédent ;
- **F8**, **Prochaine alerte** ou l’action Stream Deck correspondante active la plus ancienne demande d’attention ;
- un clic sur une touche Personnage du Stream Deck active directement sa fenêtre.

La ligne active est mise en évidence dans l’application. Le bouton Stream Deck actif utilise un état vert.

Lorsqu’une fenêtre Dofus fait clignoter son bouton dans la barre des tâches Windows, elle passe en orange avec un repère `!` dans l’application, le mode compact, l’overlay et le Stream Deck. Plusieurs demandes forment une file chronologique : `!1` est la prochaine, puis `!2`, etc. Un signal répété pour la même fenêtre ne change pas sa place. Le bouton **Prochaine alerte** indique le nombre restant ; il est également disponible dans le mode compact, l’en-tête de l’overlay déverrouillé et parmi les actions Stream Deck. Un léger clignotement rend l’alerte plus visible ; il peut être désactivé dans **Paramètres → Demandes d’attention** sans retirer la couleur orange ni le repère. L’alerte n’est retirée qu’après un focus réussi. La détection est volontairement limitée aux demandes d’attention Windows : un événement affiché uniquement à l’intérieur du jeu, sans clignotement ni événement d’accessibilité, peut ne pas être détecté.

## Modifier l’ordre

Quatre méthodes sont disponibles :

- glisser une ligne dans **Fenêtres gérées** ;
- sélectionner une ligne puis utiliser **Monter** ou **Descendre** ;
- utiliser les touches Monter/Descendre du Stream Deck.
- utiliser les flèches ou glisser une ligne dans l’overlay déverrouillé.

Pendant un glisser-déposer, la destination est surlignée et la barre d’état précise si le dépôt se fera avant ou après. L’ordre est immédiatement transmis au Stream Deck : les personnages changent donc de touche pour rester cohérents avec la liste.

## Alias, portrait et icône

Sélectionnez un personnage puis choisissez **Personnaliser…**. L’alias possède sa propre colonne et ne remplace ni le nom ni la classe.

Un alias court améliore la lecture sur le Stream Deck, notamment :

- Terre, Feu, Eau ou Air ;
- Mineur, Paysan ou Alchimiste ;
- un rôle d’équipe ;
- une indication distinguant deux personnages de même classe.

Supprimer le contenu rend l’alias vierge. La touche Stream Deck affiche alors un tiret lorsque la ligne Alias est visible.

Le même panneau permet de choisir un portrait PNG, JPEG, WebP ou BMP, ou l’un des 38 portraits de classes fournis. L’image est recadrée en carré, réduite puis enregistrée localement dans les réglages ; elle n’est envoyée à aucun service. **Retirer** restaure la vignette générée avec l’initiale du personnage.

Une icône peut compléter le portrait : le catalogue comprend uniquement les ressources officielles fournies, soit 39 icônes de caractéristiques et 20 icônes de métiers issues de l’univers Dofus. Les anciens symboles génériques créés pour le projet ont été retirés. Les illustrations et icônes de jeu intégrées sont la propriété d’**Ankama Games** ; Dofus Window Manager reste un projet communautaire indépendant, non affilié à Ankama. Ces ressources sont isolées dans `assets/ankama` et ne sont pas couvertes par la licence GPL-3.0 du code. Les portraits personnalisés doivent être des images que l’utilisateur est autorisé à employer.

## Ignorer une fenêtre

Ignorer ne supprime pas le personnage et ne retire pas son bouton Stream Deck. Cette action l’exclut seulement de la rotation Suivant/Précédent.

- sélectionnez une fenêtre puis cliquez sur **Ignorer** ;
- utilisez F7 pour basculer la fenêtre courante ;
- ou utilisez la touche **Ignorer/réintégrer** du Stream Deck.

Une fenêtre ignorée peut toujours être activée directement. Elle conserve sa case Stream Deck et affiche un repère rouge. Réintégrez-la avant de modifier sa position.

## Profils

Un profil enregistre l’ordre des personnages et leurs alias en les associant à leur pseudo plutôt qu’à un identifiant de fenêtre temporaire.

- **Enregistrer…** conserve le profil dans les données locales ;
- **Charger** restaure la formation sélectionnée ;
- **Gérer les profils…** regroupe l’import, l’export et la suppression.

Exporter une copie JSON sert au transfert vers un autre PC. Ce n’est pas un second mécanisme d’enregistrement interne.

## Sauvegarde complète

**Sauvegarder/restaurer…** exporte dans un seul fichier :

- les réglages ;
- les profils ;
- les alias ;
- l’ordre de la session.

Les préférences internes des touches Stream Deck restent gérées par Stream Deck et ne sont pas incluses.

Les réglages, les profils et les exports JSON sont écrits dans un fichier temporaire puis remplacés en une seule opération : une fermeture ou une interruption pendant l’enregistrement ne peut donc pas laisser un fichier partiellement écrit. L’application conserve aussi la dernière version JSON valide des réglages dans `settings.json.bak`. Si `settings.json` devient illisible, cette copie est chargée automatiquement au prochain démarrage.

## Paramètres et zone de notification

Les paramètres permettent notamment de personnaliser les raccourcis, l’actualisation, le thème, la réduction dans la zone de notification et le démarrage avec Windows.

La section **Demandes d’attention**, placée près du haut des paramètres, permet d’activer ou de désactiver le léger clignotement. La couleur orange et le repère `!` restent actifs dans les deux cas.

Trois petits drapeaux en haut de l’interface sélectionnent immédiatement le français, l’anglais ou l’espagnol. Le français reste la langue par défaut. Les traductions anglaise et espagnole ont été réalisées avec l’aide d’une IA et peuvent contenir des erreurs ; un avertissement le rappelle lors de leur sélection.

Les douze thèmes sont disponibles dans les deux modes : **Standard**, **Bonta**, **Brakmar**, **Tribute**, **Gold and Steel**, **Belladone**, **Unicorn**, **Emerald Mine**, **Sufokia**, **Pandala**, **Wabbit** et **Retro**. **Standard** reste le choix par défaut en Unity et **Retro** en Dofus Retro. L’application mémorise un choix distinct pour chaque version du jeu.

Le thème **Retro — parchemin et orange** reprend les tons historiques de l’interface : crème parchemin, beige/kaki, brun-charbon et orange vif. Il ne contient aucune image ou ressource extraite du jeu.

La fenêtre des paramètres possède son propre défilement vertical. La molette permet donc d’atteindre les options d’affichage en jeu même avec une mise à l’échelle Windows élevée.

Le bouton **Réinitialiser l’affichage…**, disponible dans le panneau Application et dans le pied fixe des paramètres, restaure le thème, l’ordre des colonnes, la notification et la géométrie de l’overlay. Il conserve les profils, alias, portraits, icônes et raccourcis. La réinitialisation complète reste disponible dans **Sauvegarder/restaurer…**.

La recherche automatique des mises à jour est différée au démarrage et limitée à une tentative toutes les 24 heures. Elle peut être désactivée. L’option **Inclure les versions bêta** détermine le canal consulté aussi bien pour la recherche automatique que manuelle.

Le bouton **Rechercher une mise à jour…** interroge uniquement les Releases du dépôt GitHub officiel. Une nouvelle version détectée est signalée dans l’application ; le gestionnaire ne télécharge et n’installe jamais de fichier automatiquement. Il ouvre la page officielle uniquement après confirmation.

Par défaut, fermer la fenêtre réduit l’application dans la zone de notification pour conserver les raccourcis et le pont Stream Deck. Le menu de l’icône permet d’afficher, d’actualiser ou de quitter réellement l’application.

## Mode compact

**Application → Mode compact** masque l’interface complète et ouvre une petite fenêtre toujours au premier plan. Elle contient uniquement les personnages inclus dans la rotation, avec le personnage actuel en surbrillance.

- double-cliquez sur une ligne, ou sélectionnez-la puis appuyez sur Entrée, pour activer le personnage ;
- déplacez et redimensionnez normalement la fenêtre ; sa géométrie est mémorisée ;
- utilisez **Quitter le mode compact** ou fermez la fenêtre pour revenir à l’interface complète.

Si le moniteur qui contenait le mode compact n’est plus disponible au prochain lancement, la fenêtre est automatiquement recentrée sur l’écran le plus proche et sa position corrigée est mémorisée.

## Notification après un changement de fenêtre

Après un changement réussi depuis les raccourcis, l’application, le Stream Deck, le mode compact ou l’overlay, une courte notification affiche par défaut :

- la position dans la rotation ;
- le nom ou l’alias lorsqu’il existe ;
- le pseudo et la classe en complément.

La notification est activée par défaut. Elle ne prend pas le focus, ignore les clics, adapte automatiquement sa largeur aux informations visibles et disparaît automatiquement. Dans **Paramètres → Affichage en jeu**, elle peut être désactivée, placée dans l’un des six emplacements de la fenêtre Dofus ciblée, affichée entre 600 et 5 000 ms et réglée entre 35 et 100 % d’opacité. Son emplacement gauche et ses deux lignes utilisent les mêmes choix **Numéro**, **Nom**, **Classe**, **Alias** ou **Masqué** que l’overlay. Le portrait et l’icône peuvent chacun être activés ou masqués ; l’un peut rester visible sans l’autre.

## Overlay de rotation

**Afficher l’overlay** ouvre une liste transparente toujours visible, comparable à une liste de participants en communication. Il est masqué par défaut. Seuls les personnages inclus dans la rotation apparaissent et le personnage actuel est mis en évidence.

Lorsqu’il est déverrouillé :

- glissez l’en-tête pour déplacer l’overlay ;
- glissez une ligne vers une autre position, ou utilisez ses flèches ▲/▼, pour modifier l’ordre de rotation ;
- étirez la poignée ◢ dans l’angle inférieur droit pour passer en largeur manuelle et ajuster ses dimensions ;
- cliquez brièvement sur un personnage pour activer sa fenêtre ;
- la position, l’ordre et les dimensions sont mémorisés automatiquement.

Les paramètres permettent aussi de saisir les coordonnées X/Y, de régler l’opacité entre 35 et 100 % et de verrouiller l’overlay. Une fois verrouillé, il ignore les clics afin de ne pas gêner le jeu ; repassez par les paramètres pour le déverrouiller.

Le contenu de chaque ligne est personnalisable avec les champs **Numéro**, **Nom**, **Classe**, **Alias** ou **Masqué**. La disposition par défaut place le numéro à gauche, le nom sur la première ligne et `classe · alias` sur la seconde. Lorsqu’un alias n’est pas renseigné, un tiret est affiché.

La largeur automatique est activée par défaut et suit le texte, les portraits et les icônes réellement visibles. Elle peut être désactivée dans les paramètres ou par un redimensionnement direct. Le portrait et l’icône de l’overlay peuvent chacun être activés ou masqués. Une fenêtre demandant l’attention passe en orange ; cet état est prioritaire sur la couleur du personnage actif.

Après un retrait de moniteur ou une modification de la disposition Windows, un overlay qui n’a plus de zone suffisamment visible est recentré sur l’écran le plus proche. Une position négative reste inchangée lorsqu’elle correspond encore à un moniteur placé à gauche ou au-dessus de l’écran principal.

Lorsque l’overlay ou le mode compact est visible, un changement manuel vers une autre fenêtre Dofus actualise également le personnage mis en évidence, sans déclencher de notification supplémentaire.

## Stream Deck

Le profil standard à 15 touches est organisé ainsi :

| Ligne | Touche 1 | Touche 2 | Touche 3 | Touche 4 | Touche 5 |
|---|---|---|---|---|---|
| 1 | Monter | Personnage 1 | Personnage 2 | Personnage 3 | Personnage 4 |
| 2 | Descendre | Personnage 5 | Personnage 6 | Personnage 7 | Personnage 8 |
| 3 | Lancer/afficher | Ignorer | Actualiser | Précédent | Suivant |

Pour chaque personnage, la position, le nom, la classe et l’alias peuvent être placés sur l’une des quatre lignes ou masqués. Par défaut :

- numéro ligne 1 ;
- nom ligne 2 ;
- classe ligne 3 ;
- alias ligne 4.

La disposition et la couleur de bordure sont mémorisées par personnage et le suivent lorsqu’il change de touche. Le portrait et l’icône définis dans l’application sont également repris par le plugin 0.7.0. Le fond et l’accent des touches suivent le thème actif de l’application ; leurs libellés courts suivent sa langue. Une demande d’attention utilise temporairement une bordure orange épaisse et affiche son rang `!1`, `!2`… dans la file.

L’option **Aperçu Stream Deck…** reproduit la disposition dans l’application et permet de tester le focus, la rotation, l’ordre, l’actualisation et l’exclusion temporaire. Les préférences visuelles avancées restent configurées dans Stream Deck.

## Diagnostic et journal

**Diagnostic…** affiche la version de l’application et son tag de publication, la version du plugin installé et fourni, l’état du pont local, la dernière communication Stream Deck, la dernière recherche de mise à jour, la détection des fenêtres et les dossiers de journaux.

Le journal principal est masqué par défaut. Activez **Afficher le journal** pour suivre les scans, changements de focus et erreurs. Avant de publier un rapport, retirez les noms ou chemins personnels si nécessaire et ne publiez jamais de donnée de connexion.
