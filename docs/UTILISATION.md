# Guide d’utilisation

## Vue d’ensemble

L’interface principale comporte deux tableaux et quatre groupes de commandes :

- **Fenêtres gérées** : personnages inclus dans la rotation ;
- **Fenêtres ignorées** : personnages toujours détectés mais exclus de Suivant/Précédent ;
- **Navigation** : rotation et changement d’ordre ;
- **Fenêtre sélectionnée** : alias et statut ignoré ;
- **Profils** : enregistrement et restauration d’une formation ;
- **Application** : mode Unity/Retro, paramètres, aperçu Stream Deck, diagnostic, sauvegarde et installation du plugin.

La barre verticale à droite conserve l’accès aux commandes lorsque la fenêtre est courte ou que Windows utilise une mise à l’échelle élevée. La molette garde la priorité au tableau ou au journal lorsqu’elle se trouve au-dessus.

## Détecter les personnages

1. Ouvrez les clients Dofus.
2. Sélectionnez Unity ou Retro dans **Version de Dofus**.
3. Cliquez sur **Rafraîchir**.
4. Contrôlez le nom et la classe dans le tableau.

Le mode Unity cible les fenêtres Unity. Le mode Retro combine la classe de fenêtre Chromium et le marqueur Dofus Retro du titre afin d’éviter les faux positifs provenant d’autres applications Chromium.

## Passer d’un personnage à l’autre

- **F5** ou **Suivant** active le personnage suivant ;
- **F6** ou **Précédent** active le personnage précédent ;
- un clic sur une touche Personnage du Stream Deck active directement sa fenêtre.

La ligne active est mise en évidence dans l’application. Le bouton Stream Deck actif utilise un état vert.

## Modifier l’ordre

Trois méthodes sont disponibles :

- glisser une ligne dans **Fenêtres gérées** ;
- sélectionner une ligne puis utiliser **Monter** ou **Descendre** ;
- utiliser les touches Monter/Descendre du Stream Deck.

Pendant un glisser-déposer, la destination est surlignée et la barre d’état précise si le dépôt se fera avant ou après. L’ordre est immédiatement transmis au Stream Deck : les personnages changent donc de touche pour rester cohérents avec la liste.

## Alias

Sélectionnez un personnage puis choisissez **Modifier l’alias…**. L’alias possède sa propre colonne et ne remplace ni le nom ni la classe.

Un alias court améliore la lecture sur le Stream Deck, notamment :

- Terre, Feu, Eau ou Air ;
- Mineur, Paysan ou Alchimiste ;
- un rôle d’équipe ;
- une indication distinguant deux personnages de même classe.

Supprimer le contenu rend l’alias vierge. La touche Stream Deck affiche alors un tiret lorsque la ligne Alias est visible.

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

## Paramètres et zone de notification

Les paramètres permettent notamment de personnaliser les raccourcis, l’actualisation, le thème, la réduction dans la zone de notification et le démarrage avec Windows.

Par défaut, fermer la fenêtre réduit l’application dans la zone de notification pour conserver les raccourcis et le pont Stream Deck. Le menu de l’icône permet d’afficher, d’actualiser ou de quitter réellement l’application.

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

La disposition et la couleur de bordure sont mémorisées par personnage et le suivent lorsqu’il change de touche.

L’option **Aperçu Stream Deck…** reproduit la disposition dans l’application et permet de tester le focus, la rotation, l’ordre, l’actualisation et l’exclusion temporaire. Les préférences visuelles avancées restent configurées dans Stream Deck.

## Diagnostic et journal

**Diagnostic…** affiche la version de l’application, la version du plugin installé et fourni, l’état du pont local, la dernière communication Stream Deck, la détection des fenêtres et les dossiers de journaux.

Le journal principal est masqué par défaut. Activez **Afficher le journal** pour suivre les scans, changements de focus et erreurs. Avant de publier un rapport, retirez les noms ou chemins personnels si nécessaire et ne publiez jamais de donnée de connexion.
