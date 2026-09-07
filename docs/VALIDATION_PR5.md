# Validation du lot PR #5

Ce paquet est une compilation de test des changements de la PR #5, pas une release.
Les premiers paquets portaient le libellé bêta 4 ; les suivants portent bêta 5. Identifiez le paquet par le commit
dans BUILD_INFO.txt et par SHA256SUMS.txt. L’EXE portable utilise les mêmes réglages
que l’application installée ; sauvegardez votre configuration avant l’essai.

## Préparation — 5 minutes

1. Fermez l’application actuelle, y compris dans la zone de notification.
2. Depuis la version actuelle, exportez une sauvegarde complète, puis quittez-la.
3. Décompressez le paquet et commencez par DofusWindowManager.exe.
4. Notez le commit, Windows, le nombre de fenêtres, les écrans/échelles et le modèle Stream Deck éventuel.

## Vérification des deux corrections signalées

- Cliquer sur Rechercher une mise à jour : obtenir un résultat ou une erreur explicite
  sous environ 20 secondes, même si le suivi des fenêtres rencontre un problème.
- Choisir successivement Minimal, Équilibré et Complet dans Apparence, puis simuler :
  Minimal masque portraits/titre/flèches ; Équilibré montre les portraits et le titre ;
  Complet ajoute les icônes et flèches. Un aperçu déjà ouvert doit changer.
- Appliquer reste nécessaire pour enregistrer le formulaire. Simuler ne sauvegarde rien.

## Parcours prioritaire — environ 20 minutes

| Essai | Résultat attendu | Résultat observé |
| --- | --- | --- |
| Charger deux profils | Ordre, alias, overlay et Stream Deck changent ensemble | À tester |
| Fermer puis reconnecter le personnage 2 en mode fixe | Les autres emplacements restent stables ; le 2 retrouve sa place | À tester |
| Chiffre seul limité à Dofus, puis Bloc-notes | Changement en jeu, saisie normale dans le Bloc-notes | À tester |
| Recherche des paramètres après modification non appliquée | Navigation correcte, saisie conservée | À tester |
| Importer une sauvegarde puis annuler l’aperçu | Aucun changement des réglages ou profils | À tester |
| Changer profil/mode depuis la zone de notification | Coches et affichages synchronisés | À tester |
| Ancrer l’overlay puis débrancher/rebrancher son écran | Repli sur le principal puis retour sur l’écran enregistré | À tester |
| Quitter normalement puis relancer | Aucune alerte de fermeture anormale | À tester |
| Terminer le processus de test puis relancer | Proposition facultative d’un diagnostic local | À tester |

Sans second écran ou Stream Deck, notez « non testé ». Un test non réalisé
ne doit pas être déclaré réussi.

## Installation et mise à jour — après les essais portables

- Fermez l’EXE portable, lancez l’installateur de test et vérifiez la conservation des profils.
- Vérifiez les raccourcis de lancement et la désinstallation sans perte des données personnelles.
- La recherche de mise à jour utilise exclusivement les releases officielles.
  Tant qu’aucune release plus récente que la bêta 4 n’est disponible, le téléchargement
  guidé ne peut pas être validé de bout en bout avec ce paquet. Ne téléchargez pas
  une ancienne version en pensant tester ce lot ; notez ce parcours « à valider ».
- Les tests automatisés couvrent les erreurs de téléchargement, le SHA-256,
  l’annulation et la confirmation, mais ne remplacent pas cet essai réel.

## Retour à transmettre

Copiez le tableau avec « OK », « problème » ou « non testé », puis indiquez :
- commit testé ;
- configuration d’affichage et nombre de fenêtres ;
- étapes précises et résultat observé pour chaque problème.

Le ZIP anonymisé peut aider à analyser un problème. Relisez-le avant de le partager.
La checklist complète reste dans docs/BETA_TESTING.md.

## Critère avant publication

Les parcours de profil, de reconnexion, de raccourcis et de conservation des réglages
doivent avoir été essayés sans régression. Toute perte de données ou mauvaise cible
de focus doit être corrigée avant publication. Les autres parcours non testés doivent
être explicitement signalés dans le bilan.

## Fermeture depuis la zone de notification

- Choisir Quitter avec l’application visible puis réduite : vérifier la disparition du processus et de l’icône.
- Répéter avec le plugin Stream Deck connecté, puis avec Retro et la surveillance des invitations.
- Relancer : aucun avertissement de fermeture anormale après ces sorties.
- La croix conserve son comportement de réduction si cette option est activée.

## Bilan des retours avant bêta 5

L’utilisateur a indiqué que le reste du lot semblait fonctionner après avoir signalé
l’absence de retour de mise à jour et les aperçus identiques. Ces deux parcours ont
été corrigés et couverts par des tests. Le gel lors de Quitter depuis la zone de
notification a ensuite été corrigé ; le dernier paquet a été confirmé fonctionnel.

Validation automatique : 269 tests Python, 37 tests Stream Deck, Ruff, compilation
Windows de l’EXE et de l’installateur. La configuration matérielle détaillée et chaque
ligne du tableau n’ont pas fait l’objet d’un retour individuel : ne pas les considérer
comme validées séparément. Le téléchargement d’une prochaine release plus récente
reste à vérifier de bout en bout après publication.
