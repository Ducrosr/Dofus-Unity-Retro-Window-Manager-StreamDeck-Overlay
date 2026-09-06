# Validation du lot PR #5

Ce paquet est une compilation de test des changements de la PR #5, pas une release.
Les libellés de version restent ceux de la bêta 4 : identifiez le paquet par le commit
dans BUILD_INFO.txt et par SHA256SUMS.txt. L’EXE portable utilise les mêmes réglages
que l’application installée ; sauvegardez votre configuration avant l’essai.

## Préparation — 5 minutes

1. Fermez l’application actuelle, y compris dans la zone de notification.
2. Depuis la version actuelle, exportez une sauvegarde complète, puis quittez-la.
3. Décompressez le paquet et commencez par DofusWindowManager.exe.
4. Notez le commit, Windows, le nombre de fenêtres, les écrans/échelles et le modèle Stream Deck éventuel.

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
