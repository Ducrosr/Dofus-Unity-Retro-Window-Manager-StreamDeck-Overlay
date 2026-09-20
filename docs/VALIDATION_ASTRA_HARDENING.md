# Validation — durcissement après audit Astra

## Référence

- Dépôt : `Ducrosr/Dofus-Unity-Retro-Window-Manager-StreamDeck-Overlay`
- Base auditée : `0610ef1669567212a708a4724bc62716798044b7`
- `main` et `v2.20.0-beta.6` ont été vérifiés sur ce même commit avant les modifications.
- Branche de travail : `fix/astra-audit-localized-hardening`
- Aucun tag, aucune release et aucun déploiement ne font partie de cette passe.

## Correctifs implémentés

1. Pompe Tk bornée et exception-safe ; chaque message est acquitté en `finally` et les scans sont finalisés même si leur application échoue.
2. Blocage des mutations après début de fermeture ; annulation des rotations différées et rejet explicite des commandes Stream Deck encore en file.
3. Propriété explicite des fenêtres OBS par `OverlayUI`, popup persistant, fermeture idempotente et séparation simulation/production.
4. Géométrie Tk négative absolue sous forme `+-N` et migration explicite de l’ancienne syntaxe relative au bord.
5. Reconnaissance Dofus centralisée et empreinte PID/classe/mode/processus ; revalidation pair-local de la cible juste avant focus.
6. Génération structurelle pour les scans et génération dédiée aux hooks WinEvent afin de rejeter tout résultat ou événement périmé.
7. Requêtes Stream Deck mutatrices à état atomique et échéance ; suppression du retry ambigu côté plugin, erreurs HTTP structurées.
8. Sauvegarde des réglages protégée contre les principaux invalides et les schémas futurs ; profils futurs non écrasables.
9. Watcher Retro lié au HWND + génération, invalidation sous verrou, arrêt des contrôles hors verrou et revalidation avant focus.

## Tests de régression ajoutés

Les sources de test couvrent notamment :

- exception de pompe suivie d’un message valide ;
- scan périmé et événement provenant d’un ancien hook ;
- shutdown avec commande Stream Deck en attente et rotation coalescée ;
- expiration d’une mutation avant son démarrage ;
- HWND réutilisé juste avant focus ;
- cycle de vie des fenêtres OBS, conservation du popup inactif et fermeture terminale idempotente ;
- géométrie négative absolue et migration de syntaxe historique ;
- test Tk natif Windows de position négative réellement obtenue ;
- timeout HTTP Stream Deck structuré et absence de second POST côté TypeScript ;
- principal de réglages invalide, backup valide et schémas futurs ;
- profil à schéma futur ;
- génération de captures Retro, fermeture périmée et arrêt hors verrou.

## État de validation automatisée

À ce stade, **aucun résultat de test n’est revendiqué pour cette branche** tant qu’une exécution réelle n’a pas été observée.

Commandes requises par les workflows :

### Python

```powershell
python -m pip install -r requirements.txt -r requirements-dev.txt
python -m unittest discover -s tests -v
python -m ruff check .
```

### Plugin Stream Deck

```powershell
Set-Location streamdeck-plugin
npm ci
npm test
npm run typecheck
npm run build:profiles
npm run build
npm run validate
npm run pack
Set-Location ..
```

### Packaging principal

```powershell
python build_exe.py
```

### Packaging Retro facultatif

```powershell
python build_exe.py --with-popup
& ".\.venv-build-popup\Scripts\python.exe" -m pip show windows-capture
```

La version exacte de `windows-capture` doit être consignée après cette dernière commande. La plage déclarée reste `>=1.5.0,<2` et n’est pas ajoutée au build principal.

## Validation réelle requise

Les tests automatisés, y compris ceux qui simulent Win32/OBS, ne valident pas le comportement réel de Windows.

Restent à vérifier sur la machine cible :

- focus déjà actif, minimisé et refusé ;
- Combobox pendant scan et arrêt sous rafale ;
- 0/1/8 clients Unity et Retro, reconnexion et changement de mode ;
- ordre, profils, emplacements fixes, alertes et hotkeys ;
- sources OBS déjà configurées pendant palette/verrouillage/dimensions/mode/popup rapide ;
- backend Stream Deck absent/redémarré, requête retardée, cible disparue et privilèges différents ;
- écran à gauche/au-dessus, déconnexion et DPI 100/125/150/200 % et mixtes ;
- watcher Retro avec la version exacte de `windows-capture` résolue par le build facultatif.

## Critère de fusion

Avant fusion, consigner ici :

- nombre exact de tests Python exécutés/réussis ;
- résultat Ruff ;
- nombre exact de tests TypeScript exécutés/réussis ;
- résultat typecheck/build/validate/pack ;
- résultat du packaging principal ;
- résultat du packaging facultatif si celui-ci est testé ;
- version exacte de `windows-capture` pour le build facultatif ;
- les essais Windows/Dofus/OBS réellement effectués séparément des tests mockés.

Un test non exécuté doit rester indiqué comme **non testé**.
